from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from database import init_db, get_db_connection
import datetime
from datetime import datetime as dt
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize database on startup
with app.app_context():
    init_db()

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d'):
    if isinstance(value, str):
        try:
            value = dt.strptime(value, '%Y-%m-%d')
        except ValueError:
            try:
                value = dt.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
    return value.strftime(format)

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get top 5-8 clients with approaching deadlines
    cursor.execute("""
        SELECT c.name, cf.cloth_type, cf.status, cf.deadline
        FROM client_fabrics cf
        JOIN clients c ON cf.client_id = c.id
        WHERE cf.status = 'in-process' AND date(cf.deadline) <= date('now', '+3 days')
        ORDER BY cf.deadline ASC
        LIMIT 8
    """)
    deadline_clients = cursor.fetchall()

    # Get in-progress orders for pop-up
    cursor.execute("""
        SELECT c.name, cf.cloth_type, cf.quantity_meter, cf.quantity_gauze, cf.receiving_date, cf.deadline
        FROM client_fabrics cf
        JOIN clients c ON cf.client_id = c.id
        WHERE cf.status = 'in-process'
        ORDER BY cf.deadline ASC
    """)
    inprogress_orders = cursor.fetchall()

    # Dummy data for graphs (replace with real data from DB later)
    # Orders Line Graph (Monthly)
    orders_data = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "data": [65, 59, 80, 81, 56, 55, 40, 60, 70, 75, 80, 85]
    }

    # Raw Material Graph (Example: Wood quantity over time)
    material_data = {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "data": [1000, 950, 800, 700]  # Example: wood quantity in kg
    }

    conn.close()
    return render_template('dashboard.html',
                           deadline_clients=deadline_clients,
                           inprogress_orders=inprogress_orders,
                           orders_data=orders_data,
                           material_data=material_data)


