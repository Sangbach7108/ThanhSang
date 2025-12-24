from gym import db, app
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
import hashlib

# --- 1. ĐỊNH NGHĨA ROLE ---
class UserRole(RoleEnum):
    ADMIN = 1
    LETAN = 2
    PT = 3
    THUNGAN = 4

# --- 2. CÁC CLASS ---
class Staff(db.Model, UserMixin):
    __tablename__ = 'staff'
    __table_args__ = {'extend_existing': True}
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(500), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    role = db.Column(Enum(UserRole))

    def get_id(self):
        return str(self.user_id)

class Member(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True}
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(500), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    def get_id(self):
        return (self.user_id)
    def __str__(self):
        return self.full_name

class GoiTap(db.Model):
    __tablename__ = 'goitap'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

class Receipt(db.Model):
    __tablename__ = 'receipt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_amount = db.Column(db.Float, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.user_id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('goitap.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.user_id'), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.now)
    is_paid = db.Column(db.Boolean, default=False)

class Exercises(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    muscle_group = db.Column(db.String(100))
    description = db.Column(db.Text)

class Regulation(db.Model):
    __tablename__ = 'regulation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))

# --- 3. RELATIONSHIPS ---
Staff.sales_made = relationship('Receipt', backref='staff_ref', lazy=True)
Member.my_receipts = relationship('Receipt', backref='member_ref', lazy=True)
GoiTap.receipts = relationship('Receipt', backref='package_ref', lazy=True)

# --- 4. TẠO DATA MẪU TRONG MODELS ---
if __name__ == '__main__':
    with app.app_context():
        # LƯU Ý: Bạn cần xóa Database cũ (hoặc drop bảng member)
        # để cấu hình mới có hiệu lực
        db.create_all()

        def hash_password(p):
            return hashlib.md5(p.encode("utf-8")).hexdigest()

        # TẠO STAFF MẪU
        if not Staff.query.filter_by(username='admin').first():
            db.session.add(Staff(username="admin", password=hash_password("123"),
                                 full_name="Quản Trị Viên", email="admin@gym.com",
                                 phone="011", role=UserRole.ADMIN))

        if not Staff.query.filter_by(username='letan').first():
            db.session.add(Staff(username="letan", password=hash_password("123"),
                                 full_name="Lễ Tân A", email="letan@gym.com",
                                 phone="012", role=UserRole.LETAN))

        if not Staff.query.filter_by(username='test2').first():
            u3 = Staff(username="test2", password=hash_password("123"),
                       full_name="Nguoi Dung", email="nd@gmail.com",
                       phone="01273", role=UserRole.PT)
            db.session.add(u3)

        # TẠO MEMBER MẪU (Đã bỏ username/password)
        if not Member.query.filter_by(email='hv@gmail.com').first():
            u4 = Member(full_name="Hoi Vien", email="hv@gmail.com", phone="0849")
            db.session.add(u4)

        # QUY ĐỊNH MẪU
        if not Regulation.query.first():
            db.session.add_all([
                Regulation(name='Độ tuổi tối thiểu', value=15, description='Tuổi tối thiểu đăng ký'),
                Regulation(name='Giá PT mặc định', value=200000, description='Giá HLV mỗi giờ'),
                Regulation(name='Giảm giá gia hạn (%)', value=10, description='Khuyến mãi cho hội viên cũ')
            ])

        if not GoiTap.query.filter_by(name="Gói 1 Tháng").first():
            db.session.add(GoiTap(name="Gói 1 Tháng", duration=1, price=300000))

        db.session.commit()
        print("🎉 [Models] Khởi tạo dữ liệu thành công (Đã bỏ Member Login)!")