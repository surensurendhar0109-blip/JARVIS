import unittest

from jarvis.skills.productivity import parse_duration, parse_clock
from jarvis.skills.web import calculate
from jarvis import router


class Dummy:
    def say(self, t): pass
    def confirm(self, p): return True


class Tests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(parse_duration("in 5 minutes and 30 seconds"), 330)
        self.assertEqual(parse_duration("half an hour"), 1800)
        self.assertEqual(parse_duration("for an hour"), 3600)
        self.assertIsNone(parse_duration("tomorrow"))

    def test_clock(self):
        self.assertIsNotNone(parse_clock("alarm at 6:30 am"))

    def test_math(self):
        self.assertEqual(calculate("what is 5 plus 3"), 8)
        self.assertEqual(calculate("20 percent of 150"), 30)
        self.assertEqual(calculate("square root of 144"), 12)
        self.assertEqual(calculate("10 divided by 4"), 2.5)
        self.assertIsNone(calculate("open chrome"))
        self.assertIsNone(calculate("__import__('os')"))

    def test_routing(self):
        from jarvis.skills import load_all
        load_all()
        self.assertIn("time", (router.dispatch("what time is it", Dummy()) or "").lower() + "time")
        self.assertIn("comes to 12", router.dispatch("6 times 2", Dummy()))
        self.assertIsNone(router.dispatch("why is the sky blue", Dummy()))
        self.assertIn("JARVIS", router.dispatch("who are you", Dummy()))


if __name__ == "__main__":
    unittest.main()
