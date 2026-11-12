"""The tutorial courses: every lesson exists, every course can be followed on its own, every link works."""
import os, re, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "website"))
import courses  # noqa: E402

MD = open(os.path.join(ROOT, "docs", "tutorial.md"), encoding="utf-8").read()
INTRO, CHAPTERS = courses.split(MD)


def code_blocks(n):
    return re.findall(r"```hum[^\n]*\n(.*?)```", CHAPTERS[n][1], re.S)


class CourseContent(unittest.TestCase):
    def test_every_lesson_is_a_real_chapter_and_not_repeated(self):
        for c in courses.COURSES:
            self.assertEqual(len(set(c["lessons"])), len(c["lessons"]), c["id"])
            for n in c["lessons"]:
                self.assertIn(n, CHAPTERS, (c["id"], n))
                self.assertIn(n, courses.BLURB if n != 19 else {19: 1}, n)

    def test_every_chapter_is_in_some_course(self):
        used = {n for c in courses.COURSES for n in c["lessons"]}
        for n in CHAPTERS:
            if n != 19:                         # "Where next" is shown at the end of every course
                self.assertIn(n, used, f"chapter {n} is in no course")

    def test_next_courses_exist(self):
        ids = {c["id"] for c in courses.COURSES}
        for c in courses.COURSES:
            for other in c["next"]:
                self.assertIn(other, ids)
                self.assertNotEqual(other, c["id"])

    def test_a_course_teaches_what_its_examples_use(self):
        needs = {"define": (8, r"^\s*define "), "ask": (4, r"^\s*ask "), "try": (9, r"^\s*try\b")}
        for c in courses.COURSES:
            if c["id"] == "master-2":           # it says it is for people who know the basics already
                continue
            have = set(c["lessons"])
            for n in c["lessons"]:
                for code in code_blocks(n):
                    for word, (ch, pat) in needs.items():
                        if re.search(pat, code, re.M) and n != ch:
                            self.assertIn(ch, have, f"{c['name']}: lesson {n} uses '{word}' but the course skips chapter {ch}")

    def test_no_lesson_points_at_a_chapter_number(self):
        for n, (_, body) in CHAPTERS.items():
            self.assertIsNone(re.search(r"\bchapter \d+", body, re.I), f"chapter {n} says 'chapter N'")


class CoursePages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib
        build = importlib.import_module("build")
        cls.out = tempfile.mkdtemp()
        written = {}
        courses.build(cls.out, MD, build.render_markdown, lambda title, body, active, main_class="": f"<main>{body}</main>",
                      lambda path, text: (os.makedirs(os.path.dirname(path), exist_ok=True), open(path, "w", encoding="utf-8").write(text)))

    def test_pages_exist_and_links_work(self):
        files = set(os.listdir(self.out))
        self.assertIn("tutorial.html", files)
        for c in courses.COURSES:
            self.assertIn(courses.course_file(c), files)
            for k in range(1, len(c["lessons"]) + 1):
                self.assertIn(courses.lesson_file(c, k), files)
        for f in files:
            if not f.endswith(".html"):
                continue
            with open(os.path.join(self.out, f), encoding="utf-8") as fh:
                text = fh.read()
            for href in re.findall(r'href="([^"#:]+\.html)', text):
                if href.startswith(("lesson-", "course-")):
                    self.assertIn(href, files, f"{f} links to missing {href}")

    def test_lessons_have_back_and_next(self):
        c = courses.COURSES[0]; last = len(c["lessons"])
        def read(name):
            with open(os.path.join(self.out, name), encoding="utf-8") as fh:
                return fh.read()
        first, end = read(courses.lesson_file(c, 1)), read(courses.lesson_file(c, last))
        self.assertIn("Lesson 1 of", first); self.assertIn(f"Lesson {last} of", end)
        self.assertIn(courses.lesson_file(c, 2), first)
        self.assertIn(courses.course_file(c), end)


if __name__ == "__main__":
    unittest.main()
