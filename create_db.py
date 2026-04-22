import sqlite3

conn = sqlite3.connect("bank.db")
c = conn.cursor()

# ---------------- USERS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ---------------- CUSTOMERS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT UNIQUE,
    name TEXT,
    mobile TEXT UNIQUE,
    address TEXT,
    created TEXT
)
""")

# ---------------- TRANSACTIONS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    type TEXT CHECK(type IN ('deposit','withdraw')),
    amount REAL,
    date TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
""")

# ---------------- LOANS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS loans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    loan_amount REAL,
    interest REAL,
    months INTEGER,
    service_charge REAL,
    created TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
""")

# ---------------- LOAN PAYMENTS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS loan_payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    amount REAL,
    date TEXT,
    FOREIGN KEY(loan_id) REFERENCES loans(id)
)
""")

# ---------------- SERVICE EXPENSE ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS service_expense(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    note TEXT,
    date TEXT
)
""")

# ---------------- OPTIONAL: INDEXES (FASTER) ----------------
c.execute("CREATE INDEX IF NOT EXISTS idx_customer_id ON transactions(customer_id)")
c.execute("CREATE INDEX IF NOT EXISTS idx_loan_customer ON loans(customer_id)")

# ---------------- RESET USERS ----------------
c.execute("DELETE FROM users")

# ---------------- INSERT DEFAULT USERS ----------------
c.execute("INSERT INTO users(username,password) VALUES('admin','admin123')")
c.execute("INSERT INTO users(username,password) VALUES('staff','staff123')")

conn.commit()
conn.close()

print("✅ Full database created successfully (Bank + Loan System)")