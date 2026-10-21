#!/usr/bin/env python3
"""Manage local blog metadata and import unwrapped Typst articles."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile


MANAGED_HEADER = (
    '#import "/site-lib/post.typ": post-template, tufted\n'
    '#show: post-template.with(json("_post.json"))\n\n'
).encode("utf-8")
POST_FIELDS = {"title", "description", "date", "lang", "categories"}
TEMPLATE_HEADER = re.compile(
    r"^[ \t]*#(?:show\s*:\s*(?:post-template|template)\s*\.with\b"
    r"|import\s+\"[^\"\n]+\"\s*:\s*[^\n]*\b(?:post-template|template)\b)",
    re.MULTILINE,
)


class BlogError(Exception):
    """An actionable user input or project-data error."""


@dataclass(frozen=True)
class Post:
    slug: str
    metadata: dict


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def validate_slug(slug):
    if (
        not isinstance(slug, str)
        or not slug
        or slug in {".", ".."}
        or slug.startswith("_")
        or any(character in slug for character in ("/", "\\", "\0"))
    ):
        raise BlogError(f"unsafe article slug: {slug!r}")
    return slug


def validate_date(value, context):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise BlogError(f"{context}: date must be a real YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise BlogError(f"{context}: invalid date {value!r}") from None
    if parsed.isoformat() != value:
        raise BlogError(f"{context}: date must use canonical YYYY-MM-DD format")


def validate_metadata(value, context):
    if not isinstance(value, dict) or set(value) != POST_FIELDS:
        raise BlogError(f"{context}: metadata must contain exactly title, description, date, lang, categories")
    for field in ("title", "lang"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise BlogError(f"{context}: {field} must be a nonblank string")
    if not isinstance(value["description"], str):
        raise BlogError(f"{context}: description must be a string")
    validate_date(value["date"], context)
    categories = value["categories"]
    if not isinstance(categories, list):
        raise BlogError(f"{context}: categories must be a list of unique nonblank strings")
    seen = set()
    for category in categories:
        if not isinstance(category, str) or not category.strip():
            raise BlogError(f"{context}: categories must be nonblank strings")
        if category in seen:
            raise BlogError(f"{context}: duplicate category {category!r}")
        seen.add(category)
    return value


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BlogError(f"missing {path}") from None
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BlogError(f"invalid JSON in {path}: {error}") from None


def resolve_root(root=None):
    root = Path(root).expanduser().resolve() if root is not None else Path(__file__).resolve().parent.parent
    if not (root / "config.typ").is_file():
        raise BlogError(f"project root requires config.typ: {root}")
    if not (root / "content" / "Blog").is_dir():
        raise BlogError(f"project root requires content/Blog: {root}")
    return root


def article_path(blog, slug):
    validate_slug(slug)
    target = blog / slug
    if target.resolve().parent != blog.resolve():
        raise BlogError(f"article escapes Blog directory: {slug!r}")
    return target


def scan_posts(blog):
    posts = []
    for directory in sorted(blog.iterdir(), key=lambda path: path.name):
        if directory.name.startswith("_") or not directory.is_dir():
            continue
        article = directory / "index.typ"
        if not article.exists() and not article.is_symlink():
            continue
        article_path(blog, directory.name)
        if not article.is_file():
            raise BlogError(f"article is not a regular file: {article}")
        metadata_path = directory / "_post.json"
        metadata = validate_metadata(read_json(metadata_path), str(metadata_path))
        posts.append(Post(directory.name, metadata))
    return posts


def build_index(posts):
    grouped = defaultdict(list)
    # Stable sorting retains slug order when dates tie.
    ordered = sorted(posts, key=lambda post: post.slug)
    ordered.sort(key=lambda post: post.metadata["date"], reverse=True)
    for post in ordered:
        item = {"date": post.metadata["date"], "path": post.slug + "/", "title": post.metadata["title"]}
        for category in post.metadata["categories"] or ["未分类"]:
            grouped[category].append(item)
    return [
        {"category": category, "posts": grouped[category]}
        for category in sorted(grouped, key=lambda category: (category == "未分类", category))
    ]


def atomic_write(path, data):
    """Replace one file only after its complete bytes are safely staged beside it."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_index(blog, index):
    path = blog / "_index.json"
    data = json_bytes(index)
    try:
        if path.read_bytes() == data:
            return False
    except FileNotFoundError:
        pass
    atomic_write(path, data)
    return True


