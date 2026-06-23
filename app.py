from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "service_management_secret_key"

DATABASE = "database.db"


# ==========================
# DATABASE CONNECTION
# ==========================
# ==========================
# DATABASE CONNECTION
# ==========================
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# CREATE TABLES
# ==========================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'customer',
    phone TEXT,
    address TEXT,
    profession TEXT,
    experience TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
    """)

    # Services Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        image TEXT
    )
    """)

    # Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        worker_id INTEGER,
        service_name TEXT,
        phone TEXT,
        address TEXT,
        booking_date TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(worker_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# ==========================
# CREATE DEFAULT ADMIN
# ==========================
def create_admin():
    conn = get_db_connection()

    admin = conn.execute(
        "SELECT * FROM users WHERE role='admin'"
    ).fetchone()

    if not admin:
        conn.execute("""
        INSERT INTO users
        (name,email,password,role,status)
        VALUES(?,?,?,?,?)
        """,
        (
            "Admin",
            "admin@gmail.com",
            generate_password_hash("admin123"),
            "admin",
            "approved"
        ))

        conn.commit()

    conn.close()


# Run Database Setup
init_db()
create_admin()


# ==========================
# HOME PAGE
# ==========================
@app.route("/")
def home():
    services = [
        "Home Cleaning",
        "Deep Cleaning",
        "Electrician",
        "Plumber",
        "AC Repair",
        "AC Installation",
        "Refrigerator Repair",
        "Washing Machine Repair",
        "RO Water Purifier Service",
        "Pest Control",
        "Painting",
        "Carpentry",
        "Bathroom Cleaning",
        "Kitchen Cleaning",
        "Salon at Home",
        "Spa at Home"
    ]

    return render_template("index.html", services=services)


# ==========================
# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        phone = request.form["phone"]
        address = request.form["address"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                phone,
                address,
                role,
                status
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                name,
                email,
                hashed_password,
                phone,
                address,
                "customer",
                "approved"
            ))

            conn.commit()

            flash(
                "Registration Successful. You can Login Now.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "Email Already Exists",
                "danger"
            )

        finally:

            conn.close()

    return render_template("auth/register.html")




@app.route("/worker-register", methods=["GET", "POST"])
def worker_register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        phone = request.form["phone"]
        address = request.form["address"]

        profession = request.form["profession"]
        experience = request.form["experience"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                phone,
                address,
                profession,
                experience,
                role,
                status
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                name,
                email,
                hashed_password,
                phone,
                address,
                profession,
                experience,
                "worker",
                "pending"
            ))

            conn.commit()

            flash(
                "Registration Submitted. Wait for Admin Approval.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "Email Already Exists",
                "danger"
            )

        finally:

            conn.close()

    return render_template("auth/worker_register.html")

@app.route("/worker-dashboard")
def worker_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "worker":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    assigned_jobs = conn.execute("""
        SELECT *
        FROM bookings
        WHERE worker_id=?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "worker/dashboard.html",
        assigned_jobs=assigned_jobs
    )



# ==========================
# LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user:

            if check_password_hash(
                user["password"],
                password
            ):

                # Worker must be approved by Admin
                if user["role"] == "worker" and user["status"] != "approved":

                    flash(
                        "Your worker account is waiting for Admin Approval.",
                        "warning"
                    )

                    return redirect(url_for("login"))

                # Create Session
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["role"] = user["role"]

                flash(
                    "Login Successful",
                    "success"
                )

                # Admin Login
                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))

                # Worker Login
                elif user["role"] == "worker":
                    return redirect(url_for("worker_dashboard"))

                # Customer Login
                else:
                    return redirect(url_for("dashboard"))

        flash(
            "Invalid Email or Password",
            "danger"
        )

    return render_template("auth/login.html")


# ==========================
# LOGOUT
# ==========================
@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully", "info")

    return redirect(url_for("home"))



@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "customer":
        return redirect(url_for("login"))

    return render_template(
        "customer/dashboard.html",
        customer_name=session["user_name"]
    )


# ==========================
# SERVICES PAGE
# ==========================
@app.route("/services")
def services():

    services_list = [
        "Home Cleaning",
        "Deep Cleaning",
        "Electrician",
        "Plumber",
        "AC Repair",
        "AC Installation",
        "Refrigerator Repair",
        "Washing Machine Repair",
        "RO Water Purifier Service",
        "Pest Control",
        "Painting",
        "Carpentry",
        "Bathroom Cleaning",
        "Kitchen Cleaning",
        "Salon at Home",
        "Spa at Home"
    ]

    return render_template(
        "customer/services.html",
        services=services_list
    )


# ==========================
# BOOKINGS
# ==========================
@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    bookings = conn.execute("""
    SELECT * FROM bookings
    WHERE user_id=?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "customer/bookings.html",
        bookings=bookings
    )