@app.route('/clients')
def client_management():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.company_name, c.contact_no, c.status, c.product_balance,
               SUM(CASE WHEN cp.type = 'cash' THEN cp.amount ELSE 0 END) AS received_cash,
               SUM(CASE WHEN cp.type = 'account' THEN cp.amount ELSE 0 END) AS received_account,
               c.notes
        FROM clients c
        LEFT JOIN client_payments cp ON c.id = cp.client_id
        GROUP BY c.id
        ORDER BY c.name
    """)
    clients = cursor.fetchall()
    
    # Get all client fabrics for the outgoing modal dropdown
    cursor.execute("SELECT id, client_id, cloth_type, quantity_meter, processing_type FROM client_fabrics WHERE quantity_meter > 0")
    client_fabrics = cursor.fetchall()

    conn.close()
    return render_template('client_management.html', clients=clients, client_fabrics=client_fabrics)
@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form['name']
    company_name = request.form.get('company_name', '')
    category = request.form['category']
    contact_no = request.form.get('contact_no', '')
    status = request.form['status']
    product_balance = float(request.form.get('product_balance', 0))
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (name, company_name, category, contact_no, status, product_balance, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, company_name, category, contact_no, status, product_balance, notes))
    conn.commit()
    conn.close()
    flash('Client added successfully!', 'success')
    return redirect(url_for('client_management'))
@app.route('/delete_worker/<int:worker_id>')
def delete_worker(worker_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
    conn.commit()
    conn.close()
    flash('Worker deleted successfully!', 'success')
    return redirect(url_for('worker_management'))

@app.route('/delete_distributor/<int:distributor_id>')
def delete_distributor(distributor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM distributors WHERE id = ?", (distributor_id,))
    conn.commit()
    conn.close()
    flash('Distributor successfully deleted!', 'success')
    return redirect(url_for('distributor_management'))


@app.route('/client/<int:client_id>')
def client_detail(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    cursor.execute("SELECT * FROM client_fabrics WHERE client_id = ?", (client_id,))
    fabrics = cursor.fetchall()

    cursor.execute("SELECT * FROM client_payments WHERE client_id = ? ORDER BY date DESC", (client_id,))
    payments = cursor.fetchall()

    conn.close()
    
    if client:
        return jsonify({
            'client': dict(client) if client else None,
            'fabrics': [dict(f) for f in fabrics],
            'payments': [dict(p) for p in payments]
        })
    else:
        return jsonify({'error': 'Client not found'}), 404
@app.route('/add_outgoing_fabric/<int:client_id>', methods=['POST'])
def add_outgoing_fabric(client_id):
    fabric_id = request.form['fabric_id']
    quantity = float(request.form['quantity'])
    recipient_name = request.form['recipient_name']
    destination_city = request.form['destination_city']
    notes = request.form.get('notes', '')
    outgoing_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if a specific fabric item is selected
    if not fabric_id:
        flash('Please select a fabric item to deduct from.', 'error')
        conn.close()
        return redirect(url_for('client_management'))

    # Get the current quantity of the specific fabric
    cursor.execute("SELECT quantity_meter, cloth_type FROM client_fabrics WHERE id = ?", (fabric_id,))
    fabric_item = cursor.fetchone()

    if not fabric_item:
        flash('Fabric item not found!', 'error')
        conn.close()
        return redirect(url_for('client_management'))

    current_quantity = fabric_item['quantity_meter']
    cloth_type = fabric_item['cloth_type']

    if quantity > current_quantity:
        flash(f'Error: Outgoing quantity ({quantity}m) cannot exceed available quantity ({current_quantity}m) for {cloth_type} fabric.', 'error')
        conn.close()
        return redirect(url_for('client_management'))

    try:
        # Deduct the quantity from the client_fabrics table
        new_quantity = current_quantity - quantity
        cursor.execute("UPDATE client_fabrics SET quantity_meter = ? WHERE id = ?", (new_quantity, fabric_id))

        # Insert the outgoing record into the new fabric_outgoing table
        cursor.execute("""
            INSERT INTO fabric_outgoing (client_id, fabric_id, quantity, recipient_name, destination_city, outgoing_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_id, fabric_id, quantity, recipient_name, destination_city, outgoing_date, notes))

        conn.commit()
        flash('Outgoing fabric recorded successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred: {e}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('client_management'))

@app.route('/add_fabric_order/<int:client_id>', methods=['POST'])
def add_fabric_order(client_id):
    cloth_type = request.form['cloth_type']
    quality = request.form.get('quality', '')
    color = request.form.get('color', '')
    quantity_meter = float(request.form.get('quantity_meter', 0))
    quantity_gauze = float(request.form.get('quantity_gauze', 0))
    processing_type = request.form.get('processing_type', '')
    receiving_date = request.form['receiving_date']
    deadline = request.form['deadline']
    status = request.form['status']
    notes = request.form.get('notes', '')
    
    # Calculate price based on processing type
    price_per_meter = 100  # Base price
    if processing_type == 'waterproof':
        price_per_meter += 50
    elif processing_type == 'heatproof':
        price_per_meter += 70
    elif processing_type == 'moom':
        price_per_meter += 60
    
    total_amount = quantity_meter * price_per_meter

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add fabric order
    cursor.execute("""
        INSERT INTO client_fabrics (client_id, cloth_type, quality, color, quantity_meter, 
                                   quantity_gauze, processing_type, receiving_date, deadline, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (client_id, cloth_type, quality, color, quantity_meter, quantity_gauze, 
          processing_type, receiving_date, deadline, status, notes))
    
    # Update client balance
    cursor.execute("UPDATE clients SET product_balance = product_balance + ? WHERE id = ?", 
                  (total_amount, client_id))
    
    conn.commit()
    conn.close()
    flash('Fabric order added successfully!', 'success')
    return redirect(url_for('client_management'))

@app.route('/add_client_payment/<int:client_id>', methods=['POST'])
def add_client_payment(client_id):
    amount = float(request.form['amount'])
    payment_type = request.form['payment_type']
    date = request.form.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO client_payments (client_id, amount, type, date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (client_id, amount, payment_type, date, notes))

    # Update client's balance
    cursor.execute("UPDATE clients SET product_balance = product_balance - ? WHERE id = ?", (amount, client_id))

    conn.commit()
    conn.close()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('client_management'))
@app.route('/update_material_usage/<material_type>/<int:material_id>', methods=['POST'])
def update_material_usage(material_type, material_id):
    used_quantity = float(request.form['used_quantity'])
    used_by = request.form.get('used_by', '')
    notes = request.form.get('notes', '')
    usage_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity based on material type
    if material_type == 'liquid_chemical':
        cursor.execute("SELECT quantity_liter FROM liquid_chemicals WHERE id = ?", (material_id,))
        table_name = 'liquid_chemicals'
        quantity_field = 'quantity_liter'
    elif material_type == 'powder_chemical':
        cursor.execute("SELECT quantity_kg FROM powder_chemicals WHERE id = ?", (material_id,))
        table_name = 'powder_chemicals'
        quantity_field = 'quantity_kg'
    elif material_type == 'wood':
        cursor.execute("SELECT quantity_kg FROM wood WHERE id = ?", (material_id,))
        table_name = 'wood'
        quantity_field = 'quantity_kg'
    elif material_type == 'electronics':
        cursor.execute("SELECT quantity FROM electronics WHERE id = ?", (material_id,))
        table_name = 'electronics'
        quantity_field = 'quantity'
    else:
        flash('Invalid material type', 'error')
        return redirect(url_for('material_management'))
    
    current_quantity = cursor.fetchone()[quantity_field]
    
    if used_quantity > current_quantity:
        flash('Error: Used quantity cannot exceed available quantity!', 'error')
        return redirect(url_for('material_management'))
    
    new_quantity = current_quantity - used_quantity
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update material quantity
    cursor.execute(f"UPDATE {table_name} SET {quantity_field} = ?, date_updated = ? WHERE id = ?", 
                  (new_quantity, date_updated, material_id))
    
    # Record usage
    cursor.execute("""
        INSERT INTO material_usage (material_type, material_id, quantity_used, usage_date, notes, used_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (material_type, material_id, used_quantity, usage_date, notes, used_by))
    
    conn.commit()
    conn.close()
    flash('Material usage updated successfully!', 'success')
    return redirect(url_for('material_management'))

@app.route('/update_client/<int:client_id>', methods=['POST'])
def update_client(client_id):
    name = request.form['name']
    company_name = request.form.get('company_name', '')
    category = request.form['category']
    contact_no = request.form.get('contact_no', '')
    status = request.form['status']
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients 
        SET name = ?, company_name = ?, category = ?, contact_no = ?, status = ?, notes = ?
        WHERE id = ?
    """, (name, company_name, category, contact_no, status, notes, client_id))
    conn.commit()
    conn.close()
    flash('Client updated successfully!', 'success')
    return redirect(url_for('client_management'))

# Distributor Management Routes
@app.route('/distributors')
def distributor_management():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, d.name, d.company_name, d.contact_no, d.category, d.address, d.notes,
               SUM(CASE WHEN dp.type = 'cash' THEN dp.amount ELSE 0 END) AS paid_cash,
               SUM(CASE WHEN dp.type = 'account' THEN dp.amount ELSE 0 END) AS paid_account,
               SUM(ms.total_amount) AS total_supply_amount,
               SUM(ms.total_amount) - SUM(COALESCE(dp.amount, 0)) AS remaining_balance
        FROM distributors d
        LEFT JOIN distributor_payments dp ON d.id = dp.distributor_id
        LEFT JOIN material_supply ms ON d.id = ms.distributor_id
        GROUP BY d.id
        ORDER BY d.name
    """)
    distributors = cursor.fetchall()
    
    conn.close()
    return render_template('distributor_management.html', distributors=distributors)

@app.route('/add_distributor', methods=['POST'])
def add_distributor():
    name = request.form['name']
    company_name = request.form.get('company_name', '')
    category = request.form['category']
    contact_no = request.form.get('contact_no', '')
    address = request.form.get('address', '')
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO distributors (name, company_name, category, contact_no, address, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, company_name, category, contact_no, address, notes))
    conn.commit()
    conn.close()
    flash('Distributor added successfully!', 'success')
    return redirect(url_for('distributor_management'))

