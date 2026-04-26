"""
Seed data — port từ database.sql của bản PHP.
Idempotent: --reset để drop & recreate, không reset thì insert nếu rỗng.
"""
from __future__ import annotations
import logging
from datetime import date, time

import click

from app.extensions import db
from app.models import (
    Faculty, Department, User, Semester, Course,
    ClassSection, Enrollment, Material, Notification,
    ForumCategory, ForumThread,
)

log = logging.getLogger(__name__)


def _faculties():
    return [
        Faculty(name="Khoa Công nghệ Thông tin", code="CNTT",
                description="Đào tạo các ngành liên quan đến công nghệ thông tin."),
        Faculty(name="Khoa Kinh tế", code="KT",
                description="Đào tạo các ngành kinh tế và quản trị."),
        Faculty(name="Khoa Ngoại ngữ", code="NN",
                description="Đào tạo ngôn ngữ Anh, Nhật, Hàn."),
        Faculty(name="Khoa Điện - Điện tử", code="DDT",
                description="Đào tạo các ngành điện và điện tử."),
    ]


def _departments():
    return [
        Department(faculty_id=1, name="Kỹ thuật Phần mềm", code="KTPM", total_credits=140),
        Department(faculty_id=1, name="Hệ thống Thông tin", code="HTTT", total_credits=135),
        Department(faculty_id=1, name="Khoa học Máy tính", code="KHMT", total_credits=140),
        Department(faculty_id=2, name="Quản trị Kinh doanh", code="QTKD", total_credits=130),
        Department(faculty_id=2, name="Kế toán", code="KT01", total_credits=130),
        Department(faculty_id=3, name="Ngôn ngữ Anh", code="NNA", total_credits=125),
        Department(faculty_id=4, name="Kỹ thuật Điện tử", code="KTDT", total_credits=140),
    ]


def _users():
    admin = User(email="admin@unireg.edu.vn", full_name="Quản Trị Viên", role="admin")
    admin.set_password("admin123")

    rows = [
        ("SV20210001", "sv001@student.edu.vn", "Nguyễn Văn Minh", "0901234567", 1, 1, "2021-2025"),
        ("SV20210002", "sv002@student.edu.vn", "Trần Thị Lan", "0912345678", 1, 1, "2021-2025"),
        ("SV20220003", "sv003@student.edu.vn", "Lê Hoàng Nam", "0923456789", 1, 2, "2022-2026"),
    ]
    students = []
    for code, email, name, phone, fac, dept, year in rows:
        u = User(student_code=code, email=email, full_name=name, phone=phone,
                 role="student", faculty_id=fac, department_id=dept, academic_year=year)
        u.set_password("123456")
        students.append(u)
    return [admin] + students


def _semesters():
    return [
        Semester(name="Học kỳ 1", academic_year="2025-2026",
                 start_date=date(2025, 9, 1), end_date=date(2026, 1, 15),
                 registration_start=date(2025, 8, 1), registration_end=date(2025, 8, 25),
                 is_current=False),
        Semester(name="Học kỳ 2", academic_year="2025-2026",
                 start_date=date(2026, 2, 15), end_date=date(2026, 6, 30),
                 registration_start=date(2026, 3, 15), registration_end=date(2026, 5, 31),
                 is_current=True),
    ]


def _courses():
    rows = [
        (1, "Lập trình Web", "KTPM101", 3, 30, 15, "HTML, CSS, JavaScript và PHP cơ bản."),
        (1, "Cơ sở dữ liệu", "KTPM102", 3, 30, 15, "Thiết kế và quản trị cơ sở dữ liệu quan hệ."),
        (1, "Cấu trúc dữ liệu và giải thuật", "KTPM103", 4, 45, 15, "Các cấu trúc dữ liệu và giải thuật nền tảng."),
        (1, "Lập trình hướng đối tượng", "KTPM104", 3, 30, 15, "Nhập môn OOP."),
        (1, "Mạng máy tính", "KTPM105", 3, 30, 15, "Kiến trúc mạng và giao thức truyền thông."),
        (2, "Hệ thống thông tin quản lý", "HTTT201", 3, 30, 15, "Phân tích và thiết kế hệ thống thông tin."),
        (3, "Trí tuệ nhân tạo", "KHMT301", 3, 30, 15, "Nhập môn AI và machine learning."),
        (4, "Marketing căn bản", "QTKD401", 3, 45, 0, "Nguyên lý marketing căn bản."),
        (5, "Kế toán tài chính", "KT501", 3, 45, 0, "Nguyên lý kế toán tài chính."),
        (6, "Tiếng Anh giao tiếp", "NNA601", 2, 15, 15, "Kỹ năng giao tiếp tiếng Anh."),
        (7, "Mạch điện tử", "KTDT701", 3, 30, 15, "Phân tích mạch điện tử cơ bản."),
    ]
    return [
        Course(department_id=d, name=n, code=c, credits=cr,
               theory_hours=th, practice_hours=pr, description=desc)
        for d, n, c, cr, th, pr, desc in rows
    ]


