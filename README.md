# OVH VPS Notifier

A lightweight Python script that polls the OVH API and sends a **Telegram alert** when a specific VPS plan becomes available in your chosen datacenters.

## How it works

It queries the `ca.api.ovh.com/v1/vps/order/rule/datacenter` endpoint every N seconds and checks `linuxStatus` for each watched zone. When a zone transitions from any status to `available`, you get a Telegram message with a direct link to the OVH configurator.

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

**Foreground (test):**
```bash
.venv/bin/python3 checker.py
```

**Background (persistent after SSH logout):**
```bash
nohup .venv/bin/python3 checker.py > checker.log 2>&1 &
```

### 5. Manage

```bash
# Check it's running
ps aux | grep checker.py

# Watch logs
tail -f checker.log

# Stop
pkill -f checker.py
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
