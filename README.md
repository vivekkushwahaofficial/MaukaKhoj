# MaukaKhoj

> **Personalized Job Discovery Intelligence Engine**

MaukaKhoj is a profile-driven job discovery intelligence engine designed to discover legitimate software and technology opportunities, normalize and validate job data, remove duplicates, filter unsuitable roles, match opportunities against user profiles, rank relevant jobs, and explain why they are recommended.

MaukaKhoj focuses on **quality personalized job discovery**, not maximum scraping or maximum job count.

> **MaukaKhoj is not an auto-apply bot.**
>
> Users always review and submit applications manually.

---

## What MaukaKhoj Does

MaukaKhoj is designed to answer:

> **Among all legitimately discoverable jobs, which opportunities are genuinely worth this user's attention, and why?**

The system focuses on:

- Reliable job discovery
- Profile-aware matching
- Deterministic scoring
- Explainable ranking
- Duplicate prevention
- Remote-location classification
- Job freshness
- Source reliability
- Optional AI-assisted analysis
- Automated email digests

The goal is to reduce job-search noise and surface a smaller set of opportunities that are genuinely worth reviewing.

---

## Core Architecture

```text
Job Market
    │
    ├── Job Boards
    ├── ATS Platforms
    └── Company Career Pages
    │
    ↓
Source Adapters
    ↓
Raw Jobs
    ↓
Normalization
    ↓
Canonical Jobs
    ↓
Validation
    ↓
Deduplication
    ↓
Hard Filters
    ↓
Profile Matching
    ↓
Scoring
    ↓
Ranking
    ↓
Explanation
    ↓
Digest / API / UI
````

The architecture separates **job discovery**, **job intelligence**, and **delivery** so that individual components can evolve independently.

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

This separation keeps source-specific fetching and parsing independent from the core matching and ranking system.

---

## Design Principles

MaukaKhoj follows several core engineering principles.

### Profile-Driven

User preferences, skills, experience, and goals are represented as data rather than hardcoded application logic.

### Source-Agnostic

Source-specific fetching and parsing remain inside source adapters.

### Configuration-Driven

Source settings and application rules are configurable without modifying core pipeline logic.

### Deterministic

Filtering, matching, scoring, and ranking are predictable and reproducible.

### Explainable

Recommended jobs include understandable reasons explaining why they match the user's profile.

### Quality-First

Irrelevant and unsuitable jobs are removed before ranking.

### Failure-Isolated

Failure of one job source should not stop the entire discovery pipeline.

### Privacy-Conscious

Personal profiles, credentials, and secrets are kept outside the public repository.

### Manual Application

MaukaKhoj discovers and recommends jobs. Users remain responsible for reviewing and submitting applications.

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

The system produces a deterministic **0–100 match score**.

Eligible jobs are then ranked using consistent tie-breaking rules.

Each recommendation can also include an explanation describing:

* Why the role matches
* Which skills are relevant
* How the experience level compares
* Why the location is compatible
* Other factors affecting the recommendation

The matching system is designed to remain understandable and testable without depending on AI.

---

## Hard Filters

Hard eligibility rules are applied before profile scoring.

Examples include:

* Remote/location eligibility
* Employment-type compatibility
* Experience constraints
* Job freshness
* Other explicitly configured eligibility rules

This prevents unsuitable jobs from receiving a high relevance score simply because they contain matching keywords.

---

## Job Sources

MaukaKhoj is designed around modular source adapters.

### Job Boards

The architecture can support sources such as:

* Naukri
* Indeed
* LinkedIn
* Foundit
* Internshala
* Cutshort
* Wellfound

### ATS Platforms

The architecture supports adapters for platforms such as:

* Lever
* Greenhouse
* Ashby
* SmartRecruiters
* Workable

### Company Career Pages

The architecture can also support direct company career sources such as:

* TCS
* Infosys
* Wipro
* HCLTech
* Startups
* Other company career sites

Source availability depends on the adapters implemented and configured in a particular version or fork.

New adapters can be added without redesigning the core job intelligence pipeline.

---

## Remote Job Classification

MaukaKhoj does not treat every job containing the word `remote` as equivalent.

Supported remote classifications include:

```text
INDIA_REMOTE
COUNTRY_REMOTE
REGION_REMOTE
WORLDWIDE_REMOTE
HYBRID
ONSITE
UNKNOWN
```

This allows the matching system to distinguish between:

* Remote within India
* Remote within a specific country
* Remote within a specific region
* Worldwide remote
* Hybrid opportunities
* On-site opportunities
* Unknown location arrangements

---

## Job Freshness

Job freshness is treated as part of job quality.

A configurable freshness policy can reject jobs that are older than the configured threshold.

Example:

```yaml
freshness:
  enabled: true
  max_age_days: 30
