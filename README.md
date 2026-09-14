# MaukaKhoj

> Personalized Job Discovery Intelligence Engine

MaukaKhoj is an independent, profile-driven job discovery intelligence engine that discovers legitimate software and technology opportunities, normalizes and validates job data, removes duplicates, filters unsuitable roles, matches jobs against user profiles, ranks relevant opportunities, and explains why they are recommended.

MaukaKhoj is **not an auto-apply bot**.

Users always review and submit applications manually.

---

## What MaukaKhoj Does

MaukaKhoj is designed to answer:

> **Among all legitimately discoverable jobs, which opportunities are genuinely worth this user's attention, and why?**

The system focuses on:

- Reliable job discovery
- Profile-aware matching
- Explainable ranking
- Duplicate prevention
- Remote-location classification
- Job freshness
- Source reliability
- Optional AI-assisted analysis

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