# ==========================
# BOOK SERVICE
# ==========================
@app.route("/book-service", methods=["GET", "POST"])
def book_service():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        service_name = request.form["service_name"]
        phone = request.form["phone"]
        address = request.form["address"]
        booking_date = request.form["booking_date"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO bookings(
                user_id,
                service_name,
                phone,
                address,
                booking_date
            )
            VALUES (?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            service_name,
            phone,
            address,
            booking_date
        ))

        conn.commit()
        conn.close()

        flash("Booking Submitted Successfully", "success")

        return redirect(url_for("my_bookings"))

    return render_template("customer/booking.html")





# ==========================
# ADMIN DASHBOARD
# ==========================
@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        flash("Access Denied", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    # User Statistics
    total_customers = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='customer'"
    ).fetchone()[0]

    total_workers = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='worker'"
    ).fetchone()[0]

    pending_users = conn.execute(
        "SELECT COUNT(*) FROM users WHERE status='pending'"
    ).fetchone()[0]

    approved_users = conn.execute(
        "SELECT COUNT(*) FROM users WHERE status='approved'"
    ).fetchone()[0]

    # Booking Statistics
    total_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings"
    ).fetchone()[0]

    pending_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE status='Pending'"
    ).fetchone()[0]

    completed_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE status='Completed'"
    ).fetchone()[0]

    # Services Count
    total_services = conn.execute(
        "SELECT COUNT(*) FROM services"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_customers=total_customers,
        total_workers=total_workers,
        pending_users=pending_users,
        approved_users=approved_users,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        total_services=total_services
    )

@app.route("/admin-users")
def admin_users():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    users = conn.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()

    total_customers = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='customer'
    """).fetchone()[0]

    total_workers = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role='worker'
    """).fetchone()[0]

    pending_users = conn.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE status='pending'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin/users.html",
        users=users,
        total_customers=total_customers,
        total_workers=total_workers,
        pending_users=pending_users
    )

@app.route("/approve-user/<int:id>")
def approve_user(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Approved Successfully", "success")

    return redirect(url_for("admin_users"))


@app.route("/reject-user/<int:id>")
def reject_user(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='rejected' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Rejected", "danger")

    return redirect(url_for("admin_users"))

@app.route("/delete-user/<int:id>")
def delete_user(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Deleted Successfully", "success")

    return redirect(url_for("admin_users"))

@app.route("/admin-services")
def admin_services():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    services = conn.execute("""
        SELECT *
        FROM services
        ORDER BY id DESC
    """).fetchall()

    total_services = conn.execute("""
        SELECT COUNT(*)
        FROM services
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin/services.html",
        services=services,
        total_services=total_services
    )


@app.route("/delete-service/<int:id>")
def delete_service(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM services WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Service Deleted Successfully", "success")

    return redirect(url_for("admin_services"))


@app.route("/edit-service/<int:id>", methods=["GET", "POST"])
def edit_service(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    if request.method == "POST":

        service_name = request.form["service_name"]
        category = request.form["category"]
        description = request.form["description"]

        conn.execute("""
            UPDATE services
            SET service_name=?,
                category=?,
                description=?
            WHERE id=?
        """,
        (
            service_name,
            category,
            description,
            id
        ))

        conn.commit()

        flash("Service Updated Successfully", "success")

        conn.close()

        return redirect(url_for("admin_services"))

    service = conn.execute(
        "SELECT * FROM services WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "admin/edit_service.html",
        service=service
    )



@app.route("/admin-bookings")
def admin_bookings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    bookings = conn.execute("""
        SELECT *
        FROM bookings
        ORDER BY id DESC
    """).fetchall()

    total_bookings = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
    """).fetchone()[0]

    pending_bookings = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Pending'
    """).fetchone()[0]

    accepted_bookings = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Accepted'
    """).fetchone()[0]

    completed_bookings = conn.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Completed'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
        completed_bookings=completed_bookings
    )


@app.route("/cancel-booking/<int:id>")
def cancel_booking(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE bookings SET status='Cancelled' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Booking Cancelled", "warning")

    return redirect(url_for("admin_bookings"))

@app.route("/assign-worker/<int:booking_id>/<int:worker_id>")
def assign_worker(booking_id, worker_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE bookings
        SET worker_id=?,
            status='Assigned'
        WHERE id=?
    """,
    (
        worker_id,
        booking_id
    ))

    conn.commit()
    conn.close()

    flash(
        "Worker Assigned Successfully",
        "success"
    )

    return redirect(url_for("admin_bookings"))



@app.route("/accept-booking/<int:id>")
def accept_booking(id):

    conn = get_db_connection()

    conn.execute(
        "UPDATE bookings SET status='Accepted' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_bookings"))


@app.route("/complete-booking/<int:id>")
def complete_booking(id):

    conn = get_db_connection()

    conn.execute(
        "UPDATE bookings SET status='Completed' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_bookings"))
# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)