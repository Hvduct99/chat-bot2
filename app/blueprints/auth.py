from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, Faculty, Department

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("forum.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Chào mừng, {user.full_name}!", "success")
            target = url_for("forum.index") if user.is_admin \
                else url_for("student.dashboard")
            return redirect(request.args.get("next") or target)
        flash("Email hoặc mật khẩu không đúng.", "error")

    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("forum.index"))

    faculties = Faculty.query.all()
    departments = Department.query.all()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        student_code = request.form.get("student_code", "").strip() or None
        faculty_id = request.form.get("faculty_id") or None
        department_id = request.form.get("department_id") or None

        error = _validate_register(email, full_name, password, confirm)
        if error:
            flash(error, "error")
        else:
            u = User(
                email=email, full_name=full_name, student_code=student_code,
                role="student",
                faculty_id=int(faculty_id) if faculty_id else None,
                department_id=int(department_id) if department_id else None,
            )
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            login_user(u)
            flash("Tạo tài khoản thành công!", "success")
            return redirect(url_for("student.dashboard"))

    return render_template("auth/register.html",
                           faculties=faculties, departments=departments)


def _validate_register(email: str, full_name: str, password: str, confirm: str) -> str | None:
    if not email or not full_name or not password:
        return "Vui lòng điền đầy đủ thông tin."
    if password != confirm:
        return "Mật khẩu xác nhận không khớp."
    if len(password) < 6:
        return "Mật khẩu phải ít nhất 6 ký tự."
    if User.query.filter_by(email=email).first():
        return "Email đã được sử dụng."
    return None


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))
