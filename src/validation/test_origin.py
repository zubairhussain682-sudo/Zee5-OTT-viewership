"""Boundary fixtures: anchor selection, origin classification and anchor-relative reach."""
import datetime as dt
import unittest

import numpy as np
import pandas as pd

from src.analytical_transforms.opportunity import profile_opportunity
from src.analytical_transforms.origin import (
    baseline_origin_anchor, cross_origin_mask, cross_origin_opportunity,
    cross_origin_minute_share, new_origin_entry)


class Calendar:
    start = dt.date(2025, 1, 1)
    n_days = 6

    def day_index(self, day):
        return (day - self.start).days


def minutes(rows):
    return pd.DataFrame(rows, columns=['profile_id', 'original_language', 'qualified_minutes'])


class BaselineAnchorTests(unittest.TestCase):
    def test_anchor_is_the_largest_baseline_origin_with_a_deterministic_tie_break(self):
        anchors = baseline_origin_anchor(minutes([
            ['clear', 'Hindi', 600], ['clear', 'Tamil', 400],
            ['tied', 'Telugu', 300], ['tied', 'Bengali', 300],
        ])).set_index('profile_id')
        self.assertEqual(anchors.loc['clear', 'baseline_anchor_origin'], 'Hindi')
        self.assertAlmostEqual(anchors.loc['clear', 'baseline_anchor_share'], 0.6)
        self.assertAlmostEqual(anchors.loc['clear', 'baseline_second_origin_share'], 0.4)
        self.assertEqual(anchors.loc['tied', 'baseline_anchor_origin'], 'Bengali')

    def test_anchor_stays_fixed_when_final_behaviour_moves(self):
        baseline = minutes([['p', 'Hindi', 900], ['p', 'Tamil', 100]])
        final = minutes([['p', 'Hindi', 100], ['p', 'Tamil', 900]])
        anchor = baseline_origin_anchor(baseline).set_index('profile_id')['baseline_anchor_origin']
        self.assertEqual(anchor.loc['p'], 'Hindi')
        moved = cross_origin_minute_share(final, anchor).set_index('profile_id')
        self.assertAlmostEqual(moved.loc['p', 'cross_origin_minute_share'], 0.9)
        self.assertEqual(
            baseline_origin_anchor(final).set_index('profile_id').loc['p', 'baseline_anchor_origin'],
            'Tamil', 'recomputing on final viewing would move the reference with the outcome')

    def test_consumed_audio_never_reclassifies_a_titles_origin(self):
        # Qualified minutes carrying the audio track that was actually played. The
        # anchor is Hindi, and every row here was watched in Hindi audio - including
        # the Telugu-origin title, watched through its Hindi dub.
        watched = pd.DataFrame([
            ['p', 'Hindi', 'Hindi', 300],
            ['p', 'Hindi', 'Tamil', 200],
            ['p', 'Telugu', 'Hindi', 500],
        ], columns=['profile_id', 'original_language', 'audio_language', 'qualified_minutes'])
        anchor = pd.Series({'p': 'Hindi'})

        by_origin = (watched.groupby(['profile_id', 'original_language'], as_index=False)
                     ['qualified_minutes'].sum())
        share = cross_origin_minute_share(by_origin, anchor).set_index('profile_id')
        # 500 of 1000 minutes sit on the Telugu-origin title, dub notwithstanding.
        self.assertAlmostEqual(share.loc['p', 'cross_origin_minute_share'], 0.5)

        # Relabelling every consumed track leaves the classification identical, because
        # origin comes from the title and audio never enters the measure.
        relabelled = watched.assign(audio_language='Tamil')
        same = cross_origin_minute_share(
            relabelled.groupby(['profile_id', 'original_language'], as_index=False)
            ['qualified_minutes'].sum(), anchor).set_index('profile_id')
        self.assertAlmostEqual(same.loc['p', 'cross_origin_minute_share'], 0.5)

        # And the audio language a title offers never makes it cross-origin either.
        np.testing.assert_array_equal(
            cross_origin_mask(['Hindi', 'Telugu', 'Hindi'], 'Hindi'), [False, True, False])

    def test_new_origin_entry_needs_baseline_absence(self):
        entry = new_origin_entry(
            minutes([['p', 'Hindi', 500], ['q', 'Hindi', 500]]),
            minutes([['p', 'Hindi', 300], ['p', 'Tamil', 100],
                     ['q', 'Hindi', 400]])).set_index('profile_id')
        self.assertTrue(entry.loc['p', 'entered_new_origin'])
        self.assertAlmostEqual(entry.loc['p', 'new_origin_minute_share'], 0.25)
        self.assertFalse(entry.loc['q', 'entered_new_origin'])


