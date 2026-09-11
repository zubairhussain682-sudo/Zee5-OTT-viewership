"""Transparent profile eligibility, applied to an existing measurement frame."""


def apply_eligibility(frame):
    """Return a copy with the existing opportunity/activity eligibility flags.

    Entitled days must already reflect profile existence and historical access.
    No rows are removed; an eligibility flag is not a segment assignment.
    """
    out = frame.copy()
    out["vod_entitled_days_in_window"] = out["entitled_days_in_window"].fillna(0)
    out["meets_entitled_days"] = out["vod_entitled_days_in_window"] >= 30
    out["meets_active_days"] = out["active_days"] >= 3
    out["meets_qualified_minutes"] = out["qualified_watch_minutes"] >= 120
    out["is_main_analytical_eligible"] = (
        out["meets_entitled_days"]
        & out["meets_active_days"]
        & out["meets_qualified_minutes"]
    )
    return out
