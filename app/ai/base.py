from abc import ABC, abstractmethod

from app.ai.models import AIEnhancementRequest, AIEnhancementResponse


class JobAIEnhancer(ABC):
    """Interface for optional AI enhancement of ranked job results."""

    @abstractmethod
    def enhance(
        self,
        request: AIEnhancementRequest,
    ) -> AIEnhancementResponse:
        """Enhance ranked jobs with human-readable AI insights."""
        raise NotImplementedError