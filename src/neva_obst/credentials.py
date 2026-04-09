"""
Credential resolution for nevaobst CLI.

Priority order (highest → lowest):
  1. CLI flags (--access-key / --secret-key / --bucket / --endpoint)
  2. Environment variables (NEVA_ACCESS_KEY, NEVA_SECRET_KEY, …)
  3. Config file (~/.azzte/neva-obst.conf)
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".azzte"
CONFIG_FILE = CONFIG_DIR / "neva-obst.conf"

DEFAULT_ENDPOINT = "https://s3.nevaobjects.id"

ENV_MAP = {
    "access_key": "NEVA_ACCESS_KEY",
    "secret_key": "NEVA_SECRET_KEY",
    "bucket": "NEVA_BUCKET",
    "endpoint": "NEVA_ENDPOINT",
}


@dataclass
class ResolvedCredentials:
    access_key: str
    secret_key: str
    bucket: str
    endpoint: str = DEFAULT_ENDPOINT


def load_config_file(profile: str = "default") -> dict:
    """Read ~/.azzte/neva-obst.conf and return the given profile section as a dict."""
    if not CONFIG_FILE.exists():
        return {}
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    section = profile if cfg.has_section(profile) else "default"
    return dict(cfg[section]) if cfg.has_section(section) else {}


def save_config_file(
    access_key: str,
    secret_key: str,
    bucket: str,
    endpoint: str = DEFAULT_ENDPOINT,
    profile: str = "default",
) -> None:
    """Write credentials to ~/.azzte/neva-obst.conf."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        cfg.read(CONFIG_FILE)
    if not cfg.has_section(profile):
        cfg.add_section(profile)
    cfg[profile]["access_key"] = access_key
    cfg[profile]["secret_key"] = secret_key
    cfg[profile]["bucket"] = bucket
    cfg[profile]["endpoint"] = endpoint
    with open(CONFIG_FILE, "w") as fh:
        cfg.write(fh)
    CONFIG_FILE.chmod(0o600)


def resolve(
    *,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    bucket: Optional[str] = None,
    endpoint: Optional[str] = None,
    profile: str = "default",
) -> ResolvedCredentials:
    """
    Resolve credentials from (in order): flags → env vars → config file.

    Raises:
        SystemExit: with a helpful message if required fields are missing.
    """
    file_cfg = load_config_file(profile)

    def _get(field: str, flag_val: Optional[str]) -> Optional[str]:
        return (
            flag_val
            or os.environ.get(ENV_MAP[field])
            or file_cfg.get(field)
        )

    resolved_access = _get("access_key", access_key)
    resolved_secret = _get("secret_key", secret_key)
    resolved_bucket = _get("bucket", bucket)
    resolved_endpoint = _get("endpoint", endpoint) or DEFAULT_ENDPOINT

    missing = []
    if not resolved_access:
        missing.append("access_key  (--access-key / NEVA_ACCESS_KEY / ~/.azzte/neva-obst.conf)")
    if not resolved_secret:
        missing.append("secret_key  (--secret-key / NEVA_SECRET_KEY / ~/.azzte/neva-obst.conf)")
    if not resolved_bucket:
        missing.append("bucket      (--bucket / NEVA_BUCKET / ~/.azzte/neva-obst.conf)")

    if missing:
        import click
        raise click.UsageError(
            "Missing credentials:\n  " + "\n  ".join(missing)
            + "\n\nRun `nevaobst configure` to set up credentials."
        )

    return ResolvedCredentials(
        access_key=resolved_access,
        secret_key=resolved_secret,
        bucket=resolved_bucket,
        endpoint=resolved_endpoint,
    )