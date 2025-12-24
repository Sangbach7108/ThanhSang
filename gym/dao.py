import hashlib
from datetime import datetime
from sqlalchemy import func, extract
from gym import app, db
from gym.models import Staff, Member, GoiTap, Exercises, Regulation, Receipt, UserRole


# ==========================================
# 1. XÁC THỰC NGƯỜI DÙNG
# ==========================================
def get_user_by_id(user_id):
    return Staff.query.get(user_id)


def auth_user(username, password, role_name):
    username = username.strip()
    password = password.strip()
    password_hashed = hashlib.md5(password.encode("utf-8")).hexdigest()

    try:
        if isinstance(role_name, str):
            role_enum = UserRole[role_name]
        else:
            role_enum = role_name
    except KeyError:
        return None

    return Staff.query.filter(
        Staff.username == username,
        Staff.password == password_hashed,
        Staff.role == role_enum,
        Staff.is_active == True
    ).first()


# ==========================================
# 2. QUẢN LÝ NHÂN VIÊN (STAFF) - CẬP NHẬT MỚI
# ==========================================

def get_all_staff():
    """Lấy danh sách tất cả nhân viên"""
    return Staff.query.all()


def add_staff(username, password, name, email, phone, role_name):
    """Thêm nhân viên mới với mật khẩu MD5 và Role Enum"""
    pw_hash = hashlib.md5(password.strip().encode('utf-8')).hexdigest()

    # Chuyển đổi role_name từ String sang Enum nếu cần
    role_enum = UserRole[role_name] if isinstance(role_name, str) else role_name

    new_staff = Staff(
        username=username.strip(),
        password=pw_hash,
        full_name=name,
        email=email,
        phone=phone,
        role=role_enum,
        is_active=True
    )
    db.session.add(new_staff)
    db.session.commit()
    return True


def update_staff(staff_id, name, email, phone, role_name):
    """Cập nhật thông tin nhân viên"""
    s = Staff.query.get(staff_id)
    if s:
        s.full_name = name
        s.email = email
        s.phone = phone
        if isinstance(role_name, str):
            s.role = UserRole[role_name]
        else:
            s.role = role_name
        db.session.commit()
        return True
    return False


def toggle_staff_status(staff_id):
    """Khóa hoặc mở khóa tài khoản (Xóa mềm)"""
    s = Staff.query.get(staff_id)
    if s:
        s.is_active = not s.is_active
        db.session.commit()
        return True
    return False


# ==========================================
# 3. QUẢN LÝ GÓI TẬP (PACKAGES)
# ==========================================

def get_goitap(kw=None):
    query = GoiTap.query
    if kw:
        query = query.filter(GoiTap.name.contains(kw))
    return query.all()


def add_goitap(name, duration, price, description=None):
    p = GoiTap(name=name, duration=duration, price=price, description=description)
    db.session.add(p)
    db.session.commit()
    return True


def delete_goitap(goitap_id):
    p = GoiTap.query.get(goitap_id)
    if p:
        db.session.delete(p)
        db.session.commit()
        return True
    return False


def update_goitap_price(goitap_id, new_price):
    p = GoiTap.query.get(goitap_id)
    if p:
        p.price = new_price
        db.session.commit()
        return True
    return False


# ==========================================
# 4. QUẢN LÝ BÀI TẬP (EXERCISES)
# ==========================================

def get_exercises(kw=None):
    query = Exercises.query
    if kw:
        query = query.filter(Exercises.name.contains(kw))
    return query.all()


def add_exercise(name, muscle_group, description=None):
    ex = Exercises(name=name, muscle_group=muscle_group, description=description)
    db.session.add(ex)
    db.session.commit()
    return True


def update_exercise(ex_id, name, muscle_group, description):
    ex = Exercises.query.get(ex_id)
    if ex:
        ex.name = name
        ex.muscle_group = muscle_group
        ex.description = description
        db.session.commit()
        return True
    return False


def delete_exercise(ex_id):
    ex = Exercises.query.get(ex_id)
    if ex:
        db.session.delete(ex)
        db.session.commit()
        return True
    return False


# ==========================================
# 5. QUẢN LÝ QUY ĐỊNH (REGULATIONS)
# ==========================================

def get_regulations():
    return Regulation.query.all()


def update_regulation(reg_id, new_value):
    reg = Regulation.query.get(reg_id)
    if reg:
        reg.value = new_value
        db.session.commit()
        return True
    return False


# ==========================================
# 6. BÁO CÁO & THỐNG KÊ (REPORTS)
# ==========================================

def count_new_members_by_month(year):
    return db.session.query(
        extract('month', Receipt.created_date),
        func.count(Receipt.member_id)
    ).filter(
        extract('year', Receipt.created_date) == year
    ).group_by(
        extract('month', Receipt.created_date)
    ).order_by(
        extract('month', Receipt.created_date)
    ).all()


def revenue_stats_by_month(year):
    return db.session.query(
        extract('month', Receipt.created_date),
        func.sum(Receipt.total_amount)
    ).filter(
        extract('year', Receipt.created_date) == year,
        Receipt.is_paid == True
    ).group_by(
        extract('month', Receipt.created_date)
    ).order_by(
        extract('month', Receipt.created_date)
    ).all()


def get_active_member_list():
    now = datetime.now()
    return db.session.query(Member, Receipt, GoiTap) \
        .join(Receipt, Member.user_id == Receipt.member_id) \
        .join(GoiTap, Receipt.package_id == GoiTap.id) \
        .filter(func.adddate(Receipt.created_date, GoiTap.duration * 30) >= now).all()


if __name__ == "__main__":
    with app.app_context():
        print(auth_user("admin", "123", UserRole.ADMIN))