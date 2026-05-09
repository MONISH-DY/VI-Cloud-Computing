import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# ======================================
# ======================================
# GET USER NAME
# ======================================
def get_user_name(user_id):
    try:
        users_resp = supabase.auth.admin.list_users()
        user_list = users_resp.users if hasattr(users_resp, "users") else users_resp
        for user in user_list:
            if user.id == user_id:
                meta = getattr(user, 'user_metadata', {})
                if isinstance(meta, dict) and "name" in meta:
                    return meta["name"]
    except Exception:
        pass
    return "User"

# ======================================
# REGISTER
# ======================================
def register_user(name, email, password):
    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name
                }
            }
        })

        return True, "Registered Successfully"

    except Exception as e:
        return False, str(e)


# ======================================
# LOGOUT
# ======================================
def logout_user():
    try:
        supabase.auth.sign_out()
        return True
    except Exception:
        return False


# ======================================
# LOGIN
# ======================================
def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user = response.user

        return {
            "id": user.id,
            "email": user.email,
            "name": user.user_metadata.get(
                "name",
                "User"
            )
        }

    except Exception:
        return None


# ======================================
# FORGOT PASSWORD
# ======================================
def send_reset_email(email):
    try:
        supabase.auth.reset_password_email(
            email,
            {
                "redirect_to": "http://127.0.0.1:5000/reset-password"
            }
        )

        return True, "Reset link sent to email"

    except Exception as e:
        return False, str(e)