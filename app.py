import hashlib
import os
from datetime import date

from flask import Flask, flash, g, redirect, render_template, request, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-key-change-me")


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "2006"),
            database=os.getenv("MYSQL_DATABASE", "Student_Wellness_DB"),
            autocommit=False,
        )
    return g.db


def get_cursor():
    return get_db().cursor(dictionary=True)


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def safe_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def hashed_student_ref(student_id):
    salt = os.getenv("FEEDBACK_SALT", "change-this-salt")
    raw = f"{salt}:{student_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def ensure_feedback_anonymized_column():
    cur = get_cursor()
    changed = False

    cur.execute("SHOW COLUMNS FROM feedback LIKE 'feedback_id'")
    feedback_id_column = cur.fetchone()
    if feedback_id_column and "auto_increment" not in str(feedback_id_column.get("Extra", "")).lower():
        cur.execute(
            """
            ALTER TABLE feedback
            MODIFY feedback_id INT NOT NULL AUTO_INCREMENT
            """
        )
        changed = True

    cur.execute("SHOW COLUMNS FROM feedback LIKE 'anonymized_student_key'")
    has_anonymized_column = cur.fetchone() is not None
    if not has_anonymized_column:
        cur.execute("ALTER TABLE feedback ADD COLUMN anonymized_student_key CHAR(64) NULL")
        changed = True

        cur.execute("SHOW COLUMNS FROM feedback LIKE 'student_id'")
        has_student_id_column = cur.fetchone() is not None
        salt = os.getenv("FEEDBACK_SALT", "change-this-salt")

        if has_student_id_column:
            cur.execute(
                """
                UPDATE feedback
                SET anonymized_student_key = SHA2(CONCAT(%s, ':', student_id), 256)
                WHERE anonymized_student_key IS NULL OR anonymized_student_key = ''
                """,
                (salt,),
            )

        cur.execute(
            """
            UPDATE feedback
            SET anonymized_student_key = SHA2(CONCAT(%s, ':', feedback_id), 256)
            WHERE anonymized_student_key IS NULL OR anonymized_student_key = ''
            """,
            (salt,),
        )
        cur.execute("ALTER TABLE feedback MODIFY anonymized_student_key CHAR(64) NOT NULL")
        changed = True

    if changed:
        get_db().commit()
    cur.close()


