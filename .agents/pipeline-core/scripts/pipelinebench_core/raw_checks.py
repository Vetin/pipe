"""Public raw artifact checks for pipelinebench."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from .common import BenchError

DEFAULT_RAW_BASE_URL = "https://raw.githubusercontent.com/Vetin/pipe/main"
DEFAULT_RAW_PATHS = [
    ".agents/pipeline-core/scripts/featurectl.py",
    ".agents/pipeline-core/scripts/pipelinebench.py",
    ".gitignore",
    ".ai/features/index.yaml",
    ".ai/features/pipeline/raw-schema-and-execution-boundary-hardening/events.yaml",
]


@dataclass(frozen=True)
class RawCheckResult:
    path: str
    line_count: int
    passed: bool


def check_public_raw_paths(base_url: str, paths: list[str], min_lines: int) -> list[RawCheckResult]:
    results = []
    for path in paths:
        content = fetch_raw_bytes(base_url, path)
        line_count = content.count(b"\n")
        results.append(RawCheckResult(path=path, line_count=line_count, passed=line_count >= min_lines))
    return results


def fetch_raw_bytes(base_url: str, path: str) -> bytes:
    url = raw_url(base_url, path)
    try:
        with urlopen(url, timeout=20) as response:
            return response.read()
    except URLError as exc:
        raise BenchError(f"failed to fetch raw artifact {path}: {exc}") from exc


def raw_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    quoted_path = "/".join(quote(part) for part in path.strip("/").split("/"))
    return f"{base}/{quoted_path}"

