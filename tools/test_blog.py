"""Behavioral tests: isolated roots only, no Typst, home configuration or real yazi."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import blog


CLI = Path(blog.__file__).resolve()
HEADER = (
    '#import "/site-lib/post.typ": post-template, tufted\n'
    '#show: post-template.with(json("_post.json"))\n\n'
).encode("utf-8")


class BlogCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="blog-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "project"
        self.blog = self.root / "content" / "Blog"
        self.blog.mkdir(parents=True)
        (self.root / "config.typ").write_text("// isolated test project\n", encoding="utf-8")
        (self.blog / "index.typ").write_bytes(b"// existing landing page\n")
        self.caller = self.base / "caller"
        self.caller.mkdir()
        self.source = self.caller / "draft.typ"
        self.source.write_bytes("= 原样正文\r\n\r\n$ a + b $\n".encode("utf-8"))
        self.environment = dict(os.environ, HOME=str(self.base / "unused-home"))

    def run_cli(self, *arguments, root=True, script=CLI):
        command = [sys.executable, str(script)]
        if root:
            command += ["--root", str(self.root)]
        return subprocess.run(
            command + list(arguments), cwd=self.caller, env=self.environment,
            input="", text=True, capture_output=True, check=False,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def assert_failure(self, result, context):
        self.assertNotEqual(result.returncode, 0, f"{context}: {result.stdout}")
        self.assertNotIn("Traceback", result.stderr)


    def add_post(self, slug, *, title=None, date="2026-04-16", categories=None):
        directory = self.blog / slug
        directory.mkdir()
        metadata = {
            "title": slug if title is None else title,
            "description": "",
            "date": date,
            "lang": "zh",
            "categories": [] if categories is None else categories,
        }
        (directory / "index.typ").write_bytes(HEADER + b"= Existing body\n")
        (directory / "_post.json").write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        return metadata

    def index(self):
        return json.loads((self.blog / "_index.json").read_text(encoding="utf-8"))

    def snapshot(self):
        result = {}
        for path in self.root.rglob("*"):
            name = str(path.relative_to(self.root))
            if path.is_symlink():
                result[name] = ("symlink", os.readlink(path))
            elif path.is_file():
                stat = path.stat()
                result[name] = (path.read_bytes(), stat.st_ino, stat.st_mtime_ns)
            else:
                result[name] = ("directory",)
        return result

    def import_arguments(self, *extra):
        return ["import", str(self.source), "--title", '标题 "quoted"', "--date", "2026-06-01", *extra]

    def test_deterministic_multicategory_index_and_idempotence(self):
        self.add_post("乙 old", date="2025-12-31", categories=["Z", "A"])
        self.add_post("b tie", date="2026-07-06", categories=["A"])
        self.add_post("a tie", date="2026-07-06", categories=["A", "中文"])
        self.add_post("empty", date="2026-08-01")
        self.add_post("named", date="2026-03-01", categories=["未分类"])
        self.assert_success(self.run_cli("reindex"))
        self.assertEqual(self.index(), [
            {"category": "A", "posts": [
                {"date": "2026-07-06", "path": "a tie/", "title": "a tie"},
                {"date": "2026-07-06", "path": "b tie/", "title": "b tie"},
                {"date": "2025-12-31", "path": "乙 old/", "title": "乙 old"},
            ]},
            {"category": "Z", "posts": [{"date": "2025-12-31", "path": "乙 old/", "title": "乙 old"}]},
            {"category": "中文", "posts": [{"date": "2026-07-06", "path": "a tie/", "title": "a tie"}]},
            {"category": "未分类", "posts": [
                {"date": "2026-08-01", "path": "empty/", "title": "empty"},
                {"date": "2026-03-01", "path": "named/", "title": "named"},
            ]},
        ])
        before = self.snapshot()
        self.assert_success(self.run_cli("reindex"))
        self.assert_success(self.run_cli("reindex"))
        self.assertEqual(self.snapshot(), before)
        result = self.run_cli("check")
        self.assert_success(result)
        self.assertEqual(self.snapshot(), before)

    def test_empty_blog_and_ignored_nonarticles(self):
        (self.blog / "_private").mkdir()
        (self.blog / "_private" / "index.typ").write_text("not an article", encoding="utf-8")
        (self.blog / "assets").mkdir()
        self.assert_success(self.run_cli("reindex"))
        self.assertEqual(self.index(), [])
        self.assert_success(self.run_cli("check"))

    def test_check_is_semantic_and_never_reformats(self):
        self.add_post("post")
        self.assert_success(self.run_cli("reindex"))
        value = self.index()
        # Both dictionary key order and whitespace differ from the generator.
        group = value[0]
        post = group["posts"][0]
        alternative = [{"posts": [{"title": post["title"], "path": post["path"], "date": post["date"]}], "category": group["category"]}]
        (self.blog / "_index.json").write_text(json.dumps(alternative, ensure_ascii=False, indent=4), encoding="utf-8")
        before = self.snapshot()
        self.assert_success(self.run_cli("check"))
        self.assertEqual(self.snapshot(), before)

    def test_missing_stale_and_invalid_indexes_are_read_only_errors(self):
        self.add_post("post")
        cases = [(None, "missing"), (b"[]\n", "stale index"), (b"{broken", "invalid JSON"), (b"{}", "invalid index")]
        for contents, message in cases:
            with self.subTest(contents=contents):
                path = self.blog / "_index.json"
                if contents is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(contents)
                before = self.snapshot()
                self.assert_failure(self.run_cli("check"), message)
                self.assertEqual(self.snapshot(), before)
        self.assert_success(self.run_cli("reindex"))
        self.assert_success(self.run_cli("check"))



    def test_noninteractive_import_requires_title(self):
        before = self.snapshot()
        self.assert_failure(self.run_cli("import", str(self.source)), "--title")
        self.assertEqual(self.snapshot(), before)

    def test_invalid_date_and_conflicting_target_preserve_user_files(self):
        self.add_post("existing")
        self.assert_success(self.run_cli("reindex"))
        for extra, diagnostic in [
            (["--date", "2026-02-30"], "invalid date"),
            (["--date", "20260601"], "YYYY-MM-DD"),
            (["--slug", "existing"], "target already exists"),
        ]:
            with self.subTest(extra=extra):
                before = self.snapshot()
                original = self.source.read_bytes()
                self.assert_failure(self.run_cli(*self.import_arguments(*extra)), diagnostic)
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(self.source.read_bytes(), original)

    def test_dangling_symlink_target_is_not_overwritten(self):
        (self.blog / "draft").symlink_to(self.blog / "absent")
        before = self.snapshot()
        self.assert_failure(self.run_cli(*self.import_arguments()), "target already exists")
        self.assertEqual(self.snapshot(), before)

    def test_unsafe_slugs_are_rejected_before_writes(self):
        for slug in ("", ".", "..", "_hidden", "../escape", "a/b", "a\\b"):
            with self.subTest(slug=slug):
                before = self.snapshot()
                self.assert_failure(self.run_cli(*self.import_arguments("--slug", slug)), "unsafe article slug")
                self.assertEqual(self.snapshot(), before)

    def test_source_requirements_and_preexisting_headers(self):
        for body in (
            HEADER + b"= Already managed\n",
            b'#import "../index.typ": template, tufted\n#show: template.with(title: "old")\nBody\n',
            b'#show: template.with(title: "legacy")\nBody\n',
        ):
            with self.subTest(body=body):
                self.source.write_bytes(body)
                before = self.snapshot()
                self.assert_failure(self.run_cli(*self.import_arguments()), "template header")
                self.assertEqual(self.source.read_bytes(), body)
                self.assertEqual(self.snapshot(), before)
        self.source.write_bytes(b"\xff\xfe")
        before = self.snapshot()
        self.assert_failure(self.run_cli(*self.import_arguments()), "UTF-8")
        self.assertEqual(self.snapshot(), before)
        self.source.unlink()
        self.assert_failure(self.run_cli(*self.import_arguments()), "regular .typ file")
        self.source.mkdir()
        self.assert_failure(self.run_cli(*self.import_arguments()), "regular .typ file")
        self.source.rmdir()
        other = self.source.with_suffix(".txt")
        other.write_text("body", encoding="utf-8")
        self.assert_failure(self.run_cli("import", str(other), "--title", "title"), "regular .typ file")

    def test_missing_metadata_blocks_reindex_check_and_import(self):
        self.add_post("missing")
        self.assert_success(self.run_cli("reindex"))
        (self.blog / "missing" / "_post.json").unlink()
        before = self.snapshot()
        for arguments in (("reindex",), ("check",), self.import_arguments()):
            with self.subTest(arguments=arguments):
                self.assert_failure(self.run_cli(*arguments), "_post.json")
                self.assertEqual(self.snapshot(), before)

    def test_metadata_schema_is_strict_and_never_silently_omits_articles(self):
        valid = self.add_post("post")
        self.assert_success(self.run_cli("reindex"))
        variants = [
            {**valid, "title": "  "}, {**valid, "description": 3},
            {**valid, "lang": ""}, {**valid, "date": "2026-02-29"},
            {**valid, "date": "2026-4-16"}, {**valid, "categories": ["x", "x"]},
            {**valid, "categories": [""]}, {**valid, "categories": "category"},
            {**valid, "extra": "unexpected"}, {key: value for key, value in valid.items() if key != "date"},
            [],
        ]
        metadata_path = self.blog / "post" / "_post.json"
        for invalid in variants:
            with self.subTest(metadata=invalid):
                metadata_path.write_text(json.dumps(invalid), encoding="utf-8")
                before = self.snapshot()
                result = self.run_cli("reindex")
                self.assert_failure(result, "invalid metadata must fail")
                self.assertEqual(self.snapshot(), before)

    def test_article_symlink_cannot_escape_blog(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "index.typ").write_text("body", encoding="utf-8")
        (self.blog / "escape").symlink_to(outside, target_is_directory=True)
        before = self.snapshot()
        self.assert_failure(self.run_cli("reindex"), "escapes Blog")
        self.assertEqual(self.snapshot(), before)

    def test_default_root_comes_from_script_not_caller(self):
        tools = self.root / "tools"
        tools.mkdir()
        script = tools / "blog.py"
        shutil.copyfile(CLI, script)
        self.assert_success(self.run_cli("reindex", root=False, script=script))
        self.assert_success(self.run_cli("check", root=False, script=script))
        self.assertEqual(self.index(), [])

    def test_explicit_root_requires_project_structure(self):
        (self.root / "config.typ").unlink()
        self.assert_failure(self.run_cli("reindex"), "config.typ")
        (self.root / "config.typ").write_text("", encoding="utf-8")
        (self.blog / "index.typ").unlink()
        self.blog.rmdir()
        self.assert_failure(self.run_cli("reindex"), "content/Blog")

    def test_failed_index_replace_rolls_back_only_new_article(self):
        self.add_post("existing")
        self.assert_success(self.run_cli("reindex"))
        before = self.snapshot()
        original_source = self.source.read_bytes()
        real_replace = os.replace

        def fail_index_replace(source, destination):
            if Path(destination) == self.blog / "_index.json":
                raise OSError("simulated index replacement failure")
            return real_replace(source, destination)

        output, errors = io.StringIO(), io.StringIO()
        with patch.object(blog.os, "replace", side_effect=fail_index_replace), patch.object(blog.sys, "stdin", io.StringIO("")), redirect_stdout(output), redirect_stderr(errors):
            code = blog.main(["--root", str(self.root), *self.import_arguments()])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.source.read_bytes(), original_source)

    def test_yazi_failure_propagates_without_project_changes(self):
        before = self.snapshot()
        output, errors = io.StringIO(), io.StringIO()
        failed = subprocess.CompletedProcess(["yazi"], 23)
        with patch.object(blog.subprocess, "run", return_value=failed), redirect_stdout(output), redirect_stderr(errors):
            code = blog.main(["--root", str(self.root), "import"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.snapshot(), before)

    def test_yazi_cancellation_uses_unique_cleaned_chooser_and_leaves_project_untouched(self):
        before = self.snapshot()
        chooser_paths = []
        caller_directories = []

        def cancel(command, *, cwd, check):
            chooser = Path(command[2])
            chooser_paths.append(chooser)
            caller_directories.append(cwd)
            return subprocess.CompletedProcess(command, 0 if len(chooser_paths) == 1 else 130)

        with patch.object(blog.subprocess, "run", side_effect=cancel), redirect_stdout(io.StringIO()):
            for _ in range(2):
                self.assertEqual(blog.main(["--root", str(self.root), "import"]), 0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(set(chooser_paths)), 2)
        self.assertTrue(all(not path.exists() for path in chooser_paths))
        self.assertEqual(caller_directories, [Path.cwd(), Path.cwd()])




if __name__ == "__main__":
    unittest.main()
