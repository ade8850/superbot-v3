from datetime import timedelta
from typing import Any

from krules_core.providers import subject_factory
from pydantic import BaseModel
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

    def get_subject(self) -> Subject:
        if "_subject" not in self or self._subject is None:
            self._subject = subject_factory(f"symbol:{self.provider}:{self.category}:{self.name.lower()}")
        return self._subject
