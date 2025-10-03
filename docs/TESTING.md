# Testing Guide

This document outlines how to run the automated test suite for the FC Registration Notifications application.

## Running the Test Suite

The entire test suite can be run using `pytest` from the project root:

```bash
pytest
```

To run specific tests, you can use `pytest`'s `-k` flag with a keyword expression. For example, to run only tests related to fencers:

```bash
pytest -k "fencer"
```

## Test Environment

Tests are designed to run in a local environment and do not require network access. External services like Mailgun and FencingTracker.com are mocked.

### Environment Variables

No special environment variables are required to run the tests. The test suite uses the default in-memory SQLite database configuration.

## Simulating Scraper Behavior

Some tests for the fencer scraper service (`tests/services/test_fencer_scraper_service.py`) involve time-sensitive behavior like cooldowns and retries. These tests use `monkeypatch` to control time and other variables.

### Controlling Time

To test cooldowns, tests can patch `datetime.utcnow()` to simulate the passage of time. This allows verification that a fencer in cooldown is not scraped until the cooldown period has expired.

### Disabling Jitter and Delays

To make scraper tests deterministic and faster, the `FENCER_SCRAPE_DELAY_SEC` and `FENCER_SCRAPE_JITTER_SEC` settings are effectively zeroed out during tests by patching the configuration or the `time.sleep` function.

## End-to-End Smoke Test

An end-to-end smoke test is available to verify the entire fencer tracking and digest flow. This test seeds a database, runs the scrapers, generates a digest, and cleans up after itself.

To run this test specifically:

```bash
pytest tests/e2e/test_tracked_fencer_flow.py
```
