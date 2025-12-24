import gym.reception
from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_login import current_user, login_user, logout_user, login_required
from gym import dao, login, reception, db, app, mail
from gym.models import UserRole, Exercises, Regulation, Staff, GoiTap, Receipt, Member
from datetime import datetime


# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(int(user_id))


@app.route('/')
def index():
    packages = GoiTap.query.limit(3).all()
    return render_template("index.html", packages=packages)


# ==========================================
# QUẢN LÝ NHÂN VIÊN (STAFF)
# ==========================================
@app.route("/admin/staff", methods=['GET', 'POST'])
@login_required
def manage_staff():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            dao.add_staff(
                username=request.form.get('username'), password=request.form.get('password'),
                name=request.form.get('name'), email=request.form.get('email'),
                phone=request.form.get('phone'), role_name=request.form.get('role')
            )
            flash("Thêm nhân viên thành công!", "success")
        elif action == 'edit':
            dao.update_staff(
                staff_id=request.form.get('staff_id'), name=request.form.get('name'),
                email=request.form.get('email'), phone=request.form.get('phone'),
                role_name=request.form.get('role')
            )
            flash("Cập nhật thông tin thành công!", "info")
        elif action == 'toggle':
            dao.toggle_staff_status(request.form.get('staff_id'))
            return redirect(url_for('manage_staff'))
        return redirect(url_for('manage_staff'))

    staff_list = dao.get_all_staff()
    return render_template('admin/staff.html', staff_list=staff_list)


# ==========================================
# QUẢN LÝ BÀI TẬP (EXERCISES)
# ==========================================
@app.route("/admin/exercises", methods=['GET', 'POST'])
@login_required
def manage_exercises():
    if current_user.role != UserRole.ADMIN: return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            dao.add_exercise(name=request.form.get('name'),
                             description=request.form.get('description'),
                             muscle_group=request.form.get('muscle_group'))

        elif action == 'edit':
            dao.update_exercise(ex_id=request.form.get('id'),
                                name=request.form.get('name'),
                                description=request.form.get('description'),
                                muscle_group=request.form.get('muscle_group'))

        elif action == 'delete':
            dao.delete_exercise(ex_id=request.form.get('id'))

        return redirect(url_for('manage_exercises'))

    return render_template('admin/exercises.html', exercises=Exercises.query.all())


# ==========================================
# QUẢN LÝ GÓI TẬP (PACKAGES)
# ==========================================
@app.route("/admin/packages", methods=['GET', 'POST'])
@login_required
def manage_packages():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            dao.add_package(
                name=request.form.get('name'),
                price=request.form.get('price'),
                duration=request.form.get('duration'),
                description=request.form.get('description')
            )
            flash("Thêm gói tập thành công!", "success")

        elif action == 'edit':
            package_id = request.form.get('id')
            new_name = request.form.get('name')
            new_price = request.form.get('price')

            if dao.update_package(p_id=package_id, name=new_name, price=new_price):
                flash("Cập nhật giá gói tập thành công!", "info")
            else:
                flash("Lỗi cập nhật!", "danger")

        return redirect(url_for('manage_packages'))

    packages = GoiTap.query.all()
    return render_template('admin/packages.html', packages=packages)


# ==========================================
# BÁO CÁO THỐNG KÊ (Stats)
# ==========================================
@app.route("/admin/stats")
@login_required
def admin_stats():
    if current_user.role != UserRole.ADMIN: return redirect('/')

    year = request.args.get('year', datetime.now().year, type=int)

    raw_revenue = dao.revenue_stats_by_month(year=year)
    raw_members = dao.count_new_members_by_month(year=year)
    active_members_list = dao.get_active_member_list()

    revenue_list = [0] * 12
    for month, total in raw_revenue:
        revenue_list[month - 1] = float(total) if total else 0

    member_list = [0] * 12
    for month, count in raw_members:
        member_list[month - 1] = count

    return render_template('admin/stats.html',
                           year=year,
                           revenue_list=revenue_list,
                           member_list=member_list,
                           active_count=len(active_members_list),
                           active_members_list=active_members_list)