@app.route('/distributor/<int:distributor_id>')
def distributor_detail(distributor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM distributors WHERE id = ?", (distributor_id,))
    distributor = cursor.fetchone()

    cursor.execute("SELECT * FROM material_supply WHERE distributor_id = ? ORDER BY receiving_date DESC", (distributor_id,))
    supplies = cursor.fetchall()

    cursor.execute("SELECT * FROM distributor_payments WHERE distributor_id = ? ORDER BY date DESC", (distributor_id,))
    payments = cursor.fetchall()

    conn.close()
    
    if distributor:
        return jsonify({
            'distributor': dict(distributor) if distributor else None,
            'supplies': [dict(s) for s in supplies],
            'payments': [dict(p) for p in payments]
        })
    else:
        return jsonify({'error': 'Distributor not found'}), 404

@app.route('/add_material_supply/<int:distributor_id>', methods=['POST'])
def add_material_supply(distributor_id):
    material_type = request.form['material_type']
    quantity = float(request.form['quantity'])
    unit = request.form['unit']
    rate = float(request.form['rate'])
    total_amount = quantity * rate
    receiving_date = request.form['receiving_date']
    notes = request.form.get('notes', '')
    chemical_name = request.form.get('chemical_name', '')  # Add this field for chemicals

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add material supply
    cursor.execute("""
        INSERT INTO material_supply (distributor_id, material_type, quantity, unit, rate, total_amount, receiving_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, material_type, quantity, unit, rate, total_amount, receiving_date, notes))
    
    # Update material inventory based on type
    if material_type == 'wood':
        cursor.execute("""
            INSERT INTO wood (distributor_id, quantity_kg, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'liquid_chemical':
        cursor.execute("""
            INSERT INTO liquid_chemicals (distributor_id, name, quantity_liter, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, chemical_name, quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'powder_chemical':
        cursor.execute("""
            INSERT INTO powder_chemicals (distributor_id, name, quantity_kg, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, chemical_name, quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'electronics':
        cursor.execute("""
            INSERT INTO electronics (distributor_id, item_name, quantity, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, chemical_name, quantity, total_amount, total_amount, notes, receiving_date))
    
    conn.commit()
    conn.close()
    flash('Material supply added successfully!', 'success')
    return redirect(url_for('distributor_management'))    
    # Add material supply
    cursor.execute("""
        INSERT INTO material_supply (distributor_id, material_type, quantity, unit, rate, total_amount, receiving_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, material_type, quantity, unit, rate, total_amount, receiving_date, notes))
    
    # Update material inventory based on type
    if material_type == 'wood':
        cursor.execute("""
            INSERT INTO wood (distributor_id, quantity_kg, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'liquid_chemical':
        cursor.execute("""
            INSERT INTO liquid_chemicals (distributor_id, name, quantity_liter, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, notes.split('-')[0] if notes else 'Chemical', quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'powder_chemical':
        cursor.execute("""
            INSERT INTO powder_chemicals (distributor_id, name, quantity_kg, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, notes.split('-')[0] if notes else 'Powder', quantity, total_amount, total_amount, notes, receiving_date))
    elif material_type == 'electronics':
        cursor.execute("""
            INSERT INTO electronics (distributor_id, item_name, quantity, total_amount, payment, remaining, notes, date_added)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (distributor_id, notes.split('-')[0] if notes else 'Electronic Item', quantity, total_amount, total_amount, notes, receiving_date))
    
    conn.commit()
    conn.close()
    flash('Material supply added successfully!', 'success')
    return redirect(url_for('distributor_management'))

@app.route('/add_distributor_payment/<int:distributor_id>', methods=['POST'])
def add_distributor_payment(distributor_id):
    amount = float(request.form['amount'])
    payment_type = request.form['payment_type']
    date = request.form.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO distributor_payments (distributor_id, amount, type, date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (distributor_id, amount, payment_type, date, notes))

    conn.commit()
    conn.close()
    flash('Distributor payment recorded successfully!', 'success')
    return redirect(url_for('distributor_management'))

@app.route('/update_distributor/<int:distributor_id>', methods=['POST'])
def update_distributor(distributor_id):
    name = request.form['name']
    company_name = request.form.get('company_name', '')
    category = request.form['category']
    contact_no = request.form.get('contact_no', '')
    address = request.form.get('address', '')
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE distributors 
        SET name = ?, company_name = ?, category = ?, contact_no = ?, address = ?, notes = ?
        WHERE id = ?
    """, (name, company_name, category, contact_no, address, notes, distributor_id))
    conn.commit()
    conn.close()
    flash('Distributor updated successfully!', 'success')
    return redirect(url_for('distributor_management'))

# Worker Management Routes
@app.route('/workers')
def worker_management():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()
    conn.close()
    return render_template('worker_management.html', workers=workers)

@app.route('/add_worker', methods=['POST'])
def add_worker():
    name = request.form['name']
    contact_no = request.form['contact_no']
    total_salary = float(request.form['total_salary'])
    advance_salary = float(request.form.get('advance_salary', 0))
    joining_date =  datetime.now()

    remaining_salary = total_salary - advance_salary

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workers (name, contact_no, total_salary, advance_salary, remaining_salary, joining_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, contact_no, total_salary, advance_salary, remaining_salary, joining_date))
    conn.commit()
    conn.close()
    flash('Worker added successfully!', 'success')
    return redirect(url_for('worker_management'))

@app.route('/update_worker/<int:worker_id>', methods=['POST'])
def update_worker(worker_id):
    name = request.form['name']
    contact_no = request.form['contact_no']
    total_salary = float(request.form['total_salary'])
    advance_salary = float(request.form['advance_salary'])
    bonus = float(request.form.get('bonus', 0))

    remaining_salary = total_salary - advance_salary + bonus

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE workers
        SET name = ?, contact_no = ?, total_salary = ?, advance_salary = ?, remaining_salary = ?, bonus = ?
        WHERE id = ?
    """, (name, contact_no, total_salary, advance_salary, remaining_salary, bonus, worker_id))
    conn.commit()
    conn.close()
    flash('Worker updated successfully!', 'success')
    return redirect(url_for('worker_management'))

@app.route('/attendance')
def attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()
    cursor.execute("SELECT wa.worker_id, w.name, wa.date, wa.status FROM worker_attendance wa JOIN workers w ON wa.worker_id = w.id ORDER BY wa.date DESC")
    attendance_records = cursor.fetchall()
    conn.close()
    return render_template('attendance.html', workers=workers, attendance_records=attendance_records)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    worker_id = request.form['worker_id']
    date = request.form['date']
    status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if attendance already marked for this date
    cursor.execute("SELECT * FROM worker_attendance WHERE worker_id = ? AND date = ?", (worker_id, date))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE worker_attendance SET status = ? WHERE worker_id = ? AND date = ?", 
                      (status, worker_id, date))
    else:
        cursor.execute("""
            INSERT INTO worker_attendance (worker_id, date, status)
            VALUES (?, ?, ?)
        """, (worker_id, date, status))
        
    conn.commit()
    conn.close()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('attendance'))

@app.route('/materials')
def material_management():
    return render_template('material_management.html')

@app.route('/materials/wood')
def wood_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get individual wood records
    cursor.execute("SELECT w.*, d.name as distributor_name FROM wood w LEFT JOIN distributors d ON w.distributor_id = d.id")
    wood_stock = cursor.fetchall()
    
    # Calculate total wood metrics
    cursor.execute("""
        SELECT 
            SUM(quantity_kg) as total_quantity,
            SUM(total_amount) as total_amount,
            SUM(payment) as total_payment,
            SUM(remaining) as total_remaining
        FROM wood
    """)
    total_wood = cursor.fetchone()
    
    conn.close()
    return render_template('wood_materials.html', 
                         wood_stock=wood_stock,
                         total_wood=total_wood)

@app.route('/add_wood', methods=['POST'])
def add_wood():
    distributor_id = request.form.get('distributor_id')
    quantity_kg = float(request.form['quantity_kg'])
    total_amount = float(request.form['total_amount'])
    payment = float(request.form.get('payment', 0))
    notes = request.form.get('notes', '')
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    remaining = total_amount - payment

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wood (distributor_id, quantity_kg, total_amount, payment, remaining, notes, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, quantity_kg, total_amount, payment, remaining, notes, date_added))
    conn.commit()
    conn.close()
    flash('Wood stock added successfully!', 'success')
    return redirect(url_for('wood_materials'))

@app.route('/update_wood_usage/<int:wood_id>', methods=['POST'])
def update_wood_usage(wood_id):
    used_quantity = float(request.form['used_quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity
    cursor.execute("SELECT quantity_kg FROM wood WHERE id = ?", (wood_id,))
    current_quantity = cursor.fetchone()['quantity_kg']
    
    if used_quantity > current_quantity:
        flash('Error: Used quantity cannot exceed available quantity!', 'error')
        return redirect(url_for('wood_materials'))
    
    new_quantity = current_quantity - used_quantity
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update wood quantity
    cursor.execute("UPDATE wood SET quantity_kg = ?, date_updated = ? WHERE id = ?", 
                  (new_quantity, date_updated, wood_id))
    
    # Record usage
    cursor.execute("""
        INSERT INTO material_usage (material_type, material_id, quantity_used, usage_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ('wood', wood_id, used_quantity, date_updated, notes))
    
    conn.commit()
    conn.close()
    flash('Wood usage updated successfully!', 'success')
    return redirect(url_for('wood_materials'))

@app.route('/materials/liquid_chemicals')
def liquid_chemical_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lc.*, d.name as distributor_name FROM liquid_chemicals lc LEFT JOIN distributors d ON lc.distributor_id = d.id")
    chemicals_stock = cursor.fetchall()
    
    # Calculate totals
    cursor.execute("""
        SELECT 
            SUM(quantity_liter) as total_quantity,
            SUM(total_amount) as total_amount,
            SUM(payment) as total_payment,
            SUM(remaining) as total_remaining
        FROM liquid_chemicals
    """)
    total_chemicals = cursor.fetchone()
    
    conn.close()
    return render_template('liquid_chemical_materials.html', 
                         chemicals_stock=chemicals_stock,
                         total_chemicals=total_chemicals)

@app.route('/add_liquid_chemical', methods=['POST'])
def add_liquid_chemical():
    distributor_id = request.form.get('distributor_id')
    name = request.form['name']
    quantity_liter = float(request.form['quantity_liter'])
    total_amount = float(request.form['total_amount'])
    payment = float(request.form.get('payment', 0))
    notes = request.form.get('notes', '')
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    remaining = total_amount - payment

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO liquid_chemicals (distributor_id, name, quantity_liter, total_amount, payment, remaining, notes, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, name, quantity_liter, total_amount, payment, remaining, notes, date_added))
    conn.commit()
    conn.close()
    flash('Liquid chemical added successfully!', 'success')
    return redirect(url_for('liquid_chemical_materials'))

@app.route('/update_liquid_chemical_usage/<int:chemical_id>', methods=['POST'])
def update_liquid_chemical_usage(chemical_id):
    used_quantity = float(request.form['used_quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity
    cursor.execute("SELECT quantity_liter FROM liquid_chemicals WHERE id = ?", (chemical_id,))
    current_quantity = cursor.fetchone()['quantity_liter']
    
    if used_quantity > current_quantity:
        flash('Error: Used quantity cannot exceed available quantity!', 'error')
        return redirect(url_for('liquid_chemical_materials'))
    
    new_quantity = current_quantity - used_quantity
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update chemical quantity
    cursor.execute("UPDATE liquid_chemicals SET quantity_liter = ?, date_updated = ? WHERE id = ?", 
                  (new_quantity, date_updated, chemical_id))
    
    # Record usage
    cursor.execute("""
        INSERT INTO material_usage (material_type, material_id, quantity_used, usage_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ('liquid_chemical', chemical_id, used_quantity, date_updated, notes))
    
    conn.commit()
    conn.close()
    flash('Liquid chemical usage updated successfully!', 'success')
    return redirect(url_for('liquid_chemical_materials'))

@app.route('/materials/powder_chemicals')
def powder_chemical_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pc.*, d.name as distributor_name FROM powder_chemicals pc LEFT JOIN distributors d ON pc.distributor_id = d.id")
    chemicals_stock = cursor.fetchall()
    
    # Calculate totals
    cursor.execute("""
        SELECT 
            SUM(quantity_kg) as total_quantity,
            SUM(total_amount) as total_amount,
            SUM(payment) as total_payment,
            SUM(remaining) as total_remaining
        FROM powder_chemicals
    """)
    total_chemicals = cursor.fetchone()
    
    conn.close()
    return render_template('powder_chemical_materials.html', 
                         chemicals_stock=chemicals_stock,
                         total_chemicals=total_chemicals)

@app.route('/add_powder_chemical', methods=['POST'])
def add_powder_chemical():
    distributor_id = request.form.get('distributor_id')
    name = request.form['name']
    quantity_kg = float(request.form['quantity_kg'])
    total_amount = float(request.form['total_amount'])
    payment = float(request.form.get('payment', 0))
    notes = request.form.get('notes', '')
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    remaining = total_amount - payment

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO powder_chemicals (distributor_id, name, quantity_kg, total_amount, payment, remaining, notes, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, name, quantity_kg, total_amount, payment, remaining, notes, date_added))
    conn.commit()
    conn.close()
    flash('Powder chemical added successfully!', 'success')
    return redirect(url_for('powder_chemical_materials'))

@app.route('/update_powder_chemical_usage/<int:chemical_id>', methods=['POST'])
def update_powder_chemical_usage(chemical_id):
    used_quantity = float(request.form['used_quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity
    cursor.execute("SELECT quantity_kg FROM powder_chemicals WHERE id = ?", (chemical_id,))
    current_quantity = cursor.fetchone()['quantity_kg']
    
    if used_quantity > current_quantity:
        flash('Error: Used quantity cannot exceed available quantity!', 'error')
        return redirect(url_for('powder_chemical_materials'))
    
    new_quantity = current_quantity - used_quantity
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update chemical quantity
    cursor.execute("UPDATE powder_chemicals SET quantity_kg = ?, date极dated = ? WHERE id = ?", 
                  (new_quantity, date_updated, chemical_id))
    
    # Record usage
    cursor.execute("""
        INSERT INTO material_usage (material_type, material_id, quantity_used, usage_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ('powder_chemical', chemical_id, used_quantity, date_updated, notes))
    
    conn.commit()
    conn.close()
    flash('Powder chemical usage updated successfully!', 'success')
    return redirect(url_for('powder_chemical_materials'))

@app.route('/materials/electronics')
def electronics_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT e.*, d.name as distributor_name FROM electronics e LEFT JOIN distributors d ON e.distributor_id = d.id")
    electronics_stock = cursor.fetchall()
    
    # Calculate totals
    cursor.execute("""
        SELECT 
            SUM(quantity) as total_quantity,
            SUM(total_amount) as total_amount,
            SUM(payment) as total_payment,
            SUM(remaining) as total_remaining
        FROM electronics
    """)
    total_electronics = cursor.fetchone()
    
    conn.close()
    return render_template('electronics_materials.html', 
                         electronics_stock=electronics_stock,
                         total_electronics=total_electronics)

@app.route('/add_electronics', methods=['POST'])
def add_electronics():
    distributor_id = request.form.get('distributor_id')
    item_name = request.form['item_name']
    quantity = int(request.form['quantity'])
    total_amount = float(request.form['total_amount'])
    payment = float(request.form.get('payment', 0))
    notes = request.form.get('notes', '')
    date_add极 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    remaining = total_amount - payment
    date_added = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO electronics (distributor_id, item_name, quantity, total_amount, payment, remaining, notes, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (distributor_id, item_name, quantity, total_amount, payment, remaining, notes, date_added))
    conn.commit()
    conn.close()
    flash('Electronics item added successfully!', 'success')
    return redirect(url_for('electronics_materials'))

@app.route('/update_electronics_usage/<int:electronics_id>', methods=['POST'])
def update_electronics_usage(electronics_id):
    used_quantity = int(request.form['used_quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity
    cursor.execute("SELECT quantity FROM electronics WHERE id = ?", (electronics_id,))
    current_quantity = cursor.fetchone()['quantity']
    
    if used_quantity > current_quantity:
        flash('Error: Used quantity cannot exceed available quantity!', 'error')
        return redirect(url_for('electronics_materials'))
    
    new_quantity = current_quantity - used_quantity
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update electronics quantity
    cursor.execute("UPDATE electronics SET quantity = ?, date_updated = ? WHERE id = ?", 
                  (new_quantity, date_updated, electronics_id))
    
    # Record usage
    cursor.execute("""
        INSERT INTO material_usage (material_type, material_id, quantity_used, usage_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, ('electronics', electronics_id, used_quantity, date_updated, notes))
    
    conn.commit()
    conn.close()
    flash('Electronics usage updated successfully!', 'success')
    return redirect(url_for('electronics_materials'))

@app.route('/generate_invoice/<int:client_id>')
def generate_invoice(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()

    cursor.execute("SELECT * FROM client_fabrics WHERE client_id = ?", (client_id,))
    fabrics = cursor.fetchall()

    cursor.execute("SELECT * FROM client_payments WHERE client_id = ? ORDER BY date DESC", (client_id,))
    payments = cursor.fetchall()

    conn.close()

    if client:
        total_paid = sum(p['amount'] for p in payments)
        remaining_balance = client['product_balance'] - total_paid
        
        invoice_html = render_template('invoice_template.html', 
                                     client=dict(client),
                                     fabrics=[dict(f) for f in fabrics],
                                     payments=[dict(p) for p in payments],
                                     total_paid=total_paid,
                                     remaining_balance=remaining_balance,
                                     invoice_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return invoice_html
    return "Invoice not found or client not found.", 404

if __name__ == '__main__':
    app.run(debug=True)