```

Jobs with unavailable posting dates can remain eligible rather than being incorrectly discarded.

Freshness can also contribute to the final job score.

---

## Configuration-Driven Design

MaukaKhoj keeps user-specific preferences and source configuration separate from application logic.

### Profile

```text
Profile
├── Name
├── Target Roles
├── Skills
├── Experience
├── Education
├── Locations
├── Remote Preferences
├── Employment Preferences
├── Domains
└── Projects
```

### Source Configuration

```text
Source Configuration
├── Source
├── Account / Company
├── Request Settings
└── Source-Specific Settings
```

This makes MaukaKhoj easier to customize and fork for different users without changing the core matching engine.

---

# Quick Start

## 1. Fork the Repository

Fork MaukaKhoj to your own GitHub account.

Then clone your fork:

```bash
git clone https://github.com/<your-username>/MaukaKhoj.git
cd MaukaKhoj
```

---

## 2. Create a Python Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it according to your operating system.

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create Your Personal Profile

Copy the public profile template:

### Windows

```bash
copy data\profile.example.json data\profile.json
```

### Linux / macOS

```bash
cp data/profile.example.json data/profile.json
```

Then customize:

```text
data/profile.json
```

with your own:

* Target job titles
* Skills
* Experience
* Education
* Locations
* Remote preferences
* Employment preferences
* Domains
* Projects

Example structure:

```json
{
  "name": "Candidate",
  "target_titles": [
    "Software Engineer",
    "Backend Developer"
  ],
  "skills": [
    "Java",
    "Spring Boot",
    "SQL"
  ],
  "experience": {
    "years": 0,
    "current_title": "Student"
  },
  "education": {
    "degree": "B.Tech",
    "field": "Computer Science Engineering",
    "institution": "Example University"
  },
  "locations": [
    "India"
  ],
  "remote_preferences": [
    "INDIA_REMOTE",
    "COUNTRY_REMOTE",
    "WORLDWIDE_REMOTE"
  ],
  "employment_preferences": [
    "FULL_TIME",
    "INTERNSHIP"
  ],
  "domains": [
    "Backend Development",
    "Software Engineering"
  ],
  "projects": [
    "Example Project"
  ]
}
```

> `data/profile.json` contains personal configuration and is intentionally ignored by Git. **Never commit it.**

The public repository only contains:

```text
data/profile.example.json
```

as a safe template.

---

## 5. Configure Job Sources

Source configuration is maintained in:

```text
config/config.yaml
```

Example:

```yaml
sources:
  request_timeout_seconds: 20

  lever:
    account_name: your-lever-company
```

Configure the sources and source-specific settings required by your fork.

The core application does not need to be modified simply because the profile or source configuration changes.

---

## 6. Run the Test Suite

Run all tests:

```bash
python -m pytest -q
```

The test suite verifies important parts of the system including:

* Configuration loading
* Profile loading
* Source adapters
* Normalization
* Validation
* Deduplication
* Hard filtering
* Matching
* Scoring
* Ranking
* Explanations
* Digest rendering
* Email configuration
* Application orchestration

---

## 7. Run MaukaKhoj

```bash
python -m app.main
```

The application will:

```text
Load Configuration
      ↓
Load Profile
      ↓
Fetch Jobs
      ↓
Normalize
      ↓
Validate
      ↓
Deduplicate
      ↓
Apply Hard Filters
      ↓
Match Profile
      ↓
Score & Rank
      ↓
Generate Digest
      ↓
Send Email
```

---

# Fork-Friendly Personalization

MaukaKhoj is designed so that a new user can customize the system primarily through **configuration and profile data**, rather than changing the core application.

The intended customization flow is:

```text
Fork Repository
      ↓
Create Personal Profile
      ↓
Configure Job Sources
      ↓
Configure Secrets
      ↓
Run MaukaKhoj
```

A fork should not require rewriting the matching engine simply to support another person's:

* Skills
* Target roles
* Education
* Experience
* Location
* Remote preferences
* Employment preferences
* Domains
* Projects

---

# GitHub Actions

MaukaKhoj includes a GitHub Actions workflow for automated job discovery and email delivery.

The workflow can run automatically on a daily schedule and can also be triggered manually.

## Required Repository Secrets

Configure the following GitHub repository secrets:

```text
PROFILE_JSON
GEMINI_API_KEY
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASS
MAIL_TO
```

### PROFILE_JSON

`PROFILE_JSON` should contain the complete contents of your private:

```text
data/profile.json
```

The GitHub Actions workflow creates the profile at runtime instead of storing it in the public repository.

```text
GitHub Secret
PROFILE_JSON
     ↓
Runtime data/profile.json
     ↓
MaukaKhoj
     ↓
Job Discovery Pipeline
     ↓
Digest
     ↓
Email
```

This allows the public repository to remain generic while each fork can use its own private profile.

---

## Manual GitHub Actions Run

The workflow can be started manually from:

```text
GitHub
  ↓
Actions
  ↓
MaukaKhoj Daily Digest
  ↓
