from abc import ABC, abstractmethod

from app.domain.job import Job
from app.domain.profile import Profile
from app.explanation.models import JobExplanation
from app.matching.models import MatchResult
from app.scoring.models import JobScore


class JobExplainer(ABC):
    """Base contract for generating deterministic job explanations."""

    @abstractmethod
    def explain(
        self,
        job: Job,
        profile: Profile,
        match_result: MatchResult,
        job_score: JobScore,
    ) -> JobExplanation:
        """Return human-readable evidence explaining the job match."""

        raise NotImplementedError
