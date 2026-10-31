"""Verify every member of the delivered ZIP against its embedded SHA-256 list."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def hash_stream(stream) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def verify(archive: Path) -> dict:
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member names")
        for name in names:
            parts = PurePosixPath(name).parts
            if not parts or name.startswith("/") or ".." in parts or "\\" in name:
                raise ValueError(f"Unsafe ZIP member path: {name}")
            if any(part in {".venv", ".git", "private", "genuity_env"} for part in parts):
                raise ValueError(f"Excluded directory in ZIP: {name}")
            if name.endswith((".pem", ".key")):
                raise ValueError(f"Credential-shaped ZIP member: {name}")
        manifest_name = "btp_ec2_handoff/ARTIFACT_SHA256_MANIFEST.json"
        manifest = json.loads(bundle.read(manifest_name))
        if manifest["archive_name"] != archive.name:
            raise ValueError("Archive filename differs from embedded manifest")
        entries = manifest["files"]
        expected = {"btp_ec2_handoff/" + item["path"] for item in entries}
        original = manifest["original_handoff_zip"]
        expected.update({manifest_name, original["path"]})
        if set(names) != expected or manifest["file_count"] != len(entries):
            raise ValueError("ZIP members do not exactly match the manifest")
        for item in entries:
            name = "btp_ec2_handoff/" + item["path"]
            if bundle.getinfo(name).file_size != item["bytes"]:
                raise ValueError(f"Size mismatch: {name}")
            with bundle.open(name) as stream:
                if hash_stream(stream) != item["sha256"]:
                    raise ValueError(f"SHA-256 mismatch: {name}")
        with bundle.open(original["path"]) as stream:
            if hash_stream(stream) != original["sha256"]:
                raise ValueError("Original handoff ZIP SHA-256 mismatch")
    return {"status": "verified", "archive": str(archive.resolve()),
            "project_files": len(entries), "zip_members": len(names),
            "original_handoff_sha256": original["sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive), sort_keys=True))


if __name__ == "__main__":
    main()
