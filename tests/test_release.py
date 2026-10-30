"""Release hygiene: versions agree, and the website builds."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
import humanlang  # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class Release(unittest.TestCase):
    def test_versions_agree(self):
        pyproject = re.search(r'^version = "([^"]+)"', read("pyproject.toml"), re.M).group(1)
        self.assertEqual(pyproject, humanlang.__version__)
        self.assertIn(f"## {humanlang.__version__}", read("CHANGELOG.md"))
        self.assertIn(f'"version": "{humanlang.__version__}"', read("editors", "vscode", "package.json"))

    def test_required_files(self):
        for name in ("LICENSE", "README.md", "CONTRIBUTING.md", "CHANGELOG.md", ".gitignore",
                     ".github/workflows/tests.yml", ".github/workflows/release.yml",
                     ".github/workflows/pages.yml", "docs/tutorial.md", "docs/reference.md"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, name)), name)

    def test_website_builds(self):
        try:
            import markdown  # noqa: F401
        except ImportError:
            self.skipTest("the `markdown` package is not installed")
        with tempfile.TemporaryDirectory() as out:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "website", "build.py"), "--out", out],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            for page in ("index", "tutorial", "reference", "install", "playground"):
                html = open(os.path.join(out, page + ".html"), encoding="utf-8").read()
                self.assertIn("<title>", html)
                self.assertNotIn("@@BOX", html)
            with open(os.path.join(out, "humanlang_src.json"), encoding="utf-8") as f:
                self.assertIn("interpreter.py", f.read())
            with open(os.path.join(out, "config.js"), encoding="utf-8") as f:
                self.assertIn("cdn.jsdelivr.net/pyodide", f.read())


class Growth(unittest.TestCase):
    def test_issue_forms_are_valid(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml is not installed")
        folder = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE")
        names = sorted(os.listdir(folder))
        self.assertIn("beginner_feedback.yml", names)
        for name in names:
            data = yaml.safe_load(read(".github", "ISSUE_TEMPLATE", name))
            self.assertIsInstance(data, dict, name)
            if name != "config.yml":
                self.assertTrue(data["body"], name)
                ids = [b["id"] for b in data["body"] if "id" in b]
                self.assertEqual(len(ids), len(set(ids)), name)

    def test_workflows_are_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml is not installed")
        folder = os.path.join(ROOT, ".github", "workflows")
        for name in os.listdir(folder):
            self.assertIn("jobs", yaml.safe_load(read(".github", "workflows", name)), name)

    def test_bump_version_tool(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            for item in ("pyproject.toml", "CHANGELOG.md", "humanlang", "editors", "tests"):
                src = os.path.join(ROOT, item)
                (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(tmp, item))
            r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "bump_version.py"), "7.8.9", "--root", tmp],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_release.Release.test_versions_agree"],
                               capture_output=True, text=True, cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("## 7.8.9", read(tmp, "CHANGELOG.md"))
            bad = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "bump_version.py"), "seven", "--root", tmp],
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)

    def test_policy_documents_exist(self):
        for name in ("docs/versioning.md", "docs/community.md", "docs/proposals/README.md",
                     "docs/proposals/TEMPLATE.md", "ROADMAP.md", "CODE_OF_CONDUCT.md", "SUPPORT.md",
                     ".github/PULL_REQUEST_TEMPLATE.md"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, name)), name)


if __name__ == "__main__":
    unittest.main()
