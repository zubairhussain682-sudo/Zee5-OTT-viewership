"""Historical access projected separately at account and profile grain.

Cycles contain inclusive Python date boundaries. Profiles supply creation dates.
An absent account cycle, a gap or a day before profile creation contributes zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def access_day_matrix(cycles: pd.DataFrame, cal) -> tuple[pd.Index, np.ndarray, np.ndarray]:
    accounts = pd.Index(sorted(cycles['account_id'].unique()))
    pos = {a: i for i, a in enumerate(accounts)}
    n_days = cal.n_days
    has = np.zeros((len(accounts), n_days), dtype=bool)
    code = np.full((len(accounts), n_days), -1, dtype=np.int16)
    codes = plan_codes()
    for r in cycles.itertuples(index=False):
        i = pos[r.account_id]
        s = max(cal.day_index(r.cycle_start_date), 0)
        e = min(cal.day_index(r.cycle_end_date), n_days - 1)
        if e < s:
            continue
        has[i, s:e + 1] = True
        key = (r.plan_family, r.plan_language_group)
        code[i, s:e + 1] = codes.index(key) if key in codes else -1
    return (accounts, has, code)


def profile_access_day_matrix(profiles, cycles, cal):
    accounts, has, code = access_day_matrix(cycles, cal)
    positions = accounts.get_indexer(profiles['account_id'])
    phas = np.zeros((len(profiles), cal.n_days), dtype=bool)
    pcode = np.full(phas.shape, -1, dtype=np.int16)
    known = positions >= 0
    phas[known] = has[positions[known]]
    pcode[known] = code[positions[known]]
    created = pd.to_datetime(profiles['profile_created_date'])
    if created.isna().any() or profiles['profile_id'].duplicated().any():
        raise ValueError('Profile opportunity requires unique profiles and creation dates')
    first = np.array([cal.day_index(x.date()) for x in created])
    exists = np.arange(cal.n_days)[None, :] >= first[:, None]
    phas &= exists & (pcode >= 0)
    pcode[~phas] = -1
    return (pd.Index(profiles['profile_id']), phas, pcode)


def plan_codes() -> list[tuple[str, str]]:
    packs = ['Hindi', 'Telugu', 'Tamil', 'Marathi', 'Bengali', 'Kannada', 'Malayalam']
    return [('ALL_ACCESS', 'ALL'), ('ALL_ACCESS_SPORTS', 'ALL')] + [('REGIONAL', p) for p in packs]


def language_membership(parents: pd.DataFrame, audio: pd.DataFrame) -> dict[str, np.ndarray]:
    order = {p: i for i, p in enumerate(parents['parent_title_id'].values)}
    out: dict[str, np.ndarray] = {}
    for lang, grp in audio.groupby('language'):
        mask = np.zeros(len(order), dtype=bool)
        for pid in grp['parent_title_id']:
            i = order.get(pid)
            if i is not None:
                mask[i] = True
        out[lang] = mask
    return out


def catalogue_intervals(catalogue, cal):
    """Playable interval: max(release, entry) through inclusive exit."""
    begin = catalogue[["release_date", "catalogue_entry_date"]].max(axis=1)
    finish = (catalogue["catalogue_exit_date"] + pd.Timedelta(days=1)).fillna(
        pd.Timestamp(cal.end) + pd.Timedelta(days=1))
    return begin, finish
