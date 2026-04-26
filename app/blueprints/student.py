from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import (
    Course, ClassSection, Enrollment, Material, Notification,
    current_semester, DAY_VN,
)
from app.services.enrollment import enroll, drop, EnrollmentError

bp = Blueprint("student", __name__, url_prefix="/student")


def student_required(view):
    """Decorator: chỉ sinh viên mới được vào."""
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_student:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@bp.route("/dashboard")
@student_required
def dashboard():
    sem = current_semester()
    enrollments = []
    total_credits = 0
    if sem:
        enrollments = (Enrollment.query
                       .filter_by(student_id=current_user.id,
                                  semester_id=sem.id, status="registered")
                       .all())
        total_credits = sum(e.class_section.course.credits for e in enrollments)

    graded = (Enrollment.query
              .filter(Enrollment.student_id == current_user.id,
                      Enrollment.total_score.isnot(None))
              .all())
    gpa = round(sum(e.total_score for e in graded) / len(graded), 2) if graded else 0.0

    notifs = (Notification.query
              .order_by(Notification.is_pinned.desc(),
                        Notification.created_at.desc())
              .limit(5).all())

    return render_template("student/dashboard.html",
                           enrollments=enrollments,
                           total_credits=total_credits,
                           gpa=gpa, notifs=notifs,
                           current_sem=sem, day_vn=DAY_VN)


@bp.route("/registration")
@student_required
def registration():
    sem = current_semester()
    if not sem:
        flash("Chưa có học kỳ hiện tại.", "info")
        return redirect(url_for("student.dashboard"))

    q = request.args.get("q", "").strip()
    sections_q = (ClassSection.query.filter_by(semester_id=sem.id)
                  .join(Course, ClassSection.course_id == Course.id))
    if q:
        like = f"%{q}%"
        sections_q = sections_q.filter(or_(
            Course.name.like(like),
            Course.code.like(like),
            ClassSection.instructor_name.like(like),
        ))
    sections = sections_q.order_by(Course.code, ClassSection.section_code).all()

    enrolled_ids = {
        e.class_section_id
        for e in Enrollment.query.filter_by(
            student_id=current_user.id, semester_id=sem.id, status="registered"
        )
    }
    return render_template("student/registration.html",
                           sections=sections, enrolled_ids=enrolled_ids,
                           q=q, sem=sem, day_vn=DAY_VN)


@bp.route("/registration/enroll/<int:section_id>", methods=["POST"])
@student_required
def enroll_action(section_id):
    try:
        result = enroll(current_user.id, section_id)
        flash(f"Đăng ký lớp {result.section.section_code} "
              f"({result.section.course.name}) thành công!", "success")
    except EnrollmentError as e:
        flash(str(e), "error")
    return redirect(url_for("student.registration"))


@bp.route("/registration/drop/<int:section_id>", methods=["POST"])
@student_required
def drop_action(section_id):
    try:
        drop(current_user.id, section_id)
        flash("Đã hủy đăng ký.", "success")
    except EnrollmentError as e:
        flash(str(e), "error")
    return redirect(url_for("student.registration"))


@bp.route("/schedule")
@student_required
def schedule():
    sem = current_semester()
    enrollments = []
    if sem:
        enrollments = (Enrollment.query
                       .filter_by(student_id=current_user.id,
                                  semester_id=sem.id, status="registered")
                       .all())
    return render_template("student/schedule.html",
                           enrollments=enrollments, sem=sem, day_vn=DAY_VN)


@bp.route("/materials")
@student_required
def materials():
    q = request.args.get("q", "").strip()
    course_id = request.args.get("course_id", type=int)

    query = Material.query.filter_by(status="active")
    if q:
        query = query.filter(Material.title.like(f"%{q}%"))
    if course_id:
        query = query.filter_by(course_id=course_id)

    items = query.order_by(Material.created_at.desc()).all()
    courses = Course.query.order_by(Course.code).all()
    return render_template("student/materials.html",
                           items=items, courses=courses,
                           q=q, course_id=course_id)


@bp.route("/grades")
@student_required
def grades():
    rows = (Enrollment.query
            .filter(Enrollment.student_id == current_user.id,
                    Enrollment.total_score.isnot(None))
            .all())
    return render_template("student/grades.html", rows=rows)


@bp.route("/profile")
@student_required
def profile():
    return render_template("student/profile.html", user=current_user)
