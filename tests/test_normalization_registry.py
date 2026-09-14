from typing import Any

import pytest

from app.domain.job import Job
from app.normalization.base import JobNormalizer
from app.normalization.registry import NormalizationRegistry


class FakeNormalizer(JobNormalizer):
    """Test normalizer implementation."""

    def normalize(self, raw_job: dict[str, Any]) -> Job:
        raise NotImplementedError


def test_register_and_get_normalizer() -> None:
    registry = NormalizationRegistry()
    normalizer = FakeNormalizer()

    registry.register("lever", normalizer)

    assert registry.get("lever") is normalizer


def test_source_lookup_is_case_insensitive() -> None:
    registry = NormalizationRegistry()
    normalizer = FakeNormalizer()

    registry.register("Lever", normalizer)

    assert registry.get("LEVER") is normalizer


def test_contains_returns_true_for_registered_source() -> None:
    registry = NormalizationRegistry()

    registry.register("lever", FakeNormalizer())

    assert registry.contains("lever") is True


def test_contains_returns_false_for_unknown_source() -> None:
    registry = NormalizationRegistry()

    assert registry.contains("lever") is False


def test_empty_source_is_rejected() -> None:
    registry = NormalizationRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("", FakeNormalizer())


def test_unknown_source_is_rejected() -> None:
    registry = NormalizationRegistry()

    with pytest.raises(
        ValueError,
        match="No job normalizer registered",
    ):
        registry.get("lever")
