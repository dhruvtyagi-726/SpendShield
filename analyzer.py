def get_debit_transactions(df):
    return df[df["type"] == "debit"]


def get_credit_transactions(df):
    return df[df["type"] == "credit"]


def calculate_kpis(df):
    debit_df = get_debit_transactions(df)
    credit_df = get_credit_transactions(df)

    total_income = credit_df["amount"].sum()
    total_spending = debit_df["amount"].sum()
    balance = total_income - total_spending

    return {
        "total_income": total_income,
        "total_spending": total_spending,
        "balance": balance,
    }


def get_category_summary(df):
    debit_df = get_debit_transactions(df)

    return (
        debit_df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )


def get_payment_summary(df):
    debit_df = get_debit_transactions(df)

    return (
        debit_df.groupby("payment_method", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )


def get_top_expenses(df, limit=5):
    debit_df = get_debit_transactions(df)

    return debit_df.sort_values("amount", ascending=False).head(limit)