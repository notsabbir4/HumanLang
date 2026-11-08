import json
import os
import tempfile
import unittest

from humanlang import livehost
from humanlang.livepage import live_to_html

PROG = '''set total to 0
show a page titled "Adder"
    put an input called amount
    put a button "Add"
    put a text "Total: {total}"
when the button "Add" is clicked
    change total to total + the number in amount
'''


def click(values):
    return json.loads(livehost.event(json.dumps({"type": "click", "name": "", "text": "Add", "values": values})))


class LiveTests(unittest.TestCase):
    def test_click_updates_page(self):
        r = json.loads(livehost.start(PROG))
        self.assertTrue(r["live"])
        self.assertIn("Total: 0", r["page"])
        self.assertIn("Total: 5", click({"amount": "5"})["html"])
        self.assertIn("Total: 7.5", click({"amount": "2.5"})["html"])

    def test_not_a_number_is_a_friendly_error(self):
        livehost.start(PROG)
        self.assertIn("not a number", click({"amount": "x"})["error"])

    def test_unknown_input(self):
        livehost.start(PROG.replace("the number in amount", "the number in nothere"))
        self.assertIn("no input called", click({})["error"])

    def test_plain_page_is_not_live(self):
        r = json.loads(livehost.start('show a page\n    put a text "hi"'))
        self.assertFalse(r["live"])

    def test_standalone_page_has_boot(self):
        from humanlang.interpreter import Interpreter
        i = Interpreter(out=lambda t: None)
        i.run(PROG)
        html = live_to_html(i.designs[-1], i.live_keys(), PROG)
        self.assertIn("humanlang.livehost", html)
        self.assertIn('"click": ["Add"]', html)


if __name__ == "__main__":
    unittest.main()
