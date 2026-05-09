import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


# =====================================
# FIND USER BY EMAIL
# =====================================
def get_user_by_email(email):
    users = supabase.auth.admin.list_users()

    user_list = users.users if hasattr(users, "users") else users

    for user in user_list:
        if user.email == email:
            return user

    return None


# =====================================
# SHARE DRIVE
# =====================================
def share_drive(owner_id, owner_email, target_email, permission):

    target_user = get_user_by_email(target_email)

    if not target_user:
        return False, "User not found"

    # check existing share
    existing = supabase.table("shared_access") \
        .select("*") \
        .eq("owner_id", owner_id) \
        .eq("shared_with_id", target_user.id) \
        .execute()

    if existing.data:
        supabase.table("shared_access") \
            .update({
                "permission": permission
            }) \
            .eq("owner_id", owner_id) \
            .eq("shared_with_id", target_user.id) \
            .execute()

        return True, "Permission updated"

    # new share
    supabase.table("shared_access").insert({
        "owner_id": owner_id,
        "owner_email": owner_email,
        "shared_with_id": target_user.id,
        "shared_with_email": target_email,
        "permission": permission
    }).execute()

    return True, "Access granted"


# =====================================
# SHARED WITH ME
# =====================================
def get_shared_with_me(user_id):
    result = supabase.table("shared_access") \
        .select("*") \
        .eq("shared_with_id", user_id) \
        .execute()

    data = result.data
    
    try:
        users_resp = supabase.auth.admin.list_users()
        user_list = users_resp.users if hasattr(users_resp, "users") else users_resp
        
        # Build a dictionary mapping user_id to name
        id_to_name = {}
        for user in user_list:
            meta = getattr(user, 'user_metadata', {})
            if isinstance(meta, dict) and "name" in meta:
                id_to_name[user.id] = meta["name"]
                
        for row in data:
            # Fallback to username from email if name not found
            fallback = row.get("owner_email", "User").split("@")[0]
            row["owner_name"] = id_to_name.get(row.get("owner_id"), fallback)
            
    except Exception:
        # Fallback if admin API fails
        for row in data:
            row["owner_name"] = row.get("owner_email", "User").split("@")[0]

    return data


# =====================================
# MY SHARES
# =====================================
def get_my_shares(owner_id):
    result = supabase.table("shared_access") \
        .select("*") \
        .eq("owner_id", owner_id) \
        .execute()

    return result.data


# =====================================
# CHECK PERMISSION
# =====================================
def get_permission(owner_id, user_id):
    result = supabase.table("shared_access") \
        .select("*") \
        .eq("owner_id", owner_id) \
        .eq("shared_with_id", user_id) \
        .execute()

    if result.data:
        return result.data[0]["permission"]

    return None


# =====================================
# REMOVE ACCESS
# =====================================
def remove_access(owner_id, shared_user_id):
    supabase.table("shared_access") \
        .delete() \
        .eq("owner_id", owner_id) \
        .eq("shared_with_id", shared_user_id) \
        .execute()