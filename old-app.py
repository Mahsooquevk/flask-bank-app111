from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import random 

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        db = get_db()
        result = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (user,pwd)).fetchone()

        if result:
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    db = get_db()

    total_customers = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    deposits = db.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='deposit'"
    ).fetchone()[0] or 0

    withdraw = db.execute(
        "SELECT SUM(amount) FROM transactions WHERE type='withdraw'"
    ).fetchone()[0] or 0

    balance = deposits - withdraw

    return render_template("dashboard.html",
                           customers=total_customers,
                           deposits=deposits,
                           withdraw=withdraw,
                           balance=balance)

import random

@app.route("/create_account", methods=["GET","POST"])
def create_account():

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        address = request.form["address"]

        db = get_db()

	acc_no = "AC" + datetime.now().strftime("%Y%m%d%H%M%S")

        db.execute(
            "INSERT INTO customers(account_number,name,mobile,address,created) VALUES (?,?,?,?,?)",
            (acc_no, name, mobile, address, datetime.now())
        )

        db.commit()

        return redirect("/dashboard")

    return render_template("create_account.html")


@app.route("/deposit", methods=["GET","POST"])
def deposit():

    db = get_db()

    customers = db.execute("SELECT * FROM customers").fetchall()

    if request.method == "POST":

        cid = request.form["customer"]
        amount = request.form["amount"]

        db.execute(
            "INSERT INTO transactions(customer_id,type,amount,date) VALUES (?,?,?,?)",
            (cid,"deposit",amount,datetime.now())
        )

        db.commit()

        return redirect("/dashboard")

    return render_template("deposit.html", customers=customers)


@app.route("/withdraw", methods=["GET","POST"])
def withdraw():

    db = get_db()

    customers = db.execute("SELECT * FROM customers").fetchall()

    if request.method == "POST":

        cid = request.form["customer"]
        amount = request.form["amount"]

        db.execute(
            "INSERT INTO transactions(customer_id,type,amount,date) VALUES (?,?,?,?)",
            (cid,"withdraw",amount,datetime.now())
        )

        db.commit()

        return redirect("/dashboard")

    return render_template("withdraw.html", customers=customers)


@app.route("/report")
def report():

    db = get_db()

    data = db.execute("""
        SELECT customers.name, transactions.type, transactions.amount, transactions.date
        FROM transactions
        JOIN customers ON customers.id = transactions.customer_id
        ORDER BY date DESC
    """).fetchall()

    return render_template("report.html", data=data)

@app.route("/customers")
def customers_list():

    db = get_db()

    customers = db.execute("""
        SELECT * FROM customers ORDER BY created DESC
    """).fetchall()

    return render_template("customers.html", customers=customers)


if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run()