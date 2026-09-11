"""Boundary fixtures for progression, access interruptions and attribution."""
import datetime as dt
import unittest

import pandas as pd

from src.analytical_transforms.continuation import continuation_table


class Calendar:
    start = dt.date(2025, 9, 1)
    end = dt.date(2026, 2, 27)
    analytical_start = dt.date(2025, 11, 30)
    n_days = 180

    def day_index(self, day):
        return (day - self.start).days


def build_frame(d, cal):
    e = (d['events']
         .merge(d['sessions'][['session_id', 'profile_id', 'device_type']], on='session_id')
         .merge(d['catalogue'], on='content_id'))
    e['progress'] = e.playback_end_position / (e.runtime_minutes * 60)
    return e


class ContinuationFixtures(unittest.TestCase):
    def fixture(self, next_entry="2025-09-01", end="2026-02-27"):
        self.cal = Calendar()
        cat = pd.DataFrame([
            dict(content_id=c, parent_title_id="T", season_number=1, episode_number=i,
                 content_type="EPISODE", program_type="WEB_SERIES", runtime_minutes=10,
                 release_date=pd.Timestamp(next_entry if i == 2 else "2025-09-01"),
                 catalogue_entry_date=pd.Timestamp(next_entry if i == 2 else "2025-09-01"),
                 catalogue_exit_date=pd.NaT, primary_genre="Drama", original_language="Hindi")
            for i, c in enumerate(["A", "B"], 1)])
        return dict(
            catalogue=cat,
            profiles=pd.DataFrame([dict(
                profile_id="P", account_id="X",
                profile_created_date=pd.Timestamp("2025-09-01"))]),
            accounts=pd.DataFrame([dict(
                account_id="X", account_created_date=pd.Timestamp("2025-09-01"))]),
            cycles=pd.DataFrame([dict(
                account_id="X",
                cycle_start_date=pd.Timestamp("2025-09-01").date(),
                cycle_end_date=pd.Timestamp(end).date(),
                plan_family="ALL_ACCESS", plan_language_group="ALL")]),
            audio=pd.DataFrame([dict(parent_title_id="T", language="Hindi")]))

    def run_case(self, d, rows):
        sessions, events = [], []
        for i, (asset, ts, autoplay, seconds, progress) in enumerate(rows):
            start = pd.Timestamp(ts)
            stop = start + pd.Timedelta(seconds=seconds)
            sessions.append(dict(session_id=str(i), profile_id="P", device_type="MOBILE",
                                 session_start_ts=start, session_end_ts=stop))
            events.append(dict(view_event_id=str(i), session_id=str(i), content_id=asset,
                               event_start_ts=start, event_end_ts=stop, watch_seconds=seconds,
                               playback_end_position=600 * progress, audio_language="Hindi",
                               is_autoplay=autoplay))
        d["sessions"], d["events"] = pd.DataFrame(sessions), pd.DataFrame(events)
        return continuation_table(build_frame(d, self.cal), d, self.cal,
                                  {"continuation_observation_days": 7})

    def event(self, asset="A", ts="2025-09-02 10:00", auto=False, seconds=540, progress=.9):
        return asset, ts, auto, seconds, progress

    def test_revisit_does_not_move_anchor(self):
        d = self.fixture()
        c = self.run_case(d, [self.event(),
                              self.event(ts="2025-09-12 10:00"),
                              self.event("B", "2025-09-03 10:00")])
        self.assertEqual(c.iloc[0].progression_ts, pd.Timestamp("2025-09-02 10:09"))
        self.assertTrue(c.iloc[0].continued)

    def test_late_known_positive_not_censored(self):
        d = self.fixture()
        c = self.run_case(d, [self.event(ts="2026-02-25 10:00"),
                              self.event("B", "2026-02-26 10:00")])
        self.assertTrue(c.iloc[0].continued)
        self.assertFalse(c.iloc[0].censored)

    def test_late_unknown(self):
        d = self.fixture()
        c = self.run_case(d, [self.event(ts="2026-02-25 10:00")])
        self.assertTrue(c.iloc[0].censored)

    def test_negative_and_delayed_availability(self):
        d = self.fixture(next_entry="2025-09-05")
        c = self.run_case(d, [self.event()])
        self.assertEqual(c.iloc[0].opportunity_start, pd.Timestamp("2025-09-05"))
        self.assertTrue(c.iloc[0].observed_negative)

    def test_delayed_access(self):
        d = self.fixture(next_entry="2025-09-05", end="2025-09-03")
        row = d['cycles'].iloc[0].copy()
        row.cycle_start_date = pd.Timestamp('2025-09-08').date()
        row.cycle_end_date = self.cal.end
        d['cycles'] = pd.concat([d['cycles'], row.to_frame().T], ignore_index=True)
        c = self.run_case(d, [self.event()])
        self.assertEqual(c.iloc[0].opportunity_start, pd.Timestamp('2025-09-08'))

    def test_interrupt_resume_does_not_reopen(self):
        d = self.fixture(end="2025-09-04")
        row = d['cycles'].iloc[0].copy()
        row.cycle_start_date = pd.Timestamp('2025-09-06').date()
        row.cycle_end_date = self.cal.end
        d['cycles'] = pd.concat([d['cycles'], row.to_frame().T], ignore_index=True)
        c = self.run_case(d, [self.event(), self.event('B', '2025-09-07 10:00')])
        self.assertEqual(len(c), 1)
        self.assertTrue(c.iloc[0].censored)
        self.assertTrue(c.iloc[0].access_resumed_later)

    def test_catalogue_exit(self):
        d = self.fixture()
        d['catalogue'].loc[1, 'catalogue_exit_date'] = pd.Timestamp('2025-09-04')
        c = self.run_case(d, [self.event()])
        self.assertTrue(c.iloc[0].censored)

    def test_regional_mismatch_no_opportunity(self):
        d = self.fixture()
        d['cycles']['plan_family'] = 'REGIONAL'
        d['cycles']['plan_language_group'] = 'Tamil'
        c = self.run_case(d, [self.event()])
        self.assertEqual(len(c), 0)

    def test_attribution_ignores_prior_and_unqualified_events(self):
        d = self.fixture()
        c = self.run_case(d, [self.event('B', '2025-09-01 10:00'),
                              self.event(),
                              self.event('B', '2025-09-03 10:00', True, 80, .2),
                              self.event('B', '2025-09-04 10:00')])
        self.assertEqual(c.iloc[0].next_view_event_id, '3')
        self.assertFalse(c.iloc[0].next_is_autoplay)

    def test_cross_season_and_ambiguous_order(self):
        d = self.fixture()
        d['catalogue'].loc[1, ['season_number', 'episode_number']] = [2, 1]
        c = self.run_case(d, [self.event()])
        self.assertEqual(c.iloc[0].next_season_number, 2)

        d = self.fixture()
        d['catalogue'].loc[1, 'episode_number'] = 1
        with self.assertRaises(ValueError):
            self.run_case(d, [self.event()])

    def test_positive_before_access_loss_is_known(self):
        d = self.fixture(end="2025-09-04")
        c = self.run_case(d, [self.event(), self.event('B', '2025-09-03 10:00')])
        self.assertTrue(c.iloc[0].continued)
        self.assertFalse(c.iloc[0].censored)

    def test_seven_day_endpoint(self):
        d = self.fixture()
        c = self.run_case(d, [self.event(), self.event('B', '2025-09-09 10:09')])
        self.assertTrue(c.iloc[0].continued)
        c = self.run_case(d, [self.event(), self.event('B', '2025-09-09 10:09:00.000001')])
        self.assertTrue(c.iloc[0].observed_negative)

    def test_parent_specific_timing(self):
        d = self.fixture(next_entry='2025-09-05')
        other = d['catalogue'].copy()
        other['parent_title_id'] = 'OTHER'
        other['content_id'] = ['X1', 'X2']
        other['release_date'] = pd.Timestamp('2025-09-12')
        other['catalogue_entry_date'] = pd.Timestamp('2025-09-12')
        d['catalogue'] = pd.concat([other, d['catalogue']], ignore_index=True)
        c = self.run_case(d, [self.event()])
        self.assertEqual(c.iloc[0].next_content_id, 'B')
        self.assertEqual(c.iloc[0].opportunity_start, pd.Timestamp('2025-09-05'))

    def test_next_asset_exits_before_readiness(self):
        d = self.fixture()
        d['catalogue'].loc[1, 'catalogue_exit_date'] = pd.Timestamp('2025-09-01')
        self.assertEqual(len(self.run_case(d, [self.event()])), 0)


if __name__ == '__main__':
    unittest.main()
