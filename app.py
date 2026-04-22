from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB CONNECTION ----------------
def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- SESSION TIMEOUT ----------------
@app.before_request
def session_timeout():
    if "user" in session:
        now = datetime.now().timestamp()
        last_activity = session.get("last_activity", now)

        if now - last_activity > 300:
            session.clear()
            return redirect("/")

        session["last_activity"] = now

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db()
        result = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (user, pwd)
        ).fetchone()

        if result:
            session["user"] = user
            session["last_activity"] = datetime.now().timestamp()
            return redirect("/dashboard")
        else:
            return "❌ Invalid username or password"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    total_customers = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    deposits = db.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='deposit'"
    ).fetchone()[0] or 0

    withdraw = db.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='withdraw'"
    ).fetchone()[0] or 0

    balance = deposits - withdraw

    # ✅ FIXED SAFE COUNT
    result = db.execute("SELECT COUNT(*) FROM loans").fetchone()
    total_loans = result[0] if result and result[0] else 0

    total_loan_amount = db.execute(
        "SELECT SUM(loan_amount) FROM loans"
    ).fetchone()[0] or 0

    available_loan = balance - total_loan_amount

    service_collected = db.execute(
        "SELECT SUM(service_charge) FROM loans"
    ).fetchone()[0] or 0

    service_spent = db.execute(
        "SELECT SUM(amount) FROM service_expense"
    ).fetchone()[0] or 0

    service_balance = service_collected - service_spent

    return render_template(
        "dashboard.html",
        customers=total_customers,
        deposits=deposits,
        withdraw=withdraw,
        balance=balance,
        loans=total_loans,
        total_loan_amount=total_loan_amount,
        available_loan=available_loan,
        service_collected=service_collected,
        service_spent=service_spent,
        service_balance=service_balance
    )

# ---------------- CREATE ACCOUNT ----------------
@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    error = None

    used_numbers = db.execute("SELECT account_number FROM customers").fetchall()
    used_numbers = [int(row["account_number"]) for row in used_numbers if row["account_number"].isdigit()]

    next_acc = None
    for i in range(100, 1001):
        if i not in used_numbers:
            next_acc = i
            break

    if request.method == "POST":
        acc_no = request.form["account_number"]
        name = request.form["name"]
        mobile = request.form["mobile"]
        address = request.form["address"]

        if not acc_no.isdigit() or not (100 <= int(acc_no) <= 1000):
            error = "Account number must be between 100 and 1000"
        else:
            existing_acc = db.execute(
                "SELECT * FROM customers WHERE account_number=?", (acc_no,)
            ).fetchone()

            existing_mobile = db.execute(
                "SELECT * FROM customers WHERE mobile=?", (mobile,)
            ).fetchone()

            if existing_acc:
                error = f"Account exists! Try {next_acc}"
            elif existing_mobile:
                error = "Mobile number already exists!"
            else:
                db.execute(
                    "INSERT INTO customers(account_number,name,mobile,address,created) VALUES (?,?,?,?,?)",
                    (acc_no, name, mobile, address, datetime.now())
                )
                db.commit()
                return redirect("/dashboard")

    return render_template("create_account.html", error=error, next_acc=next_acc)

# ---------------- CUSTOMERS ----------------
@app.route("/customers")
def customers_list():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers ORDER BY created DESC").fetchall()
    return render_template("customers.html", customers=customers)

# ---------------- DEPOSIT ----------------
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers").fetchall()

    if request.method == "POST":
        db.execute(
            "INSERT INTO transactions(customer_id,type,amount,date) VALUES (?,?,?,?)",
            (request.form["customer"], "deposit", float(request.form["amount"]), datetime.now())
        )
        db.commit()
        return redirect("/dashboard")

    return render_template("deposit.html", customers=customers)

# ---------------- WITHDRAW ----------------
@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers").fetchall()

    if request.method == "POST":
        db.execute(
            "INSERT INTO transactions(customer_id,type,amount,date) VALUES (?,?,?,?)",
            (request.form["customer"], "withdraw", float(request.form["amount"]), datetime.now())
        )
        db.commit()
        return redirect("/dashboard")

    return render_template("withdraw.html", customers=customers)

# ---------------- NEW LOAN ----------------
@app.route("/new_loan", methods=["GET", "POST"])
def new_loan():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    customers = db.execute("SELECT * FROM customers").fetchall()
    error = None

    if request.method == "POST":
        try:
            months = int(request.form["months"])

            # ✅ FIX: prevent months error
            if months <= 0:
                error = "Months must be greater than 0"
            else:
                db.execute(
                    "INSERT INTO loans(customer_id,loan_amount,interest,months,service_charge,created) VALUES (?,?,?,?,?,?)",
                    (
                        request.form["customer"],
                        float(request.form["loan_amount"]),
                        float(request.form.get("interest", 0)),
                        months,
                        float(request.form.get("service_charge", 0)),
                        datetime.now()
                    )
                )
                db.commit()
                return redirect("/dashboard")

        except Exception as e:
            error = f"Error: {e}"

    return render_template("new_loan.html", customers=customers, error=error)

# ---------------- LOAN REPORT ----------------
@app.route("/loan_report")
def loan_report():
    if "user" not in session:
        return redirect("/")

    db = get_db()

    data = db.execute("""
        SELECT 
            loans.id,
            customers.account_number,
            customers.name,
            customers.mobile,
            loans.loan_amount,
            loans.interest,
            loans.months,
            loans.service_charge,
            loans.created,
            COALESCE(SUM(loan_payments.amount), 0) as total_paid
        FROM loans
        JOIN customers ON customers.id = loans.customer_id
        LEFT JOIN loan_payments ON loan_payments.loan_id = loans.id
        GROUP BY loans.id
        ORDER BY loans.created DESC
    """).fetchall()

    # ✅ CALCULATE TOTALS
    total_loans = len(data)
    total_amount = sum(row["loan_amount"] for row in data)
    total_paid = sum(row["total_paid"] for row in data)
    total_balance = total_amount - total_paid

    return render_template(
        "loan_report.html",
        data=data,
        total_loans=total_loans,
        total_amount=total_amount,
        total_paid=total_paid,
        total_balance=total_balance
    )
# ---------------- report----------------
@app.route("/report")
def report_menu():
    if "user" not in session:
        return redirect("/")
    return render_template("report.html")

# ---------------- deposit report----------------
@app.route("/deposit_report")
def deposit_report():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    data = db.execute("""
        SELECT customers.name, customers.account_number,
               transactions.amount, transactions.date
        FROM transactions
        JOIN customers ON customers.id = transactions.customer_id
        WHERE type='deposit'
        ORDER BY date DESC
    """).fetchall()

    total = sum(row["amount"] for row in data)

    return render_template("deposit_report.html", data=data, total=total)
# ---------------- Service charge report----------------

@app.route("/service_report")
def service_report():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    data = db.execute("""
        SELECT customers.name, customers.account_number,
               loans.service_charge, loans.created
        FROM loans
        JOIN customers ON customers.id = loans.customer_id
        ORDER BY loans.created DESC
    """).fetchall()

    total = sum(row["service_charge"] for row in data)

    return render_template("service_report.html", data=data, total=total)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)