import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).parent / "DATA"
DB_PATH = Path(__file__).parent / "spendshield.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def sync_transactions_to_database(df):
    with get_connection() as conn:
        df.to_sql("transactions", conn, if_exists="replace", index=False)


def get_transaction_count():
    with get_connection() as conn:
        result = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM transactions",
            conn,
        )
        return int(result["count"].iloc[0])


def run_sql_query(query):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def clean_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df


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
    df["category"] = df["category"].fillna("").astype(str).str.strip()

    df["category"] = df.apply(
        lambda row: categorize_transaction(row["description"])
        if row["category"] == ""
        else row["category"],
        axis=1,
    )

    return df


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

    if debit_df.empty:
        return alerts

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


st.set_page_config(page_title="SpendShield AI", layout="wide")

st.title("SpendShield AI")
st.caption("Personal finance fraud and expense intelligence dashboard")

transactions_path = DATA_DIR / "transactions.csv"

try:
    df = clean_columns(pd.read_csv(transactions_path))
except FileNotFoundError as error:
    st.error("transactions.csv not found. Check DATA folder.")
    st.code(str(error))
    st.stop()

required_columns = {
    "date",
    "description",
    "category",
    "type",
    "amount",
    "payment_method",
    "notes",
}

missing_columns = required_columns - set(df.columns)

if missing_columns:
    st.error(f"transactions.csv missing columns: {missing_columns}")
    st.write("Available columns:", list(df.columns))
    st.stop()

df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["type"] = df["type"].astype(str).str.strip().str.lower()
df["payment_method"] = df["payment_method"].fillna("Unknown")
df["notes"] = df["notes"].fillna("")
df = df.dropna(subset=["amount"])

df = fill_missing_categories(df)

category_options = ["All"] + sorted(df["category"].dropna().unique().tolist())
payment_options = ["All"] + sorted(df["payment_method"].dropna().unique().tolist())

with st.sidebar:
    st.header("Database")

    if st.button("Sync Transactions to Database"):
        try:
            sync_transactions_to_database(df)
            st.success("Transactions synced to SQLite database.")
        except Exception as error:
            st.error("Database sync failed.")
            st.code(str(error))

    try:
        transaction_count = get_transaction_count()
        st.write(f"Database Rows: {transaction_count}")
    except Exception:
        st.info("Click Sync Transactions to Database first.")

    st.header("Filters")
    selected_category = st.selectbox("Category", category_options)
    selected_payment = st.selectbox("Payment Method", payment_options)

filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

if selected_payment != "All":
    filtered_df = filtered_df[filtered_df["payment_method"] == selected_payment]

debit_df = filtered_df[filtered_df["type"] == "debit"]
credit_df = filtered_df[filtered_df["type"] == "credit"]

total_income = credit_df["amount"].sum()
total_spending = debit_df["amount"].sum()
balance = total_income - total_spending

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"Rs.{total_income:,.0f}")
col2.metric("Total Spending", f"Rs.{total_spending:,.0f}")
col3.metric("Balance", f"Rs.{balance:,.0f}")

st.divider()

st.subheader("Category-wise Spending")

category_summary = (
    debit_df.groupby("category", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

st.dataframe(category_summary, use_container_width=True)

if not category_summary.empty:
    st.bar_chart(category_summary.set_index("category")["amount"])

st.divider()

st.subheader("Payment Method Analysis")

payment_summary = (
    debit_df.groupby("payment_method", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

st.dataframe(payment_summary, use_container_width=True)

if not payment_summary.empty:
    st.bar_chart(payment_summary.set_index("payment_method")["amount"])

st.divider()

st.subheader("Top Expenses")

top_expenses = debit_df.sort_values("amount", ascending=False).head(5)
st.dataframe(top_expenses, use_container_width=True)

st.divider()

st.subheader("All Transactions")
st.dataframe(filtered_df, use_container_width=True)

st.divider()

st.subheader("Fraud and Expense Alerts")

alerts = []
alerts.extend(detect_duplicate_payments(filtered_df))
alerts.extend(detect_suspicious_transactions(filtered_df))
alerts.extend(detect_subscriptions(filtered_df))

if alerts:
    alerts_df = pd.DataFrame(alerts)
    st.dataframe(alerts_df, use_container_width=True)

    for alert in alerts:
        if alert["severity"] == "High":
            st.error(alert["message"])
        elif alert["severity"] == "Medium":
            st.warning(alert["message"])
        else:
            st.info(alert["message"])
else:
    st.success("No suspicious activity found.")

st.divider()

st.subheader("Saving Suggestions")

for suggestion in generate_saving_suggestions(category_summary):
    st.info(suggestion)

st.divider()

st.subheader("SQL Explorer")

sample_query = """
SELECT category, SUM(amount) AS total_amount
FROM transactions
WHERE type = 'debit'
GROUP BY category
ORDER BY total_amount DESC
"""

query = st.text_area("Write SQL Query", value=sample_query, height=130)

if st.button("Run SQL Query"):
    try:
        result_df = run_sql_query(query)
        st.dataframe(result_df, use_container_width=True)
    except Exception as error:
        st.error("SQL query failed. Sync transactions to database first.")
        st.code(str(error))