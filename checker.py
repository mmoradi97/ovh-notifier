import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── config ────────────────────────────────────────────────────────────────────
PLAN_CODE        = os.environ["PLAN_CODE"]
OVH_SUBSIDIARY   = os.environ.get("OVH_SUBSIDIARY", "WE")
ZONES            = [z.strip().upper() for z in os.environ["ZONES"].split(",")]
CHECK_INTERVAL   = int(os.environ.get("CHECK_INTERVAL", "180"))
BOT_TOKEN        = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID          = os.environ["TELEGRAM_CHAT_ID"]
ALERT_LINUX      = os.environ.get("ALERT_LINUX", "true").lower() == "true"
ALERT_WINDOWS    = os.environ.get("ALERT_WINDOWS", "false").lower() == "true"
STATE_FILE       = os.environ.get("STATE_FILE", "state.json")

# OVH API endpoints by region. CA is the default (works for most subsidiaries).
# Set OVH_API_ENDPOINT in .env to override: CA, EU, US, or a full URL.
_OVH_ENDPOINTS = {
    "CA": "https://ca.api.ovh.com/v1/vps/order/rule/datacenter",
    "EU": "https://eu.api.ovh.com/v1/vps/order/rule/datacenter",
    "US": "https://api.us.ovhcloud.com/v1/vps/order/rule/datacenter",
}
_endpoint_env = os.environ.get("OVH_API_ENDPOINT", "CA")
OVH_API_URL = _OVH_ENDPOINTS.get(_endpoint_env.upper(), _endpoint_env)

# ── state ─────────────────────────────────────────────────────────────────────
last_status: dict[str, str] = {}


def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                last_status.update(json.load(f))
            log(f"Loaded state from {STATE_FILE} ({len(last_status)} entries)")
        except Exception as e:
            log(f"WARNING: could not load state file: {e}")


def save_state():
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(last_status, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        log(f"WARNING: could not save state: {e}")
        try:
            os.unlink(tmp)
        except OSError:
            pass


def with_retry(fn, *args, retries=3, backoff=5, **kwargs):
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            wait = backoff * (2 ** attempt)
            log(f"WARNING: {type(e).__name__}: {e} — retrying in {wait}s")
            time.sleep(wait)


def telegram_notify(message: str, dry_run: bool = False):
    if dry_run:
        log(f"[DRY RUN] Telegram: {message!r}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": message, "disable_web_page_preview": True},
        timeout=10,
    )
    r.raise_for_status()


def fetch_statuses() -> dict[str, dict]:
    def _get():
        r = requests.get(
            OVH_API_URL,
            params={"ovhSubsidiary": OVH_SUBSIDIARY, "planCode": PLAN_CODE},
            headers={"User-Agent": "ovh-vps-notifier/1.2"},
            timeout=15,
        )
        r.raise_for_status()
        return r

    r = with_retry(_get)

    result = {}
    for dc in r.json().get("datacenters", []):
        name = str(dc.get("datacenter", "")).upper()
        if name in ZONES:
            result[name] = {
                "status": dc.get("status"),
                "linuxStatus": dc.get("linuxStatus"),
                "windowsStatus": dc.get("windowsStatus"),
            }
    return result


def check_and_notify(zone: str, os_type: str, current: str, dry_run: bool = False):
    """Compare current status to previous and send Telegram alert on transition."""
    key = f"{zone}_{os_type}"
    previous = last_status.get(key)

    if previous is None:
        # first run — record state, no alert
        last_status[key] = current
        save_state()
        return

    if previous != "available" and current == "available":
        with_retry(
            telegram_notify,
            f"✅ OVH VPS AVAILABLE ({os_type.upper()})\n"
            f"Plan: {PLAN_CODE}\n"
            f"Zone: {zone}\n"
            f"{os_type}Status: {current}\n"
            f"https://www.ovhcloud.com/en/vps/configurator/?planCode={PLAN_CODE}",
            dry_run=dry_run,
        )

    if previous == "available" and current != "available":
        with_retry(
            telegram_notify,
            f"❌ OVH VPS no longer available ({os_type.upper()})\n"
            f"Plan: {PLAN_CODE}\n"
            f"Zone: {zone}\n"
            f"{os_type}Status: {current}",
            dry_run=dry_run,
        )

    last_status[key] = current
    save_state()


# ── main loop ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OVH VPS availability notifier")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Poll the API and log alerts without sending Telegram messages",
    )
    args = parser.parse_args()

    if not ALERT_LINUX and not ALERT_WINDOWS:
        sys.exit("ERROR: both ALERT_LINUX and ALERT_WINDOWS are false — nothing to monitor")

    alert_types = []
    if ALERT_LINUX:
        alert_types.append("linux")
    if ALERT_WINDOWS:
        alert_types.append("windows")

    load_state()

    log(
        f"OVH VPS Notifier started | plan={PLAN_CODE} zones={ZONES} "
        f"interval={CHECK_INTERVAL}s alerting={alert_types}"
        + (" [DRY RUN]" if args.dry_run else "")
    )

    try:
        with_retry(
            telegram_notify,
            f"\U0001f680 OVH VPS Notifier started\n"
            f"Plan: {PLAN_CODE}\n"
            f"Zones: {', '.join(ZONES)}\n"
            f"Alerting: {', '.join(alert_types)}\n"
            f"Interval: {CHECK_INTERVAL}s",
            dry_run=args.dry_run,
        )
    except Exception as e:
        log(f"WARNING: startup Telegram message failed: {e}")

    while True:
        try:
            statuses = fetch_statuses()

            for zone in ZONES:
                info = statuses.get(zone)

                if not info:
                    log(f"[{zone}] not found in API response")
                    continue

                log(
                    f"[{zone}] linux={info['linuxStatus']} "
                    f"windows={info['windowsStatus']} "
                    f"status={info['status']}"
                )

                if ALERT_LINUX:
                    check_and_notify(zone, "linux", info["linuxStatus"] or "unknown", args.dry_run)

                if ALERT_WINDOWS:
                    check_and_notify(zone, "windows", info["windowsStatus"] or "unknown", args.dry_run)

        except Exception as e:
            log(f"ERROR: {type(e).__name__}: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
