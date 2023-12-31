from datetime import timedelta

from krules_core.providers import subject_factory
from pydantic import BaseModel
from krules_core.subject.storaged_subject import Subject


class Interval(BaseModel):
    interval: timedelta
    freq: str  # https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.round.html
    name: str


class Symbol(BaseModel):
    name: str
    category: str
    provider: str

    def get_subject(self) -> Subject:
        return subject_factory(f"symbol:{self.provider}:{self.category}:{self.name.lower()}")
