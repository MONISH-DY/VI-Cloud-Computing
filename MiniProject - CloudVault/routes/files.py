from flask import Blueprint, render_template, request, redirect, session, send_file, Response
from werkzeug.utils import secure_filename
from io import BytesIO
import mimetypes

from services.shared_service import (
    share_drive,
    get_shared_with_me,
    get_permission
)

from services.file_service import (
    create_folder,
    get_folder_items,
    get_storage_used,
    format_size,
    get_breadcrumbs,
    upload_user_file,
    search_user_files,
    download_user_file,
    delete_user_file,
    get_recent_files,
    move_to_trash,
    restore_from_trash,
    get_trash_items,
    empty_trash
)

files_bp = Blueprint("files", __name__)


def apply_sorting(folders, files, sort_by):
    # Sort folders by name always
    folders.sort(key=lambda x: x.lower())

    # Apply Sorting to files
    if sort_by == "size":
        files.sort(key=lambda x: x.get("size", 0), reverse=True)
    elif sort_by == "modified":
        files.sort(key=lambda x: str(x.get("modified", "")), reverse=True)
    else: # name
        files.sort(key=lambda x: x.get("name", "").lower())
    
    return folders, files


@files_bp.app_context_processor
def inject_storage_info():
    default_info = {
        "used": "0 B",
        "storage_percent": 0,
        "storage_breakdown": {"images": 0, "videos": 0, "documents": 0, "others": 0},
        "storage_raw": {"images": 0, "videos": 0, "documents": 0, "others": 0}
    }
    if "user_id" in session:
        try:
            storage_data = get_storage_used(session["user_id"])
            used_bytes = storage_data["total"]
            
            # 15GB limit
            limit = 15 * 1024 * 1024 * 1024
            
            breakdown = {}
            for cat, size in storage_data["categories"].items():
                if used_bytes > 0:
                    pct = (size / used_bytes) * 100
                else:
                    pct = 0
                breakdown[cat] = round(pct, 2)
                
            storage_pct = (used_bytes / limit) * 100
            if used_bytes > 0 and storage_pct < 2:
                storage_pct = 2  # At least 2% so it's visible
                
            return {
                "used": format_size(used_bytes),
                "storage_percent": round(storage_pct, 2),
                "storage_breakdown": breakdown,
                "storage_raw": storage_data["categories"]
            }
        except Exception:
            return default_info
    return default_info


# =====================================
# DASHBOARD
# =====================================
@files_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    path = request.args.get("path", "")
    search = request.args.get("search", "")
    sort_by = request.args.get("sort", "name")

    if search:
        # Search My Drive
        folders, files = search_user_files(session["user_id"], search)
        
        # Search Shared Drives
        shared_access = get_shared_with_me(session["user_id"])
        for access in shared_access:
            owner_id = access["owner_id"]
            owner_email = access["owner_email"]
            s_folders, s_files = search_user_files(owner_id, search)
            
            # Tag shared items with owner info
            for f in s_files:
                f["owner_id"] = owner_id
                f["owner_email"] = owner_email
                f["shared"] = True
            
            for fld in s_folders:
                # folders from search are just strings, so we wrap them
                # wait, search_user_files returns sorted(list(found_folders)) which are strings
                pass 
                
            files.extend(s_files)
            # For simplicity, we only show files in global search results for now
            # or we could implement a more complex folder structure
    else:
        folders, files = get_folder_items(session["user_id"], path)

    folders, files = apply_sorting(folders, files, sort_by)
    breadcrumbs = get_breadcrumbs(path)

    return render_template(
        "drive/my_drive.html",
        name=session["user_name"],
        folders=folders,
        files=files,
        path=path,
        search=search,
        breadcrumbs=breadcrumbs,
        sort_by=sort_by
    )


# =====================================
# CREATE FOLDER
# =====================================
@files_bp.route("/create-folder", methods=["POST"])
def new_folder():
    if "user_id" not in session:
        return redirect("/login")

    folder = request.form["folder"]
    path = request.form.get("path", "")

    full = f"{path}/{folder}" if path else folder

    create_folder(session["user_id"], full)

    return redirect(f"/dashboard?path={path}")


# =====================================
# UPLOAD
# =====================================
@files_bp.route("/upload", methods=["POST"])
def upload():
    if "user_id" not in session:
        return redirect("/login")

    file = request.files["file"]
    path = request.form.get("path", "")
    relative_path = request.form.get("relative_path", "")

    if file:
        if relative_path:
            # Use relative path but remove the root folder name from webkitRelativePath if it matches current path context
            # Actually, webkitRelativePath is folder/subfolder/file.txt
            # We want to preserve everything after the root of the selection if we're in a specific path
            full_name = f"{path}/{relative_path}" if path else relative_path
        else:
            filename = secure_filename(file.filename)
            full_name = f"{path}/{filename}" if path else filename

        upload_user_file(
            session["user_id"],
            full_name,
            file
        )

    return redirect(f"/dashboard?path={path}")


