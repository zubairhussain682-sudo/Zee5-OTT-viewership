"""Independent checks on continuation opportunities and their mart projections.

canonical_checks tests each opportunity against source tables: ordering, reachability,
access at opening, a single outcome state, full follow-up for negatives and attribution
of positives to real qualifying events. mart_checks tests that the title and profile
marts reproduce those opportunities exactly. Each returns violation counts; zero is
required. Both need prepared full-resolution source and mart frames.
"""
import numpy as np
import pandas as pd

from src.analytical_transforms.access import profile_access_day_matrix, plan_codes
from src.analytical_transforms.qualification import COMPLETION, qualified_start


def canonical_checks(c, ev, d, cal):
    required = ["opportunity_key", "current_content_id", "next_content_id",
                "opportunity_start", "opportunity_end", "progression_ts",
                "continuous_end_exclusive", "continued", "censored", "observed_negative"]
    absent = set(required) - set(c.columns)
    if absent:
        raise ValueError(f"Canonical continuation metadata missing: {sorted(absent)}")
    out = {}

    def check(key, bad):
        out["C" + key] = int(np.asarray(bad).sum())

    cat = d["catalogue"].set_index("content_id")
    profiles = d["profiles"].set_index("profile_id")
    check("A_unique_opportunity",
          c.duplicated(["profile_id", "current_content_id", "next_content_id"]))
    check("B_same_parent",
          c.current_content_id.map(cat.parent_title_id).ne(c.parent_title_id)
          | c.next_content_id.map(cat.parent_title_id).ne(c.parent_title_id))
    ep = cat.reset_index().query("content_type == 'EPISODE'").sort_values(
        ["parent_title_id", "season_number", "episode_number"])
    ep["expected_next"] = ep.groupby("parent_title_id").content_id.shift(-1)
    next_map = ep.set_index("content_id").expected_next
    check("C_next_order", c.current_content_id.map(next_map).ne(c.next_content_id))

    q = qualified_start(ev, ev.runtime_minutes * 60)
    first = ev.loc[q & ev.content_type.eq("EPISODE") & ev.progress.ge(COMPLETION)].groupby(
        ["profile_id", "content_id"]).event_end_ts.min()
    actual = pd.MultiIndex.from_frame(c[["profile_id", "current_content_id"]])
    anchors = first.reindex(actual).to_numpy()
    check("D_earliest_progression",
          (c.progression_ts.to_numpy() != anchors)
          | c.opportunity_start.lt(c.progression_ts).to_numpy())

    begin = pd.concat([c.next_content_id.map(cat.release_date),
                       c.next_content_id.map(cat.catalogue_entry_date)], axis=1).max(axis=1)
    exit_ts = c.next_content_id.map(cat.catalogue_exit_date) + pd.Timedelta(days=1)
    check("E_asset_available",
          c.opportunity_start.lt(begin)
          | (exit_ts.notna() & c.opportunity_start.ge(exit_ts)))
    check("F_profile_exists",
          c.opportunity_start.lt(c.profile_id.map(profiles.profile_created_date))
          | c.account_id.ne(c.profile_id.map(profiles.account_id)))

    # Resolve opening directly against dated cycles; missing and multiple matches fail.
    cycles = d["cycles"].copy()
    cycles["cycle_start_date"] = pd.to_datetime(cycles.cycle_start_date)
    cycles["cycle_end_exclusive"] = pd.to_datetime(cycles.cycle_end_date) + pd.Timedelta(days=1)
    j = c[["opportunity_key", "account_id", "parent_title_id", "opportunity_start"]].merge(
        cycles, on="account_id")
    j = j.loc[j.opportunity_start.ge(j.cycle_start_date)
              & j.opportunity_start.lt(j.cycle_end_exclusive)]
    multiplicity = j.groupby("opportunity_key").size().reindex(c.opportunity_key, fill_value=0)
    check("G_opening_access", multiplicity.ne(1))
    audio = set(map(tuple, d["audio"][["parent_title_id", "language"]].to_numpy()))
    regional = j.plan_family.eq("REGIONAL")
    check("H_regional_access",
          [r and (p, l) not in audio
           for r, p, l in zip(regional, j.parent_title_id, j.plan_language_group)])

    check("I_positive_not_censored", c.continued & c.censored)
    check("J_positive_not_negative", c.continued & c.observed_negative)
    check("K_censored_not_negative", c.censored & c.observed_negative)
    check("L_exactly_one_state",
          c[["continued", "censored", "observed_negative"]].astype(int).sum(axis=1).ne(1))

    # Independently establish continuous coverage by checking all calendar states
    # touched by the intended horizon; compare with retained end evidence.
    ids, has, codes = profile_access_day_matrix(d["profiles"], d["cycles"], cal)
    ip = ids.get_indexer(c.profile_id)
    day0 = pd.Timestamp(cal.start)
    full = np.ones(len(c), dtype=bool)
    expected_end = np.full(len(c), np.datetime64(pd.Timestamp(cal.end) + pd.Timedelta(days=1)),
                           dtype="datetime64[ns]")
    # Inspect the opening day and the next seven days. A horizon ending at
    # midnight requires coverage up to, but not beyond, that boundary.
    for offset in range(8):
        t = c.opportunity_start.dt.normalize() + pd.Timedelta(days=offset)
        relevant = t.lt(c.opportunity_end).to_numpy()
        di = (t - day0).dt.days.to_numpy()
        inside = (di >= 0) & (di < cal.n_days)
        safe = np.clip(di, 0, cal.n_days - 1)
        pc = codes[ip, safe]
        ok = inside & has[ip, safe] & (pc >= 0)
        for code, (fam, lang) in enumerate(plan_codes()):
            if fam == "REGIONAL":
                allowed = c.parent_title_id.isin(
                    d["audio"].loc[d["audio"].language.eq(lang), "parent_title_id"]).to_numpy()
                ok &= (pc != code) | allowed
        ok &= (exit_ts.isna() | t.lt(exit_ts)).to_numpy()
        failed = relevant & ~ok
        full &= ~failed
        expected_end = np.minimum(
            expected_end, np.where(failed, t.to_numpy(), np.datetime64('2262-01-01')))
    check("N_negative_full_followup", c.observed_negative & ~full)
    check("N2_horizon_evidence", c.full_horizon_observed.to_numpy() != full)

    # Actual matching qualified events, not the canonical positive label, are evidence.
    ne = ev.loc[q, ["profile_id", "content_id", "event_start_ts", "view_event_id", "session_id",
                    "is_autoplay", "audio_language", "device_type"]].rename(columns={
                        "content_id": "next_content_id", "event_start_ts": "positive_ts"})
    m = c[["opportunity_key", "profile_id", "next_content_id",
           "opportunity_start", "opportunity_end"]].merge(
        ne, on=["profile_id", "next_content_id"])
    ends = pd.Series(expected_end, index=c.opportunity_key)
    m = m.loc[m.positive_ts.ge(m.opportunity_start)
              & m.positive_ts.le(m.opportunity_end)
              & m.positive_ts.lt(m.opportunity_key.map(ends))]
    m = (m.sort_values(["positive_ts", "view_event_id"])
         .drop_duplicates("opportunity_key")
         .set_index("opportunity_key"))
    positive = c.opportunity_key.isin(m.index)
    check("M_positive_horizon_and_attribution",
          c.continued.ne(positive)
          | (positive & c.next_view_event_id.ne(c.opportunity_key.map(m.view_event_id))))
    for field in ["session_id", "is_autoplay", "audio_language", "device_type"]:
        check("M_" + field, positive & c["next_" + field].ne(c.opportunity_key.map(m[field])))
    check("O_censored_contains_no_positive", c.censored & positive)
    check("P_no_fanout", c.opportunity_key.duplicated())
    check("P2_window_ownership", c.window_label.ne(np.where(
        c.opportunity_start.lt(pd.Timestamp(cal.analytical_start)), "BASELINE_90", "FINAL_90")))
    return out