def _class_sections():
    rows = [
        (1, 2, "KTPM101-01", "TS. Nguyễn Văn An",     50, "A301", "Monday",    time(7, 0),  time(9, 30),  1, 3),
        (1, 2, "KTPM101-02", "ThS. Trần Thị Bình",    45, "B205", "Wednesday", time(13, 0), time(15, 30), 7, 9),
        (2, 2, "KTPM102-01", "PGS.TS. Lê Văn Cường",  50, "A302", "Tuesday",   time(7, 0),  time(9, 30),  1, 3),
        (3, 2, "KTPM103-01", "TS. Phạm Thị Dung",     40, "C101", "Thursday",  time(9, 30), time(12, 0),  4, 6),
        (4, 2, "KTPM104-01", "ThS. Hoàng Văn Em",     50, "A303", "Friday",    time(7, 0),  time(9, 30),  1, 3),
        (5, 2, "KTPM105-01", "TS. Vũ Thị Phương",     45, "B301", "Monday",    time(13, 0), time(15, 30), 7, 9),
        (6, 2, "HTTT201-01", "PGS.TS. Đỗ Văn Giang",  50, "A201", "Wednesday", time(7, 0),  time(9, 30),  1, 3),
        (7, 2, "KHMT301-01", "TS. Nguyễn Thị Hoa",    40, "C201", "Tuesday",   time(13, 0), time(15, 30), 7, 9),
        (8, 2, "QTKD401-01", "ThS. Trần Văn Khải",    60, "D101", "Thursday",  time(7, 0),  time(9, 30),  1, 3),
        (10, 2, "NNA601-01", "ThS. Emily Johnson",    35, "E101", "Friday",    time(13, 0), time(15, 0),  7, 8),
    ]
    return [
        ClassSection(course_id=cid, semester_id=sid, section_code=sc,
                     instructor_name=inst, max_students=ms, room=room,
                     day_of_week=dow, start_time=st, end_time=et,
                     start_period=sp, end_period=ep)
        for cid, sid, sc, inst, ms, room, dow, st, et, sp, ep in rows
    ]


def _materials():
    rows = [
        (1, "The Missing Link - Web Development",
         "Tài liệu web development công khai phù hợp môn Lập trình Web.",
         "https://mds.marshall.edu/cgi/viewcontent.cgi?article=1042&context=oa-textbooks", "pdf"),
        (2, "Database Design - 2nd Edition",
         "Tài liệu thiết kế cơ sở dữ liệu công khai.",
         "https://opentextbc.ca/dbdesign01/open/download?type=pdf", "pdf"),
        (5, "Computer Networking: Principles, Protocols and Practice",
         "Tài liệu mạng máy tính công khai.",
         "https://www.computer-networking.info/2nd/pdf/computer-networking-principles-protocols-and-practice-libre.pdf", "pdf"),
        (7, "Introduction to Artificial Intelligence",
         "Tài liệu AI công khai.",
         "https://mountainscholar.org/bitstreams/82553455-11f0-42e1-8948-6487835004d5/download", "pdf"),
    ]
    return [
        Material(course_id=cid, title=t, description=desc,
                 file_path=fp, file_type=ft, uploaded_by=1)
        for cid, t, desc, fp, ft in rows
    ]


def _notifications():
    rows = [
        ("Thông báo đăng ký tín chỉ HK2 2025-2026",
         "Sinh viên đăng ký tín chỉ học kỳ 2 năm học 2025-2026 từ ngày 15/03/2026 đến 31/05/2026. "
         "Vui lòng vào trang Đăng ký tín chỉ để chọn lớp và đăng ký môn học.",
         "registration", True),
        ("Lịch học và đăng ký đã được cập nhật",
         "Sau khi đăng ký, sinh viên có thể xem lịch học và tài liệu học tập ngay trên hệ thống.",
         "schedule", False),
        ("Tài liệu môn Lập trình Web đã sẵn sàng",
         "Một số tài liệu PDF công khai đã được bổ sung vào hệ thống để hỗ trợ học tập.",
         "material", False),
    ]
    return [
        Notification(title=t, content=c, type=tp, target="students",
                     created_by=1, is_pinned=p)
        for t, c, tp, p in rows
    ]


