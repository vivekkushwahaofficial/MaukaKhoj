from abc import ABC, abstractmethod

from app.ai.semantic.models import (
    SemanticJobAnalysisRequest,
    SemanticJobAnalysisResponse,
)


class SemanticJobAnalyzer(ABC):
    """Interface for extracting semantic job evidence."""

    @abstractmethod
    def analyze(
        self,
        request: SemanticJobAnalysisRequest,
    ) -> SemanticJobAnalysisResponse:
        """Analyze jobs and return structured semantic evidence."""
        raise NotImplementedError
