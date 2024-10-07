import os

from krules_core.providers import subject_factory
from krules_core.subject.storaged_subject import Subject
from pydantic import BaseModel, Field

from app_common.models import Symbol


class Strategy(BaseModel):
    _subject: Subject | None = None
    name: str = Field(..., description="The name of the strategy.", validation_alias="strategy_name",
                      default_factory=lambda: os.environ['APP_NAME'].replace("strategy-", "", 1).lower())
    leverage: float = Field(..., description="Leverage")
    fee: float = Field(0.00055, description="Fee", validation_alias="taker_fee")
    isMockStrategy: bool = Field(..., validation_alias="is_mock_strategy",
                                 description="This is a mock strategy for testing purposes")
    resetLimitOnExit: bool = Field(...,validation_alias="reset_limit_on_exit",
                                   description="Set limit to None when exiting strategy")
    symbol: Symbol = Field(..., description="The symbol to use")

    outerLimitFollows: str | None = Field(validation_alias="outer_limit_follows",
                                          description="Move the outer limit following this indicator",
                                          default=None)

    def get_subject(self) -> Subject:
        #if "_subject" not in self or self._subject is None:
        return subject_factory(f"strategy|{self.symbol.provider}|{self.name}", use_cache_default=False)
        #return self._subject

    def publish(self, **kwargs):
        from celery_app.tasks import cm_publish
        cm_publish.delay(
            group=f"strategies.{self.symbol.provider}",
            entity=self.name,
            properties=kwargs
        )
