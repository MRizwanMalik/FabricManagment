import sqlite3
import datetime

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Drop old tables if they exist to clean up the schema
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS client_payments")
    cursor.execute("DROP TABLE IF EXISTS distributors")
    cursor.execute("DROP TABLE IF EXISTS employees")
    cursor.execute("DROP TABLE IF EXISTS electronics")
    cursor.execute("DROP TABLE IF EXISTS liquid_chemicals")
    cursor.execute("DROP TABLE IF EXISTS solid_chemicals")
    cursor.execute("DROP TABLE IF EXISTS fabrics")
    cursor.execute("DROP TABLE IF EXISTS material_usage_history")
    cursor.execute("DROP TABLE IF EXISTS client_fabrics")  # This is the table from the error

    # Clients Table (updated)
    cursor.execute('''
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            category TEXT,
            contact_no TEXT,
            status TEXT,
            notes TEXT,
            product_balance REAL DEFAULT 0
        )
    ''')

    # Client Payments Table
    cursor.execute('''
        CREATE TABLE client_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL, -- cash, account
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # Client Fabrics Table (Corrected based on the error and HTML)
    cursor.execute('''
        CREATE TABLE client_fabrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            order_type TEXT,
            cloth_type TEXT,
            quality TEXT,
            quantity REAL,
            unit TEXT,
            status TEXT NOT NULL,
            receiving_date TEXT,
            deadline TEXT,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # Other tables from your project
    cursor.execute('''
        CREATE TABLE distributors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            contact_no TEXT,
            address TEXT,
            notes TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_no TEXT,
            joining_date TEXT,
            address TEXT,
            notes TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE electronics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE liquid_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE solid_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE material_usage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_type TEXT NOT NULL,
            material_id INTEGER NOT NULL,
            quantity_used REAL NOT NULL,
            date_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            used_by TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn
