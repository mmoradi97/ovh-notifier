# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (foreground, for testing)
.venv/bin/python3 checker.py

# Lint (CI uses ruff)
pip install ruff
ruff check .
ruff check . --fix
```

## Architecture

This is a single-file Python script (`checker.py`) with no framework. The flow is:

1. Config is loaded from `.env` via `python-dotenv` at startup.
2. `main()` sends a Telegram startup message, then enters an infinite poll loop.
3. Each iteration calls `fetch_statuses()` → hits `ca.api.ovh.com/v1/vps/order/rule/datacenter` with the configured plan and subsidiary, returns a dict keyed by zone name.
4. `check_and_notify()` compares the current `linuxStatus`/`windowsStatus` to `last_status` (in-memory dict). Alerts fire only on transitions: unavailable→available (✅) and available→unavailable (❌). The first run silently seeds state with no alert.
5. `telegram_notify()` posts to the Telegram Bot API.

State is in-memory only — restarting the process re-seeds from the live API on the first poll (no alert on startup for existing availability).

## Configuration

Copy `.env.example` to `.env`. Required variables: `PLAN_CODE`, `ZONES`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. See `.env.example` for all options and available zone/plan codes.

## Deployment

The repo includes `ovh-notifier.service` for running as a systemd unit. Default path in the service file is `/root/ovh-notifier` — edit if deploying elsewhere.
