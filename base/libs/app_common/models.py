import os
from datetime import timedelta
from typing import Any

from krules_core.providers import subject_factory
from pydantic import BaseModel, Field
from krules_core.subject.storaged_subject import Subject


class Interval(BaseModel):
    interval: timedelta
    freq: str  # https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.round.html
    name: str


class Symbol(BaseModel):
    _subject: Subject | None = None
    name: str
    category: str
    provider: str

    def get_subject(self, **kwargs) -> Subject:
        if "_subject" not in self or self._subject is None:
            self._subject = subject_factory(f"symbol:{self.provider.lower()}:{self.category.lower()}:{self.name.lower()}", **kwargs)
        return self._subject


class Strategy(BaseModel):
    name: str = Field(..., description="The name of the strategy.", validation_alias="strategy_name",
                      default_factory=lambda: os.environ['APP_NAME'].replace("strategy-", "", 1).lower())
    leverage: float = Field(..., description="Leverage")
    fee: float = Field(0.00055, description="Fee", validation_alias="taker_fee")
    isMockStrategy: bool = Field(..., validation_alias="is_mock_strategy",
                                 description="This is a mock strategy for testing purposes")
    resetLimitOnExit: bool = Field(...,validation_alias="reset_limit_on_exit",
                                   description="Set limit to None when exiting strategy")
    symbol: Symbol = Field(..., description="The symbol to use")

    def get_subject(self) -> Subject:
        return subject_factory(f"strategy|{self.symbol.provider}|{self.name}", use_cache_default=False)

    def publish(self, **kwargs):
        from celery_app.tasks import cm_publish
        cm_publish.delay(
            group=f"strategies.{self.symbol.provider}",
            entity=self.name,
            properties=kwargs
        )
