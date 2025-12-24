import gym.reception
from flask import Flask, render_template, redirect, request, session, flash
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message

from gym import dao, login, reception, db
from gym import app, mail
from gym.models import UserRole, Exercises, Regulation, Staff, GoiTap, Receipt, Member
from datetime import datetime, timedelta


@app.route('/')
def index():
    # Lấy 3 gói tập tiêu biểu hiển thị trang chủ
    packages = GoiTap.query.limit(3).all()
    return render_template("index.html", packages=packages)


@app.route('/login', methods=['GET', 'POST'])
def login_my_user():
    if current_user.is_authenticated:
        return redirect('/')
    err_msg = None

    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # Lấy role từ select box trong login.html

        user = dao.auth_user(username, password, role)
        if user:
            login_user(user)
            # Nếu là Lễ tân, chuyển hướng thẳng vào trang reception
            if user.role == UserRole.LETAN:
                return redirect('/reception')
            return redirect('/')
        else:
            err_msg = "Tài khoản, mật khẩu hoặc vai trò không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route('/logout')
def logout_by_user():
    logout_user()
    return redirect('/login')


# --- ROUTE DÀNH CHO LỄ TÂN ---
@app.route('/reception')
@login_required
def reception_dashboard():
    if current_user.role != UserRole.LETAN:
        return redirect('/')
    return render_template('letan/index.html')


# --- HỆ THỐNG ĐĂNG KÝ CHO KHÁCH HÀNG (BOOKING FLOW) ---
@app.route('/booking', methods=['GET', 'POST'])
def booking_step1():
    if request.method.__eq__('POST'):
        phone = request.form.get('phone')
        user = Member.query.filter_by(phone=phone).first()
        session['booking_phone'] = phone
        if user:
            session['booking_user_id'] = user.user_id
            session['booking_type'] = 'RENEW'
            return redirect('/booking/select-package')
        else:
            session['booking_type'] = 'NEW'
            return redirect('/booking/register-info')
    return render_template('client/step1_check_phone.html')


@app.route('/booking/register-info', methods=['GET', 'POST'])
def booking_new_member():
    if request.method == 'POST':
        session['new_user_info'] = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
        }
        return redirect('/booking/select-package')
    phone = session.get('booking_phone')
    return render_template('client/step2_register.html', phone=phone)


@app.route('/booking/select-package')
def booking_select_package():
    packages = GoiTap.query.all()
    return render_template('client/step3_packages.html', packages=packages)


@app.route('/booking/payment')
def booking_payment():
    package_id = request.args.get('package_id')
    package = GoiTap.query.get(package_id)
    session['selected_package_id'] = package_id
    user_info = {}
    if session.get('booking_type') == 'NEW':
        user_info = session.get('new_user_info')
        user_info['phone'] = session.get('booking_phone')
        user_info['type'] = 'Khách hàng mới'
    else:
        user = Member.query.get(session.get('booking_user_id'))
        user_info['name'] = user.full_name
        user_info['phone'] = user.phone
        user_info['type'] = 'Hội viên cũ'
    return render_template('client/step4_payment.html', package=package, user=user_info)


@app.route('/booking/complete', methods=['POST'])
def booking_complete():
    try:
        booking_type = session.get('booking_type')
        package_id = session.get('selected_package_id')
        package = GoiTap.query.get(package_id)
        user_id = None

        if booking_type == 'NEW':
            info = session.get('new_user_info')
            phone = session.get('booking_phone')
            new_user = Member(full_name=info['name'], email=info['email'], phone=phone)
            db.session.add(new_user)
            db.session.commit()
            user_id = new_user.user_id
        else:
            user_id = session.get('booking_user_id')
        receipt = Receipt(total_amount=package.price, member_id=user_id, package_id=package_id, is_paid=True)
        db.session.add(receipt)
        db.session.commit()

        # Logic gửi Email (Giữ nguyên của bạn)
        try:
            expire_date = datetime.now() + timedelta(days=package.duration * 30)  # Quy đổi tháng sang ngày
            expire_str = expire_date.strftime("%d/%m/%Y")
            user_email = info['email'] if booking_type == 'NEW' else Member.query.get(user_id).email
            msg = Message("XÁC NHẬN THANH TOÁN - MUSCLE GYM", recipients=[user_email])
            msg.html = f"<h2>Thanh toán thành công gói {package.name}</h2><p>Hết hạn ngày: {expire_str}</p>"
            mail.send(msg)
        except:
            pass

        session.clear()
        return render_template('client/success.html')
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"


# --- CÁC ROUTE QUẢN TRỊ (ADMIN) ---

@app.route("/admin/packages", methods=['GET', 'POST'])
@login_required
def admin_packages():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            dao.add_goitap(request.form.get('name'), request.form.get('duration'),
                           request.form.get('price'), request.form.get('description'))
        elif action == 'edit_price':
            dao.update_goitap_price(request.form.get('id'), request.form.get('price'))
        return redirect('/admin/packages')

    packages = dao.get_goitap(request.args.get('kw'))
    return render_template('admin/packages.html', packages=packages)


@app.route("/admin/exercises", methods=['GET', 'POST'])
@login_required
def admin_exercises():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            dao.add_exercise(request.form.get('name'), request.form.get('muscle_group'),
                             request.form.get('description'))
        elif action == 'edit':
            dao.update_exercise(request.form.get('id'), request.form.get('name'),
                                request.form.get('muscle_group'), request.form.get('description'))
        elif action == 'delete':
            dao.delete_exercise(request.form.get('id'))
        return redirect('/admin/exercises')

    kw = request.args.get('kw')
    exercises = dao.get_exercises(kw)
    return render_template('admin/exercises.html', exercises=exercises)


@app.route("/admin/regulation", methods=['GET', 'POST'])
@login_required
def admin_regulation():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    if request.method == 'POST':
        dao.update_regulation(request.form.get('id'), request.form.get('value'))
        return redirect('/admin/regulation')

    regulations = dao.get_regulations()
    return render_template('admin/regulation.html', regulations=regulations)


@login.user_loader
def get_user(id):
    return dao.get_user_by_id(id)


@app.route("/admin/stats")
@login_required
def admin_stats():
    if current_user.role != UserRole.ADMIN:
        return redirect('/')

    # Lấy năm từ request, mặc định là năm hiện tại
    year = request.args.get('year', datetime.now().year, type=int)

    # Truy vấn dữ liệu từ DAO
    active_members_list = dao.get_active_member_list()
    revenue_data = dao.revenue_stats_by_month(year)
    member_data = dao.count_new_members_by_month(year)

    # Khởi tạo danh sách 12 tháng với giá trị 0
    revenue_list = [0] * 12
    member_list = [0] * 12

    # Điền dữ liệu thực tế vào mảng 12 tháng
    for month, val in revenue_data:
        revenue_list[int(month) - 1] = val

    for month, val in member_data:
        member_list[int(month) - 1] = val

    return render_template('admin/stats.html',
                           revenue_list=revenue_list,
                           member_list=member_list,
                           active_members_list=active_members_list,
                           active_count=len(active_members_list),
                           year=year)

if __name__ == '__main__':
    app.run(debug=True)