Run workflow
```

The workflow is also configured for scheduled daily execution.

---

# Personalization Model

MaukaKhoj separates public application logic from private user configuration.

```text
PUBLIC REPOSITORY
│
├── Application Code
├── Source Adapters
├── Normalizers
├── Matching Rules
├── config/config.yaml
├── data/profile.example.json
└── Tests
│
└──────────────────────┐
                       │
PRIVATE CONFIGURATION  │
                       │
                 PROFILE_JSON
                 API Credentials
                 SMTP Credentials
                       │
                       ↓
                Runtime Configuration
```

This separation allows developers to fork MaukaKhoj without exposing the original user's personal profile.

---

# Source Registry

MaukaKhoj uses a source registry to keep source construction separate from the main application composition.

```text
Source Configuration
        ↓
   Source Registry
        ↓
 ┌────────────────────┐
 │   Source Adapter   │
 │         +          │
 │     Normalizer     │
 └────────────────────┘
        ↓
      Pipeline
```

The registry provides a clean foundation for adding new sources while keeping source-specific implementation isolated.

A new source should primarily require:

1. A source adapter
2. A normalizer
3. Source registration
4. Source-specific configuration
5. Tests

The core job intelligence pipeline remains unchanged.

---

# Optional AI Assistance

AI is an optional intelligence layer.

It can assist with tasks such as:

* Improving job summaries
* Generating human-readable explanations
* Qualitative job analysis
* Enhancing digest presentation

AI does **not** replace deterministic:

* Eligibility
* Hard filtering
* Matching
* Scoring
* Ranking

The core system remains functional without AI.

If AI is unavailable or fails, the deterministic pipeline can continue using its fallback behavior.

---

# Output

MaukaKhoj separates job discovery and intelligence from presentation and delivery.

Potential downstream outputs include:

```text
Digest
API
UI
JSON
YAML
CSV
HTML
```

This allows the same job intelligence pipeline to support different interfaces in the future.

---

# Security & Privacy

MaukaKhoj is designed to keep personal configuration and credentials outside the public repository.

## Never Commit

Do not commit:

```text
data/profile.json
.env
*.secret
```

or any file containing:

* Personal profile information
* API keys
* Passwords
* SMTP credentials
* Access tokens
* Other private credentials

## Safe Public Template

The repository provides:

```text
data/profile.example.json
```

as the public profile template.

Use it to create your own private profile:

```text
data/profile.example.json
        ↓
data/profile.json
```

The private file is intentionally ignored by Git.

For GitHub Actions, use repository secrets instead of committing private configuration.

> **Never place personal credentials or private profile information directly in source code, workflow files, `config.yaml`, or the public example profile.**

---

# Project Structure

The project follows a modular structure that separates domain logic, application orchestration, sources, normalization, delivery, and configuration.

```text
MaukaKhoj/
│
├── app/
│   ├── ai/
│   ├── config/
│   ├── delivery/
│   ├── domain/
│   ├── normalization/
│   ├── sources/
│   ├── application.py
│   ├── logging_config.py
│   └── main.py
│
├── config/
│   └── config.yaml
│
├── data/
│   └── profile.example.json
│
├── tests/
│
├── .github/
│   └── workflows/
│       └── daily.yml
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# What MaukaKhoj Is Not

MaukaKhoj is intentionally **not**:

* An auto-apply bot
* A mass job scraper
* A system designed to maximize job count
* A browser automation tool for submitting applications
* A replacement for user decision-making

Its purpose is to reduce the noise of the job market and surface opportunities that are genuinely worth reviewing.

---

# Engineering Philosophy

MaukaKhoj intentionally avoids unnecessary complexity.

The project favors:

```text
Simple Architecture
       +
Clear Boundaries
       +
Deterministic Logic
       +
Configuration
       +
Testability
```

over prematurely introducing infrastructure that is not required.

The system is designed as a modular application so that components can be replaced or expanded when real requirements justify it.

---

# Roadmap

The architecture is designed to evolve toward broader job-market coverage.

Potential areas of expansion include:

* More job-board adapters
* More ATS adapters
* More company career sources
* Improved job deduplication
* Advanced job freshness detection
* Better location intelligence
* Profile-aware eligibility rules
* Additional output formats
* Persistent job tracking
* Application tracking
* Analytics
* Web UI
* API access
* Improved AI-assisted analysis

New functionality should preserve the core principles of deterministic filtering, explainability, privacy, and source isolation.

---

## Project Goal

The long-term goal of MaukaKhoj is to build a reliable job discovery intelligence layer that can answer:

> **What jobs should this person actually spend their time looking at today?**

Instead of overwhelming users with hundreds or thousands of postings, MaukaKhoj aims to deliver a smaller set of:

* Relevant
* Eligible
* Fresh
* Explainable
* High-quality

job opportunities.

---

## License

This project is licensed under the **Apache License 2.0**.

See the `LICENSE` file for details.

---

## Built for Developers

MaukaKhoj is built for developers who want to spend less time searching through job boards and more time focusing on the opportunities that actually matter.

**Fork it. Personalize it. Configure it. Build on it.**
