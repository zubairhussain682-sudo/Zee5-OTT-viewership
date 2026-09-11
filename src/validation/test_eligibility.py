"""Boundary checks for the published profile eligibility rule."""
import unittest
import pandas as pd
from src.analytical_transforms.eligibility import apply_eligibility


class EligibilityTests(unittest.TestCase):
    def test_all_three_requirements_are_inclusive_and_rows_are_retained(self):
        source = pd.DataFrame({
            'entitled_days_in_window': [30, 29, 30, 30, 0],
            'active_days': [3, 3, 2, 3, 0],
            'qualified_watch_minutes': [120, 120, 120, 119.99, 0],
        })
        out = apply_eligibility(source)
        self.assertEqual(out.is_main_analytical_eligible.tolist(),
                         [True, False, False, False, False])
        self.assertEqual(len(out), len(source))
        self.assertNotIn('is_main_analytical_eligible', source)


if __name__ == '__main__':
    unittest.main()
