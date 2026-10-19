import hashlib
import unittest

from unicode_normalization import review


class UnicodeNormalizationTests(unittest.TestCase):
    def test_hangul_jamo_compose_across_class_zero_boundary(self):
        original = "각"
        result = review(("x" + original + " y").encode("utf-8"))
        self.assertEqual(result["finding_count"], 1)
        detail = result["details"][0]
        self.assertEqual(detail["original"], original.encode("unicode_escape").decode("ascii"))
        self.assertEqual(detail["nfc"], "각".encode("unicode_escape").decode("ascii"))
        self.assertEqual(detail["source_byte_range"], [1, 10])
        self.assertEqual(detail["source_span_sha256"], hashlib.sha256(original.encode()).hexdigest())

    def test_combining_run_is_one_finding_with_exact_bytes(self):
        result = review("é A\u030a\u0301".encode("utf-8"))
        self.assertEqual(result["finding_count"], 1)
        self.assertEqual(result["details"][0]["source_byte_range"], [3, 8])

    def test_cap_counts_all_and_bounds_details(self):
        result = review(("Ａ " * 20).encode(), max_details=1)
        self.assertEqual((result["finding_count"], result["retained_details"], result["omitted_details"]), (20, 1, 19))

    def test_long_combining_run(self):
        # The old suffix scan and repeated prefix encoding grew quadratically.
        result = review(("A" + "\u0301" * 10000).encode(), max_details=0)
        self.assertEqual(result["finding_count"], 1)
        self.assertEqual(result["details"], [])


if __name__ == "__main__":
    unittest.main()
