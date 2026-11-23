from functools import wraps
import hmac
import os
import secrets
import sqlite3
from flask import Flask, abort, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app_environment = os.environ.get("APP_ENV", "development")
secret_key = os.environ.get("SECRET_KEY")

if app_environment == "production" and not secret_key:
    raise RuntimeError("SECRET_KEY must be configured in production.")

app.config.update(
    SECRET_KEY=secret_key or "local-development-only-secret",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=app_environment == "production",
)

DATABASE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
)


# ==========================
# DATABASE CONNECTION
# ==========================
# ==========================
# DATABASE CONNECTION
# ==========================
def get_db_connection():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def role_required(role, approved_worker=False):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if user_id is None:
                return redirect(url_for("login", next=request.path))

            conn = get_db_connection()
            user = conn.execute(
                "SELECT role, status FROM users WHERE id=?",
                (user_id,)
            ).fetchone()
            conn.close()

            if user is None:
                session.clear()
                return redirect(url_for("login"))

            if user["role"] != role:
                abort(403)

            if approved_worker and user["status"] != "approved":
                abort(403)

            return view(*args, **kwargs)

        return wrapped
    return decorator


def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": generate_csrf_token}


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        expected_token = session.get("csrf_token")
        submitted_token = request.form.get("csrf_token")
        if (
            not expected_token
            or not submitted_token
            or not hmac.compare_digest(expected_token, submitted_token)
        ):
            abort(400, description="Invalid or missing CSRF token.")


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

    category TEXT,

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
    if app_environment == "production":
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if not admin_email and not admin_password:
            app.logger.warning(
                "ADMIN_EMAIL and ADMIN_PASSWORD are unset; skipping admin creation."
            )
            return

        if not admin_email or not admin_password:
            raise RuntimeError(
                "ADMIN_EMAIL and ADMIN_PASSWORD must both be configured."
            )
    else:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

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
            admin_email,
            generate_password_hash(admin_password),
            "admin",
            "approved"
        ))

        conn.commit()

    conn.close()


# Run Database Setup
init_db()
create_admin()
# ==========================
# DATABASE UPDATE
# ==========================
conn = get_db_connection()

try:
    conn.execute(
        "ALTER TABLE bookings ADD COLUMN category TEXT"
    )

    conn.execute(
        "UPDATE bookings SET category = service_name"
    )

    conn.commit()

    print("Category column added successfully")

except Exception as e:
    print("Database already updated:", e)

conn.close()



# ==========================
# HOME PAGE
# ==========================
@app.route("/health")
def health():
    conn = get_db_connection()
    try:
        conn.execute("SELECT 1")
    finally:
        conn.close()

    return {"status": "ok"}


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
@role_required("worker", approved_worker=True)
def worker_dashboard():



    if "user_id" not in session:

        return redirect(url_for("login"))



    if session.get("role") != "worker":

        return redirect(url_for("dashboard"))



    conn = get_db_connection()



    # Get worker details

    worker = conn.execute(

        "SELECT * FROM users WHERE id=?",

        (session["user_id"],)

    ).fetchone()



    if worker is None:

        conn.close()

        flash("Worker not found.", "danger")

        return redirect(url_for("login"))



    # Filter from buttons

    status = request.args.get("status")



    if status:



        assigned_jobs = conn.execute("""

            SELECT *

            FROM bookings

            WHERE category=?

            AND worker_id=?

            AND status=?

        """,

        (

            worker["profession"],

            session["user_id"],

            status

        )).fetchall()



    else:



        assigned_jobs = conn.execute("""

            SELECT *

            FROM bookings

            WHERE category=?

            AND (

                status='Pending'

                OR worker_id=?

            )

        """,

        (

            worker["profession"],

            session["user_id"]

        )).fetchall()



    # Dashboard Statistics

    total_jobs = conn.execute("""

        SELECT COUNT(*)

        FROM bookings

        WHERE category=?

        AND (

            status='Pending'

            OR worker_id=?

        )

    """,

    (

        worker["profession"],

        session["user_id"]

    )).fetchone()[0]



    pending_jobs = conn.execute("""

        SELECT COUNT(*)

        FROM bookings

        WHERE category=?

        AND status='Pending'

    """,

    (

        worker["profession"],

    )).fetchone()[0]



    accepted_jobs = conn.execute("""

        SELECT COUNT(*)

        FROM bookings

        WHERE worker_id=?

        AND status='Accepted'

    """,

    (

        session["user_id"],

    )).fetchone()[0]



    completed_jobs = conn.execute("""

        SELECT COUNT(*)

        FROM bookings

        WHERE worker_id=?

        AND status='Completed'

    """,

    (

        session["user_id"],

    )).fetchone()[0]



    conn.close()



    return render_template(

        "provider/provider_dashboard.html",

        worker=worker,

        assigned_jobs=assigned_jobs,

        total_jobs=total_jobs,

        pending_jobs=pending_jobs,

        accepted_jobs=accepted_jobs,

        completed_jobs=completed_jobs

    )




