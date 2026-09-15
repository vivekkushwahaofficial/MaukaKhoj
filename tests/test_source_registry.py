from typing import Any

import pytest

from app.domain.job import Job
from app.normalization.base import JobNormalizer
from app.sources.base import JobSourceAdapter
from app.sources.registry import SourceRegistry


class FakeSourceAdapter(JobSourceAdapter):
    @property
    def source_name(self) -> str:
        return "fake"

    def fetch_jobs(self) -> list[dict[str, Any]]:
        return []


class FakeNormalizer(JobNormalizer):
    def normalize(self, raw_job: dict[str, Any]) -> Job:
        raise NotImplementedError


def build_fake_source(
    config: dict[str, Any],
) -> tuple[JobSourceAdapter, JobNormalizer]:
    return FakeSourceAdapter(), FakeNormalizer()


def test_registry_builds_registered_source() -> None:
    registry = SourceRegistry()
    registry.register("fake", build_fake_source)

    adapter, normalizer = registry.build(
        "fake",
        {"example": "value"},
    )

    assert isinstance(adapter, FakeSourceAdapter)
    assert isinstance(normalizer, FakeNormalizer)


def test_registry_normalizes_source_name() -> None:
    registry = SourceRegistry()
    registry.register("fake", build_fake_source)

    adapter, normalizer = registry.build(
        "  FAKE  ",
        {},
    )

    assert isinstance(adapter, FakeSourceAdapter)
    assert isinstance(normalizer, FakeNormalizer)


def test_registry_rejects_empty_source_name() -> None:
    registry = SourceRegistry()

    with pytest.raises(ValueError, match="Source name cannot be empty"):
        registry.register("   ", build_fake_source)


def test_registry_rejects_empty_build_source_name() -> None:
    registry = SourceRegistry()

    with pytest.raises(ValueError, match="Source name cannot be empty"):
        registry.build("   ", {})


def test_registry_rejects_unknown_source() -> None:
    registry = SourceRegistry()

    with pytest.raises(
        ValueError,
        match="No source builder registered for source 'unknown'",
    ):
        registry.build("unknown", {})