# ==========================================
# CẤU HÌNH QUY ĐỊNH
# ==========================================
@app.route("/admin/regulation", methods=['GET', 'POST'])
@login_required
def manage_regulations():
    if current_user.role != UserRole.ADMIN: return redirect('/')
    if request.method == 'POST':
        dao.update_regulation(reg_id=request.form.get('id'),
                              new_value=request.form.get('value'))
        flash("Cập nhật quy định thành công!", "success")
    return render_template('admin/regulation.html', regulations=Regulation.query.all())


# ==========================================
# QUY TRÌNH ĐĂNG KÝ (BOOKING FLOW)
# ==========================================
@app.route('/booking', methods=['GET', 'POST'])
def booking_step1():
    if request.method == 'POST':
        phone = request.form.get('phone')
        session['booking_phone'] = phone
        user = Member.query.filter_by(phone=phone).first()
        if user:
            session['booking_user_id'], session['booking_type'] = user.user_id, 'RENEW'
            return redirect(url_for('booking_select_package'))
        session['booking_type'] = 'NEW'
        return redirect(url_for('booking_new_member'))
    return render_template('client/step1_check_phone.html')


@app.route('/booking/register-info', methods=['GET', 'POST'])
def booking_new_member():
    phone = session.get('booking_phone')
    if not phone: return redirect(url_for('booking_step1'))
    if request.method == 'POST':
        session['new_user_info'] = {
            'phone': phone,
            'name': request.form.get('name'),
            'email': request.form.get('email')
        }
        return redirect(url_for('booking_select_package'))
    return render_template('client/step2_register.html', phone=phone)


@app.route('/booking/select-package')
def booking_select_package():
    return render_template('client/step3_packages.html', packages=GoiTap.query.all())


# FIX LỖI ĐIỀU HƯỚNG: Hỗ trợ cả Path Variable và Query Parameter
@app.route('/booking/payment/<int:package_id>')
@app.route('/booking/payment')
def booking_payment(package_id=None):
    if package_id is None:
        package_id = request.args.get('package_id', type=int)

    if package_id is None:
        return redirect(url_for('booking_select_package'))

    package = GoiTap.query.get_or_404(package_id)

    # CHUẨN BỊ BIẾN 'user' ĐỂ TRÁNH LỖI UNDEFINED TRONG HTML
    user_info = {}
    booking_type = session.get('booking_type')

    if booking_type == 'NEW':
        new_info = session.get('new_user_info')
        user_info = {
            'name': new_info.get('name') if new_info else "Khách hàng mới",
            'type': "Đăng ký mới"
        }
    else:
        member_id = session.get('booking_user_id')
        member = Member.query.get(member_id) if member_id else None
        user_info = {
            'name': member.full_name if member else "Thành viên cũ",
            'type': "Gia hạn"
        }

    return render_template('client/step4_payment.html',
                           package=package,
                           user=user_info)


# FIX LỖI 404: Route xác nhận thanh toán đồng bộ với Form
@app.route('/booking/confirm-payment', methods=['POST'])
def booking_confirm_payment():
    package_id = request.form.get('package_id')
    package = GoiTap.query.get(package_id)

    if session.get('booking_type') == 'NEW':
        info = session.get('new_user_info')
        # Tạo hội viên mới
        member = Member(full_name=info['name'], email=info['email'], phone=info['phone'])
        db.session.add(member)
        db.session.commit()
        member_id = member.user_id
    else:
        member_id = session.get('booking_user_id')

    # Lưu hóa đơn để phục vụ thống kê
    receipt = Receipt(total_amount=package.price, member_id=member_id,
                      package_id=package.id, created_date=datetime.now(), is_paid=True)
    db.session.add(receipt)
    db.session.commit()

    flash("Đăng ký gói tập thành công!", "success")
    session.clear()  # Dọn dẹp session sau khi hoàn tất
    return redirect(url_for('index'))


# ==========================================
# XÁC THỰC NGƯỜI DÙNG
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login_my_user():
    if current_user.is_authenticated: return redirect('/')
    err_msg = None
    if request.method == 'POST':
        user = dao.auth_user(request.form.get('username'),
                             request.form.get('password'),
                             request.form.get('role'))
        if user:
            login_user(user)
            return redirect('/reception' if user.role == UserRole.LETAN else '/')
        err_msg = "Tài khoản hoặc mật khẩu không chính xác!"
    return render_template("login.html", err_msg=err_msg)


@app.route('/logout')
def logout_by_user():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)