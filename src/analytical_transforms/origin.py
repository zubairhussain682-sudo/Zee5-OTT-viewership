"""Title-origin ecosystems: a fixed behavioural anchor and anchor-relative opportunity.

Title origin is the language ecosystem a parent title comes from. It is not the
audio track consumed and not the language that admitted the title into a regional
pack, so nothing here reads `view_events.audio_language` or plan language.

Opportunity is split from the same day-by-day exposure matrix the marts are built
on, so a later plan can never enlarge an earlier window's opportunity: each window
is reconstructed from the access held on its own days.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def baseline_origin_anchor(origin_minutes: pd.DataFrame) -> pd.DataFrame:
    """The origin ecosystem holding the largest share of qualified Baseline minutes.

    `origin_minutes` carries one row per profile × original language with the
    qualified minutes viewed in the Baseline window. Ties are resolved by minutes
    descending then language ascending, matching the published analysis.

    The result is a behavioural reference, not native language, home region, plan
    language or a permanent preference.
    """
    frame = origin_minutes.rename(columns={'qualified_minutes': 'minutes'}).copy()
    frame['minutes'] = frame['minutes'].astype(float)
    ranked = frame.sort_values(['profile_id', 'minutes', 'original_language'],
                               ascending=[True, False, True], kind='mergesort')
    totals = ranked.groupby('profile_id')['minutes'].sum()
    first = ranked.groupby('profile_id').head(1).set_index('profile_id')
    second = (ranked.groupby('profile_id').nth(1).set_index('profile_id')
              if len(ranked) else ranked.set_index('profile_id'))
    out = pd.DataFrame({
        'baseline_anchor_origin': first['original_language'],
        'baseline_anchor_minutes': first['minutes'],
        'baseline_total_minutes': totals,
    })
    out['baseline_anchor_share'] = np.where(
        out['baseline_total_minutes'] > 0,
        out['baseline_anchor_minutes'] / out['baseline_total_minutes'].replace(0, np.nan),
        np.nan)
    out['baseline_second_origin_share'] = (
        second['minutes'].reindex(out.index) / out['baseline_total_minutes']).fillna(0.0)
    return out.reset_index()[['profile_id', 'baseline_anchor_origin', 'baseline_anchor_share',
                              'baseline_second_origin_share']]


def cross_origin_mask(parent_origins, anchor_origin: str) -> np.ndarray:
    """Parent titles whose origin differs from the fixed anchor.

    A dubbed title stays cross-origin: the track consumed never changes a title's
    origin.
    """
    return np.asarray(parent_origins, dtype=object) != anchor_origin


def cross_origin_opportunity(exposure: np.ndarray, parent_origins, anchors) -> pd.DataFrame:
    """Split each profile's reachable catalogue around its own fixed anchor.

    `exposure` is the profile × parent-title day matrix for one window, as
    returned by ``profile_opportunity``; `anchors` is each profile's fixed
    Baseline anchor in the same row order. Reach counts a title once; title-days
    weight it by the historically valid days it was reachable. Shares are
    undefined, not zero, where a profile had no reachable catalogue at all.
    """
    origins = np.asarray(parent_origins, dtype=object)
    anchors = np.asarray(anchors, dtype=object)
    missing = pd.isna(anchors)
    if missing.any():
        raise ValueError(
            f'{int(missing.sum())} profile(s) have no fixed anchor; without one every '
            'reachable title would be counted as cross-origin')
    if exposure.shape[1] != origins.shape[0]:
        raise ValueError('exposure columns and parent origins disagree')
    if exposure.shape[0] != anchors.shape[0]:
        raise ValueError('exposure rows and anchors disagree')

    reachable = exposure > 0
    total_titles = reachable.sum(axis=1).astype(np.int64)
    total_days = exposure.sum(axis=1).astype(np.int64)
    anchor_titles = np.zeros(len(anchors), dtype=np.int64)
    anchor_days = np.zeros(len(anchors), dtype=np.int64)
    for origin in pd.unique(anchors):
        rows = anchors == origin
        columns = origins == origin
        anchor_titles[rows] = reachable[np.ix_(rows, columns)].sum(axis=1)
        anchor_days[rows] = exposure[np.ix_(rows, columns)].sum(axis=1)

    cross_titles = total_titles - anchor_titles
    cross_days = total_days - anchor_days
    return pd.DataFrame({
        'reachable_parent_titles_total': total_titles,
        'reachable_anchor_origin_titles': anchor_titles,
        'reachable_cross_origin_titles': cross_titles,
        'eligible_parent_title_days_total': total_days,
        'anchor_origin_title_days': anchor_days,
        'cross_origin_title_days': cross_days,
        'cross_origin_reachable_title_share': _share(cross_titles, total_titles),
        'cross_origin_title_day_share': _share(cross_days, total_days),
    })


def cross_origin_minute_share(origin_minutes: pd.DataFrame, anchors: pd.Series) -> pd.DataFrame:
    """Qualified minutes on titles originating outside the fixed anchor.

    Classification uses the title's original language only, so this is movement
    across catalogue ecosystems rather than audio-track switching.
    """
    frame = origin_minutes.rename(columns={'qualified_minutes': 'minutes'}).copy()
    frame['minutes'] = frame['minutes'].astype(float)
    frame['anchor'] = frame['profile_id'].map(anchors)
    if frame['anchor'].isna().any():
        raise ValueError('every profile needs a fixed anchor before classification')
    frame['is_cross_origin'] = frame['original_language'] != frame['anchor']
    grouped = frame.groupby('profile_id')
    total = grouped['minutes'].sum()
    cross = grouped.apply(lambda g: g.loc[g['is_cross_origin'], 'minutes'].sum(),
                          include_groups=False)
    return pd.DataFrame({
        'qualified_minutes': total,
        'cross_origin_qualified_minutes': cross,
        'cross_origin_minute_share': _share(cross.to_numpy(), total.to_numpy()),
    }).reset_index()


def new_origin_entry(baseline_minutes: pd.DataFrame, final_minutes: pd.DataFrame) -> pd.DataFrame:
    """Origins consumed in the final window that were not consumed in the baseline."""
    seen = {(p, o) for p, o in
            baseline_minutes.loc[baseline_minutes['qualified_minutes'] > 0,
                                 ['profile_id', 'original_language']].itertuples(index=False)}
    final = final_minutes[final_minutes['qualified_minutes'] > 0].copy()
    final['is_new_origin'] = [
        (p, o) not in seen for p, o in
        final[['profile_id', 'original_language']].itertuples(index=False)]
    grouped = final.groupby('profile_id')
    total = grouped['qualified_minutes'].sum()
    new = grouped.apply(lambda g: g.loc[g['is_new_origin'], 'qualified_minutes'].sum(),
                        include_groups=False)
    return pd.DataFrame({
        'entered_new_origin': new > 0,
        'new_origin_minute_share': _share(new.to_numpy(), total.to_numpy()),
    }).reset_index()


def _share(numerator, denominator) -> np.ndarray:
    """Undefined where there is no denominator, never silently zero."""
    numerator = np.asarray(numerator, dtype=float)
    denominator = np.asarray(denominator, dtype=float)
    return np.divide(numerator, denominator,
                     out=np.full(np.broadcast(numerator, denominator).shape, np.nan),
                     where=denominator > 0)
