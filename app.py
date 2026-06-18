import re
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "replace-this-secret-key"

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            course TEXT NOT NULL,
            semester TEXT,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


@app.route("/")
def dashboard():
    conn = get_db_connection()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_courses = conn.execute(
        "SELECT COUNT(DISTINCT course) FROM students"
    ).fetchone()[0]

    recent_students = conn.execute(
        "SELECT * FROM students ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_courses=total_courses,
        recent_students=recent_students,
    )


@app.route("/students")
def students():
    search_query = request.args.get("q", "").strip()

    conn = get_db_connection()

    if search_query:
        students_data = conn.execute(
            """
            SELECT * FROM students
            WHERE name LIKE ? OR email LIKE ? OR course LIKE ? OR city LIKE ?
            ORDER BY id DESC
            """,
            (
                f"%{search_query}%",
                f"%{search_query}%",
                f"%{search_query}%",
                f"%{search_query}%",
            ),
        ).fetchall()
    else:
        students_data = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students_data,
        search_query=search_query,
    )


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        city = request.form.get("city", "").strip()

        if not name or not email or not course:
            flash("Name, email, and course are required.", "danger")
            return render_template("student_form.html", student=request.form, action="Add")

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("student_form.html", student=request.form, action="Add")

        try:
            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO students (name, email, phone, course, semester, city)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, email, phone, course, semester, city),
            )
            conn.commit()
            conn.close()

            flash("Student added successfully.", "success")
            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            return render_template("student_form.html", student=request.form, action="Add")

    return render_template("student_form.html", student=None, action="Add")


@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if student is None:
        conn.close()
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester", "").strip()
        city = request.form.get("city", "").strip()

        if not name or not email or not course:
            flash("Name, email, and course are required.", "danger")
            return render_template("student_form.html", student=request.form, action="Edit")

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("student_form.html", student=request.form, action="Edit")

        try:
            conn.execute(
                """
                UPDATE students
                SET name = ?, email = ?, phone = ?, course = ?, semester = ?, city = ?
                WHERE id = ?
                """,
                (name, email, phone, course, semester, city, student_id),
            )
            conn.commit()
            conn.close()

            flash("Student updated successfully.", "success")
            return redirect(url_for("students"))

        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different email.", "danger")
            return render_template("student_form.html", student=request.form, action="Edit")

    conn.close()
    return render_template("student_form.html", student=student, action="Edit")


@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("students"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
