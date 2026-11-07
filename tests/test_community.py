"""The community bot: 100% HumanLang, no copies, no private details, and it never runs a post."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import community_check as cc  # noqa: E402

GOOD = '''set total to 0
for each n from 1 to 10
    change total to total + n
say "The total is {total}"
say "Thank you for using my adder"
if total is greater than 50
    say "That is a big total"
otherwise
    say "That is a small total"
'''


def body(code=GOOD, desc="A tiny adder that adds the numbers from one to ten and says the total.", category="Tools and utilities",
         together="", rules=True, fence="hum", thumb=""):
    return (f"### Category\n\n{category}\n\n### What is it? (describe your work)\n\n{desc}\n\n"
            f"### Your HumanLang code\n\n```{fence}\n{code}\n```\n\n### Thumbnail picture (optional)\n\n{thumb or '_No response_'}\n\n### Made together with (optional)\n\n{together or '_No response_'}\n\n"
            f"### Rules\n\n- [{'x' if rules else ' '}] I read the rules.\n")


def post(n=10, user="ada", **kw):
    return {"number": n, "user": user, "body": body(**kw)}


def labels(result):
    return set(result["labels_add"])


class Reading(unittest.TestCase):
    def test_fields_and_code(self):
        f = cc.fields(body())
        self.assertEqual(f["Category"], "Tools and utilities")
        self.assertEqual(cc.code_of(f["Your HumanLang code"]).splitlines()[0], "set total to 0")

    def test_people(self):
        self.assertEqual(cc.people("@Ada and grace, @linus-t"), ["ada", "grace", "linus-t"])
        self.assertEqual(cc.people("_No response_"), [])


class Thumbnails(unittest.TestCase):
    def test_no_picture_is_fine(self):
        self.assertTrue(cc.analyse(post(), [])["ok"])

    def test_a_github_picture_is_accepted(self):
        pic = "![thumb](https://github.com/user-attachments/assets/1234abcd-0000-1111-2222-333344445555)"
        self.assertTrue(cc.analyse(post(thumb=pic), [])["ok"])
        self.assertEqual(cc.image_of(pic), "https://github.com/user-attachments/assets/1234abcd-0000-1111-2222-333344445555")

    def test_a_link_to_another_site_is_refused(self):
        r = cc.analyse(post(thumb="![x](https://example.com/me.png)"), [])
        self.assertFalse(r["ok"])
        self.assertIn("needs-fix", labels(r))

    def test_html_image_tag(self):
        self.assertTrue(cc.image_ok(cc.image_of('<img width="400" src="https://github.com/user-attachments/assets/ab" />')))


class Publishing(unittest.TestCase):
    def test_a_good_post_is_published(self):
        r = cc.analyse(post(), [])
        self.assertTrue(r["ok"])
        self.assertIn("verified-hl", labels(r))
        self.assertIn("Post ID: #10", r["comment"])

    def test_python_is_refused(self):
        r = cc.analyse(post(code="def add(a, b):\n    return a + b\nprint(add(1, 2))\n"), [])
        self.assertFalse(r["ok"])
        self.assertIn("needs-fix", labels(r))
        self.assertNotIn("verified-hl", labels(r))

    def test_javascript_and_html_in_the_description_are_refused(self):
        for desc in ("Use <script>alert(1)</script> to run it. Really fun!", "```javascript\nconsole.log(1)\n```\nHuman text here."):
            r = cc.analyse(post(desc=desc), [])
            self.assertFalse(r["ok"], desc)
            self.assertIn("100% HumanLang", r["comment"])

    def test_other_language_hidden_in_a_hl_string_is_just_text(self):
        code = GOOD + 'say "print(1) and def x(): are Python"\n'
        self.assertTrue(cc.analyse(post(code=code), [])["ok"])

    def test_mistake_in_the_program_says_where(self):
        r = cc.analyse(post(code=GOOD + "set to 5 five\n"), [])
        self.assertFalse(r["ok"])
        self.assertIn("line 10", r["comment"].lower())

    def test_rules_must_be_ticked(self):
        r = cc.analyse(post(rules=False), [])
        self.assertFalse(r["ok"])
        self.assertIn("rules", r["comment"])

    def test_private_details_are_refused(self):
        r = cc.analyse(post(desc="Email me at kid@example.com if it breaks, thanks a lot."), [])
        self.assertFalse(r["ok"])
        self.assertIn("email", r["comment"])

    def test_empty_and_huge_posts(self):
        self.assertFalse(cc.analyse(post(code=""), [])["ok"])
        self.assertFalse(cc.analyse(post(code="say \"x\"\n" * 20000), [])["ok"])

    def test_banned_accounts_are_removed(self):
        r = cc.analyse(post(user="Mallory"), [], banned=["mallory"])
        self.assertIn("banned", labels(r))
        self.assertTrue(r["ban"])

    def test_a_post_that_writes_files_is_marked(self):
        r = cc.analyse(post(code=GOOD + 'write "hi" to file "notes.txt"\n'), [])
        self.assertIn("writes-files", labels(r))


class Copying(unittest.TestCase):
    def other(self, code=GOOD, user="grace", n=3, co=()):
        return {"number": n, "user": user, "code": code, "coauthors": list(co)}

    def test_exact_copy_is_flagged(self):
        r = cc.analyse(post(), [self.other()])
        self.assertIn("possible-copy", labels(r))
        self.assertFalse(r["ok"])
        self.assertIn("#3", r["comment"])

    def test_renaming_things_does_not_hide_a_copy(self):
        renamed = GOOD.replace("total", "sum_of_all").replace("big", "huge").replace("10", "12").replace("50", "60")
        self.assertIn("possible-copy", labels(cc.analyse(post(code=renamed), [self.other()])))

    def test_comments_and_blank_lines_do_not_hide_a_copy(self):
        padded = "note: mine!\n\n" + GOOD.replace("\n", "\n\n")
        self.assertIn("possible-copy", labels(cc.analyse(post(code=padded), [self.other()])))

    def test_a_different_program_is_fine(self):
        different = 'ask "Your name?" and save it as who\nsay "Hello {who}"\nsay "Nice to meet you"\nrepeat 3 times\n    say "Hi again"\nset a to 1\nset b to 2\nsay a + b\nsay "done"\n'
        self.assertTrue(cc.analyse(post(code=GOOD), [self.other(different)])["ok"])

    def test_co_authors_are_not_copying(self):
        self.assertTrue(cc.analyse(post(together="@grace"), [self.other()])["ok"])
        self.assertTrue(cc.analyse(post(user="grace"), [self.other(user="ada", co=["grace"])])["ok"])

    def test_your_own_other_post_is_not_a_copy(self):
        self.assertTrue(cc.analyse(post(user="grace"), [self.other(user="grace")])["ok"])

    def test_copying_an_official_example_is_flagged(self):
        with open(os.path.join(ROOT, "examples", "fizzbuzz.hum"), encoding="utf-8") as f:
            code = f.read()
        r = cc.analyse(post(code=code), [], official_code=cc.official_programs())
        self.assertIn("possible-copy", labels(r))
        r = cc.analyse(post(code=code, user="notsabbir4"), [], official_code=cc.official_programs(), officials=["notsabbir4"])
        self.assertTrue(r["ok"])


class Safety(unittest.TestCase):
    def test_a_post_is_only_read_never_run(self):
        folder = tempfile.mkdtemp()
        old = os.getcwd()
        os.chdir(folder)
        try:
            code = GOOD + 'write "x" to file "proof.txt"\nrepeat forever\n    say "x"\n'
            cc.analyse(post(code=code), [])
            self.assertEqual(os.listdir(folder), [])
            self.assertFalse(os.path.exists("proof.txt"))
        finally:
            os.chdir(old)

    def test_every_official_file_is_valid_json(self):
        self.assertTrue(cc.load_json("official.json", {}).get("accounts"))
        self.assertEqual(cc.load_json("banned.json", None), {"banned": []})

    def test_the_form_matches_the_bot(self):
        with open(os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "community-post.yml"), encoding="utf-8") as f:
            text = f.read()
        for label in ("Category", "What is it? (describe your work)", "Your HumanLang code", "Made together with (optional)", "Rules"):
            self.assertIn(f"label: {label}", text)
        for category in cc.CATEGORIES:
            self.assertIn(f"- {category}", text)


if __name__ == "__main__":
    unittest.main()
