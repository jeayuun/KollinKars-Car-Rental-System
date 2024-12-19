import os
import re
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import apology, login_required
from datetime import datetime


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///kollinkars.db")

def get_db_connection():
    conn = sqlite3.connect('kollinkars.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        role = request.form.get("role")
        username_or_id = request.form.get("username")
        password = request.form.get("password")

        if role == "admin":
            if username_or_id == "admin" and password == "password":
                session["user_id"] = 1
                session["role"] = "admin"
                flash("Logged in as Admin successfully!", "success")
                return redirect("/")
            else:
                flash("Invalid admin credentials. Please try again.", "error")
                return redirect("/login")

        elif role == "client":
            if not username_or_id or not password:
                flash("Both Customer ID and Password are required.", "error")
                return redirect("/login")

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM customer WHERE Customer_ID = ?", (username_or_id,))
            client = cursor.fetchone()
            conn.close()

            if client and password == "password123":
                session["user_id"] = client["Customer_ID"]
                session["role"] = "client"
                flash("Logged in as Client successfully!", "success")
                return redirect("/client")
            else:
                flash("Invalid client credentials or Customer ID not found.", "error")
                return redirect("/login")

    return render_template("index.html")

@app.route("/client")
@login_required
def client_home():
    # Fetch available vehicles from the database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch available vehicles (only those that are marked as 'Available')
        cursor.execute("""
            SELECT Vehicle_ID, Vehicle_Name, Vehicle_Price, Vehicle_Status, Seats
            FROM vehicle
            WHERE Vehicle_Status = 'Available'
        """)
        vehicles_data = cursor.fetchall()

        # If no vehicles are available, render the page with a message
        if not vehicles_data:
            return render_template("client.html", vehicles=[], message="No available vehicles at the moment.")

    except Exception as e:
        print(f"Error fetching vehicles: {e}")
        return render_template("client.html", vehicles=[], message="Error fetching available vehicles.")

    conn.close()

    # Pass the available vehicles data to the template
    return render_template("client.html", vehicles=vehicles_data)



@app.route('/book_vehicle', methods=['POST'])
@login_required
def book_vehicle():
    data = request.get_json()
    vehicle_id = data['vehicle_id']
    rental_startdate = data['rental_startdate']
    rental_enddate = data['rental_enddate']
    total_price = data['total_price']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Check if the vehicle is still available
        cursor.execute("SELECT Vehicle_Status FROM vehicle WHERE Vehicle_ID = ?", (vehicle_id,))
        vehicle_status = cursor.fetchone()
        if not vehicle_status or vehicle_status["Vehicle_Status"] != "Available":
            return jsonify({'success': False, 'error': 'Vehicle is no longer available.'})

        # Step 2: Generate the next Rental_ID
        cursor.execute("SELECT Rental_ID FROM rental ORDER BY Rental_ID DESC LIMIT 1")
        last_rental = cursor.fetchone()
        if last_rental:
            last_rental_id = int(last_rental["Rental_ID"].replace("RENT", ""))
            new_rental_id = f"RENT{last_rental_id + 1:05d}"
        else:
            new_rental_id = "RENT00001"  # Start with RENT00001 if no records exist

        # Step 3: Insert the new rental record (new rental transaction)
        cursor.execute("""
            INSERT INTO rental (Rental_ID, Vehicle_ID, Customer_ID, Rental_StartDate, Rental_EndDate, Total_Price, Payment_Status, Rental_Status)
            VALUES (?, ?, ?, ?, ?, ?, 'Unpaid', 'Pending')
        """, (new_rental_id, vehicle_id, session['user_id'], rental_startdate, rental_enddate, total_price))

        # Step 4: Update the vehicle status to 'Rented' so it won't appear in available vehicles
        cursor.execute("UPDATE vehicle SET Vehicle_Status = 'Rented' WHERE Vehicle_ID = ?", (vehicle_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'new_rental_id': new_rental_id})
    except Exception as e:
        print(f"Error booking vehicle: {e}")
        return jsonify({'success': False, 'error': str(e)})




@app.route("/bookings")
@login_required
def bookings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch bookings only for the logged-in client
        cursor.execute("""
            SELECT
                r.Rental_ID AS "Rental ID",
                c.Full_Name AS "Customer Name",
                v.Vehicle_Name AS "Vehicle",
                r.Rental_StartDate AS "Start Date",
                r.Rental_EndDate AS "End Date",
                r.Payment_Status AS "Payment Status",
                r.Rental_Status AS "Status"
            FROM rental r
            JOIN customer c ON r.Customer_ID = c.Customer_ID
            JOIN vehicle v ON r.Vehicle_ID = v.Vehicle_ID
            WHERE c.Customer_ID = ?
            ORDER BY r.Rental_StartDate DESC
        """, (session['user_id'],))

        bookings_data = cursor.fetchall()
        conn.close()

        # Pass the filtered bookings to the template
        return render_template("bookings.html", bookings=bookings_data)

    except Exception as e:
        print(f"Error fetching bookings: {e}")
        return render_template("bookings.html", bookings=[], error="Error loading bookings.")

@app.route('/pay_rental/<rental_id>', methods=['POST'])
@login_required
def pay_rental(rental_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update Payment_Status to 'Paid'
        cursor.execute("""
            UPDATE rental
            SET Payment_Status = 'Paid'
            WHERE Rental_ID = ?
        """, (rental_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error processing payment: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_rental/<rental_id>', methods=['DELETE'])
@login_required
def delete_rental(rental_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the rental record based on Rental_ID
        cursor.execute("DELETE FROM rental WHERE Rental_ID = ?", (rental_id,))

        # Optionally, you could update the vehicle status back to 'Available' after deleting the rental record
        cursor.execute("UPDATE vehicle SET Vehicle_Status = 'Available' WHERE Vehicle_ID = (SELECT Vehicle_ID FROM rental WHERE Rental_ID = ?)", (rental_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error deleting rental: {e}")
        return jsonify({'success': False, 'error': str(e)})

# @app.route('/cancel_rental/<rental_id>', methods=['POST'])
# @login_required
# def cancel_rental(rental_id):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Update the vehicle status back to 'Available' after canceling the rental
#         cursor.execute("""
#             UPDATE vehicle
#             SET Vehicle_Status = 'Available'
#             WHERE Vehicle_ID = (SELECT Vehicle_ID FROM rental WHERE Rental_ID = ?)
#         """, (rental_id,))

#         # Optionally, mark the rental status as 'Cancelled' instead of deleting the record
#         cursor.execute("""
#             UPDATE rental
#             SET Rental_Status = 'Cancelled'
#             WHERE Rental_ID = ?
#         """, (rental_id,))

#         conn.commit()
#         conn.close()

#         return jsonify({'success': True})
#     except Exception as e:
#         print(f"Error canceling rental: {e}")
#         return jsonify({'success': False, 'error': str(e)})



@app.route("/manage")
@login_required
def manage_bookings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch bookings only for the logged-in client
        cursor.execute("""
            SELECT
                r.Rental_ID AS "Rental ID",
                c.Full_Name AS "Customer Name",
                v.Vehicle_Name AS "Vehicle",
                r.Rental_StartDate AS "Start Date",
                r.Rental_EndDate AS "End Date",
                r.Rental_Status AS "Status"
            FROM rental r
            JOIN customer c ON r.Customer_ID = c.Customer_ID
            JOIN vehicle v ON r.Vehicle_ID = v.Vehicle_ID
            WHERE c.Customer_ID = ?
            ORDER BY r.Rental_StartDate DESC
        """, (session['user_id'],))

        bookings_data = cursor.fetchall()
        conn.close()

        # Pass the filtered bookings to the template
        return render_template("manage.html", bookings=bookings_data)
    except Exception as e:
        print(f"Error fetching bookings for manage page: {e}")
        return render_template("manage.html", bookings=[], error="Error loading bookings.")


@app.route('/update_booking/<rental_id>', methods=['POST'])
@login_required
def update_booking(rental_id):
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'success': False, 'error': 'Start and end dates are required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the original rental period and cost
        cursor.execute("""
            SELECT Rental_StartDate, Rental_EndDate, Total_Price
            FROM rental WHERE Rental_ID = ?
        """, (rental_id,))
        rental = cursor.fetchone()

        if not rental:
            return jsonify({'success': False, 'error': 'Rental not found.'}), 404

        original_start_date = rental["Rental_StartDate"]
        original_end_date = rental["Rental_EndDate"]
        original_price = rental["Total_Price"]

        # Calculate extra days and cost
        original_days = (datetime.strptime(original_end_date, "%Y-%m-%d") - datetime.strptime(original_start_date, "%Y-%m-%d")).days
        new_days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
        extra_days = max(0, new_days - original_days)

        # Assume a daily rate for additional cost
        daily_rate = original_price / original_days
        extra_cost = extra_days * daily_rate

        # Update the booking in the database
        cursor.execute("""
            UPDATE rental
            SET Rental_StartDate = ?, Rental_EndDate = ?, Total_Price = Total_Price + ?
            WHERE Rental_ID = ?
        """, (start_date, end_date, extra_cost, rental_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'extra_cost': extra_cost})
    except Exception as e:
        print(f"Error updating booking: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route("/")
@login_required
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer")
    customer_data = cursor.fetchall()
    cursor.execute("SELECT * FROM rental")
    rental_data = cursor.fetchall()
    cursor.execute("SELECT * FROM vehicle")
    vehicle_data = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", customer=customer_data, rental=rental_data, vehicle=vehicle_data)

@app.route("/get_table_data/<table_name>")
@login_required
def get_table_data(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    column_names = [info[1] for info in columns_info]
    primary_key_column = next((col[1] for col in columns_info if col[5] == 1), 'id')

    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()

    results = []
    for row in data:
        results.append(dict(zip(column_names, row)))

    return jsonify({
        "columns": column_names,
        "data": results,
        'primary_key': primary_key_column
    })

@app.route('/get_record/<table_name>/<record_id>', methods=['GET'])
def get_record(table_name, record_id):
    if table_name not in ['rental', 'customer', 'vehicle']:
        return jsonify({'success': False, 'message': 'Invalid table name'})

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]

    if table_name == 'rental':
        pk_column = 'Rental_ID'
    elif table_name == 'customer':
        pk_column = 'Customer_ID'
    elif table_name == 'vehicle':
        pk_column = 'Vehicle_ID'

    sql = f"SELECT * FROM {table_name} WHERE {pk_column} = ?"
    cur.execute(sql, (record_id,))
    record = cur.fetchone()
    conn.close()

    if record:
        record_dict = dict(zip(columns, record))
        return jsonify(record_dict)
    else:
        return jsonify({'success': False, 'message': 'Record not found'})

@app.route("/get_table_schema/<table_name>")
@login_required
def get_table_schema(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    conn.close()

    columns = [{'name': info[1], 'type': info[2]} for info in columns_info]
    return jsonify(columns)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    return render_template("add.html")

def validate_id_format(field_name, value):
    """
    Validate the format of IDs based on field names.
    """
    id_patterns = {
        "Rental_ID": {
            "pattern": r"^RENT\d{1,11}$",
            "format": "RENT00000"
        },
        "Customer_ID": {
            "pattern": r"^CUST\d{1,6}$",
            "format": "CUST0000"
        },
        "Vehicle_ID": {
            "pattern": r"^Vehicle\d{1,3}$",
            "format": "Vehicle000"
        }
    }

    if field_name in id_patterns:
        pattern = id_patterns[field_name]["pattern"]
        expected_format = id_patterns[field_name]["format"]
        if not re.match(pattern, value):
            return f"{field_name} must follow the format {expected_format}"

    return None

def validate_datatypes(table_name, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    conn.close()

    errors = []
    for column_info in columns_info:
        column_name = column_info[1]
        column_type = column_info[2]
        if column_name in data:
            value = data[column_name]
            if column_type == "INTEGER" and not value.isdigit():
                errors.append(f"{column_name} must be an integer.")
            elif column_type == "REAL" and not re.match(r"^\d+(\.\d+)?$", value):
                errors.append(f"{column_name} must be a real number.")
            elif column_type == "TEXT" and not isinstance(value, str):
                errors.append(f"{column_name} must be text.")
            elif column_type == "DATE" and not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                errors.append(f"{column_name} must be in YYYY-MM-DD format.")
    return errors

def check_for_duplicates(table_name, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    errors = []

    if table_name == "customer":
        cursor.execute("""
            SELECT * FROM customer WHERE Customer_ID = ? OR Full_Name = ? OR Email = ? OR Phone_Number = ? OR Drivers_License = ?
        """, (data["Customer_ID"], data["Full_Name"], data["Email"], data["Phone_Number"], data["Drivers_License"]))
        if cursor.fetchone():
            errors.append("Duplicate customer record: Customer_ID, Full_Name, Email, Phone_Number, or Drivers_License already exists.")

    elif table_name == "rental":
        if "Rental_ID" in data:
            cursor.execute("SELECT * FROM rental WHERE Rental_ID = ?", (data["Rental_ID"],))
            if cursor.fetchone():
                errors.append(f"Duplicate Rental_ID: {data['Rental_ID']} already exists.")

    elif table_name == "vehicle":
        if "Vehicle_ID" in data:
            cursor.execute("SELECT * FROM vehicle WHERE Vehicle_ID = ?", (data["Vehicle_ID"],))
            if cursor.fetchone():
                errors.append(f"Duplicate Vehicle_ID: {data['Vehicle_ID']} already exists.")

    conn.close()
    return errors

def validate_foreign_keys(table_name, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    errors = []

    if table_name == "rental":
        if "Customer_ID" in data:
            fk_value = data["Customer_ID"]
            cursor.execute("SELECT * FROM customer WHERE Customer_ID = ?", (fk_value,))
            if not cursor.fetchone():
                errors.append(f"Referential integrity violated: No matching Customer_ID {fk_value}")

        if "Vehicle_ID" in data:
            fk_value = data["Vehicle_ID"]
            cursor.execute("SELECT * FROM vehicle WHERE Vehicle_ID = ?", (fk_value,))
            if not cursor.fetchone():
                errors.append(f"Referential integrity violated: No matching Vehicle_ID {fk_value}")

    conn.close()
    return errors

@app.route('/add_record', methods=['POST'])
def add_record():
    data = request.json
    table_name = data.pop('table')

    missing_fields = [field for field, value in data.items() if not value]
    if missing_fields:
        return jsonify({'success': False, 'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400

    datatype_errors = validate_datatypes(table_name, data)
    if datatype_errors:
        return jsonify({'success': False, 'error': " | ".join(datatype_errors)}), 400

    id_errors = []
    for key, value in data.items():
        if key in ["Rental_ID", "Customer_ID", "Vehicle_ID"]:
            error = validate_id_format(key, value)
            if error:
                id_errors.append(error)

    if id_errors:
        return jsonify({'success': False, 'error': " | ".join(id_errors)}), 400

    fk_errors = validate_foreign_keys(table_name, data)
    if fk_errors:
        return jsonify({'success': False, 'error': " | ".join(fk_errors)}), 400

    duplicate_errors = check_for_duplicates(table_name, data)
    if duplicate_errors:
        return jsonify({'success': False, 'error': " | ".join(duplicate_errors)}), 400

    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.keys()])
    values = tuple(data.values())

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': "Record added successfully"}), 201

@app.route("/mysql")
@login_required
def mysql():
    return render_template("mysql.html")

@app.route('/update')
@login_required
def edit_record():
    return render_template('update.html')

@app.route('/update_record/<table_name>/<pk_value>', methods=['POST'])
def update_record(table_name, pk_value):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        column_types = {col[1]: col[2] for col in columns_info}

        primary_key_column = next((col[1] for col in columns_info if col[5] == 1), 'id')
        cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key_column} = ?", (pk_value,))
        record = cursor.fetchone()
        if not record:
            return jsonify({
                'success': False,
                'message': f'Record with {primary_key_column} = {pk_value} does not exist'
            }), 404

        update_data = request.json
        invalid_columns = [key for key in update_data.keys() if key not in column_names]
        if invalid_columns:
            return jsonify({
                'success': False,
                'message': f'Invalid columns in update request: {", ".join(invalid_columns)}'
            }), 400

        if not update_data:
            return jsonify({
                'success': False,
                'message': 'No data provided for update'
            }), 400

        validated_data = {}
        datatype_errors = []
        for key, value in update_data.items():
            expected_type = column_types[key].upper()

            try:
                if expected_type == "INTEGER":
                    if not str(value).isdigit():
                        raise ValueError(f"{key} must be an integer.")
                    validated_data[key] = int(value)
                elif expected_type == "REAL":
                    try:
                        validated_data[key] = float(value)
                    except ValueError:
                        raise ValueError(f"{key} must be a real number.")
                elif expected_type == "TEXT":
                    if not isinstance(value, str):
                        raise ValueError(f"{key} must be text.")
                    validated_data[key] = value
                elif expected_type == "DATE":
                    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                        raise ValueError(f"{key} must be in YYYY-MM-DD format.")
                    validated_data[key] = value
                else:
                    validated_data[key] = value
            except ValueError as e:
                datatype_errors.append(str(e))

        if datatype_errors:
            return jsonify({
                'success': False,
                'message': " | ".join(datatype_errors)
            }), 400

        id_errors = [
            validate_id_format(key, value)
            for key, value in update_data.items()
            if key in ["Rental_ID", "Customer_ID", "Vehicle_ID"]
        ]
        id_errors = [error for error in id_errors if error is not None]
        if id_errors:
            return jsonify({'success': False, 'message': " | ".join(id_errors)}), 400

        set_clause = ', '.join([f"{key} = ?" for key in validated_data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key_column} = ?"

        cursor.execute(sql, (*validated_data.values(), pk_value))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Record with {primary_key_column} = {pk_value} updated successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error occurred while updating record: {str(e)}'
        }), 500

@app.route('/delete_record/<table_name>/<pk_value>', methods=['DELETE'])
def delete_record(table_name, pk_value):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        primary_key_column = next((col[1] for col in columns_info if col[5] == 1), 'id')

        cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key_column} = ?", (pk_value,))
        record = cursor.fetchone()
        if not record:
            return jsonify({
                'success': False,
                'message': f'Record with {primary_key_column} = {pk_value} does not exist'
            }), 404

        cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key_column} = ?", (pk_value,))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Record with {primary_key_column} = {pk_value} deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error occurred while deleting record: {str(e)}'
        }), 500

@app.route("/active_clients", methods=["GET"])
def active_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute("""
        SELECT
            Customer_ID AS "Client ID",
            Vehicle_ID AS "Vehicle ID",
            date(Rental_StartDate) AS "Rental Start Date",
            date(Rental_EndDate) AS "Rental End Date"
        FROM rental
        WHERE ? BETWEEN date(Rental_StartDate) AND date(Rental_EndDate)
        ORDER BY Rental_StartDate

    """, (today,))
    active_clients_data = cursor.fetchall()
    conn.close()
    return jsonify([
        {
            "Client ID": row["Client ID"],
            "Vehicle ID": row["Vehicle ID"],
            "Rental Start Date": row["Rental Start Date"],
            "Rental End Date": row["Rental End Date"]
        }
        for row in active_clients_data
    ])

@app.route("/current_rentals", methods=["GET"])
def current_rentals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            r.Rental_ID AS "Rental ID",
            c.Full_Name AS "Customer",
            c.Phone_Number AS "Contact Number",
            r.Rental_Status AS "Payment Status"
        FROM rental r
        JOIN customer c ON r.Customer_ID = c.Customer_ID
        ORDER BY
            CASE r.Rental_Status
                WHEN 'Pending' THEN 1
                WHEN 'Completed' THEN 2
                WHEN 'Cancelled' THEN 3
                ELSE 4
            END, r.Rental_ID
    """)
    current_rentals_data = cursor.fetchall()
    conn.close()
    return jsonify([
        {
            "Rental ID": row["Rental ID"],
            "Customer": row["Customer"],
            "Contact Number": row["Contact Number"],
            "Payment Status": row["Payment Status"]
        }
        for row in current_rentals_data
    ])

@app.route("/available_vehicles", methods=["GET"])
def available_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Vehicle_ID, Vehicle_Name, Vehicle_Status
        FROM vehicle
        WHERE Vehicle_Status = 'Available'
    """)
    available_vehicles_data = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in available_vehicles_data])

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect("/login")

def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(debug=True)
