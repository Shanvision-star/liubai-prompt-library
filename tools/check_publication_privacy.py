#!/usr/bin/env python3
"""Check the complete proposed Git index before publishing; nothing is uploaded."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

# These types can conceal screenshots, metadata, embedded files, or encoded text
# even when a particular file can be decoded as UTF-8.
OPAQUE_SUFFIXES = set("""
7z aac apk avif bin bmp bz2 csvz db dmg doc docm docx exe flac gif gz ico
iso jar jpeg jpg m4a mkv mov mp3 mp4 msi odg odp ods odt ogg otf pdf png ppt
pptm pptx psd rar sqlite svgz tar tif tiff ttf wav webm webp woff woff2 xls
xlsb xlsm xlsx xz zip zst
""".split())
MAX_TEXT_BYTES = 16 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


class CheckError(Exception):
    """A failure that makes the publication snapshot unverifiable."""


def normalized(text):
    return unicodedata.normalize(
        "NFKC", unicodedata.normalize("NFKC", text).casefold()
    )


def git(*args, cwd=None):
    # Silence diagnostics that may contain private paths or other input values.
    return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.DEVNULL)


def private_file(path, root, label):
    try:
        given = Path(path).expanduser().absolute()
        actual = given.resolve(strict=True)
        if given.is_relative_to(root) or actual.is_relative_to(root):
            raise CheckError(f"{label} must be outside the repository.")
        if not actual.is_file():
            raise CheckError(f"{label} must be a regular file.")
        return actual.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError, RuntimeError) as exc:
        raise CheckError(f"Cannot read {label} as UTF-8.") from exc


def deny_terms(path, root):
    terms = sorted({normalized(line) for line in private_file(path, root, "denylist")
                    .splitlines() if line.strip()})
    if not terms or any(not term.strip() for term in terms):
        raise CheckError("The private denylist must contain at least one nonblank literal.")
    return terms


def unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise CheckError("Duplicate path in opaque review manifest.")
        obj[key] = value
    return obj


def reviews(path, root):
    if path is None:
        return {}
    try:
        entries = json.loads(private_file(path, root, "opaque review manifest"),
                             object_pairs_hook=unique_keys)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise CheckError("Opaque review manifest must be a JSON object.") from exc
    if not isinstance(entries, dict) or any(
        not key or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        for key, digest in entries.items()
    ):
        raise CheckError("Opaque reviews must map exact Git paths to lowercase SHA-256 hashes.")
    return entries


def indexed_paths(root):
    return git("ls-files", "--stage", "--full-name", "-z", cwd=root)


def entries(snapshot):
    for index, item in enumerate(snapshot.split(b"\0")[:-1], 1):
        try:
            meta, path = item.split(b"\t", 1)
            mode, oid, stage = meta.split()
            if not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", oid):
                raise ValueError
        except ValueError as exc:
            raise CheckError("Cannot parse Git index entry.") from exc
        yield index, mode, oid, stage, path


def read_blob(proc, oid):
    proc.stdin.write(oid + b"\n")
    proc.stdin.flush()
    fields = proc.stdout.readline().split()
    if len(fields) != 3 or fields[:2] != [oid, b"blob"] or not fields[2].isdigit():
        raise CheckError("A staged blob is missing or unreadable.")
    size = int(fields[2])
    keep_content = size <= MAX_TEXT_BYTES
    remaining, pieces = size, []
    digest = hashlib.sha256()
    while remaining:
        part = proc.stdout.read(min(remaining, CHUNK_BYTES))
        if not part:
            raise CheckError("A staged blob was truncated during review.")
        digest.update(part)
        if keep_content:
            pieces.append(part)
        remaining -= len(part)
    if proc.stdout.read(1) != b"\n":
        raise CheckError("Invalid response from Git object reader.")
    return (b"".join(pieces) if keep_content else None), digest.hexdigest()


def contains(text, terms):
    candidate = normalized(text)
    return any(term in candidate for term in terms)


def decode_content(raw):
    if raw is None:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Decode other conventional Unicode encodings only with an explicit BOM.
        for bom, encoding in ((b"\xff\xfe\x00\x00", "utf-32"),
                              (b"\x00\x00\xfe\xff", "utf-32"),
                              (b"\xff\xfe", "utf-16"),
                              (b"\xfe\xff", "utf-16")):
            if raw.startswith(bom):
                try:
                    return raw.decode(encoding)
                except UnicodeDecodeError:
                    break
        # A UTF-8 replacement view can still expose visible fragments in binaries.
        return raw.decode("utf-8", errors="replace")


def opaque_reason(mode, path, raw, content):
    if mode == b"120000":
        return "symlink"
    if raw is None:
        return "oversized blob"
    if Path(path).suffix.lower().removeprefix(".") in OPAQUE_SUFFIXES:
        return "opaque file type"
    if raw.startswith((b"PK\x03\x04", b"%PDF-", b"\x7fELF", b"\x89PNG", b"GIF87a",
                       b"GIF89a", b"\x1f\x8b", b"SQLite format 3\0", b"Rar!")):
        return "opaque file signature"
    # Treat replacement or non-text control characters as opaque.
    if "\ufffd" in content or any(
        unicodedata.category(char) == "Cc" and char not in "\t\r\n\f" for char in content
    ):
        return "binary or unknown encoding"
    return None


def inspect(root, terms, acknowledgements):
    snapshot = indexed_paths(root)
    problems, count = [], 0
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=root, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
        for count, mode, oid, stage, encoded_path in entries(snapshot):
            loc = f"index entry #{count} (path withheld)"
            try:
                path = encoded_path.decode("utf-8")
            except UnicodeDecodeError:
                problems.append(f"{loc}: non-UTF-8 path cannot be reviewed.")
                continue
            if contains(path, terms):
                problems.append(f"{loc}: blocked literal in path.")
            else:
                # JSON escaping keeps a crafted filename from injecting output lines.
                loc = json.dumps(path, ensure_ascii=True)
            if stage != b"0":
                problems.append(f"{loc}: unmerged entry; resolve before review.")
                continue
            if mode not in (b"100644", b"100755", b"120000"):
                problems.append(f"{loc}: unsupported entry type; remove or review separately.")
                continue
            raw, digest = read_blob(proc, oid)
            content = decode_content(raw)
            if content is not None:
                for line_no, line in enumerate(content.split("\n"), 1):
                    if contains(line, terms):
                        problems.append(f"{loc}:{line_no}: blocked literal in staged content.")
            if content is not None and content.startswith("version https://git-lfs.github.com/spec/v1"):
                problems.append(f"{loc}: Git LFS pointer does not cover its external payload.")
                continue
            reason = opaque_reason(mode, path, raw, content)
            if reason and acknowledgements.get(path) != digest:
                problems.append(f"{loc}: {reason}; exact-path SHA-256 review missing or stale.")
        proc.stdin.close()
        if proc.wait():
            raise CheckError("Git object reader failed.")
    if indexed_paths(root) != snapshot:
        raise CheckError("Git index changed during review. Rerun against the final snapshot.")
    if count == 0:
        raise CheckError("Git index has no paths to review.")
    return count, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--denylist", required=True, metavar="PRIVATE_PATH",
                        help="external UTF-8 text file, one nonblank literal per line")
    parser.add_argument("--opaque-reviews", metavar="PRIVATE_JSON",
                        help="external JSON: exact repository-relative path to raw blob SHA-256")
    args = parser.parse_args(argv)
    try:
        root = Path(git("rev-parse", "--show-toplevel").decode("utf-8").rstrip("\r\n")).resolve()
        count, problems = inspect(root, deny_terms(args.denylist, root),
                                  reviews(args.opaque_reviews, root))
    except CheckError as exc:
        print(f"Publication blocked: {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, subprocess.SubprocessError):
        print("Publication blocked: unable to read the Git snapshot.", file=sys.stderr)
        return 2
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"Publication blocked ({len(problems)} finding(s)).", file=sys.stderr)
        return 1
    print(f"Publication check passed for {count} staged path(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
