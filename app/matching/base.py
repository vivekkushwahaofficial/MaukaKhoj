from abc import ABC, abstractmethod

from app.domain.job import Job
from app.domain.profile import Profile
from app.matching.models import MatchResult


class JobProfileMatcher(ABC):
    """Base contract for matching a canonical job against a profile."""

    @abstractmethod
    def match(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchResult:
        """Return structured matching evidence for a job and profile."""

        raise NotImplementedError