# =====================================
# DOWNLOAD
# =====================================
@files_bp.route("/download/<path:filename>")
def download(filename):
    if "user_id" not in session:
        return redirect("/login")

    data = download_user_file(session["user_id"], filename)

    return send_file(
        BytesIO(data),
        as_attachment=True,
        download_name=filename.split("/")[-1]
    )


# =====================================
# PREVIEW
# =====================================
@files_bp.route("/preview/<path:filename>")
def preview(filename):
    if "user_id" not in session:
        return redirect("/login")

    data = download_user_file(session["user_id"], filename)

    mime = mimetypes.guess_type(filename)[0]

    if not mime:
        mime = "application/octet-stream"

    return Response(data, mimetype=mime)


# =====================================
# DELETE
# =====================================
@files_bp.route("/delete/<path:filename>")
def delete(filename):
    if "user_id" not in session:
        return redirect("/login")

    # Move to trash instead of permanent delete
    move_to_trash(session["user_id"], filename)

    return redirect("/dashboard")

@files_bp.route("/delete", methods=["POST"])
def delete_post():
    if "user_id" not in session:
        return "Unauthorized", 401

    filename = request.form.get("filename")
    if filename:
        move_to_trash(session["user_id"], filename)
        return "OK", 200
    
    return "Bad Request", 400


# =====================================
# SHARE DRIVE
# =====================================
@files_bp.route("/share", methods=["POST"])
def share():
    if "user_id" not in session:
        return redirect("/login")

    share_drive(
        session["user_id"],
        session["email"],
        request.form["email"],
        request.form["permission"]
    )

    return redirect("/dashboard")

@files_bp.route("/shared/remove/<owner_id>", methods=["POST"])
def remove_shared_access(owner_id):
    if "user_id" not in session:
        return "Unauthorized", 401

    from services.shared_service import remove_access
    remove_access(owner_id, session["user_id"])
    return "OK", 200



# =====================================
# SHARED LIST
# =====================================
@files_bp.route("/shared")
def shared_list():
    if "user_id" not in session:
        return redirect("/login")

    shared = get_shared_with_me(session["user_id"])

    return render_template(
        "drive/shared.html",
        name=session["user_name"],
        shared=shared
    )


# =====================================
# OPEN SHARED DRIVE
# =====================================
@files_bp.route("/shared/<owner_id>")
def view_shared_drive(owner_id):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if not permission:
        return "Access Denied"

    path = request.args.get("path", "")
    sort_by = request.args.get("sort", "name")

    folders, files = get_folder_items(owner_id, path)
    folders, files = apply_sorting(folders, files, sort_by)
    
    from services.auth_service import get_user_name
    owner_name = get_user_name(owner_id)

    return render_template(
        "shared_drive.html",
        folders=folders,
        files=files,
        owner_id=owner_id,
        owner_name=owner_name,
        permission=permission,
        path=path,
        sort_by=sort_by
    )


# =====================================
# UPLOAD SHARED
# =====================================
@files_bp.route("/shared/upload/<owner_id>", methods=["POST"])
def upload_shared(owner_id):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if permission != "write":
        return "Write Access Denied"

    file = request.files["file"]
    path = request.form.get("path", "")

    if file:
        filename = secure_filename(file.filename)

        full_name = f"{path}/{filename}" if path else filename

        upload_user_file(owner_id, full_name, file)

    return redirect(f"/shared/{owner_id}?path={path}")

@files_bp.route("/share/public", methods=["POST"])
def create_public_link():
    if "user_id" not in session:
        return "Unauthorized", 401
    
    filename = request.form.get("filename")
    hours = int(request.form.get("hours", 24))
    
    from services.file_service import get_public_link
    link = get_public_link(session["user_id"], filename, hours)
    
    return {"link": link}, 200

@files_bp.route("/bulk-download", methods=["POST"])
def bulk_download():
    if "user_id" not in session:
        return redirect("/login")
    
    import json
    import zipfile
    from io import BytesIO
    from services.file_service import download_user_file
    
    items = json.loads(request.form.get("items", "[]"))
    
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for item in items:
            try:
                # Use download_user_file which returns bytes
                content = download_user_file(session["user_id"], item)
                zf.writestr(item, content)
            except Exception:
                continue
                
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='cloudvault_export.zip'
    )

# =====================================
# STARRED
# =====================================
@files_bp.route("/starred")
def starred_view():
    if "user_id" not in session:
        return redirect("/login")
    
    from services.file_service import get_starred_items
    files = get_starred_items(session["user_id"])
    sort_by = request.args.get("sort", "name")
    _, files = apply_sorting([], files, sort_by)
    
    return render_template(
        "drive/starred.html",
        name=session["user_name"],
        files=files,
        sort_by=sort_by
    )

@files_bp.route("/star/<path:filename>")
def star_file(filename):
    if "user_id" not in session:
        return "Unauthorized", 401
    from services.file_service import toggle_star
    toggle_star(session["user_id"], filename, True)
    return redirect(request.referrer or "/dashboard")

