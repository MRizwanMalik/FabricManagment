import sqlite3
import datetime

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Drop old tables if they exist to clean up the schema
    cursor.execute("DROP TABLE IF EXISTS client_fabrics")
    
    # Clients Table (updated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            category TEXT,
            contact_no TEXT,
            status TEXT,
            notes TEXT
        )
    ''')
    
    # Client Payments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL, -- cash, account
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # New Client Orders Table to handle multiple orders per client
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            order_type TEXT NOT NULL,
            initial_quantity REAL NOT NULL,
            current_quantity REAL NOT NULL,
            unit TEXT,
            status TEXT NOT NULL,
            received_date TEXT NOT NULL,
            deadline TEXT,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    
    # New Outgoing Fabrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outgoing_fabrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            outgoing_date TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (order_id) REFERENCES client_orders(id)
        )
    ''')

    # Distributors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS distributors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            category TEXT,
            contact_no TEXT,
            status TEXT,
            notes TEXT
        )
    ''')

    # Powder Chemicals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS powder_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    # Liquid Chemicals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS liquid_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')
    
    # Electronics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS electronics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            stock REAL NOT NULL,
            unit TEXT NOT NULL,
            distributor_id INTEGER,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    # Create material usage history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_usage_history (
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

if __name__ == '__main__':
    init_db()
