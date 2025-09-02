import sqlite3
import datetime

DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Clients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            category TEXT NOT NULL,
            contact_no TEXT,
            status TEXT,
            balance REAL DEFAULT 0,
            inventory_quantity INTEGER DEFAULT 0,
            product_balance REAL DEFAULT 0,
            notes TEXT
        )
    ''')

    # Client Payments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # Fabrics Table (for client orders)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_fabrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            cloth_type TEXT NOT NULL,
            quality TEXT,
            color TEXT,
            quantity_meter REAL,
            quantity_gauze REAL,
            processing_type TEXT,
            receiving_date TEXT,
            deadline TEXT,
            status TEXT,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')
    # Fabric Outgoing Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fabric_outgoing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            fabric_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            recipient_name TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            outgoing_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (fabric_id) REFERENCES client_fabrics(id)
        )
    ''')

    # Distributors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS distributors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_name TEXT,
            category TEXT NOT NULL,
            contact_no TEXT,
            address TEXT,
            notes TEXT
        )
    ''')

    # Distributor Payments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS distributor_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    # Material Supply Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER NOT NULL,
            material_type TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            rate REAL,
            total_amount REAL,
            receiving_date TEXT,
            notes TEXT,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    # Workers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_no TEXT,
            total_salary REAL,
            advance_salary REAL DEFAULT 0,
            remaining_salary REAL,
            bonus REAL DEFAULT 0,
            joining_date TEXT
        )
    ''')

    # Worker Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS worker_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (worker_id) REFERENCES workers(id)
        )
    ''')

    # Raw Materials Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wood (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER,
            quantity_kg REAL,
            total_amount REAL,
            payment REAL DEFAULT 0,
            remaining REAL,
            notes TEXT,
            date_added TEXT,
            date_updated TEXT,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS liquid_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER,
            name TEXT,
            quantity_liter REAL,
            total_amount REAL,
            payment REAL DEFAULT 0,
            remaining REAL,
            notes TEXT,
            date_added TEXT,
            date_updated TEXT,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS powder_chemicals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER,
            name TEXT,
            quantity_kg REAL,
            total_amount REAL,
            payment REAL DEFAULT 0,
            remaining REAL,
            notes TEXT,
            date_added TEXT,
            date_updated TEXT,
            FOREIGN KEY (distributor_id) REFERENCES distributors(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS electronics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distributor_id INTEGER,
            item_name TEXT,
            quantity INTEGER,
            total_amount REAL,
            payment REAL DEFAULT 0,
            remaining REAL,
            notes TEXT,
            date_added TEXT,
            date_updated TEXT,
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
    
    # Add distributor_id column to liquid_chemicals if it doesn't exist
    try:
        cursor.execute("ALTER TABLE liquid_chemicals ADD COLUMN distributor_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add distributor_id column to powder_chemicals if it doesn't exist
    try:
        cursor.execute("ALTER TABLE powder_chemicals ADD COLUMN distributor_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add distributor_id column to electronics if it doesn't exist
    try:
        cursor.execute("ALTER TABLE electronics ADD COLUMN distributor_id INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")