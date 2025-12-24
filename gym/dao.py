import json
import hashlib
from datetime import datetime
from sqlalchemy import func, extract
from gym import app, db
from gym.models import Staff, Member, GoiTap, Exercises, Regulation, Receipt

# ==========================================
# 1. XÁC THỰC NGƯỜI DÙNG
# ==========================================

def auth_user(username, password, role):
    # Băm mật khẩu MD5 để so khớp với cơ sở dữ liệu
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return Staff.query.filter(
        Staff.username.__eq__(username),
        Staff.password.__eq__(password),
        Staff.role.__eq__(role)
    ).first()

def get_user_by_id(user_id):
    return Staff.query.get(user_id)


# ==========================================
# 2. QUẢN LÝ GÓI TẬP (PACKAGES)
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
# 3. QUẢN LÝ BÀI TẬP (EXERCISES)
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
# 4. QUẢN LÝ QUY ĐỊNH (REGULATIONS)
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
# 5. BÁO CÁO & THỐNG KÊ (REPORTS)
# ==========================================

# RPT-01: Thống kê hội viên mới theo tháng trong năm
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

# RPT-02: Thống kê doanh thu theo tháng trong năm
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

# RPT-03: Danh sách hội viên đang hoạt động (Còn hạn gói tập)
def get_active_member_list():
    now = datetime.now()
    return db.session.query(Member, Receipt, GoiTap)\
        .join(Receipt, Member.user_id == Receipt.member_id)\
        .join(GoiTap, Receipt.package_id == GoiTap.id)\
        .filter(func.adddate(Receipt.created_date, GoiTap.duration * 30) >= now).all()




if __name__ == "__main__":
    with app.app_context():
        from gym.models import UserRole
        print(auth_user("admin", "123", UserRole.ADMIN))