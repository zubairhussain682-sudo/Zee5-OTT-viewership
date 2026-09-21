"""Reconstruct return behaviour from raw playback and separate resume from replay.

Inputs are analyst-facing exports of view_events, viewing_sessions,
content_catalogue and profile_viewership_window. Assets are anchored at their
first qualified start and kept for analytically eligible profile-windows, the
population used by the published evidence. The script writes three compact
evidence files:
return_decomposition.csv, resume_playback_continuity.csv and
return_semantic_closure.csv.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

OBSERVATION_START = pd.Timestamp("2025-09-01")
FINAL_WINDOW_START = pd.Timestamp("2025-11-30")
OBSERVATION_END_EXCLUSIVE = pd.Timestamp("2026-02-28")
OBSERVATION_LAST_DAY = OBSERVATION_END_EXCLUSIVE - pd.Timedelta(days=1)
COMPLETION = 0.90
ABANDONMENT_HORIZON = pd.Timedelta(days=14)
REWATCH_DELAY = pd.Timedelta(hours=12)


def read_inputs(events_path: Path, sessions_path: Path, catalogue_path: Path) -> pd.DataFrame:
    ev = pd.read_csv(events_path, parse_dates=["event_start_ts", "event_end_ts"])
    sessions = pd.read_csv(sessions_path, usecols=["session_id", "profile_id"])
    catalogue = pd.read_csv(
        catalogue_path,
        usecols=["content_id", "runtime_minutes", "parent_title_id", "program_type"],
    )
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


def build_asset_spine(ev: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    completed = anchored.loc[anchored["progress"].ge(COMPLETION)].copy()
    first_completion = (
        completed.sort_values(["event_end_ts", "view_event_id"])
        .drop_duplicates(["profile_id", "content_id"])
        [["profile_id", "content_id", "event_end_ts"]]
        .rename(columns={"event_end_ts": "first_completion_ts"})
    )
    assets = first_q.merge(first_completion, on=["profile_id", "content_id"], how="left", validate="one_to_one")
    last_event = (
        anchored.groupby(["profile_id", "content_id"], as_index=False)["event_start_ts"]
        .max()
        .rename(columns={"event_start_ts": "last_event_start_ts"})
    )
    assets = assets.merge(last_event, on=["profile_id", "content_id"], validate="one_to_one")
    return assets, anchored


def eligible_profile_windows(pvw_path: Path) -> pd.DataFrame:
    pvw = pd.read_csv(pvw_path, usecols=["profile_id", "window_label", "is_main_analytical_eligible"])
    return pvw.loc[pvw["is_main_analytical_eligible"].eq(1), ["profile_id", "window_label"]]


def cross_session_returns(assets: pd.DataFrame, anchored: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = anchored.sort_values(["profile_id", "content_id", "event_start_ts", "view_event_id"]).copy()
    ordered["previous_session_id"] = ordered.groupby(["profile_id", "content_id"])["session_id"].shift()
    ordered["is_cross_session_return"] = ordered["previous_session_id"].notna() & ordered["session_id"].ne(ordered["previous_session_id"])
    returns = ordered.loc[ordered["is_cross_session_return"]].copy()
    returns = returns.merge(
        assets[["profile_id", "content_id", "first_completion_ts"]],
        on=["profile_id", "content_id"],
        validate="many_to_one",
    )
    returns["is_pre_completion_return"] = returns["first_completion_ts"].isna() | returns["event_start_ts"].lt(returns["first_completion_ts"])
    returns["is_post_completion_return"] = returns["first_completion_ts"].notna() & returns["event_start_ts"].ge(returns["first_completion_ts"])

    strict = anchored.merge(
        assets[["profile_id", "content_id", "first_completion_ts"]],
        on=["profile_id", "content_id"],
        validate="many_to_one",
    )
    strict["is_strict_rewatch"] = (
        strict["is_qualified_start"]
        & strict["first_completion_ts"].notna()
        & strict["event_start_ts"].ge(strict["first_completion_ts"] + REWATCH_DELAY)
    )
    strict_assets = (
        strict.loc[strict["is_strict_rewatch"], ["profile_id", "content_id"]]
        .drop_duplicates()
        .assign(strict_rewatch=1)
    )
    assets = assets.merge(strict_assets, on=["profile_id", "content_id"], how="left")
    assets["strict_rewatch"] = assets["strict_rewatch"].fillna(0).astype(int)
    return returns, assets


def return_decomposition(returns: pd.DataFrame, assets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for window, a in assets.groupby("window_label"):
        r = returns.loc[returns["window_label"].eq(window)]
        cross_assets = r[["profile_id", "content_id"]].drop_duplicates()
        pre_assets = r.loc[r["is_pre_completion_return"], ["profile_id", "content_id"]].drop_duplicates()
        post_assets = r.loc[r["is_post_completion_return"], ["profile_id", "content_id"]].drop_duplicates()
        strict_assets = a.loc[a["strict_rewatch"].eq(1), ["profile_id", "content_id"]]
        both = pre_assets.merge(post_assets, on=["profile_id", "content_id"], how="inner")
        post_not_strict = post_assets.merge(strict_assets, on=["profile_id", "content_id"], how="left", indicator=True)
        rows.append({
            "window_label": window,
            "anchored_qualified_assets": len(a),
            "assets_with_cross_session_return": len(cross_assets),
            "assets_with_pre_completion_return": len(pre_assets),
            "assets_with_post_completion_return": len(post_assets),
            "assets_with_strict_rewatch": len(strict_assets),
            "assets_with_both_pre_and_post_return": len(both),
            "post_completion_return_not_strict_rewatch": int(post_not_strict["_merge"].eq("left_only").sum()),
            "pre_share_of_cross_session_return_assets": len(pre_assets) / len(cross_assets) if len(cross_assets) else np.nan,
            "post_share_of_cross_session_return_assets": len(post_assets) / len(cross_assets) if len(cross_assets) else np.nan,
            "strict_rewatch_share_of_post_return_assets": len(strict_assets) / len(post_assets) if len(post_assets) else np.nan,
        })
    out = pd.DataFrame(rows)
    share_cols = [c for c in out.columns if "_share_" in c]
    out[share_cols] = out[share_cols].round(4)
    return out


def playback_continuity(returns: pd.DataFrame, anchored: pd.DataFrame) -> pd.DataFrame:
    ordered = anchored.sort_values(["profile_id", "content_id", "event_start_ts", "view_event_id"]).copy()
    ordered["previous_end_position"] = ordered.groupby(["profile_id", "content_id"])["playback_end_position"].shift()
    pre = returns.loc[returns["is_pre_completion_return"]].copy()
    pre = pre.merge(
        ordered[["view_event_id", "previous_end_position"]],
        on="view_event_id",
        how="left",
        validate="one_to_one",
    )
    pre["signed_restart_gap_sec"] = pre["playback_start_position"].astype(float) - pre["previous_end_position"].astype(float)
    pre["abs_restart_gap_sec"] = pre["signed_restart_gap_sec"].abs()
    pre["runtime_seconds"] = pre["runtime_minutes"].astype(float) * 60.0
    pre["abs_gap_share_runtime"] = pre["abs_restart_gap_sec"] / pre["runtime_seconds"]

    rows = []
    for window, g in pre.groupby("window_label"):
        positioned = g.dropna(subset=["previous_end_position", "playback_start_position"]).copy()
        signed = positioned["signed_restart_gap_sec"]
        absolute = positioned["abs_restart_gap_sec"]
        rows.append({
            "window_label": window,
            "pre_completion_return_sessions": len(g),
            "assets_with_pre_completion_return": g[["profile_id", "content_id"]].drop_duplicates().shape[0],
            "missing_position_pairs": int(g["previous_end_position"].isna().sum()),
            "positioned_return_sessions": len(positioned),
            "avg_signed_restart_gap_sec": signed.mean(),
            "p10_signed_gap_sec": signed.quantile(0.10),
            "p25_signed_gap_sec": signed.quantile(0.25),
            "median_signed_gap_sec": signed.median(),
            "p75_signed_gap_sec": signed.quantile(0.75),
            "p90_signed_gap_sec": signed.quantile(0.90),
            "median_abs_gap_sec": absolute.median(),
            "p75_abs_gap_sec": absolute.quantile(0.75),
            "p90_abs_gap_sec": absolute.quantile(0.90),
            "avg_abs_gap_share_of_runtime": positioned["abs_gap_share_runtime"].mean(),
            "share_backtracking": signed.lt(0).mean(),
            "share_exact_same_position": signed.eq(0).mean(),
            "share_forward_jump": signed.gt(0).mean(),
            "share_restart_from_beginning": positioned["playback_start_position"].eq(0).mean(),
        })
    return pd.DataFrame(rows)


def semantic_closure(assets: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    pre_assets = (
        returns.loc[returns["is_pre_completion_return"], ["profile_id", "content_id"]]
        .drop_duplicates()
        .assign(has_pre_completion_resume=1)
    )
    x = assets.merge(pre_assets, on=["profile_id", "content_id"], how="left")
    x["has_pre_completion_resume"] = x["has_pre_completion_resume"].fillna(0).astype(int)
    last_day = x["last_event_start_ts"].dt.normalize()
    full_horizon = last_day.add(ABANDONMENT_HORIZON).le(OBSERVATION_LAST_DAY)
    x["canonical_outcome"] = np.select(
        [x["first_completion_ts"].notna(), full_horizon],
        ["COMPLETED", "ABANDONED"],
        default="CENSORED",
    )
    grid = pd.MultiIndex.from_product(
        [sorted(x["window_label"].unique()), [0, 1], ["ABANDONED", "CENSORED", "COMPLETED"]],
        names=["window_label", "has_pre_completion_resume", "canonical_outcome"],
    )
    out = (
        x.groupby(["window_label", "has_pre_completion_resume", "canonical_outcome"])
        .size()
        .reindex(grid, fill_value=0)
        .rename("asset_count")
        .reset_index()
    )
    out["share_within_resume_status"] = out["asset_count"] / out.groupby(
        ["window_label", "has_pre_completion_resume"]
    )["asset_count"].transform("sum")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--sessions", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--profile-viewership", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ev = read_inputs(args.events, args.sessions, args.catalogue)
    assets, anchored = build_asset_spine(ev)
    eligible = eligible_profile_windows(args.profile_viewership)
    assets = assets.merge(eligible, on=["profile_id", "window_label"], validate="many_to_one")
    anchored = anchored.merge(eligible, on=["profile_id", "window_label"], validate="many_to_one")
    returns, assets = cross_session_returns(assets, anchored)

    return_decomposition(returns, assets).to_csv(args.output_dir / "return_decomposition.csv", index=False)
    playback_continuity(returns, anchored).to_csv(args.output_dir / "resume_playback_continuity.csv", index=False)
    semantic_closure(assets, returns).to_csv(args.output_dir / "return_semantic_closure.csv", index=False)


if __name__ == "__main__":
    main()