def validate_index(value, path):
    def invalid(detail):
        raise BlogError(f"invalid index {path}: {detail}; run reindex")

    if not isinstance(value, list):
        invalid("expected an array of category groups")
    for group in value:
        if not isinstance(group, dict) or set(group) != {"category", "posts"}:
            invalid("each group needs exactly category and posts")
        if not isinstance(group["category"], str) or not group["category"].strip():
            invalid("category must be a nonblank string")
        if not isinstance(group["posts"], list):
            invalid("posts must be an array")
        for post in group["posts"]:
            if not isinstance(post, dict) or set(post) != {"date", "path", "title"}:
                invalid("each post needs exactly date, path and title")
            if not isinstance(post["title"], str) or not post["title"].strip():
                invalid("post title must be a nonblank string")
            validate_date(post["date"], f"invalid index {path}")
            if not isinstance(post["path"], str) or not post["path"].endswith("/"):
                invalid("post path must be a relative slug ending in /")
            try:
                validate_slug(post["path"][:-1])
            except BlogError as error:
                invalid(str(error))


def check(blog, posts):
    index_path = blog / "_index.json"
    persisted = read_json(index_path)
    validate_index(persisted, index_path)
    expected = build_index(posts)
    if persisted != expected:
        raise BlogError(f"stale index {index_path}; run reindex")
    print(f"OK: {len(posts)} articles, {len(expected)} categories")


def choose_source():
    with tempfile.TemporaryDirectory(prefix="blog-yazi-") as temporary:
        chooser = Path(temporary) / "selection"
        chooser.touch()
        result = subprocess.run(["yazi", "--chooser-file", str(chooser)], cwd=Path.cwd(), check=False)
        if result.returncode in (130, -signal.SIGINT):
            return None
        if result.returncode != 0:
            raise BlogError(f"yazi exited with status {result.returncode}")
        choices = chooser.read_text(encoding="utf-8").splitlines()
        if not choices or choices == [""]:
            return None
        if len(choices) != 1:
            raise BlogError("select exactly one Typst source in yazi")
        return Path(choices[0])


def prompt(label, default=""):
    answer = input(f"{label}" + (f" [{default}]" if default else "") + ": ")
    return answer if answer else default


def import_post(blog, args):
    source = Path(args.source).expanduser() if args.source is not None else choose_source()
    if source is None:
        print("Import cancelled.")
        return
    if source.suffix.lower() != ".typ" or not source.is_file():
        raise BlogError(f"source must be a regular .typ file: {source}")
    body = source.read_bytes()
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        raise BlogError(f"source must be UTF-8: {source}") from None
    if TEMPLATE_HEADER.search(text.lstrip("\ufeff")):
        raise BlogError("source already has a managed or legacy template header; import an unwrapped body")

    interactive = sys.stdin.isatty()
    title = args.title
    if title is None:
        if not interactive:
            raise BlogError("--title is required when stdin is not a TTY")
        title = prompt("Title")
    defaults = {"description": "", "date": date.today().isoformat(), "lang": "zh"}
    metadata = {"title": title}
    for field, default in defaults.items():
        supplied = getattr(args, field)
        metadata[field] = prompt(field.capitalize(), default) if supplied is None and interactive else (default if supplied is None else supplied)
    categories = args.category
    if categories is None:
        categories = [value.strip() for value in prompt("Categories (comma-separated)").split(",") if value.strip()] if interactive else []
    metadata["categories"] = categories
    slug = args.slug
    if slug is None:
        slug = prompt("Slug", source.stem) if interactive else source.stem
    validate_slug(slug)
    target = blog / slug
    print(f"Target: {target}")
    if os.path.lexists(target):
        raise BlogError(f"target already exists: {target}")
    article_path(blog, slug)
    validate_metadata(metadata, "new article")
    posts = scan_posts(blog)
    index = build_index(posts + [Post(slug, metadata)])

    # mkdir is the ownership boundary: never remove or overwrite a preexisting target.
    try:
        target.mkdir()
    except FileExistsError:
        raise BlogError(f"target already exists: {target}") from None
    try:
        atomic_write(target / "index.typ", MANAGED_HEADER + body)
        atomic_write(target / "_post.json", json_bytes(metadata))
        write_index(blog, index)
    except BaseException:
        shutil.rmtree(target)
        raise
    print(f"Imported {slug}")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, help="project root (default: directory containing tools/)")
    commands = result.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import", help="copy an unwrapped Typst body into a managed article")
    importer.add_argument("source", nargs="?", help="UTF-8 .typ source; omit to select with yazi")
    for field in ("title", "description", "date", "lang", "slug"):
        importer.add_argument(f"--{field}")
    importer.add_argument("--category", action="append", help="category (repeat for multiple categories)")
    commands.add_parser("reindex", help="regenerate only content/Blog/_index.json")
    commands.add_parser("check", help="read-only metadata and generated index check")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        root = resolve_root(args.root)
        blog = root / "content" / "Blog"
        if args.command == "import":
            import_post(blog, args)
        else:
            posts = scan_posts(blog)
            if args.command == "reindex":
                changed = write_index(blog, build_index(posts))
                print(f"{'Updated' if changed else 'Unchanged'} index: {len(posts)} articles")
            else:
                check(blog, posts)
    except (BlogError, OSError, UnicodeError, EOFError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
