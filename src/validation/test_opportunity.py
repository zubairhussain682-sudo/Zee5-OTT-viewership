"""Regression fixtures: existence, gaps, historical upgrades and catalogue edges."""
import datetime as dt
import unittest

import numpy as np
import pandas as pd

from src.analytical_transforms.access import access_day_matrix, profile_access_day_matrix
from src.analytical_transforms.opportunity import profile_opportunity, account_parent_exposure


class Calendar:
    start = dt.date(2025, 1, 1)
    n_days = 6

    def day_index(self, day):
        return (day - self.start).days


class ProfileOpportunityTests(unittest.TestCase):
    def setUp(self):
        self.cal = Calendar()
        self.cycles = pd.DataFrame([
            ['A', '2025-01-01', '2025-01-02', 'ALL_ACCESS', 'ALL'],
            ['A', '2025-01-04', '2025-01-05', 'REGIONAL', 'Hindi'],
            ['A', '2025-01-06', '2025-01-06', 'ALL_ACCESS', 'ALL'],
        ], columns=['account_id', 'cycle_start_date', 'cycle_end_date',
                    'plan_family', 'plan_language_group'])
        for c in ['cycle_start_date', 'cycle_end_date']:
            self.cycles[c] = pd.to_datetime(self.cycles[c]).dt.date
        self.profiles = pd.DataFrame([
            ['old', 'A', '2024-12-01'],
            ['late', 'A', '2025-01-05'],
            ['future', 'A', '2025-01-07'],
            ['no_cycle', 'B', '2025-01-01'],
        ], columns=['profile_id', 'account_id', 'profile_created_date'])
        self.catalogue = pd.DataFrame([
            ['H', '2025-01-05', '2025-01-01', None],
            ['T', '2025-01-01', '2025-01-01', None],
            ['X', '2025-01-01', '2025-01-01', '2025-01-04'],
        ], columns=['parent_title_id', 'release_date', 'catalogue_entry_date',
                    'catalogue_exit_date'])
        for c in ['release_date', 'catalogue_entry_date', 'catalogue_exit_date']:
            self.catalogue[c] = pd.to_datetime(self.catalogue[c])
        self.audio = pd.DataFrame([['H', 'Hindi'], ['T', 'Tamil'], ['X', 'Hindi']],
                                  columns=['parent_title_id', 'language'])

    def test_access_existence_gap_and_account_immutability(self):
        before = access_day_matrix(self.cycles, self.cal)
        ids, has, code = profile_access_day_matrix(self.profiles, self.cycles, self.cal)
        np.testing.assert_array_equal(has.sum(axis=1), [5, 2, 0, 0])
        np.testing.assert_array_equal(has[0], [True, True, False, True, True, True])
        np.testing.assert_array_equal(code[1], [-1, -1, -1, -1, 2, 0])
        after = access_day_matrix(self.cycles, self.cal)
        np.testing.assert_array_equal(before[1], after[1])
        np.testing.assert_array_equal(before[2], after[2])

    def test_title_release_exit_regional_upgrade_and_window(self):
        start, end = pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06')
        (ids, parents, exposure), opp = profile_opportunity(
            self.profiles, self.cycles, self.catalogue, self.audio, self.cal, start, end)
        np.testing.assert_array_equal(exposure, [[2, 3, 3], [2, 1, 0], [0, 0, 0], [0, 0, 0]])
        np.testing.assert_array_equal(opp.eligible_parent_title_days, [8, 3, 0, 0])
        np.testing.assert_allclose(opp.mean_daily_eligible_parent_titles, [1.6, 1.5, 0, 0])

        _, _, account = account_parent_exposure(
            self.cycles, self.catalogue, self.audio, self.cal, start, end)
        np.testing.assert_array_equal(account[0], exposure[0])

        (_, _, short), short_opp = profile_opportunity(
            self.profiles, self.cycles, self.catalogue, self.audio, self.cal,
            pd.Timestamp('2025-01-06'), end)
        np.testing.assert_array_equal(short, [[1, 1, 0], [1, 1, 0], [0, 0, 0], [0, 0, 0]])
        np.testing.assert_array_equal(short_opp.entitled_days_in_window, [1, 1, 0, 0])


if __name__ == '__main__':
    unittest.main()
