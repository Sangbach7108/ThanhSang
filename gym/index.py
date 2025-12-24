import gym.reception
from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message

from gym import dao, login, reception, db
from gym import app, mail
from gym.models import UserRole, Exercises, Regulation, Staff, GoiTap, Receipt, Member
from datetime import datetime, timedelta


# gym/__init__.py hoặc index.py
@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/')
def index():
    packages = GoiTap.query.limit(3).all()
    return render_template("index.html", packages=packages)


# ==========================================
# QUẢN LÝ NHÂN VIÊN (STAFF) - ĐÃ CẬP NHẬT
# ==========================================
@app.route("/admin/staff", methods=['GET', 'POST'])
@login_required
def manage_staff():
    # Chỉ Admin mới có quyền vào trang này
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        # 1. Thêm nhân viên
        if action == 'add':
            dao.add_staff(
                username=request.form.get('username'),
                password=request.form.get('password'),
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                role_name=request.form.get('role')
            )
            flash("Thêm nhân viên thành công!", "success")

        # 2. Sửa nhân viên (BỔ SUNG MỚI)
        elif action == 'edit':
            staff_id = request.form.get('staff_id')
            dao.update_staff(
                staff_id=staff_id,
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                role_name=request.form.get('role')
            )
            flash("Cập nhật thông tin thành công!", "info")

        # 3. Khóa/Mở khóa nhân viên
        elif action == 'toggle':
            staff_id = request.form.get('staff_id')
            dao.toggle_staff_status(staff_id)
            flash("Đã thay đổi trạng thái nhân viên!", "warning")

        return redirect(url_for('manage_staff'))

    # Lấy danh sách hiển thị
    staff_list = dao.get_all_staff()
    return render_template('admin/staff.html', staff_list=staff_list)


@app.route('/login', methods=['GET', 'POST'])
def login_my_user():
    if current_user.is_authenticated:
        return redirect('/')
    err_msg = None

    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = dao.auth_user(username, password, role)
        if user:
            login_user(user)
            if user.role == UserRole.LETAN:
                return redirect('/reception')
            return redirect('/')
        else:
            err_msg = "Tài khoản, mật khẩu hoặc vai trò không đúng!"

    return render_template("login.html", err_msg=err_msg)


# ... (Các phần còn lại của file index.py giữ nguyên) ...

@app.route('/logout')
def logout_by_user():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)