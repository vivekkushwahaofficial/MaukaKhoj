# MaukaKhoj

> **Personalized Job Discovery Intelligence Engine**

MaukaKhoj is an independent, profile-driven job discovery intelligence engine that discovers legitimate software and technology opportunities, normalizes and validates job data, removes duplicates, filters unsuitable roles, matches jobs against user profiles, ranks relevant opportunities, and explains why they are recommended.

MaukaKhoj is **not an auto-apply bot**.

Users always review and submit applications manually.

---

## What MaukaKhoj Does

MaukaKhoj is designed to answer:

> **Among all legitimately discoverable jobs, which opportunities are genuinely worth this user's attention, and why?**

The system focuses on:

* Reliable job discovery
* Profile-aware matching
* Explainable ranking
* Duplicate prevention
* Remote-location classification
* Job freshness
* Source reliability
* Optional AI-assisted analysis

The goal is **quality personalized job discovery**, not maximum scraping or maximum job count.

---

## Core Architecture

```text
Job Sources
    ↓
Source Adapters
    ↓
Raw Jobs
    ↓
Normalization
    ↓
Validation
    ↓
Deduplication
    ↓
Hard Filters
    ↓
Profile Matching
    ↓
Scoring / Ranking
    ↓
Explanation
    ↓
Digest / API / UI
```

---

## Design Principles

MaukaKhoj follows a few core engineering principles:

* **Profile-driven** — user preferences and skills are represented as data, not hardcoded logic.
* **Source-agnostic** — source-specific fetching and parsing stays inside adapters.
* **Deterministic** — filtering, matching, scoring, and ranking are predictable and reproducible.
* **Explainable** — recommendations should provide understandable reasons.
* **Quality-first** — irrelevant jobs are removed before ranking.
* **Failure-isolated** — failure of one source should not stop the entire discovery pipeline.
* **Privacy-conscious** — credentials and personal configuration are never committed to the repository.
* **Manual application** — MaukaKhoj discovers and recommends jobs; users decide whether and how to apply.

---

## Job Intelligence Pipeline

Each discovered job moves through a controlled pipeline:

```text
Raw Job
   ↓
Normalization
   ↓
Canonical Job
   ↓
Validation
   ↓
Deduplication
   ↓
Hard Eligibility Filters
   ↓
Profile Relevance
   ↓
Deterministic Score
   ↓
Ranking
   ↓
Explanation
   ↓
Digest
```

This separation keeps source-specific logic independent from the core job intelligence system.

---

## Matching & Ranking

Jobs are evaluated against a user profile using multiple dimensions:

* Role relevance
* Skill compatibility
* Experience level
* Location compatibility
* Remote eligibility
* Employment type
* Job freshness
* Domain relevance

The system produces a deterministic **0–100 match score** and ranks eligible opportunities using consistent tie-breaking rules.

Recommendations are accompanied by explanations so users can understand **why a job matched their profile**.

---

## Job Sources

MaukaKhoj is designed to support multiple categories of job sources:

### Job Boards

* Naukri
* Indeed
* LinkedIn
* Foundit
* Internshala
* Cutshort
* Wellfound

### ATS Platforms

* Lever
* Greenhouse
* Ashby
* SmartRecruiters
* Workable

### Company Career Pages

* TCS
* Infosys
* Wipro
* HCLTech
* Startups and other company career sites

Source support is designed to remain modular so additional adapters can be introduced without changing the core intelligence pipeline.

---

## Remote Job Classification

MaukaKhoj distinguishes between different types of remote opportunities rather than treating every job containing "remote" as equivalent.

Supported classifications include:

```text
INDIA_REMOTE
COUNTRY_REMOTE
REGION_REMOTE
WORLDWIDE_REMOTE
HYBRID
ONSITE
UNKNOWN
```

This allows the system to apply location eligibility more accurately.

---

## Job Freshness

Job freshness is treated as part of job quality.

Jobs can be rejected when they exceed the configured freshness threshold, while jobs with unavailable posting dates can remain eligible rather than being incorrectly discarded.

Example configuration:

```yaml
freshness:
  enabled: true
  max_age_days: 30
```

---

## Configuration-Driven Design

MaukaKhoj keeps user-specific preferences and source configuration separate from application logic.

For example:

```text
Profile
   ├── Target roles
   ├── Skills
   ├── Experience
   ├── Education
   ├── Location
   └── Preferences

Source Configuration
   ├── Source
   ├── Account / Company
   └── Source-specific settings
```

This makes the project easier to customize and fork for different users.

---

## Source Registry

MaukaKhoj uses a source registry to keep source construction separate from the main application composition.

```text
Source Configuration
        ↓
   Source Registry
        ↓
 ┌───────────────┐
 │ Source Adapter│
 │  + Normalizer │
 └───────────────┘
        ↓
      Pipeline
```

This provides a cleaner foundation for adding additional job sources while keeping source-specific implementation isolated.

---

## Optional AI Assistance

AI can be used as an **optional intelligence layer** for tasks such as:

* Improving job summaries
* Generating human-readable explanations
* Assisting with qualitative analysis
* Enhancing digest presentation

AI does **not** replace deterministic eligibility, scoring, or ranking logic.

The core system remains reliable even without AI.

---

## Output

MaukaKhoj can produce job recommendations for downstream interfaces such as:

```text
Digest
API
UI
JSON
YAML
CSV
HTML
```

The architecture keeps discovery and intelligence separate from presentation and delivery.

---

## What MaukaKhoj Is Not

MaukaKhoj is intentionally **not**:

* An auto-apply bot
* A mass job scraper
* A system designed to maximize job count
* A browser automation tool for submitting applications
* A replacement for user decision-making

Its purpose is to reduce the noise of the job market and surface opportunities that are genuinely worth reviewing.

---

## Project Goal

The long-term goal of MaukaKhoj is to build a reliable job discovery intelligence layer that can answer:

> **What jobs should this person actually spend their time looking at today?**

Instead of overwhelming users with hundreds of postings, MaukaKhoj aims to deliver a smaller set of **relevant, eligible, fresh, explainable opportunities**.