@app.route("/worker-reject/<int:id>", methods=["POST"])
@role_required("worker", approved_worker=True)
def worker_reject(id):
    conn = get_db_connection()
    worker = conn.execute(
        "SELECT profession FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    booking = conn.execute(
        "SELECT * FROM bookings WHERE id=? AND category=?",
        (id, worker["profession"])
    ).fetchone()

    if not booking or booking["status"] != "Pending":
        conn.close()
        abort(404)

    result = conn.execute("""
        UPDATE bookings
        SET status='Rejected'
        WHERE id=? AND category=? AND status='Pending' AND worker_id IS NULL
    """,
    (
        id,
        worker["profession"]
    ))

    conn.commit()
    conn.close()

    if result.rowcount:
        flash("Job Rejected Successfully", "warning")
    else:
        flash("This job is no longer available.", "warning")

    return redirect(url_for("worker_dashboard"))


@app.route("/worker-accept/<int:id>", methods=["POST"])
@role_required("worker", approved_worker=True)
def worker_accept(id):
    conn = get_db_connection()
    worker = conn.execute(
        "SELECT profession FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    booking = conn.execute(
        "SELECT * FROM bookings WHERE id=? AND category=?",
        (id, worker["profession"])
    ).fetchone()

    if not booking or booking["status"] != "Pending":
        conn.close()
        abort(404)

    result = conn.execute("""
        UPDATE bookings
        SET worker_id=?,
            status='Accepted'
        WHERE id=? AND category=? AND status='Pending' AND worker_id IS NULL
    """,
    (
        session["user_id"],
        id,
        worker["profession"]
    ))

    conn.commit()
    conn.close()

    if result.rowcount:
        flash("Job Accepted Successfully", "success")
    else:
        flash("This job has already been taken.", "warning")

    return redirect(url_for("worker_dashboard"))


@app.route("/worker-complete/<int:id>", methods=["POST"])
@role_required("worker", approved_worker=True)
def worker_complete(id):
    conn = get_db_connection()
    result = conn.execute("""
        UPDATE bookings
        SET status='Completed'
        WHERE id=? AND worker_id=? AND status='Accepted'
    """,
    (
        id,
        session["user_id"]
    ))
    conn.commit()
    conn.close()
    if not result.rowcount:
        abort(404)
    flash("Job Completed Successfully", "success")
    return redirect(url_for("worker_dashboard"))

@app.route("/provider-profile", methods=["GET", "POST"])
@role_required("worker")
def provider_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        worker = conn.execute(
            "SELECT profession FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()
        profession = request.form["profession"]
        profession_changed = profession != worker["profession"]

        if profession_changed:
            conn.execute("""
                UPDATE users
                SET name=?,
                    phone=?,
                    address=?,
                    profession=?,
                    experience=?,
                    status='pending'
                WHERE id=?
            """,
            (
                request.form["name"],
                request.form["phone"],
                request.form["address"],
                profession,
                request.form["experience"],
                session["user_id"]
            ))
        else:
            conn.execute("""
                UPDATE users
                SET name=?,
                    phone=?,
                    address=?,
                    profession=?,
                    experience=?
                WHERE id=?
            """,
            (
                request.form["name"],
                request.form["phone"],
                request.form["address"],
                profession,
                request.form["experience"],
                session["user_id"]
            ))

        conn.commit()

        if profession_changed:
            flash(
                "Profession change submitted for Admin approval. Worker actions are disabled until approval.",
                "warning"
            )
        else:
            flash(
                "Profile Updated Successfully",
                "success"
            )

    worker = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "provider/provider_profile.html",
        worker=worker
    )


