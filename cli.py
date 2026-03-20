"""
nevaobst - CLI for Neva Objects S3-compatible storage.

Usage examples:
    nevaobst configure
    nevaobst upload ./photo.jpg
    nevaobst upload "images/*" --prefix uploads/
    nevaobst list
    nevaobst list -fs
    nevaobst get-url photo.jpg --expires 3600
    nevaobst info photo.jpg
    nevaobst delete photo.jpg
    nevaobst delete photo.jpg --force
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Optional

import click

from .client import NevaObjectsClient, NevaObjectsConfig
from .credentials import DEFAULT_ENDPOINT, resolve, save_config_file
from .exceptions import NevaObjectsError
from .formatter import (
    error,
    ok,
    print_object_info,
    print_object_list,
    print_upload_results,
    print_url,
)

# --------------------------------------------------------------------------- #
# Shared options                                                                #
# --------------------------------------------------------------------------- #

_cred_options = [
    click.option("--access-key", envvar="NEVA_ACCESS_KEY", default=None, help="Access key"),
    click.option("--secret-key", envvar="NEVA_SECRET_KEY", default=None, help="Secret key"),
    click.option("--bucket", envvar="NEVA_BUCKET", default=None, help="Bucket name"),
    click.option(
        "--endpoint",
        envvar="NEVA_ENDPOINT",
        default=None,
        help=f"Endpoint URL (default: {DEFAULT_ENDPOINT})",
    ),
    click.option(
        "--profile",
        default="default",
        show_default=True,
        help="Config profile to use",
    ),
    click.option("--json", "as_json", is_flag=True, help="Output as JSON"),
]


def add_cred_options(fn):
    for opt in reversed(_cred_options):
        fn = opt(fn)
    return fn


def make_client(
    access_key, secret_key, bucket, endpoint, profile
) -> NevaObjectsClient:
    creds = resolve(
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        endpoint=endpoint,
        profile=profile,
    )
    config = NevaObjectsConfig(
        access_key=creds.access_key,
        secret_key=creds.secret_key,
        bucket=creds.bucket,
        endpoint=creds.endpoint,
    )
    return NevaObjectsClient(config)


# --------------------------------------------------------------------------- #
# Root group                                                                   #
# --------------------------------------------------------------------------- #

@click.group()
@click.version_option(package_name="ate-neva-obst")
def cli():
    """nevaobst — Neva Objects S3 CLI\n
    Set credentials once with `nevaobst configure`, then use any command.\n
    Add --json to any command for machine-readable output.
    """


# --------------------------------------------------------------------------- #
# configure                                                                    #
# --------------------------------------------------------------------------- #

@cli.command()
@click.option("--profile", default="default", show_default=True)
def configure(profile: str):
    """Interactively save credentials to ~/.neva/config."""
    click.echo(f"Configuring profile: {click.style(profile, bold=True)}\n")
    access_key = click.prompt("  Access key")
    secret_key = click.prompt("  Secret key", hide_input=True)
    bucket = click.prompt("  Default bucket")
    endpoint = click.prompt(
        "  Endpoint",
        default=DEFAULT_ENDPOINT,
        show_default=True,
    )
    save_config_file(access_key, secret_key, bucket, endpoint, profile)
    click.echo(f"\n{click.style('✓', fg='green')} Saved to ~/.neva/config [{profile}]")


# --------------------------------------------------------------------------- #
# upload                                                                       #
# --------------------------------------------------------------------------- #

@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option(
    "--prefix", "-p", default="", help="Key prefix for uploaded objects (e.g. 'uploads/')"
)
@click.option(
    "--key", "-k", default=None,
    help="Override object key (only valid when uploading a single file)",
)
@add_cred_options
def upload(paths, prefix, key, access_key, secret_key, bucket, endpoint, profile, as_json):
    """Upload one or more files. Supports shell globs.

    \b
    Examples:
      nevaobst upload photo.jpg
      nevaobst upload "images/*" --prefix uploads/2024/
      nevaobst upload report.pdf --key docs/report-q1.pdf
    """
    # Expand globs manually (needed when the shell doesn't, e.g. quoted globs)
    expanded = []
    for pattern in paths:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            expanded.extend(matches)
        else:
            expanded.append(pattern)  # let client raise FileNotFoundError

    files = [f for f in expanded if os.path.isfile(f)]
    dirs = [f for f in expanded if os.path.isdir(f)]

    if dirs:
        for d in dirs:
            click.echo(
                click.style("⚠", fg="yellow")
                + f"  Skipping directory: {d}  (use a glob like '{d}/**/*' to recurse)",
                err=True,
            )

    if not files:
        error("No files matched.", as_json=as_json)
        sys.exit(1)

    if key and len(files) > 1:
        raise click.UsageError("--key can only be used when uploading a single file.")

    client = make_client(access_key, secret_key, bucket, endpoint, profile)
    results = []

    for local_path in files:
        object_key = key if key else (prefix + os.path.basename(local_path))
        try:
            uploaded_key = client.upload(local_path, object_key=object_key)
            results.append({"status": "ok", "file": local_path, "key": uploaded_key})
        except (FileNotFoundError, NevaObjectsError) as exc:
            results.append({"status": "error", "file": local_path, "error": str(exc)})

    print_upload_results(results, as_json=as_json)

    failed = [r for r in results if r["status"] == "error"]
    if failed:
        sys.exit(1)


# --------------------------------------------------------------------------- #
# list                                                                         #
# --------------------------------------------------------------------------- #

@cli.command(name="list")
@click.option("--prefix", "-p", default="", help="Filter by key prefix")
@click.option("--file-size", "-s", "show_size", is_flag=True, help="Show file size")
@click.option("--file-modified", "-m", "show_modified", is_flag=True, help="Show last modified date")
@click.option("-fs", "show_size_and_modified", is_flag=True, help="Shortcut for -s -m")
@click.option("--max-keys", default=1000, show_default=True, help="Max objects to fetch")
@add_cred_options
def list_cmd(
    prefix, show_size, show_modified, show_size_and_modified,
    max_keys, access_key, secret_key, bucket, endpoint, profile, as_json,
):
    """List objects in the bucket.

    \b
    Examples:
      nevaobst list
      nevaobst list -fs
      nevaobst list --prefix uploads/ -s
    """
    if show_size_and_modified:
        show_size = True
        show_modified = True

    client = make_client(access_key, secret_key, bucket, endpoint, profile)
    try:
        objects = client.list(prefix=prefix, max_keys=max_keys)
    except NevaObjectsError as exc:
        error(str(exc), as_json=as_json)
        sys.exit(1)

    print_object_list(
        objects,
        as_json=as_json,
        show_size=show_size,
        show_modified=show_modified,
    )


# --------------------------------------------------------------------------- #
# get-url                                                                      #
# --------------------------------------------------------------------------- #

@cli.command(name="get-url")
@click.argument("object_key")
@click.option(
    "--expires", "-e",
    default=86400,
    show_default=True,
    help="URL validity in seconds (default: 86400 = 24h)",
)
@add_cred_options
def get_url(object_key, expires, access_key, secret_key, bucket, endpoint, profile, as_json):
    """Generate a pre-signed download URL for an object.

    \b
    Examples:
      nevaobst get-url photo.jpg
      nevaobst get-url report.pdf --expires 3600
    """
    client = make_client(access_key, secret_key, bucket, endpoint, profile)
    try:
        url = client.get_download_url(object_key, expires_in=expires)
    except NevaObjectsError as exc:
        error(str(exc), as_json=as_json)
        sys.exit(1)

    print_url(object_key, url, as_json=as_json)


# --------------------------------------------------------------------------- #
# info                                                                         #
# --------------------------------------------------------------------------- #

@cli.command()
@click.argument("object_key")
@add_cred_options
def info(object_key, access_key, secret_key, bucket, endpoint, profile, as_json):
    """Show metadata for an object (existence, size, ETag, etc.).

    \b
    Examples:
      nevaobst info photo.jpg
      nevaobst info photo.jpg --json
    """
    client = make_client(access_key, secret_key, bucket, endpoint, profile)
    try:
        exists = client.object_exists(object_key)
        if not exists:
            error(f"Object not found: {object_key}", as_json=as_json)
            sys.exit(1)

        # head_object for full metadata
        raw = client._s3.head_object(Bucket=client.config.bucket, Key=object_key)
        meta = {
            "size":          raw.get("ContentLength", "—"),
            "content_type":  raw.get("ContentType", "—"),
            "last_modified": str(raw.get("LastModified", "—")),
            "etag":          raw.get("ETag", "—").strip('"'),
            "storage_class": raw.get("StorageClass", "STANDARD"),
        }
    except NevaObjectsError as exc:
        error(str(exc), as_json=as_json)
        sys.exit(1)

    print_object_info(object_key, meta, as_json=as_json)


# --------------------------------------------------------------------------- #
# delete                                                                       #
# --------------------------------------------------------------------------- #

@cli.command()
@click.argument("object_keys", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@add_cred_options
def delete(object_keys, force, access_key, secret_key, bucket, endpoint, profile, as_json):
    """Delete one or more objects from the bucket.

    \b
    Examples:
      nevaobst delete photo.jpg
      nevaobst delete a.jpg b.jpg c.jpg --force
    """
    if not force and not as_json:
        keys_preview = ", ".join(object_keys[:5])
        if len(object_keys) > 5:
            keys_preview += f" … (+{len(object_keys) - 5} more)"
        click.confirm(
            f"Delete {len(object_keys)} object(s)? [{keys_preview}]",
            abort=True,
        )

    client = make_client(access_key, secret_key, bucket, endpoint, profile)
    results = []

    for key in object_keys:
        try:
            client.delete(key)
            results.append({"status": "ok", "key": key})
        except NevaObjectsError as exc:
            results.append({"status": "error", "key": key, "error": str(exc)})

    if as_json:
        import json as _json
        click.echo(_json.dumps(results, indent=2))
    else:
        for r in results:
            if r["status"] == "ok":
                ok(f"Deleted: {r['key']}")
            else:
                error(f"{r['key']}: {r['error']}")

    if any(r["status"] == "error" for r in results):
        sys.exit(1)


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #

def main():
    cli()


if __name__ == "__main__":
    main()