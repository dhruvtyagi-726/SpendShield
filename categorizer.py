def categorize_transaction(description):
    text = str(description).lower()

    if "swiggy" in text or "zomato" in text or "restaurant" in text:
        return "Food"
    if "netflix" in text or "spotify" in text or "subscription" in text:
        return "Subscription"
    if "metro" in text or "uber" in text or "ola" in text:
        return "Travel"
    if "amazon" in text or "flipkart" in text or "shopping" in text:
        return "Shopping"
    if "bill" in text or "recharge" in text or "electricity" in text:
        return "Bills"
    if "college" in text or "fee" in text or "course" in text:
        return "Education"
    if "pharmacy" in text or "hospital" in text or "medicine" in text:
        return "Health"
    if "salary" in text or "credited" in text or "refund" in text:
        return "Income"

    return "Other"


def fill_missing_categories(df):
    df = df.copy()

    df["category"] = df.apply(
        lambda row: categorize_transaction(row["description"])
        if row["category"] == ""
        else row["category"],
        axis=1,
    )

    return df