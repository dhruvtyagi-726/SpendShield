def detect_duplicate_payments(df):
    alerts = []
    seen = set()

    for _, row in df[df["type"] == "debit"].iterrows():
        key = (
            row["date"],
            str(row["description"]).lower(),
            float(row["amount"]),
            str(row["payment_method"]).lower(),
        )

        if key in seen:
            alerts.append(
                {
                    "alert_type": "Duplicate Payment",
                    "severity": "High",
                    "message": (
                        f"Duplicate payment found: {row['description']} "
                        f"Rs.{row['amount']} via {row['payment_method']} on {row['date']}"
                    ),
                }
            )

        seen.add(key)

    return alerts


def detect_suspicious_transactions(df):
    alerts = []
    debit_df = df[df["type"] == "debit"]

    average_spend = debit_df["amount"].mean()
    threshold = max(3000, average_spend * 2)

    for _, row in debit_df.iterrows():
        if row["amount"] >= threshold:
            alerts.append(
                {
                    "alert_type": "High Value Transaction",
                    "severity": "Medium",
                    "message": (
                        f"Review high-value transaction: {row['description']} "
                        f"Rs.{row['amount']} on {row['date']}"
                    ),
                }
            )

        if str(row["category"]).lower() == "other":
            alerts.append(
                {
                    "alert_type": "Unknown Category",
                    "severity": "Medium",
                    "message": (
                        f"Unknown category transaction: {row['description']} "
                        f"Rs.{row['amount']} on {row['date']}"
                    ),
                }
            )

    return alerts


def detect_subscriptions(df):
    alerts = []

    subscription_df = df[
        df["category"].astype(str).str.lower().str.contains("subscription", na=False)
    ]

    repeated = (
        subscription_df.groupby(["description", "amount"])
        .size()
        .reset_index(name="count")
    )

    for _, row in repeated.iterrows():
        if row["count"] >= 2:
            alerts.append(
                {
                    "alert_type": "Recurring Subscription",
                    "severity": "Low",
                    "message": (
                        f"Recurring subscription detected: "
                        f"{row['description']} Rs.{row['amount']}"
                    ),
                }
            )

    return alerts


def build_alerts(df):
    alerts = []
    alerts.extend(detect_duplicate_payments(df))
    alerts.extend(detect_suspicious_transactions(df))
    alerts.extend(detect_subscriptions(df))
    return alerts