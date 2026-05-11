#!/usr/bin/env python3
"""Export repo-scoped Codex exec sessions into reviewable Markdown and HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "pipeline-lab/showcases/real-showcases.yaml"
DEFAULT_OUT_DIR = ROOT / "pipeline-lab/showcases/nfp-real-runs/conversations"
REPO_PATTERN = re.compile(r"/pipeline-lab/showcases/repos/([^/\s]+)")


def load_showcases() -> dict[str, dict[str, Any]]:
    return yaml.safe_load(CONFIG_PATH.read_text())["showcases"]


def load_session_index() -> dict[str, dict[str, Any]]:
    index_path = Path.home() / ".codex/session_index.jsonl"
    if not index_path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for line in index_path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("id"):
            records[record["id"]] = record
    return records


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            text = item.get("text") or item.get("input_text")
            if text:
                parts.append(str(text))
    return "\n\n".join(parts)


def first_session_meta(path: Path) -> dict[str, Any] | None:
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "session_meta":
            return event.get("payload", {})
    return None


def repo_from_cwd(cwd: str) -> str | None:
    match = REPO_PATTERN.search(cwd)
    return match.group(1) if match else None


def collect_session_paths(date: str, showcases: dict[str, dict[str, Any]]) -> list[tuple[str, Path, dict[str, Any]]]:
    sessions_dir = Path.home() / ".codex/sessions" / date
    if not sessions_dir.exists():
        return []
    repo_names = set(showcases)
    sessions: list[tuple[str, Path, dict[str, Any]]] = []
    for path in sorted(sessions_dir.glob("*.jsonl")):
        meta = first_session_meta(path)
        if not meta:
            continue
        repo = repo_from_cwd(meta.get("cwd", ""))
        if repo in repo_names and meta.get("source") == "exec":
            sessions.append((repo, path, meta))
    return sessions


def parse_session(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pending_calls: dict[str, dict[str, Any]] = {}
    seen_messages: set[tuple[str, str]] = set()

    def add_message(timestamp: str, role: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        key = (role, text)
        if key in seen_messages:
            return
        seen_messages.add(key)
        items.append({"kind": "message", "timestamp": timestamp, "role": role, "text": text})

    for line in path.read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = event.get("timestamp", "")
        event_type = event.get("type")
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue

        if event_type == "event_msg":
            payload_type = payload.get("type")
            if payload_type == "user_message":
                add_message(timestamp, "user", payload.get("message", ""))
            elif payload_type == "agent_message":
                add_message(timestamp, "assistant", payload.get("message", ""))
            elif payload_type in {"task_started", "task_complete", "task_completed"}:
                items.append({"kind": "event", "timestamp": timestamp, "event": payload_type})
            continue

        if event_type != "response_item":
            continue

        payload_type = payload.get("type")
        if payload_type == "message":
            role = payload.get("role", "unknown")
            if role in {"system", "developer"}:
                continue
            add_message(timestamp, role, text_from_content(payload.get("content")))
        elif payload_type == "function_call":
            call_id = payload.get("call_id", "")
            arguments = payload.get("arguments", "")
            try:
                parsed_args = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_args = {"raw": arguments}
            item = {
                "kind": "tool_call",
                "timestamp": timestamp,
                "call_id": call_id,
                "name": payload.get("name", "unknown"),
                "arguments": parsed_args,
                "output": "",
            }
            pending_calls[call_id] = item
            items.append(item)
        elif payload_type == "function_call_output":
            call_id = payload.get("call_id", "")
            output = payload.get("output", "")
            if call_id in pending_calls:
                pending_calls[call_id]["output"] = output
            else:
                items.append(
                    {
                        "kind": "tool_output",
                        "timestamp": timestamp,
                        "call_id": call_id,
                        "output": output,
                    }
                )
    return items


def markdown_fence(text: str, language: str = "text") -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{language}\n{text.rstrip()}\n{ticks}"


def clean_rendered(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def render_markdown(session: dict[str, Any]) -> str:
    lines = [
        f"# {session['repo']} - {session['title']}",
        "",
        f"- Session id: `{session['id']}`",
        f"- Started: `{session['timestamp']}`",
        f"- Source JSONL: `{session['source_path']}`",
        f"- Repository: `{session['cwd']}`",
        f"- Final session for repo: `{str(session['final_for_repo']).lower()}`",
        f"- Feature: {session['feature_goal']}",
        "",
        "> Hidden developer/system instructions and encrypted reasoning are intentionally omitted. The export keeps user prompts, assistant-visible messages, tool calls, and tool outputs.",
        "",
        "## Conversation",
        "",
    ]
    for index, item in enumerate(session["items"], start=1):
        kind = item["kind"]
        if kind == "message":
            role = item["role"]
            lines.extend(
                [
                    f"<details open><summary>{index}. {role} - {item['timestamp']}</summary>",
                    "",
                    markdown_fence(item["text"]),
                    "",
                    "</details>",
                    "",
                ]
            )
        elif kind == "tool_call":
            args = item["arguments"]
            cmd = args.get("cmd") if isinstance(args, dict) else None
            workdir = args.get("workdir") if isinstance(args, dict) else None
            summary = f"{item['name']}"
            if cmd:
                summary += f": {cmd[:180]}"
                if len(cmd) > 180:
                    summary += "..."
            lines.extend(
                [
                    f"<details><summary>{index}. tool call - {summary}</summary>",
                    "",
                    f"- Timestamp: `{item['timestamp']}`",
                    f"- Call id: `{item['call_id']}`",
                    f"- Workdir: `{workdir or ''}`",
                    "",
                    "Arguments:",
                    "",
                    markdown_fence(json.dumps(args, indent=2, sort_keys=True), "json"),
                    "",
                    "Output:",
                    "",
                    markdown_fence(item.get("output") or "(no output recorded)"),
                    "",
                    "</details>",
                    "",
                ]
            )
        elif kind == "event":
            lines.append(f"- `{item['timestamp']}` event: `{item['event']}`")
            lines.append("")
        elif kind == "tool_output":
            lines.extend(
                [
                    f"<details><summary>{index}. tool output - {item['call_id']}</summary>",
                    "",
                    markdown_fence(item.get("output") or "(no output recorded)"),
                    "",
                    "</details>",
                    "",
                ]
            )
    return clean_rendered("\n".join(lines))


def render_html(session: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    chunks = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        f"<title>{esc(session['repo'])} - {esc(session['title'])}</title>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;background:#f7f7f4;color:#171717;line-height:1.45}",
        "main{max-width:1180px;margin:0 auto;padding:32px 24px 56px}",
        "a{color:#0a5c7a} .meta{display:grid;grid-template-columns:max-content 1fr;gap:8px 16px;background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px}",
        ".item{background:#fff;border:1px solid #ddd;border-radius:8px;margin:14px 0;padding:14px 16px}",
        ".role{font-weight:700;text-transform:uppercase;font-size:12px;color:#555}.stamp{font-size:12px;color:#777;margin-left:8px}",
        "pre{white-space:pre-wrap;word-break:break-word;background:#1f2328;color:#f0f3f6;border-radius:6px;padding:12px;overflow:auto}",
        "details summary{cursor:pointer;font-weight:700}.note{color:#555}",
        "</style>",
        "</head>",
        "<body><main>",
        f"<p><a href=\"../index.html\">Back to index</a></p>",
        f"<h1>{esc(session['repo'])} - {esc(session['title'])}</h1>",
        "<div class=\"meta\">",
        f"<strong>Session id</strong><span><code>{esc(session['id'])}</code></span>",
        f"<strong>Started</strong><span><code>{esc(session['timestamp'])}</code></span>",
        f"<strong>Repository</strong><span><code>{esc(session['cwd'])}</code></span>",
        f"<strong>Final for repo</strong><span><code>{str(session['final_for_repo']).lower()}</code></span>",
        f"<strong>Feature</strong><span>{esc(session['feature_goal'])}</span>",
        "</div>",
        "<p class=\"note\">Hidden developer/system instructions and encrypted reasoning are intentionally omitted. The export keeps user prompts, assistant-visible messages, tool calls, and tool outputs.</p>",
    ]
    for index, item in enumerate(session["items"], start=1):
        kind = item["kind"]
        if kind == "message":
            chunks.extend(
                [
                    "<section class=\"item\">",
                    f"<div><span class=\"role\">{esc(index)}. {esc(item['role'])}</span><span class=\"stamp\">{esc(item['timestamp'])}</span></div>",
                    f"<pre>{esc(item['text'])}</pre>",
                    "</section>",
                ]
            )
        elif kind == "tool_call":
            args = item["arguments"]
            cmd = args.get("cmd") if isinstance(args, dict) else ""
            workdir = args.get("workdir") if isinstance(args, dict) else ""
            cmd = cmd or ""
            workdir = workdir or ""
            chunks.extend(
                [
                    "<section class=\"item\">",
                    f"<details><summary>{esc(index)}. tool call - {esc(item['name'])}: {esc(cmd[:180])}</summary>",
                    f"<p><strong>Timestamp:</strong> <code>{esc(item['timestamp'])}</code></p>",
                    f"<p><strong>Call id:</strong> <code>{esc(item['call_id'])}</code></p>",
                    f"<p><strong>Workdir:</strong> <code>{esc(workdir)}</code></p>",
                    "<h4>Arguments</h4>",
                    f"<pre>{esc(json.dumps(args, indent=2, sort_keys=True))}</pre>",
                    "<h4>Output</h4>",
                    f"<pre>{esc(item.get('output') or '(no output recorded)')}</pre>",
                    "</details>",
                    "</section>",
                ]
            )
        elif kind == "event":
            chunks.append(
                f"<section class=\"item\"><span class=\"role\">event</span> <code>{esc(item['timestamp'])}</code> {esc(item['event'])}</section>"
            )
        elif kind == "tool_output":
            chunks.extend(
                [
                    "<section class=\"item\">",
                    f"<details><summary>{esc(index)}. tool output - {esc(item['call_id'])}</summary>",
                    f"<pre>{esc(item.get('output') or '(no output recorded)')}</pre>",
                    "</details>",
                    "</section>",
                ]
            )
    chunks.append("</main></body></html>")
    return clean_rendered("\n".join(chunks))


def session_slug(repo: str, meta: dict[str, Any]) -> str:
    timestamp = str(meta.get("timestamp", "unknown")).replace(":", "").replace(".", "-")
    session_id = str(meta.get("id", "unknown"))
    return f"{repo}-{timestamp}-{session_id}"


def write_index(out_dir: Path, sessions: list[dict[str, Any]]) -> None:
    lines = [
        "# Codex Subagent Conversation Export",
        "",
        "Repo-scoped `codex exec` sessions from the fresh NFP real-repo implementation run.",
        "",
        "Hidden developer/system instructions and encrypted reasoning are omitted. The per-session exports include user prompts, assistant-visible messages, tool calls, and tool outputs.",
        "",
        "| Repo | Final | Started | Session | Markdown | HTML |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for session in sessions:
        repo_dir = session["repo"]
        lines.append(
            f"| `{session['repo']}` | `{str(session['final_for_repo']).lower()}` | "
            f"`{session['timestamp']}` | `{session['id']}` | "
            f"[md]({repo_dir}/{session['slug']}.md) | [html]({repo_dir}/{session['slug']}.html) |"
        )
    lines.append("")
    (out_dir / "index.md").write_text(clean_rendered("\n".join(lines)))

    def esc(value: Any) -> str:
        return html.escape(str(value), quote=True)

    rows = []
    for session in sessions:
        rows.append(
            "<tr>"
            f"<td><code>{esc(session['repo'])}</code></td>"
            f"<td><code>{str(session['final_for_repo']).lower()}</code></td>"
            f"<td><code>{esc(session['timestamp'])}</code></td>"
            f"<td><code>{esc(session['id'])}</code></td>"
            f"<td><a href=\"{esc(session['repo'])}/{esc(session['slug'])}.md\">Markdown</a></td>"
            f"<td><a href=\"{esc(session['repo'])}/{esc(session['slug'])}.html\">HTML</a></td>"
            "</tr>"
        )
    html_index = "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<title>Codex Subagent Conversation Export</title>",
            "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;background:#f7f7f4;color:#171717}table{border-collapse:collapse;width:100%;background:white}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#efefea}a{color:#0a5c7a}</style>",
            "</head><body>",
            "<h1>Codex Subagent Conversation Export</h1>",
            "<p>Repo-scoped <code>codex exec</code> sessions from the fresh NFP real-repo implementation run.</p>",
            "<p>Hidden developer/system instructions and encrypted reasoning are omitted. The per-session exports include user prompts, assistant-visible messages, tool calls, and tool outputs.</p>",
            "<table><thead><tr><th>Repo</th><th>Final</th><th>Started</th><th>Session</th><th>Markdown</th><th>HTML</th></tr></thead><tbody>",
            *rows,
            "</tbody></table>",
            "</body></html>",
        ]
    )
    (out_dir / "index.html").write_text(clean_rendered(html_index))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026/05/11", help="Session date path under ~/.codex/sessions, e.g. 2026/05/11")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for generated review export")
    args = parser.parse_args()

    showcases = load_showcases()
    index = load_session_index()
    out_dir = Path(args.out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    collected = collect_session_paths(args.date, showcases)
    latest_by_repo: dict[str, str] = {}
    for repo, _path, meta in collected:
        timestamp = str(meta.get("timestamp", ""))
        if timestamp >= latest_by_repo.get(repo, ""):
            latest_by_repo[repo] = timestamp

    sessions: list[dict[str, Any]] = []
    for repo, path, meta in collected:
        case = showcases[repo]
        slug = session_slug(repo, meta)
        repo_dir = out_dir / repo
        repo_dir.mkdir(parents=True, exist_ok=True)
        session = {
            "repo": repo,
            "title": case["title"],
            "feature_goal": case["feature_goal"],
            "id": meta.get("id", ""),
            "thread_name": index.get(meta.get("id", ""), {}).get("thread_name", ""),
            "timestamp": meta.get("timestamp", ""),
            "cwd": meta.get("cwd", ""),
            "source_path": str(path),
            "source": meta.get("source", ""),
            "cli_version": meta.get("cli_version", ""),
            "final_for_repo": meta.get("timestamp", "") == latest_by_repo.get(repo),
            "slug": slug,
            "items": parse_session(path),
        }
        (repo_dir / f"{slug}.md").write_text(render_markdown(session))
        (repo_dir / f"{slug}.html").write_text(render_html(session))
        sessions.append(session)

    manifest = [
        {
            key: value
            for key, value in session.items()
            if key not in {"items"}
        }
        | {"item_count": len(session["items"])}
        for session in sessions
    ]
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump({"sessions": manifest}, sort_keys=False))
    write_index(out_dir, sessions)
    print(f"Exported {len(sessions)} sessions to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
