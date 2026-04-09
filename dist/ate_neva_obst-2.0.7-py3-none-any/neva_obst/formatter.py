"""
Output formatting helpers for nevaobst CLI.
Supports plain text and --json mode.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional


def _print_json(data: Any) -> None:
    click_echo(json.dumps(data, indent=2, default=str))


def click_echo(msg: str, err: bool = False) -> None:
    import click
    click.echo(msg, err=err)


# --------------------------------------------------------------------------- #
# Success / error                                                               #
# --------------------------------------------------------------------------- #

def ok(message: str, data: Optional[Dict] = None, *, as_json: bool = False) -> None:
    if as_json:
        _print_json({"status": "ok", "message": message, **(data or {})})
    else:
        import click
        click.echo(click.style("✓ ", fg="green") + message)


def error(message: str, data: Optional[Dict] = None, *, as_json: bool = False) -> None:
    if as_json:
        _print_json({"status": "error", "message": message, **(data or {})})
    else:
        import click
        click.echo(click.style("✗ ", fg="red") + message, err=True)


# --------------------------------------------------------------------------- #
# Tables                                                                        #
# --------------------------------------------------------------------------- #

def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} PB"


def _build_tree(objects: List) -> dict:
    """
    Convert a flat list of ObjectInfo into a nested dict tree.

    Example:
        ["a.txt", "folder/b.txt", "folder/c.txt"]
        →  {"__files__": [<a.txt>], "folder": {"__files__": [<b.txt>, <c.txt>]}}
    """
    tree: dict = {}
    for obj in objects:
        parts = obj.key.split("/")
        node = tree
        for part in parts[:-1]:          # walk/create folder nodes
            node = node.setdefault(part, {})
        node.setdefault("__files__", []).append(obj)
    return tree


def _render_tree(
    node: dict,
    indent: int = 0,
    *,
    show_size: bool = False,
    show_modified: bool = False,
) -> None:
    import click

    pad = "   " * indent

    # Files first, then sub-folders
    for obj in node.get("__files__", []):
        name = obj.key.split("/")[-1]
        meta_parts = []
        if show_size:
            meta_parts.append(click.style(_human_size(obj.size), fg="cyan"))
        if show_modified:
            meta_parts.append(click.style(str(obj.last_modified), fg="yellow"))
        meta = ("  " + "  ".join(meta_parts)) if meta_parts else ""
        click_echo(f"{pad}📄 {name}{meta}")

    for key, child in node.items():
        if key == "__files__":
            continue
        click_echo(f"{pad}📁 {click.style(key + '/', bold=True)}")
        _render_tree(child, indent + 1, show_size=show_size, show_modified=show_modified)


def print_object_list(
    objects: List,
    *,
    as_json: bool = False,
    show_size: bool = False,
    show_modified: bool = False,
) -> None:
    """Print a list of ObjectInfo items as a tree."""
    if as_json:
        _print_json([
            {
                "key": o.key,
                "size": o.size,
                "last_modified": str(o.last_modified),
                "etag": o.etag,
            }
            for o in objects
        ])
        return

    if not objects:
        click_echo("(bucket is empty)")
        return

    tree = _build_tree(objects)
    _render_tree(tree, show_size=show_size, show_modified=show_modified)



def print_url(key: str, url: str, *, as_json: bool = False) -> None:
    if as_json:
        _print_json({"key": key, "url": url})
    else:
        click_echo(url)


def print_object_info(key: str, info: Dict, *, as_json: bool = False) -> None:
    if as_json:
        _print_json({"key": key, **info})
        return

    import click
    click_echo(click.style(key, bold=True))
    for k, v in info.items():
        click_echo(f"  {k:<18} {v}")


def print_upload_results(
    results: List[Dict],
    *,
    as_json: bool = False,
) -> None:
    """Print a summary table for (bulk) upload results."""
    if as_json:
        _print_json(results)
        return

    import click
    ok_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = len(results) - ok_count

    for r in results:
        icon = click.style("✓", fg="green") if r["status"] == "ok" else click.style("✗", fg="red")
        msg = r.get("key", r.get("error", ""))
        click_echo(f"  {icon}  {r['file']}  →  {msg}")

    click_echo("")
    click_echo(
        f"Uploaded {click.style(str(ok_count), fg='green', bold=True)} file(s)"
        + (f", {click.style(str(fail_count), fg='red', bold=True)} failed" if fail_count else "")
    )