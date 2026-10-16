import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import exam_grades as eg


class SuggestTests(unittest.TestCase):
    def test_uniform(self):
        self.assertEqual(eg.suggest([("D", 7.5), ("B", 7.5)]), ("G", False, "uniform scores"))

    def test_single(self):
        self.assertEqual(eg.suggest([("C", 10)])[0], "S")

    def test_d_miss_caps_at_g(self):
        cat, review, _ = eg.suggest([("D", 5), ("C", 10), ("B", 10), ("B", 10), ("C", 10)])
        self.assertEqual(cat, "G")
        self.assertTrue(review)

    def test_mixed_flagged(self):
        cat, review, _ = eg.suggest([("D", 10), ("B", 7.5)])
        self.assertTrue(review)

    def test_letters(self):
        self.assertEqual(eg.parse_score("g"), 7.5)
        with self.assertRaises(ValueError):
            eg.parse_score("6")

    def test_grade_points(self):
        rows = [{"student": "A", "outcome": "Quad", "question": "1", "level": "D", "score": "10"}]
        res = eg.grade(rows, {"Quad": "50"})
        self.assertEqual(res[0]["points"], 50)
        res = eg.grade(rows, {"Quad": "50"}, {("A", "Quad"): "L"})
        self.assertEqual(res[0]["points"], 25)


if __name__ == "__main__":
    unittest.main()
