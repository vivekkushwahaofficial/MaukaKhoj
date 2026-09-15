from pydantic import BaseModel, Field


class Experience(BaseModel):
    years: float = Field(default=0.0, ge=0.0)
    current_title: str | None = None


class Education(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    graduation_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
    )
    is_running: bool = False


class Profile(BaseModel):
    name: str = Field(min_length=1)

    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    experience: Experience = Field(default_factory=Experience)
    education: Education = Field(default_factory=Education)

    locations: list[str] = Field(default_factory=list)
    remote_preferences: list[str] = Field(default_factory=list)
    employment_preferences: list[str] = Field(default_factory=list)

    domains: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
