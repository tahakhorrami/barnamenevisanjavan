from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)

# فقط برای نمونه آموزشی است؛ در پروژه واقعی باید از کلید محرمانه استفاده شود.
app.secret_key = "change-this-development-key"

DATABASE = Path(__file__).with_name("school.db")


# اتصال به پایگاه داده
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# ایجاد جدول دانش‌آموزان
def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                student_code TEXT NOT NULL UNIQUE,
                grade TEXT NOT NULL,
                classroom TEXT NOT NULL,
                phone TEXT DEFAULT ''
            )
        """)


# صفحه اصلی و داشبورد
@app.route("/")
def index():
    with get_db() as db:
        total_students = db.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        total_classes = db.execute(
            "SELECT COUNT(DISTINCT grade || '-' || classroom) FROM students"
        ).fetchone()[0]

        recent_students = db.execute("""
            SELECT * FROM students
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

    return render_template(
        "index.html",
        total_students=total_students,
        total_classes=total_classes,
        recent_students=recent_students
    )


# فهرست و جست‌وجوی دانش‌آموزان
@app.route("/students")
def students():
    search = request.args.get("search", "").strip()

    with get_db() as db:
        records = db.execute("""
            SELECT * FROM students
            WHERE full_name LIKE ?
               OR student_code LIKE ?
               OR grade LIKE ?
               OR classroom LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    return render_template(
        "students.html",
        students=records,
        search=search
    )


# ثبت دانش‌آموز جدید
@app.route("/students/add", methods=["POST"])
def add_student():
    full_name = request.form.get("full_name", "").strip()
    student_code = request.form.get("student_code", "").strip()
    grade = request.form.get("grade", "").strip()
    classroom = request.form.get("classroom", "").strip()
    phone = request.form.get("phone", "").strip()

    if not all([full_name, student_code, grade, classroom]):
        flash("لطفاً تمام فیلدهای ضروری را تکمیل کنید.", "error")
        return redirect(url_for("students"))

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO students
                (full_name, student_code, grade, classroom, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                student_code,
                grade,
                classroom,
                phone
            ))

        flash("دانش‌آموز با موفقیت ثبت شد.", "success")

    except sqlite3.IntegrityError:
        flash("این کد دانش‌آموزی قبلاً ثبت شده است.", "error")

    return redirect(url_for("students"))


# ویرایش اطلاعات دانش‌آموز
@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    with get_db() as db:
        student = db.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            return "دانش‌آموز پیدا نشد.", 404

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            student_code = request.form.get("student_code", "").strip()
            grade = request.form.get("grade", "").strip()
            classroom = request.form.get("classroom", "").strip()
            phone = request.form.get("phone", "").strip()

            if not all([full_name, student_code, grade, classroom]):
                flash("فیلدهای ضروری را تکمیل کنید.", "error")
                return redirect(
                    url_for("edit_student", student_id=student_id)
                )

            try:
                db.execute("""
                    UPDATE students
                    SET full_name = ?,
                        student_code = ?,
                        grade = ?,
                        classroom = ?,
                        phone = ?
                    WHERE id = ?
                """, (
                    full_name,
                    student_code,
                    grade,
                    classroom,
                    phone,
                    student_id
                ))

                flash("اطلاعات دانش‌آموز ویرایش شد.", "success")
                return redirect(url_for("students"))

            except sqlite3.IntegrityError:
                flash("این کد دانش‌آموزی متعلق به فرد دیگری است.", "error")
                return redirect(
                    url_for("edit_student", student_id=student_id)
                )

    return render_template("edit_student.html", student=student)


# حذف دانش‌آموز
@app.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_db() as db:
        db.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

    flash("اطلاعات دانش‌آموز حذف شد.", "success")
    return redirect(url_for("students"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)