def generate_saving_suggestions(category_summary):
    suggestions = []

    for _, row in category_summary.iterrows():
        category = str(row["category"]).lower()

        if category == "food" and row["amount"] > 500:
            suggestions.append("Food spending is high. Set a weekly food budget.")

        if category == "shopping" and row["amount"] > 1000:
            suggestions.append("Shopping expense is high. Review non-essential purchases.")

        if category == "subscription":
            suggestions.append("Review subscriptions and cancel unused services.")

    if not suggestions:
        suggestions.append("Spending pattern looks stable in current data.")

    return suggestions