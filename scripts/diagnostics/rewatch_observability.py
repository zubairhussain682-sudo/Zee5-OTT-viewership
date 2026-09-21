"""Build fixed-horizon rewatch evidence and a profile-level 14-day replay sidecar.

Inputs are analyst-facing exports of view_events, viewing_sessions,
content_catalogue and profile_viewership_window. Completed assets are kept for
analytically eligible profile-windows, the population used by the published
evidence. Outputs reproduce the evidence needed to choose a fixed replay horizon
and to carry measurement depth beside the profile-level rate.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

OBSERVATION_START = pd.Timestamp("2025-09-01")
FINAL_WINDOW_START = pd.Timestamp("2025-11-30")
OBSERVATION_END_EXCLUSIVE = pd.Timestamp("2026-02-28")
COMPLETION = 0.90
REWATCH_DELAY = pd.Timedelta(hours=12)
HORIZONS = (1, 3, 7, 14, 30, 60)


def build_event_frame(events_path: Path, sessions_path: Path, catalogue_path: Path) -> pd.DataFrame:
    ev = pd.read_csv(events_path, parse_dates=["event_start_ts", "event_end_ts"])
    sessions = pd.read_csv(sessions_path, usecols=["session_id", "profile_id"])
    catalogue = pd.read_csv(catalogue_path, usecols=["content_id", "runtime_minutes"])
    ev = ev.merge(sessions, on="session_id", validate="many_to_one")
    ev = ev.merge(catalogue, on="content_id", validate="many_to_one")
    runtime_seconds = ev["runtime_minutes"].astype(float) * 60.0
    threshold = np.where(
        ev["is_autoplay"].astype(bool),
        np.minimum(480.0, 0.20 * runtime_seconds),
        np.minimum(300.0, 0.10 * runtime_seconds),
    )
    ev["is_qualified_start"] = ev["watch_seconds"].astype(float).ge(threshold)
    ev["progress"] = np.minimum(ev["playback_end_position"].astype(float) / runtime_seconds, 1.0)
    return ev.sort_values(["profile_id", "content_id", "event_start_ts", "view_event_id"]).reset_index(drop=True)


def completed_asset_spine(ev: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    q = ev.loc[ev["is_qualified_start"]].copy()
    first_q = (
        q.sort_values(["event_start_ts", "view_event_id"])
        .drop_duplicates(["profile_id", "content_id"])
        [["profile_id", "content_id", "event_start_ts"]]
        .rename(columns={"event_start_ts": "first_qualified_start_ts"})
    )
    first_q = first_q.loc[
        first_q["first_qualified_start_ts"].ge(OBSERVATION_START)
        & first_q["first_qualified_start_ts"].lt(OBSERVATION_END_EXCLUSIVE)
    ].copy()
    first_q["window_label"] = np.where(
        first_q["first_qualified_start_ts"].lt(FINAL_WINDOW_START),
        "BASELINE_90",
        "FINAL_90",
    )
    anchored = ev.merge(first_q, on=["profile_id", "content_id"], how="inner", validate="many_to_one")
    anchored = anchored.loc[anchored["event_start_ts"].ge(anchored["first_qualified_start_ts"])].copy()

    completed_events = anchored.loc[anchored["progress"].ge(COMPLETION)].copy()
    completed = (
        completed_events.sort_values(["event_end_ts", "view_event_id"])
        .drop_duplicates(["profile_id", "content_id"])
        [["profile_id", "content_id", "event_end_ts"]]
        .rename(columns={"event_end_ts": "first_completion_ts"})
        .merge(first_q, on=["profile_id", "content_id"], validate="one_to_one")
    )

    qualified_after_completion = anchored.loc[anchored["is_qualified_start"]].merge(
        completed[["profile_id", "content_id", "first_completion_ts"]],
        on=["profile_id", "content_id"],
        validate="many_to_one",
    )
    qualified_after_completion = qualified_after_completion.loc[
        qualified_after_completion["event_start_ts"].ge(
            qualified_after_completion["first_completion_ts"] + REWATCH_DELAY
        )
    ].copy()
    first_rewatch = (
        qualified_after_completion.sort_values(["event_start_ts", "view_event_id"])
        .drop_duplicates(["profile_id", "content_id"])
        [["profile_id", "content_id", "event_start_ts"]]
        .rename(columns={"event_start_ts": "first_rewatch_ts"})
    )
    completed = completed.merge(first_rewatch, on=["profile_id", "content_id"], how="left", validate="one_to_one")
    completed["available_followup_days"] = (
        OBSERVATION_END_EXCLUSIVE - completed["first_completion_ts"]
    ).dt.total_seconds() / 86400.0
    completed["first_rewatch_days"] = (
        completed["first_rewatch_ts"] - completed["first_completion_ts"]
    ).dt.total_seconds() / 86400.0
    return completed, qualified_after_completion


def horizon_summary(completed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for window, g in completed.groupby("window_label"):
        for horizon in HORIZONS:
            positive = g["first_rewatch_days"].notna() & g["first_rewatch_days"].le(horizon)
            observed_negative = g["available_followup_days"].ge(horizon) & ~positive
            censored = ~(positive | observed_negative)
            known = positive | observed_negative
            rows.append({
                "window_label": window,
                "horizon_days": horizon,
                "completed_assets": len(g),
                "positive_rewatched_assets": int(positive.sum()),
                "observed_negative_assets": int(observed_negative.sum()),
                "censored_assets": int(censored.sum()),
                "known_outcome_denominator": int(known.sum()),
                "rewatch_rate_known_outcomes": positive.sum() / known.sum() if known.sum() else np.nan,
            })
    return pd.DataFrame(rows)


def latency_summary(completed: pd.DataFrame, qualified_after_completion: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for window, g in completed.groupby("window_label"):
        eventual = g.loc[g["first_rewatch_days"].notna(), "first_rewatch_days"]
        q = qualified_after_completion.merge(
            g[["profile_id", "content_id"]], on=["profile_id", "content_id"], how="inner"
        )
        rows.append({
            "window_label": window,
            "completed_assets": len(g),
            "rewatched_assets": int(g["first_rewatch_ts"].notna().sum()),
            "total_rewatch_starts": len(q),
            "naive_rewatched_asset_share": g["first_rewatch_ts"].notna().mean(),
            "p10_first_rewatch_days": eventual.quantile(0.10),
            "p25_first_rewatch_days": eventual.quantile(0.25),
            "median_first_rewatch_days": eventual.median(),
            "p75_first_rewatch_days": eventual.quantile(0.75),
            "p90_first_rewatch_days": eventual.quantile(0.90),
            "p95_first_rewatch_days": eventual.quantile(0.95),
            **{f"share_first_rewatch_within_{h}d": eventual.le(h).mean() for h in HORIZONS},
            "p10_available_followup_days": g["available_followup_days"].quantile(0.10),
            "p25_available_followup_days": g["available_followup_days"].quantile(0.25),
            "median_available_followup_days": g["available_followup_days"].median(),
            "p75_available_followup_days": g["available_followup_days"].quantile(0.75),
            "p90_available_followup_days": g["available_followup_days"].quantile(0.90),
            **{f"share_completed_with_{h}d_followup": g["available_followup_days"].ge(h).mean() for h in HORIZONS},
        })
    return pd.DataFrame(rows)


def profile_rewatch14(completed: pd.DataFrame, pvw_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    horizon = 14
    x = completed.copy()
    x["rewatched_within_14d"] = (
        x["first_rewatch_days"].notna() & x["first_rewatch_days"].le(horizon)
    ).astype(int)
    x["observed_nonrewatched_14d"] = (
        x["available_followup_days"].ge(horizon) & x["rewatched_within_14d"].eq(0)
    ).astype(int)
    x["censored_rewatch_14d"] = (
        x["rewatched_within_14d"].eq(0) & x["observed_nonrewatched_14d"].eq(0)
    ).astype(int)
    profile = (
        x.groupby(["profile_id", "window_label"], as_index=False)
        .agg(
            completed_assets=("content_id", "size"),
            rewatched_within_14d=("rewatched_within_14d", "sum"),
            observed_nonrewatched_14d=("observed_nonrewatched_14d", "sum"),
            censored_rewatch_14d=("censored_rewatch_14d", "sum"),
        )
    )
    profile["rewatch_14d_known_denominator"] = (
        profile["rewatched_within_14d"] + profile["observed_nonrewatched_14d"]
    )
    profile["rewatch_14d_rate"] = profile["rewatched_within_14d"] / profile[
        "rewatch_14d_known_denominator"
    ].replace(0, np.nan)

    pvw = pd.read_csv(
        pvw_path,
        usecols=["profile_id", "window_label", "is_main_analytical_eligible"],
    )
    eligible = pvw.loc[pvw["is_main_analytical_eligible"].eq(1), ["profile_id", "window_label"]]
    profile = eligible.merge(profile, on=["profile_id", "window_label"], how="left", validate="one_to_one")
    for col in [
        "completed_assets",
        "rewatched_within_14d",
        "observed_nonrewatched_14d",
        "censored_rewatch_14d",
        "rewatch_14d_known_denominator",
    ]:
        profile[col] = profile[col].fillna(0).astype(int)

    coverage_rows = []
    for window, g in profile.groupby("window_label"):
        denom = g["rewatch_14d_known_denominator"]
        row = {
            "window_label": window,
            "eligible_profiles": len(g),
            "profiles_denom_ge_1": int(denom.ge(1).sum()),
            "share_profiles_denom_ge_1": denom.ge(1).mean(),
            "profiles_denom_ge_3": int(denom.ge(3).sum()),
            "share_profiles_denom_ge_3": denom.ge(3).mean(),
            "profiles_denom_ge_5": int(denom.ge(5).sum()),
            "share_profiles_denom_ge_5": denom.ge(5).mean(),
            "profiles_denom_ge_10": int(denom.ge(10).sum()),
            "share_profiles_denom_ge_10": denom.ge(10).mean(),
            "median_known_denominator": denom.median(),
            "p25_known_denominator": denom.quantile(0.25),
            "p75_known_denominator": denom.quantile(0.75),
            "p90_known_denominator": denom.quantile(0.90),
        }
        for threshold in (1, 3, 5):
            r = g.loc[denom.ge(threshold), "rewatch_14d_rate"]
            row[f"mean_rewatch_14d_rate_denom_ge_{threshold}"] = r.mean()
            row[f"median_rewatch_14d_rate_denom_ge_{threshold}"] = r.median()
        row["share_profiles_denom_eq_0"] = denom.eq(0).mean()
        coverage_rows.append(row)
    return profile, pd.DataFrame(coverage_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--sessions", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--profile-viewership", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ev = build_event_frame(args.events, args.sessions, args.catalogue)
    completed, q_after = completed_asset_spine(ev)
    pvw = pd.read_csv(args.profile_viewership, usecols=["profile_id", "window_label", "is_main_analytical_eligible"])
    eligible = pvw.loc[pvw["is_main_analytical_eligible"].eq(1), ["profile_id", "window_label"]]
    completed = completed.merge(eligible, on=["profile_id", "window_label"], validate="many_to_one")
    q_after = q_after.merge(eligible, on=["profile_id", "window_label"], validate="many_to_one")
    horizon_summary(completed).to_csv(args.output_dir / "rewatch_horizon_summary.csv", index=False)
    latency_summary(completed, q_after).to_csv(args.output_dir / "rewatch_latency_observability.csv", index=False)
    profile, coverage = profile_rewatch14(completed, args.profile_viewership)
    profile.to_csv(args.output_dir / "audit_profile_rewatch14.csv", index=False)
    coverage.to_csv(args.output_dir / "rewatch_profile_coverage.csv", index=False)


if __name__ == "__main__":
    main()
