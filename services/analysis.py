
import pandas as pd


def analyze_data(data):
    """Validate a dataset and calculate Pearson correlations."""
    if data is None or data.empty:
        raise ValueError("The dataset is empty.")

    numeric_data = data.select_dtypes(include="number").copy()

    if numeric_data.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")

    # Remove columns with no useful numeric values.
    numeric_data = numeric_data.dropna(axis=1, how="all")

    if numeric_data.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")

    # Replace infinite values and remove rows containing missing values.
    numeric_data = numeric_data.replace(
        [float("inf"), float("-inf")], float("nan")
    ).dropna()

    if len(numeric_data) < 2:
        raise ValueError("At least two complete rows are required.")

    if numeric_data.shape[1] < 2:
        raise ValueError("At least two numeric columns are required.")

    correlation = numeric_data.corr(method="pearson")

    return {
        "data": numeric_data,
        "correlation": correlation
    }