class CrossOriginOpportunityTests(unittest.TestCase):
    def setUp(self):
        self.cal = Calendar()
        self.cycles = pd.DataFrame([
            ['A', '2025-01-01', '2025-01-03', 'REGIONAL', 'Hindi'],
            ['A', '2025-01-04', '2025-01-06', 'ALL_ACCESS', 'ALL'],
        ], columns=['account_id', 'cycle_start_date', 'cycle_end_date',
                    'plan_family', 'plan_language_group'])
        for c in ['cycle_start_date', 'cycle_end_date']:
            self.cycles[c] = pd.to_datetime(self.cycles[c]).dt.date
        self.profiles = pd.DataFrame([['p', 'A', '2024-12-01']],
                                     columns=['profile_id', 'account_id', 'profile_created_date'])
        # T_hin is Hindi-origin; T_tam is Tamil-origin but carries a Hindi dub, so a
        # Hindi pack admits it; T_tel is Telugu-origin and Telugu-only.
        self.catalogue = pd.DataFrame([
            ['T_hin', '2025-01-01', '2025-01-01', None],
            ['T_tam', '2025-01-01', '2025-01-01', None],
            ['T_tel', '2025-01-01', '2025-01-01', None],
        ], columns=['parent_title_id', 'release_date', 'catalogue_entry_date', 'catalogue_exit_date'])
        for c in ['release_date', 'catalogue_entry_date', 'catalogue_exit_date']:
            self.catalogue[c] = pd.to_datetime(self.catalogue[c])
        self.audio = pd.DataFrame([
            ['T_hin', 'Hindi'], ['T_tam', 'Hindi'], ['T_tam', 'Tamil'], ['T_tel', 'Telugu'],
        ], columns=['parent_title_id', 'language'])
        self.origins = ['T_hin', 'T_tam', 'T_tel'], ['Hindi', 'Tamil', 'Telugu']

    def exposure(self, start, end):
        return profile_opportunity(self.profiles, self.cycles, self.catalogue, self.audio,
                                   self.cal, pd.Timestamp(start), pd.Timestamp(end))[0][2]

    def test_regional_pack_admits_a_cross_origin_title_through_its_dub(self):
        early = self.exposure('2025-01-01', '2025-01-03')
        split = cross_origin_opportunity(early, self.origins[1], ['Hindi'])
        # The Hindi pack reaches the Hindi-origin title and the dubbed Tamil-origin
        # title, but not the Telugu-only one.
        self.assertEqual(int(split.reachable_parent_titles_total[0]), 2)
        self.assertEqual(int(split.reachable_cross_origin_titles[0]), 1)
        self.assertEqual(int(split.cross_origin_title_days[0]), 3)
        self.assertAlmostEqual(split.cross_origin_title_day_share[0], 0.5)

    def test_later_broad_access_does_not_enlarge_the_earlier_window(self):
        early = cross_origin_opportunity(
            self.exposure('2025-01-01', '2025-01-03'), self.origins[1], ['Hindi'])
        late = cross_origin_opportunity(
            self.exposure('2025-01-04', '2025-01-06'), self.origins[1], ['Hindi'])
        self.assertEqual(int(early.reachable_cross_origin_titles[0]), 1)
        self.assertEqual(int(late.reachable_cross_origin_titles[0]), 2)
        self.assertEqual(int(early.reachable_parent_titles_total[0]), 2)

    def test_a_missing_anchor_is_refused_rather_than_silently_classified(self):
        window = self.exposure('2025-01-01', '2025-01-06')
        for anchors in ([None], [np.nan], [float('nan')]):
            with self.assertRaises(ValueError):
                cross_origin_opportunity(window, self.origins[1], anchors)

    def test_origin_split_partitions_reach_and_shares_stay_undefined_without_a_pool(self):
        window = self.exposure('2025-01-01', '2025-01-06')
        split = cross_origin_opportunity(window, self.origins[1], ['Hindi'])
        self.assertEqual(int(split.reachable_anchor_origin_titles[0]
                             + split.reachable_cross_origin_titles[0]),
                         int(split.reachable_parent_titles_total[0]))
        self.assertEqual(int(split.anchor_origin_title_days[0] + split.cross_origin_title_days[0]),
                         int(split.eligible_parent_title_days_total[0]))
        empty = cross_origin_opportunity(np.zeros((1, 3), dtype=int), self.origins[1], ['Hindi'])
        self.assertTrue(np.isnan(empty.cross_origin_title_day_share[0]))
        self.assertTrue(np.isnan(empty.cross_origin_reachable_title_share[0]))


if __name__ == '__main__':
    unittest.main()
