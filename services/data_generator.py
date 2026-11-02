
import numpy as np
import pandas as pd


def generate_data(rows=100, seed=None):
    """Generate realistic-looking synthetic student data."""
    rows = int(rows)

    if not 20 <= rows <= 1000:
        raise ValueError("Rows must be between 20 and 1000.")

    rng = np.random.default_rng(seed)

    study_hours = rng.uniform(1, 10, rows)
    sleep_hours = rng.uniform(4, 10, rows)
    screen_time = rng.uniform(1, 9, rows)
    attendance = rng.uniform(50, 100, rows)

    marks = (
        12
        + 6.5 * study_hours
        + 0.18 * attendance
        + 1.5 * sleep_hours
        - 0.7 * screen_time
        + rng.normal(0, 7, rows)
    )

    marks = np.clip(marks, 0, 100)

    return pd.DataFrame({
        "Study_Hours": study_hours.round(2),
        "Sleep_Hours": sleep_hours.round(2),
        "Screen_Time": screen_time.round(2),
        "Attendance": attendance.round(2),
        "Marks": marks.round(2)
    })
