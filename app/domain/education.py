from enum import Enum
from pydantic import BaseModel


class EducationRequirementStatus(str, Enum):
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"


class EducationRequirement(BaseModel):
    status: EducationRequirementStatus = EducationRequirementStatus.UNKNOWN

    degree: str | None = None
    field: str | None = None

    minimum_graduation_year: int | None = None
    maximum_graduation_year: int | None = None

    accepts_current_students: bool | None = None
