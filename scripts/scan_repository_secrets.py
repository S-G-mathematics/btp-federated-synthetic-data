"""Conservative pre-push scan; reports paths and pattern names, never values."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private_key_block": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "openai_style_key": re.compile(rb"sk-[A-Za-z0-9]{24,}"),
    "credential_assignment": re.compile(rb"(?i)(?:api[_-]?key|license[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{30,}"),
}
TEXT = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".log", ".toml", ".bib", ".tex", ".cff", ".xml", ".sh"}


def main() -> None:
    issues = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT:
            continue
        if path.name.startswith(".env") or path.suffix.lower() in {".pem", ".key"}:
            issues.append((path.relative_to(ROOT).as_posix(), "credential_filename"))
            continue
        data = path.read_bytes()
        for name, pattern in PATTERNS.items():
            if pattern.search(data):
                issues.append((path.relative_to(ROOT).as_posix(), name))
    if issues:
        for path, name in issues:
            print(f"{path}: {name}")
        raise SystemExit(f"Secret scan requires review: {len(issues)} path-pattern hits")
    print("Secret scan: no matching credentials or private-key blocks in packaged text files")


if __name__ == "__main__":
    main()
