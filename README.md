# OVH VPS Notifier

[![Lint](https://github.com/mmoradi97/ovh-notifier/actions/workflows/lint.yml/badge.svg)](https://github.com/mmoradi97/ovh-notifier/actions/workflows/lint.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Release](https://img.shields.io/github/v/release/mmoradi97/ovh-notifier)](https://github.com/mmoradi97/ovh-notifier/releases)

A lightweight Python script that polls the OVH API and sends a **Telegram alert** when a specific VPS plan becomes available in your chosen datacenters. Supports both Linux and Windows VPS availability.

## How it works

It queries the `ca.api.ovh.com/v1/vps/order/rule/datacenter` endpoint every N seconds and checks `linuxStatus` (and optionally `windowsStatus`) for each watched zone. When a zone transitions to `available`, you get a Telegram message with a direct link to the OVH configurator.

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/mmoradi97/ovh-notifier.git
cd ovh-notifier
```

### 2. Install dependencies

```bash
apt install -y python3-venv python3-pip   # Debian/Ubuntu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
nano .env
```

Fill in your Telegram bot token, chat ID, plan code, and zones.

> **Get your bot token**: message [@BotFather](https://t.me/BotFather) on Telegram  
> **Get your chat ID**: send a message to your bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and find `chat.id`

### 4. Run

**Option A — Background with nohup (simple):**
```bash
nohup .venv/bin/python3 checker.py > checker.log 2>&1 &
```

**Option B — systemd service (recommended, survives reboots):**
```bash
# Edit the service file if your path differs from /root/ovh-notifier
sudo cp ovh-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ovh-notifier
sudo systemctl start ovh-notifier
```

**Foreground (test only):**
```bash
.venv/bin/python3 checker.py
```

### 5. Manage

**nohup:**
```bash
ps aux | grep checker.py   # check running
tail -f checker.log        # watch logs
pkill -f checker.py        # stop
```

**systemd:**
```bash
sudo systemctl status ovh-notifier    # check status
sudo journalctl -fu ovh-notifier      # watch logs
sudo systemctl stop ovh-notifier      # stop
sudo systemctl restart ovh-notifier   # restart
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `PLAN_CODE` | OVH plan code (e.g. `vps-2025-model1`) | required |
| `OVH_SUBSIDIARY` | OVH subsidiary (`WE`, `IE`, `PL`, etc.) | `WE` |
| `ZONES` | Comma-separated datacenter codes | required |
| `CHECK_INTERVAL` | Poll interval in seconds | `180` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather | required |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | required |
| `ALERT_LINUX` | Alert when `linuxStatus` becomes available | `true` |
| `ALERT_WINDOWS` | Alert when `windowsStatus` becomes available | `false` |

## Available zones

`WAW` (Warsaw), `UK` (London), `DE` (Frankfurt), `GRA` (Gravelines), `SBG` (Strasbourg), `BHS` (Beauharnois), `SGP` (Singapore), `SYD` (Sydney)

## Plan codes

| Plan | Code |
|---|---|
| VPS-1 | `vps-2025-model1` |
| VPS-2 | `vps-2025-model2` |
| VPS-3 | `vps-2025-model3` |
| VPS-4 | `vps-2025-model4` |
| VPS-5 | `vps-2025-model5` |

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
