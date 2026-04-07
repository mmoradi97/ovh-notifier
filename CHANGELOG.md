# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-07

### Added
- Windows VPS availability alerting via `ALERT_WINDOWS=true` env var
- `ALERT_LINUX` env var to toggle Linux alerts (default: `true`)
- systemd service file `ovh-notifier.service` for auto-start on reboot
- `CHANGELOG.md`

### Changed
- Alert state now tracked separately per OS type (`linux`/`windows`) per zone
- Startup Telegram message now lists which OS types are being alerted

## [1.1.0] - 2026-04-07

### Added
- GitHub Actions workflow for ruff linting on push and PR
- README badges: lint status, Python version, license

## [1.0.0] - 2026-04-07

### Added
- Initial release
- Polls `ca.api.ovh.com/v1/vps/order/rule/datacenter` for real VPS availability
- Checks `linuxStatus` per datacenter zone
- Telegram alerts on availability change (available / no longer available)
- Skips false alert on first run
- `.env` based configuration with `python-dotenv`
- `.gitignore` to keep secrets out of the repo
- `.env.example` template
