import os
import time
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

OVH_API_URL = "https://ca.api.ovh.com/v1/vps/order/rule/datacenter"

# ── state ─────────────────────────────────────────────────────────────────────
# tracks last seen status per zone per os type: {"WAW_linux": "unavailable", ...}
last_status: dict[str, str] = {}


def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def telegram_notify(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": message, "disable_web_page_preview": True},
        timeout=10,
    )
    r.raise_for_status()


def fetch_statuses() -> dict[str, dict]:
    r = requests.get(
        OVH_API_URL,
        params={"ovhSubsidiary": OVH_SUBSIDIARY, "planCode": PLAN_CODE},
        headers={"User-Agent": "ovh-vps-notifier/1.2"},
        timeout=15,
    )
    r.raise_for_status()

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


def check_and_notify(zone: str, os_type: str, current: str):
    """Compare current status to previous and send Telegram alert on change."""
    key = f"{zone}_{os_type}"
    previous = last_status.get(key)

    if previous is None:
        # first run — record state, no alert
        last_status[key] = current
        return

    if previous != "available" and current == "available":
        telegram_notify(
            f"\u2705 OVH VPS AVAILABLE ({os_type.upper()})\n"
            f"Plan: {PLAN_CODE}\n"
            f"Zone: {zone}\n"
            f"{os_type}Status: {current}\n"
            f"https://www.ovhcloud.com/en/vps/configurator/?planCode={PLAN_CODE}"
        )

    if previous == "available" and current != "available":
        telegram_notify(
            f"\u274c OVH VPS no longer available ({os_type.upper()})\n"
            f"Plan: {PLAN_CODE}\n"
            f"Zone: {zone}\n"
            f"{os_type}Status: {current}"
        )

    last_status[key] = current


# ── main loop ─────────────────────────────────────────────────────────────────
def main():
    alert_types = []
    if ALERT_LINUX:
        alert_types.append("linux")
    if ALERT_WINDOWS:
        alert_types.append("windows")

    log(
        f"OVH VPS Notifier started | plan={PLAN_CODE} zones={ZONES} "
        f"interval={CHECK_INTERVAL}s alerting={alert_types}"
    )
    telegram_notify(
        f"\U0001f680 OVH VPS Notifier started\n"
        f"Plan: {PLAN_CODE}\n"
        f"Zones: {', '.join(ZONES)}\n"
        f"Alerting: {', '.join(alert_types)}\n"
        f"Interval: {CHECK_INTERVAL}s"
    )

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
                    check_and_notify(zone, "linux", info["linuxStatus"] or "unknown")

                if ALERT_WINDOWS:
                    check_and_notify(zone, "windows", info["windowsStatus"] or "unknown")

        except Exception as e:
            log(f"ERROR: {type(e).__name__}: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