@app.route('/profile')
@role_required("customer")
def profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    conn.close()

    return render_template(
        'customer/profile.html',
        user=user
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
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["role"] = user["role"]

                next_page = request.form.get("next")
                if (
                    session["role"] == "customer"
                    and next_page == url_for("book_service")
                ):
                    return redirect(next_page)

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
@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash("Logged Out Successfully", "info")

    return redirect(url_for("home"))



@app.route("/dashboard")
@role_required("customer")
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
@role_required("customer")
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
@app.route("/user-cancel-booking/<int:id>", methods=["POST"])
@role_required("customer")
def user_cancel_booking(id):
    conn = get_db_connection()

    result = conn.execute(
        """
        UPDATE bookings
        SET status='Cancelled'
        WHERE id=? AND user_id=? AND status IN ('Pending', 'Accepted', 'Assigned')
        """,
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    if result.rowcount:
        flash("Booking Cancelled Successfully", "success")
    else:
        flash("This booking cannot be cancelled.", "warning")

    return redirect(url_for("my_bookings"))


# ==========================
# BOOK SERVICE
# ==========================
@app.route("/book-service", methods=["GET", "POST"])
@role_required("customer")
def book_service():

    if request.method == "POST":

        service_name = request.form["service_name"]

        # ==========================
        # Profession Mapping
        # ==========================
        if service_name in ["AC Repair", "AC Installation"]:
            category = "AC Technician"

        elif service_name == "Refrigerator Repair":
            category = "Refrigerator Technician"

        elif service_name == "Washing Machine Repair":
            category = "Washing Machine Technician"

        elif service_name == "Electrician":
            category = "Electrician"

        elif service_name == "Plumber":
            category = "Plumber"

        elif service_name in [
            "Home Cleaning",
            "Deep Cleaning",
            "Bathroom Cleaning",
            "Kitchen Cleaning"
        ]:
            category = "Cleaning Specialist"

        elif service_name == "Painting":
            category = "Painter"

        elif service_name == "Carpentry":
            category = "Carpenter"

        elif service_name == "RO Water Purifier Service":
            category = "RO Technician"

        elif service_name == "Salon at Home":
            category = "Beautician"

        elif service_name == "Spa at Home":
            category = "Spa Therapist"

        elif service_name == "Pest Control":
            category = "Pest Control Specialist"

        else:
            category = service_name

        phone = request.form["phone"]
        address = request.form["address"]
        booking_date = request.form["booking_date"]

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO bookings (
                user_id,
                service_name,
                category,
                phone,
                address,
                booking_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            service_name,
            category,
            phone,
            address,
            booking_date
        ))

        conn.commit()
        conn.close()

        flash(
            "Booking Submitted Successfully",
            "success"
        )

        return redirect(url_for("my_bookings"))

    return render_template("customer/booking.html")





# ==========================
# ADMIN DASHBOARD
# ==========================
@app.route("/admin")
@role_required("admin")
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
@role_required("admin")
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

@app.route("/approve-user/<int:id>", methods=["POST"])
@role_required("admin")
def approve_user(id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Approved Successfully", "success")

    return redirect(url_for("admin_users"))


@app.route("/reject-user/<int:id>", methods=["POST"])
@role_required("admin")
def reject_user(id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='rejected' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Rejected", "danger")

    return redirect(url_for("admin_users"))

@app.route("/delete-user/<int:id>", methods=["POST"])
@role_required("admin")
def delete_user(id):
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
@role_required("admin")
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


@app.route("/delete-service/<int:id>", methods=["POST"])
@role_required("admin")
def delete_service(id):
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
@role_required("admin")
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
@role_required("admin")
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


@app.route("/cancel-booking/<int:id>", methods=["POST"])
@role_required("admin")
def cancel_booking(id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE bookings SET status='Cancelled' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Booking Cancelled", "warning")

    return redirect(url_for("admin_bookings"))

@app.route(
    "/assign-worker/<int:booking_id>/<int:worker_id>",
    methods=["POST"]
)
@role_required("admin")
def assign_worker(booking_id, worker_id):
    conn = get_db_connection()

    worker = conn.execute(
        "SELECT profession FROM users WHERE id=? AND role='worker' AND status='approved'",
        (worker_id,)
    ).fetchone()
    booking = conn.execute(
        "SELECT category FROM bookings WHERE id=? AND status='Pending'",
        (booking_id,)
    ).fetchone()

    if not worker or not booking or worker["profession"] != booking["category"]:
        conn.close()
        abort(404)

    conn.execute("""
        UPDATE bookings
        SET worker_id=?,
            status='Assigned'
        WHERE id=? AND status='Pending'
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



@app.route("/accept-booking/<int:id>", methods=["POST"])
@role_required("admin")
def accept_booking(id):

    conn = get_db_connection()

    result = conn.execute(
        "UPDATE bookings SET status='Accepted' WHERE id=? AND status='Pending'",
        (id,)
    )

    conn.commit()
    conn.close()

    if not result.rowcount:
        abort(404)
    return redirect(url_for("admin_bookings"))


@app.route("/complete-booking/<int:id>", methods=["POST"])
@role_required("admin")
def complete_booking(id):

    conn = get_db_connection()

    result = conn.execute(
        "UPDATE bookings SET status='Completed' WHERE id=? AND status='Accepted'",
        (id,)
    )

    conn.commit()
    conn.close()

    if not result.rowcount:
        abort(404)
    return redirect(url_for("admin_bookings"))
# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)