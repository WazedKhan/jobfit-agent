from typing import Literal

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    text: str
    options: list[str]


class JobPost(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str
    work_mode: Literal["remote", "hybrid", "onsite"]
    open_to_bd: bool | None
    visa_support: bool | None
    years_required: int | None
    must_have: list[Requirement]
    nice_to_have: list[Requirement]
    salary: str | None