def load_lookup_data():
    cur = get_cursor()
    cur.execute("SELECT student_id, full_name FROM students ORDER BY full_name")
    students = cur.fetchall()
    cur.execute("SELECT counselor_id, full_name FROM counselors ORDER BY full_name")
    counselors = cur.fetchall()
    cur.close()
    return students, counselors


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        try:
            full_name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            year_of_study = safe_int(request.form.get("year"), "Year")
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            consent_to_share = 1 if request.form.get("consent_to_share") == "on" else 0

            if not full_name or not email:
                flash("Name and email are required.", "error")
                return redirect(url_for("add_student"))

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO students
                    (full_name, department, year_of_study, email, phone, consent_to_share)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (full_name, department, year_of_study, email, phone, consent_to_share),
            )
            get_db().commit()
            cur.close()
            flash("Student created.", "success")
            return redirect(url_for("index"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
            return redirect(url_for("add_student"))
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("add_student"))

    return render_template("add_student.html")


@app.route("/book_appointment", methods=["GET", "POST"])
def book_appointment():
    students, counselors = load_lookup_data()

    if request.method == "POST":
        try:
            appointment_date = request.form.get("date")
            appointment_time = request.form.get("time")
            student_id = safe_int(request.form.get("student_id"), "Student")
            counselor_id = safe_int(request.form.get("counselor_id"), "Counselor")

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO appointments
                    (appointment_date, appointment_time, status, student_id, counselor_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (appointment_date, appointment_time, "Scheduled", student_id, counselor_id),
            )
            get_db().commit()
            cur.close()
            flash("Appointment booked.", "success")
            return redirect(url_for("view_appointments"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "book_appointment.html", students=students, counselors=counselors
    )


@app.route("/record_session", methods=["GET", "POST"])
def record_session():
    students, counselors = load_lookup_data()

    if request.method == "POST":
        try:
            student_id = safe_int(request.form.get("student_id"), "Student")
            counselor_id = safe_int(request.form.get("counselor_id"), "Counselor")
            session_date = request.form.get("session_date")
            concerns = request.form.get("concerns", "").strip()
            session_notes = request.form.get("session_notes", "").strip()
            risk_level = request.form.get("risk_level")
            next_steps = request.form.get("next_steps", "").strip()

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO counseling_sessions
                    (student_id, counselor_id, session_date, concerns, session_notes, risk_level, next_steps)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    student_id,
                    counselor_id,
                    session_date,
                    concerns,
                    session_notes,
                    risk_level,
                    next_steps,
                ),
            )
            get_db().commit()
            cur.close()
            flash("Counseling session recorded.", "success")
            return redirect(url_for("index"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("record_session.html", students=students, counselors=counselors)


@app.route("/submit_feedback", methods=["GET", "POST"])
def submit_feedback():
    students, _ = load_lookup_data()

    if request.method == "POST":
        try:
            student_id = safe_int(request.form.get("student_id"), "Student")
            rating = safe_int(request.form.get("rating"), "Rating")
            comments = request.form.get("comments", "").strip()

            if rating < 1 or rating > 5:
                flash("Rating must be between 1 and 5.", "error")
                return redirect(url_for("submit_feedback"))

            ensure_feedback_anonymized_column()
            anonymized_key = hashed_student_ref(student_id)

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO feedback
                    (anonymized_student_key, rating, comments)
                VALUES (%s, %s, %s)
                """,
                (anonymized_key, rating, comments),
            )
            get_db().commit()
            cur.close()
            flash("Feedback submitted anonymously.", "success")
            return redirect(url_for("index"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("submit_feedback.html", students=students)


@app.route("/create_referral", methods=["GET", "POST"])
def create_referral():
    students, counselors = load_lookup_data()

    if request.method == "POST":
        try:
            student_id = safe_int(request.form.get("student_id"), "Student")
            counselor_id = safe_int(request.form.get("counselor_id"), "Counselor")
            referred_to = request.form.get("referred_to", "").strip()
            reason = request.form.get("reason", "").strip()
            referral_date = request.form.get("referral_date")
            status = request.form.get("status")

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO referrals
                    (student_id, counselor_id, referred_to, reason, referral_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (student_id, counselor_id, referred_to, reason, referral_date, status),
            )
            get_db().commit()
            cur.close()
            flash("Referral recorded.", "success")
            return redirect(url_for("view_followups"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("create_referral.html", students=students, counselors=counselors)


@app.route("/add_followup", methods=["GET", "POST"])
def add_followup():
    cur = get_cursor()
    cur.execute(
        """
        SELECT referral_id, referral_date, referred_to
        FROM referrals
        ORDER BY referral_date DESC
        """
    )
    referrals = cur.fetchall()
    cur.close()

    if request.method == "POST":
        try:
            referral_id = safe_int(request.form.get("referral_id"), "Referral")
            action_date = request.form.get("action_date")
            action_taken = request.form.get("action_taken", "").strip()
            outcome = request.form.get("outcome", "").strip()
            next_review_date = request.form.get("next_review_date") or None

            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO follow_up_actions
                    (referral_id, action_date, action_taken, outcome, next_review_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (referral_id, action_date, action_taken, outcome, next_review_date),
            )
            get_db().commit()
            cur.close()
            flash("Follow-up action saved.", "success")
            return redirect(url_for("view_followups"))
        except Error as exc:
            get_db().rollback()
            flash(f"Database error: {exc}", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("add_followup.html", referrals=referrals, today=date.today())


@app.route("/view_appointments")
def view_appointments():
    cur = get_cursor()
    cur.execute(
        """
        SELECT
            a.appointment_id,
            s.full_name AS student_name,
            c.full_name AS counselor_name,
            a.appointment_date,
            a.appointment_time,
            a.status
        FROM appointments a
        JOIN students s ON s.student_id = a.student_id
        JOIN counselors c ON c.counselor_id = a.counselor_id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """
    )
    appointments = cur.fetchall()
    cur.close()
    return render_template("view_appointments.html", appointments=appointments)


@app.route("/view_followups")
def view_followups():
    cur = get_cursor()
    cur.execute(
        """
        SELECT
            f.follow_up_id,
            s.full_name AS student_name,
            r.referred_to,
            f.action_date,
            f.action_taken,
            f.outcome,
            f.next_review_date
        FROM follow_up_actions f
        JOIN referrals r ON r.referral_id = f.referral_id
        JOIN students s ON s.student_id = r.student_id
        ORDER BY f.action_date DESC
        """
    )
    followups = cur.fetchall()
    cur.close()
    return render_template("view_followups.html", followups=followups)


if __name__ == "__main__":
    app.run(debug=True)
