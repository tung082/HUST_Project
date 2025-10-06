from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models import User

# Tạo Blueprint để quản lý đăng nhập, đăng ký
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.register(username, password)

        if user:
            flash("Đăng ký thành công! Hãy đăng nhập.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Tên người dùng đã tồn tại.", "danger")

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.find_by_username(username)

        if user and user.check_password(password):
            login_user(user)
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("index"))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.find_by_email(email)  # Hàm này cần được định nghĩa trong models.py
        if user:
            flash("Hướng dẫn đặt lại mật khẩu đã được gửi đến email của bạn.", "info")
        else:
            flash("Không tìm thấy tài khoản với email này.", "danger")

        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")
