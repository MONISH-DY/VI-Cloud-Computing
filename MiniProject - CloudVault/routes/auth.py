from flask import Blueprint, render_template, request, redirect, session

from services.auth_service import (
    register_user,
    login_user,
    send_reset_email
)

auth_bp = Blueprint("auth", __name__)


# =====================================
# HOME
# =====================================
@auth_bp.route("/")
def home():
    return render_template("index.html")


# =====================================
# REGISTER
# =====================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        success, msg = register_user(
            name,
            email,
            password
        )

        if success:
            return redirect("/login")

        return render_template(
            "register.html",
            error=msg
        )

    return render_template("register.html")


# =====================================
# LOGIN
# =====================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = login_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["email"] = user["email"]

            # Trigger automated trash cleanup
            try:
                from services.file_service import auto_cleanup_trash
                auto_cleanup_trash(user["id"])
            except Exception:
                pass

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid credentials"
        )

    return render_template("login.html")


# =====================================
# FORGOT PASSWORD
# =====================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = ""

    if request.method == "POST":

        email = request.form["email"]

        success, msg = send_reset_email(email)

        message = msg

    return render_template(
        "forgot_password.html",
        message=message
    )

# =====================================
# RESET PASSWORD
# =====================================
@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    message = ""

    if request.method == "GET":
        access_token = request.args.get("access_token")
        refresh_token = request.args.get("refresh_token")

        if access_token and refresh_token:
            try:
                from services.auth_service import supabase

                supabase.auth.set_session(
                    access_token,
                    refresh_token
                )
            except Exception:
                pass

    if request.method == "POST":

        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return render_template(
                "reset_password.html",
                message="Passwords do not match"
            )

        try:
            from services.auth_service import supabase

            supabase.auth.update_user({
                "password": password
            })

            return redirect("/login")

        except Exception as e:
            message = str(e)

    return render_template(
        "reset_password.html",
        message=message
    )


# =====================================
# LOGOUT
# =====================================
@auth_bp.route("/logout")
def logout():
    from services.auth_service import logout_user
    logout_user()
    session.clear()
    return redirect("/login")