def mart_checks(c, marts):
    out = {}
    spec = {"continuation_opportunities": ("continued", "size"),
            "continued_opportunities": ("continued", "sum"),
            "censored_continuation_opportunities": ("censored", "sum")}
    for name, keys in [("profile_title_window", ["profile_id", "parent_title_id", "window_label"]),
                       ("profile_viewership_window", ["profile_id", "window_label"])]:
        table = marts[name]
        prefix = "CT_" if name == "profile_title_window" else "CV_"
        out[prefix + "grain"] = int(table.duplicated(keys).sum())
        expected = c.groupby(keys).agg(**spec)
        actual = table.set_index(keys)
        missing = expected.index.difference(actual.index)
        out[prefix + "opportunity_coverage"] = len(missing)
        joined = actual.join(expected, rsuffix="_canonical")
        for col in spec:
            out[prefix + col] = (
                int(joined[col].ne(joined[col + "_canonical"].fillna(0)).sum()) + len(missing))
        out[prefix + "exclusive_counts"] = int((
            table.continued_opportunities + table.censored_continuation_opportunities
            > table.continuation_opportunities).sum())
        if name == "profile_viewership_window":
            observed = table.continuation_opportunities - table.censored_continuation_opportunities
            out[prefix + "observed_denominator"] = int(
                table.observed_continuation_opportunities.ne(observed).sum())
            out[prefix + "observed_positive"] = int(
                table.observed_continued.ne(table.continued_opportunities).sum())
            rate = table.continued_opportunities / observed.replace(0, np.nan)
            out[prefix + "pooled_rate"] = int((~np.isclose(
                table.continuation_rate, rate, rtol=1e-14, atol=0, equal_nan=True)).sum())
            out[prefix + "validity"] = int(
                table.continuation_rate_is_valid.ne(observed.gt(0)).sum())
        else:
            out[prefix + "meaningful_title"] = int(
                table.is_meaningful_title.ne(table.qualified_starts.gt(0)).sum())
            only = table.events.eq(0)
            out[prefix + "opportunity_only_behaviour"] = int((only & (
                table.watch_minutes.ne(0) | table.qualified_watch_minutes.ne(0)
                | table.qualified_starts.ne(0) | table.is_meaningful_title)).sum())
    return out