@files_bp.route("/unstar/<path:filename>")
def unstar_file(filename):
    if "user_id" not in session:
        return "Unauthorized", 401
    from services.file_service import toggle_star
    toggle_star(session["user_id"], filename, False)
    return redirect(request.referrer or "/dashboard")

# =====================================
# RECENT
# =====================================
@files_bp.route("/recent")
def recent():
    if "user_id" not in session:
        return redirect("/login")
    # Fetch actual recent files
    files = get_recent_files(session["user_id"])
    sort_by = request.args.get("sort", "modified") # Default to modified for recent
    
    folders, files = apply_sorting([], files, sort_by)
    
    return render_template(
        "drive/recent.html",
        name=session["user_name"],
        files=files,
        sort_by=sort_by
    )

# =====================================
# TRASH
# =====================================
@files_bp.route("/trash")
def trash():
    if "user_id" not in session:
        return redirect("/login")
    # Fetch files from .trash/ prefix
    files = get_trash_items(session["user_id"])
    sort_by = request.args.get("sort", "name")
    
    folders, files = apply_sorting([], files, sort_by)
    
    return render_template(
        "drive/trash.html",
        name=session["user_name"],
        folders=folders,
        files=files,
        sort_by=sort_by
    )

# =====================================
# RENAME
# =====================================
@files_bp.route("/rename", methods=["POST"])
def rename():
    if "user_id" not in session:
        return "Unauthorized", 401
    
    old_name = request.form.get("old_name")
    new_name_base = request.form.get("new_name")
    
    # Construct full new name path
    if "/" in old_name:
        parent_path = "/".join(old_name.split("/")[:-1])
        full_new_name = f"{parent_path}/{new_name_base}"
    else:
        full_new_name = new_name_base
    
    from services.file_service import rename_user_file
    rename_user_file(session["user_id"], old_name, full_new_name)
    
    return "OK", 200

# =====================================
# RESTORE FROM TRASH
# =====================================
@files_bp.route("/trash/restore/<path:filename>")
def restore_trash(filename):
    if "user_id" not in session:
        return redirect("/login")
        
    restore_from_trash(session["user_id"], filename)
    return redirect("/trash")

# =====================================
# EMPTY TRASH
# =====================================
@files_bp.route("/trash/empty", methods=["POST"])
def empty_trash_route():
    if "user_id" not in session:
        return "Unauthorized", 401
        
    empty_trash(session["user_id"])
    return "OK", 200


# =====================================
# DOWNLOAD SHARED
# =====================================
@files_bp.route("/shared/download/<owner_id>/<path:filename>")
def download_shared(owner_id, filename):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if not permission:
        return "Access Denied"

    data = download_user_file(owner_id, filename)

    return send_file(
        BytesIO(data),
        as_attachment=True,
        download_name=filename.split("/")[-1]
    )


# =====================================
# PREVIEW SHARED
# =====================================
@files_bp.route("/shared/preview/<owner_id>/<path:filename>")
def preview_shared(owner_id, filename):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if not permission:
        return "Access Denied"

    data = download_user_file(owner_id, filename)

    mime = mimetypes.guess_type(filename)[0]

    if not mime:
        mime = "application/octet-stream"

    return Response(data, mimetype=mime)


# =====================================
# DELETE SHARED
# =====================================
@files_bp.route("/shared/delete/<owner_id>/<path:filename>")
def delete_shared(owner_id, filename):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if permission != "write":
        return "Write Access Denied"

    # We need to check if it's a folder or file to call the right delete service
    is_folder = request.args.get("type") == "folder"
    
    if is_folder:
        from services.file_service import delete_folder
        delete_folder(owner_id, filename)
    else:
        delete_user_file(None, owner_id, filename)

    return redirect(f"/shared/{owner_id}")


# =====================================
# RENAME SHARED
# =====================================
@files_bp.route("/shared/rename/<owner_id>", methods=["POST"])
def rename_shared(owner_id):
    if "user_id" not in session:
        return "Unauthorized", 401
    
    permission = get_permission(owner_id, session["user_id"])
    if permission != "write":
        return "Write Access Denied", 403
        
    old_name = request.form.get("old_name")
    new_name_base = request.form.get("new_name")
    
    # Construct full new name path
    if "/" in old_name:
        parent_path = "/".join(old_name.split("/")[:-1])
        full_new_name = f"{parent_path}/{new_name_base}"
    else:
        full_new_name = new_name_base
    
    from services.file_service import rename_user_file
    rename_user_file(owner_id, old_name, full_new_name)
    
    return "OK", 200

# =====================================
# CREATE SHARED FOLDER
# =====================================
@files_bp.route("/shared/create-folder/<owner_id>", methods=["POST"])
def create_shared_folder(owner_id):
    if "user_id" not in session:
        return redirect("/login")

    permission = get_permission(owner_id, session["user_id"])

    if permission != "write":
        return "Write Access Denied"

    folder = request.form["folder"]
    path = request.form.get("path", "")

    full_folder = f"{path}/{folder}" if path else folder

    create_folder(owner_id, full_folder)

    return redirect(f"/shared/{owner_id}?path={path}")