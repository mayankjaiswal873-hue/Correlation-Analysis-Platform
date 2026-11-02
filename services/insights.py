
def explain_correlation(value, first_name="Variable 1",
                        second_name="Variable 2"):
    """Explain the strength and direction of a correlation."""
    if value != value:  # NaN check
        return (
            f"Correlation between {first_name} and {second_name} "
            "cannot be calculated reliably."
        )

    if abs(value) >= 0.70:
        strength = "strong"
    elif abs(value) >= 0.40:
        strength = "moderate"
    elif abs(value) >= 0.20:
        strength = "weak"
    else:
        strength = "very weak or negligible"

    if value > 0:
        direction = "positive"
    elif value < 0:
        direction = "negative"
    else:
        direction = "no"

    return (
        f"{first_name} and {second_name} show a {strength} "
        f"{direction} linear relationship (r = {value:.2f}). "
        "Correlation describes association and does not prove causation."
    )


def generate_insights(correlation):
    """Create a list of notable relationships in a correlation matrix."""
    insights = []
    columns = list(correlation.columns)

    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            first = columns[i]
            second = columns[j]
            value = correlation.loc[first, second]

            if value == value:
                insights.append({
                    "first": first,
                    "second": second,
                    "value": round(float(value), 3),
                    "description": explain_correlation(
                        float(value), first, second
                    )
                })

    insights.sort(key=lambda item: abs(item["value"]), reverse=True)
    return insights
