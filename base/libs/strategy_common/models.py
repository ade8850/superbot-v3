import os
from datetime import datetime
from typing import List, Dict, Any, Literal

from krules_core.providers import subject_factory
from krules_core.subject.storaged_subject import Subject
from pydantic import BaseModel, Field, field_validator, model_validator

from app_common.models import Symbol


class StrategyConfig(BaseModel):
    strategy: str = Field(..., description="The name of the strategy.")
    groups: List[str] = Field([], description="The groups to which the strategy applies.")
    kwargs: Dict[str, Any] = Field({}, description="Additional keyword arguments for the strategy.")


class SessionConfig(BaseModel):
    strategies: List[StrategyConfig] = Field(..., description="List of strategies for the session.")


class LimitConfig(BaseModel):
    name: str | None = Field(None,
                             description="Name of the limit. It matches the property on the subject, can be used as name in limit strategy")
    follows: str | None = Field(None, description="If set, follows variations of this indicator")
    reset_on_action: Literal["if_none", "always", "never"] = Field("if_none", description="Reset limit on action")
    engage: Literal["always", "never", "on_action"] = Field("always", description="Weather to engage the follow")

    @model_validator(mode='after')
    def set_name(self) -> 'LimitConfig':
        if self.name is None or self.name == '':
            if self.follows:
                self.name = f"limit_{self.follows}"
            else:
                raise ValueError("Either 'name' or 'follows' must be provided")
        return self


class Strategy(BaseModel):
    _subject: Subject | None = None
    name: str = Field(..., description="The name of the strategy.", validation_alias="strategy_name",
                      default_factory=lambda: os.environ['APP_NAME'].replace("strategy-", "", 1).lower())
    leverage: float = Field(..., description="Leverage")
    fee: float = Field(0.00055, description="Fee", validation_alias="taker_fee")
    isMockStrategy: bool = Field(..., validation_alias="is_mock_strategy",
                                 description="This is a mock strategy for testing purposes")
    # resetLimitOnExit: bool = Field(..., validation_alias="reset_limit_on_exit",
    #                                description="Set limit to None when exiting strategy")
    symbol: Symbol = Field(..., description="The symbol to use")

    # outerLimitFollows: str | None = Field(validation_alias="outer_limit_follows",
    #                                       description="Move the outer limit following this indicator",
    #                                       default=None)

    session: SessionConfig = Field(..., description="Session configuration including strategies.")

    limits: List[LimitConfig] = Field([], description="Limits")

    class Config:
        use_enum_values = True

    def get_subject(self) -> Subject:
        #if "_subject" not in self or self._subject is None:
        return subject_factory(f"strategy|{self.symbol.provider}|{self.name}", use_cache_default=False)
        #return self._subject

    def publish(self, **kwargs):
        from celery_app.tasks import cm_publish
        if "_last_update" not in kwargs:
            kwargs["_last_update"] = f"dt|{datetime.utcnow().isoformat()}"
        cm_publish.delay(
            group=f"strategies.{self.symbol.provider}",
            entity=self.name,
            properties=kwargs
        )

    def position(self) -> 'Position':
        return Position(strategy=self)


class Position(BaseModel):
    strategy: Strategy

    def publish(self, **kwargs):
        from celery_app.tasks import cm_publish
        if "_last_update" not in kwargs:
            kwargs["_last_update"] = f"dt|{datetime.utcnow().isoformat()}"
        cm_publish.delay(
            group=f"strategies.{self.strategy.symbol.provider}.positions",
            entity=self.strategy.name,
            properties=kwargs
        )
