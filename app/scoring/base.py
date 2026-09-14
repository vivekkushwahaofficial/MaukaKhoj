from abc import ABC, abstractmethod

from app.domain.job import Job
from app.domain.profile import Profile
from app.matching.models import MatchResult
from app.scoring.models import JobScore


class JobScorer(ABC):
    """Base contract for scoring a matched job against a profile."""

    @abstractmethod
    def score(
        self,
        job: Job,
        profile: Profile,
        match_result: MatchResult,
    ) -> JobScore:
        """Return a deterministic 0-100 score with supporting evidence."""

        raise NotImplementedError
