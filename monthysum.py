def get_monthly_expenses(cursor, logged_in_email):
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        WHERE user_email=?
        GROUP BY month
        ORDER BY month
    """, (logged_in_email,))
    return cursor.fetchall()


def get_total_spent_this_month(cursor, logged_in_email):
    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_email=?
          AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """, (logged_in_email,))
    result = cursor.fetchone()
    return result[0] if result[0] else 0


def get_user_owed_amount(cursor, logged_in_email):
    cursor.execute("""
        SELECT SUM(amount_owed)
        FROM balances
        WHERE user_email=? AND amount_owed > 0
    """, (logged_in_email,))
    result = cursor.fetchone()
    return result[0] if result[0] else 0


def get_group_expense_breakdown(cursor, logged_in_email):
    cursor.execute("""
        SELECT g.group_name, SUM(e.amount)
        FROM expenses e
        JOIN groups g ON e.group_id = g.id
        WHERE e.user_email=?
        GROUP BY g.group_name
    """, (logged_in_email,))
    return cursor.fetchall()
