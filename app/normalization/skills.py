import re
from collections.abc import Mapping, Sequence


class SkillExtractor:
    """Extract canonical technical skills using a configured vocabulary."""

    def __init__(
        self,
        skill_aliases: Mapping[str, Sequence[str]],
    ) -> None:
        if not skill_aliases:
            raise ValueError("Skill aliases cannot be empty.")

        self._skill_aliases = self._validate_aliases(skill_aliases)

    def extract(self, text: str | None) -> list[str]:
        """Extract canonical skills from text in deterministic order."""
        if not text:
            return []

        normalized_text = text.lower()
        extracted: list[str] = []

        for canonical_skill, aliases in self._skill_aliases.items():
            if any(self._contains_term(normalized_text, alias) for alias in aliases):
                extracted.append(canonical_skill)

        return extracted

    @staticmethod
    def _validate_aliases(
        skill_aliases: Mapping[str, Sequence[str]],
    ) -> dict[str, tuple[str, ...]]:
        """Validate and normalize the configured skill vocabulary."""
        validated: dict[str, tuple[str, ...]] = {}

        for canonical_skill, aliases in skill_aliases.items():
            if not isinstance(canonical_skill, str) or not canonical_skill.strip():
                raise ValueError("Skill canonical names must be non-empty strings.")

            if isinstance(aliases, str) or not isinstance(aliases, Sequence):
                raise ValueError(
                    f"Aliases for skill '{canonical_skill}' must be a sequence."
                )

            normalized_aliases = tuple(
                alias.strip().lower()
                for alias in aliases
                if isinstance(alias, str) and alias.strip()
            )

            if not normalized_aliases:
                raise ValueError(
                    f"Skill '{canonical_skill}' must have at least one alias."
                )

            validated[canonical_skill.strip()] = normalized_aliases

        return validated

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        """Check whether a skill term occurs as a standalone term."""
        pattern = rf"(?<!\w){re.escape(term.lower())}(?!\w)"
        return re.search(pattern, text) is not None
