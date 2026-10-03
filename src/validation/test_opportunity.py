"""Regression fixtures: existence, gaps, historical upgrades and catalogue edges."""
import datetime as dt
import unittest

import numpy as np
import pandas as pd

from src.analytical_transforms.access import access_day_matrix, profile_access_day_matrix
from src.analytical_transforms.opportunity import (
    profile_opportunity, account_parent_exposure, reachable_parent_titles,
    entitlement_timing, meaningful_titles_per_100_reachable,
    access_context_days, opportunity_regimes)


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


class WindowReachAndRegimeTests(ProfileOpportunityTests):
    """Window-level reach and access-regime structure used for conditioning."""

    def test_reach_counts_a_title_once_however_many_days(self):
        start, end = pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06')
        (_, _, exposure), opp = profile_opportunity(
            self.profiles, self.cycles, self.catalogue, self.audio, self.cal, start, end)
        reach = reachable_parent_titles(exposure)
        np.testing.assert_array_equal(reach, [3, 2, 0, 0])
        self.assertTrue((reach <= exposure.shape[1]).all())
        np.testing.assert_array_equal(
            entitlement_timing(opp.entitled_days_in_window, 6),
            ['PARTIAL', 'PARTIAL', 'PARTIAL', 'PARTIAL'])

    def test_per_100_reachable_is_undefined_without_a_reachable_pool(self):
        ratio = meaningful_titles_per_100_reachable([3, 1, 0, 0], [300, 2, 5, 0])
        np.testing.assert_allclose(ratio[:3], [1.0, 50.0, 0.0])
        self.assertTrue(np.isnan(ratio[3]))

    def test_regimes_follow_access_structure_not_reach_quantiles(self):
        contexts = access_context_days(
            self.profiles, self.cycles, pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06'))
        regimes = opportunity_regimes(contexts).set_index('profile_id')
        self.assertEqual(regimes.loc['old', 'opportunity_regime'], 'MIXED_ACCESS')
        self.assertEqual(regimes.loc['old', 'context_days'], 5)
        self.assertEqual(regimes.loc['late', 'opportunity_regime'], 'MIXED_ACCESS')
        self.assertNotIn('no_cycle', regimes.index)

        broad_only = self.cycles[self.cycles.plan_family.eq('ALL_ACCESS')].head(1)
        regional_only = self.cycles[self.cycles.plan_family.eq('REGIONAL')]
        for cycles, expected in ((broad_only, 'STABLE_BROAD'),
                                 (regional_only, 'STABLE_REGIONAL_Hindi')):
            regimes = opportunity_regimes(access_context_days(
                self.profiles, cycles,
                pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06')))
            self.assertEqual(
                regimes.set_index('profile_id').loc['old', 'opportunity_regime'], expected)

    def test_sports_variant_is_the_same_broad_vod_opportunity(self):
        """ALL_ACCESS to ALL_ACCESS_SPORTS reaches the same VOD catalogue."""
        cycles = pd.DataFrame([
            ['A', '2025-01-01', '2025-01-03', 'ALL_ACCESS', 'ALL'],
            ['A', '2025-01-04', '2025-01-06', 'ALL_ACCESS_SPORTS', 'ALL'],
        ], columns=['account_id', 'cycle_start_date', 'cycle_end_date',
                    'plan_family', 'plan_language_group'])
        for c in ['cycle_start_date', 'cycle_end_date']:
            cycles[c] = pd.to_datetime(cycles[c]).dt.date
        contexts = access_context_days(
            self.profiles, cycles, pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06'))
        row = opportunity_regimes(contexts).set_index('profile_id').loc['old']
        self.assertEqual(row['opportunity_regime'], 'STABLE_BROAD')
        self.assertEqual(row['distinct_access_contexts'], 2)
        self.assertEqual(row['distinct_vod_families'], 1)
        self.assertEqual(row['context_days'], 6)

        exposure = profile_opportunity(
            self.profiles, cycles, self.catalogue, self.audio, self.cal,
            pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06'))[0][2]
        np.testing.assert_array_equal(
            reachable_parent_titles(exposure)[0],
            reachable_parent_titles(profile_opportunity(
                self.profiles, cycles.head(1).assign(
                    cycle_end_date=pd.Timestamp('2025-01-06').date()),
                self.catalogue, self.audio, self.cal,
                pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06'))[0][2])[0])

    def test_language_switch_and_family_switch_stay_mixed(self):
        cycles = pd.DataFrame([
            ['A', '2025-01-01', '2025-01-03', 'REGIONAL', 'Hindi'],
            ['A', '2025-01-04', '2025-01-06', 'REGIONAL', 'Tamil'],
        ], columns=['account_id', 'cycle_start_date', 'cycle_end_date',
                    'plan_family', 'plan_language_group'])
        for c in ['cycle_start_date', 'cycle_end_date']:
            cycles[c] = pd.to_datetime(cycles[c]).dt.date
        regimes = opportunity_regimes(access_context_days(
            self.profiles, cycles, pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-06')))
        self.assertEqual(
            regimes.set_index('profile_id').loc['old', 'opportunity_regime'], 'MIXED_ACCESS')


if __name__ == '__main__':
    unittest.main()
