import json
from datetime import timedelta

from krules_core.providers import subject_factory
from krules_core.subject.storaged_subject import Subject
from pydantic import BaseModel, field_validator, field_serializer


class Interval(BaseModel):
    interval: timedelta
    freq: str
    name: str

    @field_serializer('interval')
    def serialize_timedelta(self, td: timedelta) -> float:
        return td.total_seconds()

    @field_validator('interval', mode='before')
    @classmethod
    def parse_timedelta(cls, value: float | timedelta) -> timedelta:
        if isinstance(value, (int, float)):
            return timedelta(seconds=value)
        if isinstance(value, timedelta):
            return value
        raise ValueError("Invalid value for interval")

class Symbol(BaseModel):
    _subject: Subject | None = None
    name: str
    category: str
    provider: str

    def get_subject(self, **kwargs) -> Subject:
        return subject_factory(f"symbol:{self.provider.lower()}:{self.category.lower()}:{self.name.lower()}", **kwargs)
