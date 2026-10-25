"""Bounded, read-only paired-profile validation; no segment or mart changes.

Run from any directory: python scripts/diagnostics/validate_relational_measures.py
Dependencies: polars, pandas, numpy. Quantiles: linear interpolation.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/relational_measures_validation'
PANEL = 'analysis_outputs/test7_7_2b_paired_behavioural_state_panel.csv'
PVW = 'data/marts/profile_viewership_window.csv'
PTW = 'data/marts/profile_title_window.csv'
EVENTS = 'data/stage2/view_events.csv'
SESSIONS = 'data/stage2/viewing_sessions.csv'
CAT = 'data/stage1/content_catalogue.csv'
WINDOWS = ['BASELINE_90', 'FINAL_90']
EPS = 1e-12  # Existing Test 7 floating representation tolerance, not a growth threshold.


def scan(path, cols):
    return pl.scan_csv(ROOT / path).select(cols)


def pandas(frame):
    return pd.DataFrame(frame.to_dict(as_series=False))


def window(col):
    return (pl.when(pl.col(col) < '2025-11-30').then(pl.lit(WINDOWS[0]))
            .otherwise(pl.lit(WINDOWS[1])))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def origin_inventory():
    """Availability inventory only; no third analytical reconstruction."""
    evidence = 'analysis_outputs/test7_integrated/private/profile_evidence.csv'
    origin = 'analysis_outputs/test7_integrated/private/origin_composition.csv'
    daily = 'analysis_outputs/test7_integrated/private/daily_evidence.parquet'
    c3 = 'analysis_outputs/test6c3_profile_behavior_opportunity.csv'
    raw = f'{EVENTS}; {SESSIONS}; {CAT}; fixed Baseline anchor from {c3}'
    title = f'{PTW}; {CAT}; fixed Baseline anchor from {c3}'
    rows = [
        ('Fixed Baseline origin anchor', 'profile', 'Largest Baseline qualified-minute original-language ecosystem; alphabetical original_language tie-break; held fixed in Final', c3, '8199 paired profiles', 'already computed', 'Selected Baseline maximum; not native language or consumed audio'),
        ('Outside-anchor qualified hours and shares', 'profile x window', 'Qualified minutes on titles whose original_language differs from fixed anchor; hours=minutes/60; share=outside/total qualified minutes', evidence, '8199 paired profiles in both windows', 'already computed', 'Outside absence is zero; no eligible Baseline anchor for Final-only profiles'),
        ('Anchor-origin qualified hours and shares', 'profile x window', 'Total qualified hours minus outside hours; one minus outside share on positive qualified total', evidence, '8199 paired profiles in both windows', 'derivable from approved source data', 'Arithmetic complement within the same origin partition; not opportunity share'),
        ('Outside-anchor qualified minutes', 'profile x window', '60 times existing outside qualified hours', evidence, '8199 paired profiles in both windows', 'derivable from approved source data', 'Unit conversion only; Final minutes also stored in 6C3'),
        ('Distinct outside-qualified dates', 'profile x window', 'Number of distinct event-start dates with positive qualified outside seconds; baseline_outside_days/final_outside_days', evidence + '; ' + daily, '8199 paired profiles; dates present only when playback occurs', 'already computed', 'Date count is not session count; no outside viewing gives zero days'),
        ('Outside-origin ecosystems consumed', 'profile x window', 'Count original_language rows outside anchor with positive qualified minutes in the window', origin + '; ' + c3, '8199 paired profiles; Final count stored in 6C3', 'derivable from approved source data', 'Count ecosystems rather than audio tracks; absent ecosystem rows contribute no consumption'),
        ('Same outside ecosystems in both windows', 'profile across windows', 'Count outside ecosystems with positive qualified minutes in each window; repeated_outside_origins', evidence + '; ' + origin, '8199 paired profiles', 'already computed', 'Cross-window recurrence; not number of returns or sessions'),
        ('Qualified starts on outside titles', 'profile x window (or title)', 'Sum qualified_starts after joining parent-title original language and fixed anchor', title, '8199 paired profiles; source supports finer title grain', 'derivable from approved source data', 'Repeated starts do not imply separate sessions or completed-content rewatches'),
        ('Sessions containing qualified outside playback', 'profile x window x session', 'Distinct session IDs with qualifying outside-origin events assigned by event-start window', raw, 'Available raw events for paired profiles', 'derivable from approved source data', 'Not stored in existing profile sidecars; cannot sum title session counts without double counting; not computed in this audit'),
        ('Outside playback frequency by ecosystem', 'profile x window x origin x date/session', 'Distinct observed dates or sessions carrying qualifying events in each outside ecosystem, separately labelled', raw, 'Available raw events for paired profiles', 'derivable from approved source data', 'A chronological return-episode definition is not established; no return frequency inferred from recurrence flags'),
        ('Same outside parent titles in both windows', 'profile across windows', 'Count parent IDs with meaningful outside consumption in both windows; repeated_outside_parent_titles', evidence + '; ' + title, '8199 paired profiles', 'already computed', 'Returning to a title observed in Baseline; not first-ever familiarity or necessarily a completed-content rewatch'),
        ('Qualified minutes and starts on recurring outside titles', 'profile x parent title x window', 'Filter the intersection of meaningful outside-title sets then retain qualified_watch_minutes and qualified_starts separately by window', title, '8199 paired profiles; intersecting title subset', 'derivable from approved source data', 'Actual volume/counts are recoverable; binary recurrence alone supplies neither'),
        ('Qualified repeat dates on an outside title', 'profile x parent title x window', 'Distinct dates of qualified outside-title events; events and sessions retain chronology', raw, 'Available raw events for paired profiles', 'derivable from approved source data', 'PTW active_days_with_title uses all events; use qualified_active_days for qualified title-date counts, but union dates across titles requires events'),
        ('Cross-origin benchmark deviations', 'profile x Final window x existing control', 'Existing Test 6D.4 activity/opportunity-conditioned residuals with their support flags', 'analysis_outputs/test6d4_profile_peer_residuals.csv', '8199 paired profiles with metric-specific support; 5510 support both existing controls', 'already computed', 'Cross-sectional candidate-blind controls, not exact-state-matched propensity or longitudinal recurrence'),
        ('Lifetime novelty and causal return propensity', 'viewer lifetime / counterfactual', 'First-ever exposure, motive, or causal effect of alternative titles on later consumption', 'No approved source establishes these constructs', 'Not available', 'unavailable', 'Two 90-day observation windows cannot establish lifetime history or causal substitution'),
    ]
    return pd.DataFrame(rows, columns=['measure', 'grain', 'operational_definition', 'existing_source', 'coverage', 'status', 'limitations'])


def main():
    started = time.perf_counter()
    qa = []

    def check(name, passed, detail=''):
        qa.append(dict(check=name, passed=bool(passed), detail=str(detail)))
        if not passed:
            raise AssertionError(f'{name}: {detail}')

    inputs = [PANEL, PVW, PTW, EVENTS, SESSIONS, CAT,
              'src/marts.py', 'src/mart_transforms/qualification.py',
              'docs/STAGE3_MART_DICTIONARY.md', 'docs/analytical_framework.md',
              'analysis_outputs/test7_integrated/test7_5_6_source_manifest.md',
              'analysis_outputs/test7_integrated/test7_5_review.md',
              'analysis_outputs/test7_integrated/test7_6_review.md',
              'analysis_outputs/test7_integrated/test7_7_interpretation_brief.md',
              'analysis_outputs/test7_integrated/test7_qa_checks.csv',
              'analysis_outputs/test7_integrated/test7_integrated_dashboard.html',
              'analysis_outputs/test6c3_profile_behavior_opportunity.csv',
              'analysis_outputs/test6d4_profile_peer_residuals.csv',
              'analysis_outputs/test7_integrated/private/profile_evidence.csv',
              'analysis_outputs/test7_integrated/private/origin_composition.csv',
              'analysis_outputs/test7_integrated/private/daily_evidence.parquet',
              'scripts/diagnostics/test6c3_cross_origin_opportunity_conditioning.py']
    before = {p: digest(ROOT / p) for p in inputs}
    p = pd.read_csv(ROOT / PANEL)
    check('paired panel: 8199 unique nonnull profiles', len(p) == 8199 and
          p.profile_id.nunique() == 8199 and p.profile_id.notna().all())
    ids = pl.DataFrame({'profile_id': p.profile_id.tolist()}).lazy()
    fields = ['qualified_watch_hours', 'qualified_watch_minutes', 'watch_minutes',
              'active_days', 'qualified_active_days', 'sessions', 'session_minutes',
              'mean_session_minutes', 'median_session_minutes', 'sessions_per_active_day',
              'distinct_meaningful_titles', 'top_title_qualified_share', 'title_hhi',
              'hhi_is_valid', 'entitled_days_in_window', 'is_main_analytical_eligible']
    m = pandas(scan(PVW, ['profile_id', 'window_label'] + fields)
               .join(ids, on='profile_id', how='semi').collect())
    check('paired mart: both eligible windows, unique keys', len(m) == 16398 and
          not m.duplicated(['profile_id', 'window_label']).any() and
          m.window_label.isin(WINDOWS).all() and m.is_main_analytical_eligible.all())
    for w, pre in zip(WINDOWS, ['b', 'f']):
        x = m[m.window_label == w].drop(columns='window_label')
        p = p.merge(x.rename(columns={c: pre + '_' + c for c in fields}),
                    on='profile_id', validate='one_to_one')
    for pre, panelpre in [('b', 'baseline'), ('f', 'final')]:
        for a, b in [('qualified_watch_hours', 'watch_hours'),
                     ('distinct_meaningful_titles', 'titles'), ('active_days', 'active_days'),
                     ('entitled_days_in_window', 'entitled_days'),
                     ('top_title_qualified_share', 'top_share')]:
            err = (p[f'{pre}_{a}'] - p[f'{panelpre}_{b}']).abs().max()
            check(f'panel matches mart: {pre} {a}', err < 1e-9, err)

    # Minimal raw reconstruction needed to distinguish qualified playback from elapsed sessions.
    s = scan(SESSIONS, ['session_id', 'profile_id', 'session_start_ts', 'session_end_ts'])
    s = s.join(ids, on='profile_id', how='semi').collect()
    check('session keys unique', s['session_id'].n_unique() == s.height)
    s = s.with_columns(((pl.col('session_end_ts').str.to_datetime() -
                        pl.col('session_start_ts').str.to_datetime()).dt.total_microseconds()
                       / 60_000_000).alias('elapsed_minutes'))
    check('nonnegative elapsed durations', s['elapsed_minutes'].min() >= 0)
    cat = scan(CAT, ['content_id', 'runtime_minutes']).collect()
    check('content key unique and runtime positive', cat['content_id'].n_unique() == cat.height
          and cat['runtime_minutes'].min() > 0)
    e = (scan(EVENTS, ['session_id', 'content_id', 'event_start_ts', 'watch_seconds', 'is_autoplay'])
         .join(s.lazy(), on='session_id', how='inner')
         .filter((pl.col('event_start_ts') >= '2025-09-01') &
                 (pl.col('event_start_ts') < '2026-02-28'))
         .join(cat.lazy(), on='content_id', how='left')
         .with_columns(window('event_start_ts').alias('window_label'),
                       pl.col('event_start_ts').str.slice(0, 10).alias('date'),
                       pl.when(pl.col('is_autoplay'))
                       .then(pl.min_horizontal(pl.lit(480), pl.col('runtime_minutes') * 12))
                       .otherwise(pl.min_horizontal(pl.lit(300), pl.col('runtime_minutes') * 6))
                       .alias('threshold'))
         .with_columns((pl.col('watch_seconds') >= pl.col('threshold')).alias('qualified'))
         .collect())
    check('all raw events have runtime', e['runtime_minutes'].null_count() == 0)
    crossing = e.filter(pl.col('window_label') != window('session_start_ts')).height
    # Canonical volumes use event start; canonical session counts use session start.
    # Do not force these different bases into equality at a window boundary.
    qa.append(dict(check='event/session boundary diagnostic', passed=True,
                   detail=f'{crossing} events have a different session-start window; qualified-session accounting uses event-window membership, elapsed mart sessions use session-start membership'))
    totals = e.group_by('profile_id', 'window_label').agg(
        pl.col('watch_seconds').sum().alias('raw_seconds'),
        pl.col('watch_seconds').filter(pl.col('qualified')).sum().alias('raw_qseconds'),
        pl.col('date').n_unique().alias('raw_days'),
        pl.col('date').filter(pl.col('qualified')).n_unique().alias('raw_qdays'))
    qsession = e.filter(pl.col('qualified')).group_by('profile_id', 'window_label', 'session_id').agg(
        pl.col('watch_seconds').sum().alias('qseconds'),
        pl.col('elapsed_minutes').first())
    excess = qsession.filter(pl.col('qseconds') / 60 > pl.col('elapsed_minutes') + 1e-6)
    boundary_profiles = set(e.filter(pl.col('window_label') != window('session_start_ts'))['profile_id'].to_list())
    anomaly_profiles = set(excess['profile_id'].to_list())
    qs = qsession.group_by('profile_id', 'window_label').agg(
        pl.len().alias('q_sessions'), (pl.col('qseconds').mean() / 60).alias('q_minutes_per_q_session'),
        (pl.col('qseconds').median() / 60).alias('median_q_minutes_per_q_session'),
        pl.col('elapsed_minutes').mean().alias('mean_elapsed_q_session_minutes'))
    allses = (s.filter((pl.col('session_start_ts') >= '2025-09-01') &
                      (pl.col('session_start_ts') < '2026-02-28'))
              .with_columns(window('session_start_ts').alias('window_label'))
              .group_by('profile_id', 'window_label').agg(pl.len().alias('raw_sessions'),
                    pl.col('elapsed_minutes').sum().alias('raw_session_minutes')))
    detail = pandas(totals.join(qs, on=['profile_id', 'window_label'])
                    .join(allses, on=['profile_id', 'window_label']))
    v = m.merge(detail, on=['profile_id', 'window_label'], validate='one_to_one')
    check('complete session evidence', len(v) == 16398)
    for a, b, scale in [('raw_seconds', 'watch_minutes', 60),
                         ('raw_qseconds', 'qualified_watch_minutes', 60),
                         ('raw_days', 'active_days', 1), ('raw_qdays', 'qualified_active_days', 1),
                         ('raw_sessions', 'sessions', 1), ('raw_session_minutes', 'session_minutes', 1)]:
        err = (v[a] - v[b] * scale).abs().max()
        check('raw/mart ' + a, err < 1e-6, err)
    check('qualified session identity',
          (v.q_sessions * v.q_minutes_per_q_session * 60 - v.raw_qseconds).abs().max() < 1e-6)
    extra = [c for c in detail if c not in ['profile_id', 'window_label']]
    for w, pre in zip(WINDOWS, ['b', 'f']):
        p = p.merge(detail[detail.window_label == w].drop(columns='window_label')
                    .rename(columns={c: pre + '_' + c for c in extra}), on='profile_id', validate='one_to_one')
        p[pre + '_q_hours_per_active_day'] = p[pre + '_qualified_watch_hours'] / p[pre + '_active_days']
        p[pre + '_q_sessions_per_active_day'] = p[pre + '_q_sessions'] / p[pre + '_active_days']

    # Parent-title accounting: any-event observation and meaningful observation are separate sets.
    tc = ['profile_id', 'window_label', 'parent_title_id', 'events', 'qualified_watch_minutes',
          'qualified_starts', 'is_meaningful_title', 'program_type', 'qualified_assets']
    t = scan(PTW, tc).join(ids, on='profile_id', how='semi').collect()
    check('title mart keys unique', t.unique(['profile_id', 'window_label', 'parent_title_id']).height == t.height)
    check('meaningful definition matches', t.filter(pl.col('is_meaningful_title') !=
                                                   (pl.col('qualified_starts') > 0)).height == 0)
    t = pandas(t)
    keys = ['profile_id', 'parent_title_id']
    bt = t[t.window_label == WINDOWS[0]].drop(columns='window_label')
    ft = t[t.window_label == WINDOWS[1]].drop(columns='window_label')
    z = bt.merge(ft, on=keys, how='outer', suffixes=('_b', '_f'), validate='one_to_one')
    for c in ['events', 'qualified_watch_minutes', 'qualified_starts', 'qualified_assets']:
        z[[c + '_b', c + '_f']] = z[[c + '_b', c + '_f']].fillna(0)
    b, f = z.qualified_watch_minutes_b, z.qualified_watch_minutes_f
    eb, ef = z.events_b > 0, z.events_f > 0
    mb, mf = z.qualified_starts_b > 0, z.qualified_starts_f > 0
    check('positive qualified minutes iff meaningful', ((b > 0) == mb).all() and ((f > 0) == mf).all())
    z['observed_common_delta_hours'] = np.where(eb & ef, f - b, 0) / 60
    z['final_only_observed_hours'] = np.where(~eb & ef, f, 0) / 60
    z['baseline_only_observed_hours'] = np.where(eb & ~ef, b, 0) / 60
    z['retained_meaningful_delta_hours'] = np.where(mb & mf, f - b, 0) / 60
    z['added_meaningful_hours'] = np.where(~mb & mf, f, 0) / 60
    z['lost_meaningful_hours'] = np.where(mb & ~mf, b, 0) / 60
    z['retained_loss_hours'] = np.where(mb & mf, (b - f).clip(lower=0), 0) / 60
    z['retained_gain_hours'] = np.where(mb & mf, (f - b).clip(lower=0), 0) / 60
    z['gross_gain_hours'] = (f - b).clip(lower=0) / 60
    z['gross_loss_hours'] = (b - f).clip(lower=0) / 60
    z['added_meaningful_titles'] = (~mb & mf).astype(int)
    z['lost_meaningful_titles'] = (mb & ~mf).astype(int)
    z['retained_meaningful_titles'] = (mb & mf).astype(int)
    z['added_previously_unqualified_titles'] = (eb & ~mb & mf).astype(int)
    z['added_unobserved_baseline_titles'] = (~eb & mf).astype(int)
    z['lost_still_observed_unqualified_titles'] = (mb & ~mf & ef).astype(int)
    z['b_title_qhours'] = b / 60
    z['f_title_qhours'] = f / 60
    for pre, suffix in [('b', 'b'), ('f', 'f')]:
        z[pre + '_meaningful_count'] = (z['qualified_starts_' + suffix] > 0).astype(int)
        episodic = z['program_type_' + suffix].isin(['WEB_SERIES', 'TV_CATCHUP', 'REALITY'])
        z[pre + '_episodic_hours'] = np.where(episodic, z['qualified_watch_minutes_' + suffix], 0) / 60
        z[pre + '_qualified_episodic_assets'] = np.where(episodic, z['qualified_assets_' + suffix], 0)
    newcols = list(z.columns[z.columns.get_loc('observed_common_delta_hours'):])
    alloc = z.groupby('profile_id', sort=False)[newcols].sum().reset_index()
    p = p.merge(alloc, on='profile_id', validate='one_to_one')
    for pre in ['b', 'f']:
        check(pre + ' title hours reconcile', (p[pre + '_title_qhours'] -
                                               p[pre + '_qualified_watch_hours']).abs().max() < 1e-9)
        check(pre + ' title breadth reconcile', (p[pre + '_meaningful_count'] ==
                                                 p[pre + '_distinct_meaningful_titles']).all())
        p[pre + '_episodic_hour_share'] = p[pre + '_episodic_hours'] / p[pre + '_qualified_watch_hours']
    metrics = ['qualified_watch_hours', 'active_days', 'qualified_active_days', 'sessions',
               'mean_session_minutes', 'median_session_minutes', 'sessions_per_active_day',
               'q_hours_per_active_day', 'q_sessions', 'q_minutes_per_q_session',
               'median_q_minutes_per_q_session', 'mean_elapsed_q_session_minutes',
               'q_sessions_per_active_day', 'distinct_meaningful_titles',
               'top_title_qualified_share', 'title_hhi', 'entitled_days_in_window',
               'episodic_hour_share', 'qualified_episodic_assets']
    for c in metrics:
        p['d_' + c] = p['f_' + c] - p['b_' + c]
    dh = p.d_qualified_watch_hours
    for name, calculated in {
        'any-observation additive accounting': p.observed_common_delta_hours + p.final_only_observed_hours - p.baseline_only_observed_hours,
        'meaningful-set additive accounting': p.retained_meaningful_delta_hours + p.added_meaningful_hours - p.lost_meaningful_hours,
        'gross gains minus losses': p.gross_gain_hours - p.gross_loss_hours,
    }.items():
        err = (calculated - dh).abs().max()
        check(name, err < 1e-9, err)
    check('breadth additions minus losses', (p.added_meaningful_titles - p.lost_meaningful_titles ==
                                           p.d_distinct_meaningful_titles).all())
    up = dh > EPS
    day = p.d_active_days
    p['A_group'] = np.select([up & (day > 0), up & (day == 0), up & (day < 0), ~up & (day > 0)],
                            ['hours_up_days_up', 'hours_up_days_same', 'hours_up_days_down',
                             'hours_not_up_days_up'], default='remaining')
    def direction(v):
        return np.select([v > EPS, v < -EPS], ['up', 'down'], default='same')
    p['B_group'] = 'titles_' + pd.Series(direction(p.d_distinct_meaningful_titles), index=p.index) + '_hours_' + direction(dh)
    p['session_change'] = 'q_sessions_' + pd.Series(direction(p.d_q_sessions), index=p.index) + '_q_minutes_per_session_' + direction(p.d_q_minutes_per_q_session)
    check('prior breadth+hours growers', ((p.d_distinct_meaningful_titles > 0) & up).sum() == 3784)
    check('prior breadth-only growers', ((p.d_distinct_meaningful_titles > 0) & ~up).sum() == 1652)
    samefamily = p.baseline_family == p.final_family
    samestate = p.baseline_state == p.final_state
    contexts = [('ALL', 'paired', p), ('EXPOSURE', 'FULL_90_both', p[(p.b_entitled_days_in_window == 90) & (p.f_entitled_days_in_window == 90)]),
                ('EXPOSURE', 'partial_either', p[(p.b_entitled_days_in_window < 90) | (p.f_entitled_days_in_window < 90)]),
                ('SESSION_QA', 'exclude_boundary_and_duration_anomaly', p[~p.profile_id.isin(boundary_profiles | anomaly_profiles)])]
    for field, kind in [('final_family', 'FINAL_FAMILY'), ('final_state', 'FINAL_STATE')]:
        contexts += [(kind, str(k), g) for k, g in p.groupby(field)]
    contexts += [('PERSISTENT_FAMILY', str(k), g) for k, g in p[samefamily].groupby('final_family')]
    contexts += [('TRANSITION', str(a) + ' -> ' + str(b), g) for (a, b), g in p[~samefamily].groupby(['baseline_family', 'final_family'])]
    residual = samefamily & (p.final_family == 'RESIDUAL')
    contexts += [('RESIDUAL_DETAIL', 'exact_state_stayers', p[residual & samestate]),
                 ('RESIDUAL_DETAIL', 'internal_state_movers', p[residual & ~samestate])]
    joint, distributions, sessions = [], [], []
    distribution_cols = ['d_' + c for c in metrics] + [
        'observed_common_delta_hours', 'final_only_observed_hours', 'baseline_only_observed_hours',
        'retained_meaningful_delta_hours', 'added_meaningful_hours', 'lost_meaningful_hours',
        'retained_loss_hours', 'retained_gain_hours', 'gross_gain_hours', 'gross_loss_hours',
        'added_meaningful_titles', 'lost_meaningful_titles', 'added_previously_unqualified_titles']
    for kind, label, ctx in contexts:
        if ctx.empty:
            continue
        for test in ['A', 'B']:
            for group, g in ctx.groupby(test + '_group'):
                base = dict(context_type=kind, context=label, test=test, joint_group=group,
                            context_profiles=len(ctx), profiles=len(g), share_of_context=len(g) / len(ctx))
                row = base | {
                    'median_delta_hours': g.d_qualified_watch_hours.median(),
                    'median_delta_active_days': g.d_active_days.median(),
                    'median_delta_titles': g.d_distinct_meaningful_titles.median(),
                    'median_delta_top_title_share': g.d_top_title_qualified_share.median(),
                    'joint_hhi_support': int(g.d_title_hhi.notna().sum()),
                    'median_delta_hhi': g.d_title_hhi.dropna().median() if g.d_title_hhi.notna().any() else np.nan,
                    'top_share_decreased_profiles': int((g.d_top_title_qualified_share < -EPS).sum()),
                    'gross_gain_and_loss_profiles': int(((g.gross_gain_hours > EPS) & (g.gross_loss_hours > EPS)).sum()),
                    'retained_title_loss_profiles': int((g.retained_loss_hours > EPS).sum()),
                    'previously_unqualified_addition_profiles': int((g.added_previously_unqualified_titles > 0).sum()),
                    'median_gross_gain_hours': g.gross_gain_hours.median(),
                    'median_gross_loss_hours': g.gross_loss_hours.median(),
                    'median_delta_q_sessions': g.d_q_sessions.median(),
                    'median_delta_q_minutes_per_q_session': g.d_q_minutes_per_q_session.median(),
                    'median_delta_elapsed_session_minutes': g.d_mean_session_minutes.median(),
                    'elapsed_session_mean_increased_profiles': int((g.d_mean_session_minutes > EPS).sum()),
                    'q_session_frequency_increased_profiles': int((g.d_q_sessions_per_active_day > EPS).sum()),
                    'both_full_90_profiles': int(((g.b_entitled_days_in_window == 90) & (g.f_entitled_days_in_window == 90)).sum())}
                joint.append(row)
                if kind in ['ALL', 'PERSISTENT_FAMILY', 'RESIDUAL_DETAIL', 'EXPOSURE']:
                    for c in distribution_cols:
                        v = g[c].dropna()
                        distributions.append(base | dict(metric=c, measured_profiles=len(v),
                            mean=v.mean(), p10=v.quantile(.1), p25=v.quantile(.25), median=v.median() if len(v) else np.nan,
                            p75=v.quantile(.75), p90=v.quantile(.9), minimum=v.min(), maximum=v.max()))
                if test == 'A':
                    for sg, gg in g.groupby('session_change'):
                        sessions.append(base | dict(session_change=sg, session_pattern_profiles=len(gg),
                            share_within_joint_group=len(gg) / len(g),
                            elapsed_session_mean_increased_profiles=int((gg.d_mean_session_minutes > EPS).sum())))
    # All distributions above summarize individual deltas, not subtraction of marginal medians.
    checks = {'paired_profiles': len(p), 'profile_windows': len(m), 'paired_events_read': e.height,
              'paired_sessions_read': s.height, 'paired_title_window_rows': t.shape[0],
              'events_with_different_session_window': crossing,
              'sessions_with_different_event_window': e.filter(pl.col('window_label') != window('session_start_ts'))['session_id'].n_unique(),
              'profiles_with_different_event_session_window': e.filter(pl.col('window_label') != window('session_start_ts'))['profile_id'].n_unique(),
              'profile_windows_active_days_differ_from_qualified_days': int((m.active_days != m.qualified_active_days).sum()),
              'both_full_90_profiles': int(((p.b_entitled_days_in_window == 90) & (p.f_entitled_days_in_window == 90)).sum()),
              'qualified_session_playback_longer_than_elapsed_rows': excess.height,
              'duration_anomaly_profiles': len(anomaly_profiles),
              'maximum_qualified_playback_excess_seconds': excess.select((pl.col('qseconds') - pl.col('elapsed_minutes') * 60).max()).item(),
              'hours_unchanged_profiles': int((dh.abs() <= EPS).sum())}
    qa.append(dict(check='qualified playback versus elapsed duration diagnostic', passed=True,
                   detail=f'{excess.height} session-window rows on {len(anomaly_profiles)} profiles exceed elapsed time; reported as source caveat, not repaired. See SESSION_QA sensitivity context.'))
    # Inventory only: verify fields and source coverage; do not reconstruct cross-origin behaviour.
    inventory_sources = {
        '6C3': ('analysis_outputs/test6c3_profile_behavior_opportunity.csv', ['profile_id', 'baseline_dominant_origin_language', 'baseline_cross_origin_minute_share', 'final_cross_origin_qualified_minutes']),
        '6D4': ('analysis_outputs/test6d4_profile_peer_residuals.csv', ['profile_id']),
        '7_profile': ('analysis_outputs/test7_integrated/private/profile_evidence.csv', ['profile_id', 'paired', 'baseline_outside_days', 'final_outside_days', 'repeated_outside_parent_titles', 'repeated_outside_origins', 'baseline_outside_hours', 'final_outside_hours']),
        '7_origin': ('analysis_outputs/test7_integrated/private/origin_composition.csv', ['profile_id', 'original_language', 'BASELINE_90', 'FINAL_90', 'outside']),
    }
    inventory_coverage = {}
    for tag, (path, columns) in inventory_sources.items():
        frame = scan(path, columns).collect()
        inventory_coverage[tag] = dict(path=path, rows=frame.height, distinct_profiles=frame['profile_id'].n_unique())
        check('inventory paired coverage ' + tag, set(p.profile_id).issubset(set(frame['profile_id'].to_list())))
    daily = pl.scan_parquet(ROOT / 'analysis_outputs/test7_integrated/private/daily_evidence.parquet')
    check('daily cache inventory schema', set(['profile_id', 'window_label', 'date', 'qsec', 'osec']).issubset(set(daily.collect_schema().names())))
    check('inputs and existing dashboard unchanged', all(digest(ROOT / x) == h for x, h in before.items()))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(joint).to_csv(OUT / 'joint_change_context.csv', index=False)
    pd.DataFrame(distributions).to_csv(OUT / 'individual_change_distributions.csv', index=False)
    pd.DataFrame(sessions).to_csv(OUT / 'session_decomposition.csv', index=False)
    pd.DataFrame(qa).to_csv(OUT / 'qa_checks.csv', index=False)
    origin_inventory().to_csv(OUT / 'cross_origin_measurement_inventory.csv', index=False)
    runtime = time.perf_counter() - started
    (OUT / 'source_manifest.json').write_text(json.dumps(dict(
        sources_sha256=before, counts=checks, execution_seconds=runtime,
        cross_origin_source_coverage=inventory_coverage,
        quantiles='linear', direction_tolerance=EPS,
        population='Original paired panel; no state/family re-ranking',
        script_sha256=digest(Path(__file__))), indent=2), encoding='utf-8')
    print(pd.DataFrame(joint).query("context_type == 'ALL'").to_string(index=False))
    print(json.dumps(checks, indent=2))
    print(f'QA: {len(qa)}/{len(qa)} passed. Runtime: {runtime:.2f}s. Outputs: {OUT}')


if __name__ == '__main__':
    main()