def _forum_categories():
    rows = [
        ("Thông báo & Tin tức", "thong-bao", "Tin tức từ nhà trường, lịch nghỉ, sự kiện học vụ.", "fa-bullhorn", "red", 1),
        ("Đăng ký tín chỉ", "dang-ky-tin-chi", "Hỏi đáp về đăng ký môn, đổi lớp, hủy môn.", "fa-clipboard-check", "blue", 2),
        ("Lịch học & Thời khóa biểu", "lich-hoc", "Trao đổi lịch học, phòng học, thời gian.", "fa-calendar-alt", "green", 3),
        ("Tài liệu học tập", "tai-lieu", "Chia sẻ tài liệu, slide, đề thi cũ.", "fa-book", "purple", 4),
        ("Điểm số & Học vụ", "diem-hoc-vu", "Thắc mắc điểm, khiếu nại, GPA, xếp loại.", "fa-chart-line", "orange", 5),
        ("Hỏi đáp UniBot", "hoi-dap-unibot", "Đặt câu hỏi cho trợ lý AI UniBot — trả lời tự động.", "fa-robot", "indigo", 6),
        ("Câu lạc bộ & Hoạt động", "clb-hoat-dong", "Sinh hoạt CLB, sự kiện, ngoại khóa.", "fa-users", "pink", 7),
    ]
    return [
        ForumCategory(name=n, slug=s, description=d, icon=i, color=c, sort_order=o)
        for n, s, d, i, c, o in rows
    ]


def _sample_threads():
    rows = [
        (1, 1, "Lịch nghỉ lễ 30/4 - 1/5 năm 2026",
         "Trường thông báo nghỉ lễ từ 30/04/2026 đến hết 01/05/2026. Sinh viên nghỉ học theo lịch chung."),
        (2, 2, "Cách hủy môn đã đăng ký nhầm?",
         "Em vừa đăng ký nhầm môn KTPM104, làm sao để hủy ạ?"),
        (3, 3, "Trùng lịch giữa KTPM101 và KTPM102",
         "Có ai bị trùng lịch không? Mình muốn xin đổi lớp."),
        (4, 4, "Xin slide môn Cơ sở dữ liệu",
         "Bạn nào có slide đầy đủ KTPM102 không cho mình xin với."),
        (6, 2, "UniBot trả lời nhanh hơn em tưởng!",
         "Hỏi UniBot về lịch học và GPA thì nó trả lời gần như tức thì."),
    ]
    return [
        ForumThread(category_id=cid, user_id=uid, title=t, content=c)
        for cid, uid, t, c in rows
    ]


def run(reset: bool = False) -> None:
    if reset:
        click.echo("→ Drop & recreate tables...")
        db.drop_all()
        db.create_all()
    else:
        db.create_all()
        if User.query.first() is not None:
            click.echo("✓ DB đã có dữ liệu — bỏ qua seed (dùng --reset để ghi đè).")
            return

    click.echo("→ Seeding faculties, departments, users, semesters...")
    db.session.add_all(_faculties())
    db.session.commit()
    db.session.add_all(_departments())
    db.session.commit()
    db.session.add_all(_users())
    db.session.add_all(_semesters())
    db.session.commit()

    click.echo("→ Seeding courses, class sections...")
    db.session.add_all(_courses())
    db.session.commit()
    db.session.add_all(_class_sections())
    db.session.commit()

    click.echo("→ Seeding enrollments, materials, notifications...")
    enrolls = [
        Enrollment(student_id=2, class_section_id=1, semester_id=2, status="registered"),
        Enrollment(student_id=2, class_section_id=3, semester_id=2, status="registered"),
        Enrollment(student_id=3, class_section_id=2, semester_id=2, status="registered"),
    ]
    db.session.add_all(enrolls)
    for csid in (1, 2, 3):
        cs = db.session.get(ClassSection, csid)
        cs.current_students += 1
    db.session.add_all(_materials())
    db.session.add_all(_notifications())
    db.session.commit()

    click.echo("→ Seeding forum categories + threads...")
    db.session.add_all(_forum_categories())
    db.session.commit()
    db.session.add_all(_sample_threads())
    db.session.commit()

    click.echo("✓ Seed thành công.")
    click.echo("  Admin: admin@unireg.edu.vn / admin123")
    click.echo("  SV   : sv001@student.edu.vn / 123456")
