"""JobHunt reference rules used by the MaukaKhoj benchmark."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

JOBHUNT_COMPANIES = (
    ("lever", "gohighlevel", "HighLevel"),
    ("lever", "shopback-2", "ShopBack"),
    ("lever", "geocomply-2", "GeoComply"),
    ("lever", "drivetrain", "Drivetrain"),
    ("ashby", "openai", "OpenAI"),
    ("ashby", "cohere", "Cohere"),
    ("ashby", "notion", "Notion"),
    ("ashby", "super.com", "Super.com"),
    ("greenhouse", "cloudflare", "Cloudflare"),
    ("greenhouse", "databricks", "Databricks"),
    ("greenhouse", "stripe", "Stripe"),
    ("greenhouse", "reddit", "Reddit"),
    ("lever", "levelai", "Level AI"),
    ("greenhouse", "singlestore", "SingleStore"),
    ("lever", "resilinc", "Resilinc"),
    ("lever", "zimperium", "Zimperium"),
    ("lever", "3pillarglobal", "3Pillar Global"),
    ("ashby", "ema", "Ema"),
    ("ashby", "brooklyn-health", "Brooklyn Health"),
    ("ashby", "savvymoney", "SavvyMoney"),
    ("smartrecruiters", "TechMahindraLtd1", "Tech Mahindra"),
    ("smartrecruiters", "Nagarro1", "Nagarro"),
)

INCLUDE_TITLE_PATTERNS = (
    r"\bsoftware\s+engineer\b",
    r"\bsoftware\s+developer\b",
    r"\bsoftware\s+development\s+engineer\b",
    r"\bsde\b",
    r"\bbackend\s+engineer\b",
    r"\bbackend\s+developer\b",
    r"\bback-end\s+engineer\b",
    r"\bback-end\s+developer\b",
    r"\b(engineer|developer)\b.*\bbackend\b",
    r"\b(engineer|developer)\b.*\bback-end\b",
    r"\bjava\b.*\b(engineer|developer)\b",
    r"\b(engineer|developer)\b.*\bjava\b",
    r"\bfull[\s-]?stack\s+engineer\b",
    r"\bfull[\s-]?stack\s+developer\b",
    r"\b(engineer|developer)\b.*\bfull[\s-]?stack\b",
    r"\bassociate\s+software\s+engineer\b",
    r"\bassociate\s+software\s+developer\b",
    r"\bassociate\s+engineer\b",
    r"\bassociate\s+developer\b",
    r"\bentry[\s-]?level\s+software\s+engineer\b",
    r"\bentry[\s-]?level\s+software\s+developer\b",
    r"\bjunior\s+software\s+engineer\b",
    r"\bjunior\s+software\s+developer\b",
    r"\bjunior\s+backend\s+engineer\b",
    r"\bjunior\s+backend\s+developer\b",
    r"\bjunior\s+java\s+developer\b",
    r"\bjunior\s+java\s+engineer\b",
    r"\bjunior\s+full[\s-]?stack\s+developer\b",
    r"\bjunior\s+full[\s-]?stack\s+engineer\b",
    r"\bsoftware\s+engineer\s+i\b",
    r"\bsoftware\s+engineer\s+1\b",
    r"\bsoftware\s+developer\s+i\b",
    r"\bsoftware\s+developer\s+1\b",
    r"\bgraduate\s+software\s+engineer\b",
    r"\bgraduate\s+software\s+developer\b",
    r"\bgraduate\s+engineer\b",
    r"\bgraduate\s+developer\b",
    r"\bgraduate\s+engineer\s+trainee\b",
    r"\bgraduate\s+trainee\b",
    r"\btrainee\s+software\s+engineer\b",
    r"\btrainee\s+software\s+developer\b",
    r"\btrainee\s+engineer\b",
    r"\btrainee\s+developer\b",
    r"\bsoftware\s+engineering\s+intern\b",
    r"\bsoftware\s+engineer\s+intern\b",
    r"\bsoftware\s+developer\s+intern\b",
    r"\bsoftware\s+development\s+intern\b",
    r"\bbackend\s+engineer\s+intern\b",
    r"\bbackend\s+developer\s+intern\b",
    r"\bjava\s+engineer\s+intern\b",
    r"\bjava\s+developer\s+intern\b",
    r"\bfull[\s-]?stack\s+engineer\s+intern\b",
    r"\bfull[\s-]?stack\s+developer\s+intern\b",
    r"\bengineering\s+intern\b",
    r"\bsoftware\s+intern\b",
    r"\bintern\b",
    r"\bplatform\s+engineer\b",
    r"\bplatform\s+developer\b",
    r"\bcloud\s+engineer\b",
    r"\bcloud\s+developer\b",
    r"\bsite\s+reliability\s+engineer\b",
    r"\bsre\b",
)

EXCLUDE_TITLE_PATTERNS = (
    r"\b(senior|sr\.?)\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\bdistinguished\b",
    r"\bfellow\b",
    r"\blead\b",
    r"\btech\s+lead\b",
    r"\bteam\s+lead\b",
    r"\barchitect\b",
    r"\bmanager\b",
    r"\bmanagement\b",
    r"\bdirector\b",
    r"\bvp\b",
    r"\bvice\s+president\b",
    r"\bhead\s+of\b",
    r"\bchief\b",
    r"\bcto\b",
    r"\bsales\b",
    r"\baccount\s+executive\b",
    r"\bmarketing\b",
    r"\brecruit(ment|er)?\b",
    r"\bsupport\b",
    r"\bcustomer\s+success\b",
    r"\bdesigner\b",
    r"\bios\s+(engineer|developer)\b",
    r"\bandroid\s+(engineer|developer)\b",
    r"\bmobile\s+(engineer|developer)\b",
    r"\bgame\s+(engineer|developer)\b",
    r"\bdata\s+scientist\b",
    r"\bmachine\s+learning\s+scientist\b",
    r"\bresearch\s+scientist\b",
)

LOCATION_TERMS = (
    "india",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "pune",
    "mumbai",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "chennai",
    "kolkata",
    "ahmedabad",
    "bhopal",
)

REMOTE_HINTS = (
    "remote",
    "anywhere",
    "work from home",
    "wfh",
    "distributed",
)


@dataclass(frozen=True)
class JobHuntRuleResult:
    title_allowed: bool
    location_allowed: bool
    freshness_allowed: bool

    @property
    def eligible(self) -> bool:
        return (
            self.title_allowed
            and self.location_allowed
            and self.freshness_allowed
        )


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _parse_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def evaluate_jobhunt_rules(
    *,
    title: str,
    location: str,
    posted_at: datetime | None,
    max_age_days: int = 30,
) -> JobHuntRuleResult:
    title_allowed = (
        _matches(INCLUDE_TITLE_PATTERNS, title)
        and not _matches(EXCLUDE_TITLE_PATTERNS, title)
    )

    location_text = f"{location} {title}".lower()
    location_allowed = (
        any(term in location_text for term in LOCATION_TERMS)
        or any(term in location_text for term in REMOTE_HINTS)
    )

    freshness_allowed = True

    parsed_posted_at = _parse_datetime(posted_at)
    if parsed_posted_at is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        freshness_allowed = parsed_posted_at >= cutoff

    return JobHuntRuleResult(
        title_allowed=title_allowed,
        location_allowed=location_allowed,
        freshness_allowed=freshness_allowed,
    )
