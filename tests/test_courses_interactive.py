"""Designer Go, Game Maker and Master 2.0 are interactive courses too. Every exercise is checked by REALLY RUNNING it in HumanLang
(the same way as Beginner+): a fact about a page is true for the page HL builds, a fill-in-the-blank works, a puzzle has exactly one
right order, a bug is on the line HL points at, and a game variable really holds what the answer says."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "website"))
import coursekit  # noqa: E402

COURSE_MODULES = ["designer", "gamemaker", "master"]


def load(name):
    try:
        return __import__(name)
    except ModuleNotFoundError:
        return None


class InteractiveCourseTests(unittest.TestCase):
    def mods(self):
        return [(n, load(n)) for n in COURSE_MODULES if load(n)]

    def test_every_exercise_is_right(self):
        bad = []
        for name, mod in self.mods():
            for u in mod.UNITS:
                for where, e in coursekit.exercises(u):
                    for p in coursekit.problems(e, mod):
                        bad.append(f"{name} {where}: {p}")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_shape_of_each_course(self):
        for name, mod in self.mods():
            self.assertGreaterEqual(len(mod.UNITS), 6, name)
            total_bank = 0
            for u in mod.UNITS:
                self.assertGreaterEqual(len(u["parts"]), 2, f"{name} unit {u['n']}")
                self.assertGreaterEqual(len(u["bank"]), 8, f"{name} unit {u['n']} bank")
                for p in u["parts"]:
                    self.assertGreaterEqual(len(p["ex"]), 4, f"{name} unit {u['n']} {p['title']}")
                    self.assertTrue(p["teach"].strip())
                total_bank += len(u["bank"])
            self.assertGreaterEqual(total_bank, mod.COURSE["exam"], name)
            self.assertEqual([u["n"] for u in mod.UNITS], list(range(1, len(mod.UNITS) + 1)))
            for key in ("id", "name", "key", "exam", "lead"):
                self.assertIn(key, mod.COURSE)

    def test_skills_and_tags_are_all_used_and_known(self):
        for name, mod in self.mods():
            used = set()
            for u in mod.UNITS:
                for _, e in coursekit.exercises(u):
                    used.add(e["skill"])
            self.assertEqual(sorted(set(mod.SKILLS) - used), [], f"{name}: skills nobody is asked about")
            for t, (skill, tip) in mod.TAGS.items():
                self.assertIn(skill, mod.SKILLS, f"{name} tag {t}")
                self.assertTrue(tip.strip())

    def test_teach_examples_run(self):
        """Every example in a lesson text runs without an error (unless it is marked hum-error)."""
        for name, mod in self.mods():
            for u in mod.UNITS:
                for p in u["parts"]:
                    for kind, code, *_ in re.findall(r"```(hum|hum-page|hum-game|hum-error)\n(.*?)```", p["teach"], re.S):
                        pass
                    for kind, code in re.findall(r"```(hum|hum-page|hum-game|hum-error)\n(.*?)```", p["teach"], re.S):
                        out, err = coursekit.rich_run(code, ["Sam", "20", "20", "20"])
                        if kind == "hum-error":
                            self.assertIsNotNone(err, f"{name} unit {u['n']} {p['title']}: this example should fail:\n{code}")
                        elif kind in ("hum-page", "hum-game"):
                            self.assertIsNone(err, f"{name} unit {u['n']} {p['title']}: {err}\n{code}")
                        else:
                            self.assertIsNone(err, f"{name} unit {u['n']} {p['title']}: {err}\n{code}")

    def test_export_is_json_with_every_answer_worked_out(self):
        import json
        for name, mod in self.mods():
            data = json.loads(mod.export_json(lambda t: ("<p></p>", []), lambda c: c))
            self.assertEqual(data["course"]["id"], mod.COURSE["id"])
            for u in data["units"]:
                for p in u["parts"]:
                    for e in p["ex"]:
                        if e["kind"] == "type":
                            self.assertTrue(e["answer"].strip())

    def test_the_course_list_in_learn_core_matches_the_site(self):
        """Home and Account pages use LearnCore.COURSES: it must say the same as courses.py and each course's own module."""
        import json
        import courses
        with open(os.path.join(ROOT, "website", "static", "learn-core.js"), encoding="utf-8") as fh:
            src = fh.read()
        listed = json.loads(re.search(r"const COURSES = (\[.*?\]);", src, re.S).group(1))
        self.assertEqual([c["id"] for c in listed], [c["id"] for c in courses.COURSES])
        for c, entry in zip(courses.COURSES, listed):
            mod = __import__(c["module"])
            self.assertEqual(entry["key"], mod.COURSE["key"], c["id"])
            self.assertEqual(entry["units"], len(mod.UNITS), c["id"])
            self.assertEqual(entry["units"], c["units"], c["id"])
            self.assertEqual(entry["file"], courses.course_file(c))
            self.assertEqual(mod.COURSE["id"], c["id"])
            self.assertEqual(mod.COURSE["name"], c["name"])


if __name__ == "__main__":
    unittest.main()
