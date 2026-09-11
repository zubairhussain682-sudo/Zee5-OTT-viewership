"""Shared event qualification and progression thresholds."""
import numpy as np

COMPLETION = 0.90


def qualified_start(events, runtime_seconds):
    manual = np.minimum(300.0, 0.10 * runtime_seconds)
    autoplay = np.minimum(480.0, 0.20 * runtime_seconds)
    return events["watch_seconds"] >= np.where(
        events["is_autoplay"].astype(bool), autoplay, manual)
