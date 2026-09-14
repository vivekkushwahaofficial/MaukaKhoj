from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class RemoteType(str, Enum):
    INDIA_REMOTE = "INDIA_REMOTE"
    COUNTRY_REMOTE = "COUNTRY_REMOTE"
    REGION_REMOTE = "REGION_REMOTE"
    WORLDWIDE_REMOTE = "WORLDWIDE_REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    UNKNOWN = "UNKNOWN"


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    TEMPORARY = "TEMPORARY"
    UNKNOWN = "UNKNOWN"


class ExperienceLevel(str, Enum):
    INTERN = "INTERN"
    ENTRY_LEVEL = "ENTRY_LEVEL"
    JUNIOR = "JUNIOR"
    MID_LEVEL = "MID_LEVEL"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    UNKNOWN = "UNKNOWN"


class Job(BaseModel):
    job_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_job_id: str | None = None

    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)

    location: str | None = None
    remote_type: RemoteType = RemoteType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN

    skills: list[str] = Field(default_factory=list)
    salary: str | None = None

    posted_at: datetime | None = None
    updated_at: datetime | None = None

    application_url: HttpUrl
    company_url: HttpUrl | None = None
    source_url: HttpUrl | None = None
