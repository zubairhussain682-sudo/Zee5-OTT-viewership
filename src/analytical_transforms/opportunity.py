"""Day-level opportunity using effective plans and released playable catalogue.

Catalogue date columns must be pandas timestamps (NaT for no exit).
Window bounds are inclusive pandas timestamps within the supplied calendar.
Profile outputs follow profiles row order; exposure columns follow parent IDs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .access import access_day_matrix, profile_access_day_matrix, plan_codes, language_membership


def public_parent_availability(catalogue: pd.DataFrame, cal):
    parents = pd.Index(sorted(catalogue['parent_title_id'].unique()))
    pos = {p: i for i, p in enumerate(parents)}
    avail = np.zeros((len(parents), cal.n_days), dtype=bool)
    for r in catalogue.itertuples(index=False):
        start = r.catalogue_entry_date
        if pd.notna(r.release_date) and r.release_date > start:
            start = r.release_date
        s = max(cal.day_index(start.date()), 0)
        if s >= cal.n_days:
            continue
        if pd.isna(r.catalogue_exit_date):
            e = cal.n_days - 1
        else:
            e = min(cal.day_index(r.catalogue_exit_date.date()), cal.n_days - 1)
        if e < s:
            continue
        avail[pos[r.parent_title_id], s:e + 1] = True
    return (parents, avail)


def eligibility_cube(catalogue, audio, cal):
    parents, avail = public_parent_availability(catalogue, cal)
    pf = pd.DataFrame({'parent_title_id': parents})
    langs = language_membership(pf, audio)
    codes = plan_codes()
    cube = np.zeros((len(codes), len(parents), cal.n_days), dtype=bool)
    for ci, (fam, grp) in enumerate(codes):
        if fam in ('ALL_ACCESS', 'ALL_ACCESS_SPORTS'):
            cube[ci] = avail
        else:
            mask = langs.get(grp, np.zeros(len(parents), dtype=bool))
            cube[ci] = avail & mask[:, None]
    return (parents, cube)


def account_parent_exposure(cycles, catalogue, audio, cal, w0, w1):
    accounts, has, code = access_day_matrix(cycles, cal)
    parents, cube = eligibility_cube(catalogue, audio, cal)
    d0 = cal.day_index(w0.date())
    d1 = cal.day_index(w1.date())
    pre = np.cumsum(cube[:, :, d0:d1 + 1].astype(np.int16), axis=2)
    pre = np.concatenate(
        [np.zeros((pre.shape[0], pre.shape[1], 1), dtype=np.int16), pre], axis=2)
    eff = np.where(has[:, d0:d1 + 1], code[:, d0:d1 + 1], -1)
    out = np.zeros((len(accounts), len(parents)), dtype=np.int16)
    n = eff.shape[1]
    for i in range(eff.shape[0]):
        row = eff[i]
        brk = np.flatnonzero(np.diff(row)) + 1
        starts = np.concatenate(([0], brk))
        ends = np.concatenate((brk, [n]))
        for s, e in zip(starts, ends):
            c = row[s]
            if c < 0:
                continue
            out[i] += pre[c, :, e] - pre[c, :, s]
    return (accounts, parents, out)


def account_daily_opportunity(cycles, catalogue, audio, cal, w0, w1, all_accounts=None):
    accounts, has, code = access_day_matrix(cycles, cal)
    parents, cube = eligibility_cube(catalogue, audio, cal)
    d0, d1 = (cal.day_index(w0.date()), cal.day_index(w1.date()))
    daily = cube[:, :, d0:d1 + 1].sum(axis=1)
    eff = np.where(has[:, d0:d1 + 1], code[:, d0:d1 + 1], -1)
    entitled = (eff >= 0).sum(axis=1)
    ptd = np.zeros(len(accounts), dtype=np.int64)
    for c in range(daily.shape[0]):
        ptd += ((eff == c) * daily[c][None, :]).sum(axis=1)
    out = pd.DataFrame({
        'account_id': accounts,
        'entitled_days_in_window': entitled.astype(int),
        'eligible_parent_title_days': ptd,
        'mean_daily_eligible_parent_titles': np.where(
            entitled > 0, ptd / np.maximum(entitled, 1), 0.0),
    })
    if all_accounts is not None:
        out = (out.set_index('account_id')
               .reindex(pd.Index(sorted(all_accounts), name='account_id'))
               .fillna(0)
               .reset_index())
        for c in ('entitled_days_in_window', 'eligible_parent_title_days'):
            out[c] = out[c].astype(int)
    return out


def profile_opportunity(profiles, cycles, catalogue, audio, cal, w0, w1):
    ids, has, code = profile_access_day_matrix(profiles, cycles, cal)
    parents, cube = eligibility_cube(catalogue, audio, cal)
    d0, d1 = (cal.day_index(w0.date()), cal.day_index(w1.date()))
    eff = np.where(has[:, d0:d1 + 1], code[:, d0:d1 + 1], -1)
    pre = np.cumsum(cube[:, :, d0:d1 + 1], axis=2, dtype=np.int32)
    pre = np.concatenate([np.zeros((*pre.shape[:2], 1), dtype=np.int32), pre], axis=2)
    exposure = np.zeros((len(ids), len(parents)), dtype=np.int32)
    for i, row in enumerate(eff):
        breaks = np.flatnonzero(np.diff(row)) + 1
        for start, end in zip(np.r_[0, breaks], np.r_[breaks, len(row)]):
            plan = row[start]
            if plan >= 0:
                exposure[i] += pre[plan, :, end] - pre[plan, :, start]
    entitled = (eff >= 0).sum(axis=1)
    title_days = exposure.sum(axis=1)
    opp = pd.DataFrame({
        'profile_id': ids,
        'entitled_days_in_window': entitled,
        'eligible_parent_title_days': title_days,
        'mean_daily_eligible_parent_titles': np.where(
            entitled > 0, title_days / np.maximum(entitled, 1), 0.0),
    })
    return ((ids, parents, exposure), opp)
