"""Canonical episodic progression, continuous access and observable outcomes.

One opportunity per profile/current/next asset. Dates use the project's local
calendar; catalogue exits and subscription ends are inclusive calendar dates.
The first interruption terminates follow-up permanently for that opportunity.
"""
import numpy as np
import pandas as pd

from .access import (catalogue_intervals, language_membership, plan_codes,
                     profile_access_day_matrix)
from .qualification import COMPLETION, qualified_start


def episode_sequence(catalogue):
    epi = catalogue.loc[catalogue.content_type.eq("EPISODE")].copy()
    keys = ["parent_title_id", "season_number", "episode_number"]
    if epi[keys].isna().any().any() or epi.duplicated(keys).any():
        raise ValueError("Ambiguous episodic ordering")
    if catalogue.content_id.duplicated().any():
        raise ValueError("Duplicate catalogue content_id")
    epi = epi.sort_values(keys)
    epi["episode_order"] = epi.groupby("parent_title_id").cumcount()
    for col in ["content_id", "season_number", "episode_number", "episode_order"]:
        epi["next_" + col] = epi.groupby("parent_title_id")[col].shift(-1)
    return epi


def continuation_table(ev, d, cal, b):
    """Return the authoritative opportunity object; never write source data."""
    horizon = pd.Timedelta(days=int(b["continuation_observation_days"]))
    if horizon != pd.Timedelta(days=7):
        raise ValueError("Continuation horizon is locked at seven days")
    pro, cat = d["profiles"], d["catalogue"]
    if (pro.profile_id.duplicated().any()
            or not pro.account_id.isin(d["accounts"].account_id).all()):
        raise ValueError("Invalid profile/account relationship")
    epi = episode_sequence(cat)
    q = qualified_start(ev, ev.runtime_minutes * 60)
    e = ev.loc[ev.content_type.eq("EPISODE") & q].copy()

    # Event-end evidence establishes progression, not a later revisit.
    ready = e.loc[e.progress.ge(COMPLETION)].sort_values(
        ["event_end_ts", "event_start_ts", "view_event_id"])
    ready = ready.drop_duplicates(["profile_id", "content_id"])
    cur = ready[["profile_id", "content_id", "event_end_ts", "session_id",
                 "view_event_id"]].rename(columns={
                     "content_id": "current_content_id",
                     "event_end_ts": "progression_ts",
                     "session_id": "session_id",
                     "view_event_id": "progression_event_id"})
    cur = cur.merge(epi[["content_id", "parent_title_id", "program_type",
                         "season_number", "episode_number", "episode_order",
                         "next_content_id", "next_season_number", "next_episode_number",
                         "next_episode_order"]],
                    left_on="current_content_id", right_on="content_id",
                    validate="many_to_one")
    cur = cur.dropna(subset=["next_content_id"]).merge(
        pro[["profile_id", "account_id", "profile_created_date"]],
        on="profile_id", validate="many_to_one")

    begin, finish = catalogue_intervals(cat, cal)
    starts = pd.Series(begin.to_numpy(), index=cat.content_id)
    ends = pd.Series(finish.to_numpy(), index=cat.content_id)
    cur["next_available_ts"] = cur.next_content_id.map(starts)
    cur["next_unavailable_ts"] = cur.next_content_id.map(ends)
    cur["structural_ready_ts"] = cur[["progression_ts", "next_available_ts",
                                      "profile_created_date"]].max(axis=1)

    ids, has, code = profile_access_day_matrix(pro, d["cycles"], cal)
    parents = pd.DataFrame({"parent_title_id": sorted(cat.parent_title_id.unique())})
    langs = language_membership(parents, d["audio"])
    permit = np.ones((len(plan_codes()), len(parents)), dtype=bool)
    for i, (family, lang) in enumerate(plan_codes()):
        if family == "REGIONAL":
            permit[i] = langs.get(lang, np.zeros(len(parents), dtype=bool))
    pi = ids.get_indexer(cur.profile_id)
    ti = pd.Index(parents.parent_title_id).get_indexer(cur.parent_title_id)
    if (pi < 0).any() or (ti < 0).any():
        raise ValueError("Missing continuation relationship")

    day0 = pd.Timestamp(cal.start)
    daynums = np.arange(cal.n_days)
    dates = (day0 + pd.to_timedelta(daynums, unit="D")).to_numpy()
    result = []
    for lo in range(0, len(cur), 25000):
        sub = cur.iloc[lo:lo + 25000].copy()
        pc = code[pi[lo:lo + len(sub)]]
        valid = (has[pi[lo:lo + len(sub)]]
                 & permit[np.maximum(pc, 0), ti[lo:lo + len(sub), None]])
        valid &= (dates[None, :] >= sub.next_available_ts.dt.normalize().to_numpy()[:, None])
        valid &= (dates[None, :] < sub.next_unavailable_ts.to_numpy()[:, None])
        first_possible = ((sub.structural_ready_ts.dt.normalize() - day0).dt.days).to_numpy()
        eligible = valid & (daynums[None, :] >= first_possible[:, None])
        present = eligible.any(axis=1)
        opening_day = eligible.argmax(axis=1)
        bad_after = (~valid) & (daynums[None, :] >= opening_day[:, None])
        stop_day = np.where(bad_after.any(axis=1), bad_after.argmax(axis=1), cal.n_days)
        resumed = (valid & (daynums[None, :] > stop_day[:, None])).any(axis=1)
        sub["opportunity_start"] = pd.concat([
            sub.structural_ready_ts.reset_index(drop=True),
            pd.Series(day0 + pd.to_timedelta(opening_day, unit="D")),
        ], axis=1).max(axis=1).to_numpy()
        sub["continuous_end_exclusive"] = day0 + pd.to_timedelta(stop_day, unit="D")
        sub["opening_plan_code"] = pc[np.arange(len(sub)), opening_day]
        sub["access_resumed_later"] = resumed
        result.append(sub.loc[present])

    # Preserve the complete schema even when a fixture has no opportunities.
    if not result:
        empty = cur.copy()
        for col in ["opportunity_start", "continuous_end_exclusive"]:
            empty[col] = pd.Series(dtype="datetime64[ns]")
        empty["opening_plan_code"] = pd.Series(dtype=int)
        empty["access_resumed_later"] = pd.Series(dtype=bool)
        result = [empty]
    out = pd.concat(result, ignore_index=True)
    out["opportunity_end"] = out.opportunity_start + horizon
    out["full_horizon_observed"] = out.opportunity_end.le(out.continuous_end_exclusive)
    out["interrupted_before_horizon"] = (
        ~out.full_horizon_observed
        & out.continuous_end_exclusive.lt(pd.Timestamp(cal.end) + pd.Timedelta(days=1)))
    out["opportunity_key"] = (
        out.profile_id + "|" + out.current_content_id + "|" + out.next_content_id)
    if out.opportunity_key.duplicated().any():
        raise ValueError("Duplicate continuation opportunity")

    # Attribute only the actual qualifying positive, earliest start then event id.
    metadata = ["view_event_id", "event_start_ts", "event_end_ts", "session_id",
                "is_autoplay", "audio_language", "device_type"]
    ne = e[["profile_id", "content_id"] + metadata].rename(columns={
        "content_id": "next_content_id", **{c: "next_" + c for c in metadata}})
    match = out[["opportunity_key", "profile_id", "next_content_id", "opportunity_start",
                 "opportunity_end", "continuous_end_exclusive"]].merge(
        ne, on=["profile_id", "next_content_id"], how="inner", validate="one_to_many")
    match = match.loc[match.next_event_start_ts.ge(match.opportunity_start)
                      & match.next_event_start_ts.le(match.opportunity_end)
                      & match.next_event_start_ts.lt(match.continuous_end_exclusive)]
    match = (match.sort_values(["next_event_start_ts", "next_view_event_id"])
             .drop_duplicates("opportunity_key"))
    out = out.merge(match[["opportunity_key"] + ["next_" + c for c in metadata]],
                    on="opportunity_key", how="left", validate="one_to_one")

    out["continued"] = out.next_view_event_id.notna()
    out["observed_negative"] = ~out.continued & out.full_horizon_observed
    out["censored"] = ~out.continued & ~out.full_horizon_observed
    out["opening_access_valid"] = True
    out["opening_plan_family"] = out.opening_plan_code.map(lambda x: plan_codes()[int(x)][0])
    out["opening_plan_language"] = out.opening_plan_code.map(lambda x: plan_codes()[int(x)][1])
    out["window_label"] = np.where(
        out.opportunity_start.lt(pd.Timestamp(cal.analytical_start)),
        "BASELINE_90", "FINAL_90")
    # A continuation inside the same session is kept as an observable attribute
    # of the positive outcome; it does not change the outcome state itself.
    out["same_session"] = out.continued & out.next_session_id.eq(out.session_id)
    return out
