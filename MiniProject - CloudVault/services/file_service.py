from services.azure_blob import (
    container_client,
    upload_file,
    download_file,
    delete_file
)


# ==================================
# UPLOAD
# ==================================
def upload_user_file(user_id, filename, file_obj):
    blob_name = f"user_{user_id}/{filename}"
    upload_file(blob_name, file_obj)

def get_public_link(user_id, filename, hours=24):
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    import datetime
    
    blob_name = f"user_{user_id}/{filename}"
    
    # Get connection details from environment (usually stored in the client)
    # Since we use container_client, we need the account name and key
    account_name = container_client.account_name
    account_key = container_client.credential.account_key
    
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_client.container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)
    )
    
    return f"https://{account_name}.blob.core.windows.net/{container_client.container_name}/{blob_name}?{sas_token}"


# ==================================
# BASIC FILE LIST
# ==================================
def get_user_files(user_id):
    prefix = f"user_{user_id}/"

    blobs = container_client.list_blobs(
        name_starts_with=prefix
    )

    files = []

    for blob in blobs:
        filename = blob.name.replace(prefix, "")

        if not filename or filename.endswith("/.folder") or filename.startswith(".trash"):
            continue

        files.append({
            "name": filename,
            "size": blob.size,
            "modified": blob.last_modified
        })

    return files


# ==================================
# SEARCH
# ==================================
def search_user_files(user_id, keyword):
    # Search in both files and folders
    # First get everything
    prefix = f"user_{user_id}/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    found_folders = set()
    found_files = []
    
    keyword = keyword.lower()
    
    for blob in blobs:
        full_name = blob.name.replace(prefix, "")
        if not full_name or full_name.startswith(".trash"):
            continue
            
        # Check if the blob name itself contains the keyword
        if keyword in full_name.lower():
            # If it contains a slash, it's inside a folder
            parts = full_name.split("/")
            # Add all parts that match the keyword as folders if they are directories
            # But simpler: just return the blobs that match
            if full_name.endswith("/.folder"):
                found_folders.add(full_name.replace("/.folder", ""))
            else:
                found_files.append({
                    "name": full_name,
                    "size": blob.size,
                    "modified": blob.last_modified
                })
                
    return sorted(list(found_folders)), found_files


# ==================================
# DOWNLOAD
# ==================================
def download_user_file(user_id, filename):
    blob_name = f"user_{user_id}/{filename}"
    return download_file(blob_name)


# ==================================
# DELETE FILE
# ==================================
def delete_user_file(file_id, user_id, filename):
    blob_name = f"user_{user_id}/{filename}"
    delete_file(blob_name)


# ==================================
# FILE COUNT
# ==================================
def count_user_files(user_id):
    return len(get_user_files(user_id))


# ==================================
# CREATE FOLDER
# ==================================
def create_folder(user_id, folder_name):
    blob_name = f"user_{user_id}/{folder_name}/.folder"
    upload_file(blob_name, b"")

def toggle_star(user_id, filename, starred=True):
    blob_client = container_client.get_blob_client(f"user_{user_id}/{filename}")
    metadata = blob_client.get_blob_properties().metadata or {}
    metadata["starred"] = "true" if starred else "false"
    blob_client.set_blob_metadata(metadata)

def get_starred_items(user_id):
    prefix = f"user_{user_id}/"
    blobs = container_client.list_blobs(name_starts_with=prefix, include=['metadata'])
    
    files = []
    for blob in blobs:
        if blob.metadata and blob.metadata.get("starred") == "true":
            name = blob.name.replace(prefix, "")
            if name.endswith("/.folder") or name.startswith(".trash"):
                continue
            files.append({
                "name": name,
                "size": blob.size,
                "modified": blob.last_modified,
                "starred": True
            })
    return files


# ==================================
# LIST CURRENT FOLDER
# ==================================
def get_folder_items(user_id, current_path=""):
    prefix = f"user_{user_id}/"

    if current_path:
        prefix += current_path.strip("/") + "/"

    blobs = container_client.list_blobs(
        name_starts_with=prefix,
        include=['metadata']
    )

    folders = set()
    files = []

    for blob in blobs:
        name = blob.name.replace(prefix, "")

        if not name:
            continue

        parts = name.split("/")

        if len(parts) > 1:
            if parts[0] != ".trash":
                folders.add(parts[0])
        else:
            if name != ".folder" and not name.startswith(".trash"):
                files.append({
                    "name": name,
                    "size": blob.size,
                    "modified": blob.last_modified,
                    "starred": blob.metadata.get("starred") == "true" if blob.metadata else False
                })

    return sorted(list(folders)), files


# ==================================
# GET RECENT FILES
# ==================================
def get_recent_files(user_id, limit=20):
    prefix = f"user_{user_id}/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    files = []
    for blob in blobs:
        name = blob.name.replace(prefix, "")
        if not name or name.endswith("/.folder") or name.startswith(".trash"):
            continue
            
        files.append({
            "name": name,
            "size": blob.size,
            "modified": blob.last_modified
        })
        
    # Sort by modified descending
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files[:limit]


# ==================================
# STORAGE USED
# ==================================
def get_storage_used(user_id):
    prefix = f"user_{user_id}/"
    blobs = container_client.list_blobs(name_starts_with=prefix)

    total = 0
    categories = {
        "images": 0,
        "videos": 0,
        "documents": 0,
        "others": 0
    }

    for blob in blobs:
        name_without_prefix = blob.name.replace(prefix, "")
        
        # Don't count files in the trash towards the used storage
        if name_without_prefix.startswith(".trash/"):
            continue
            
        size = blob.size
        total += size
        
        name = blob.name.lower()
        if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            categories["images"] += size
        elif name.endswith(('.mp4', '.mkv', '.avi', '.mov')):
            categories["videos"] += size
        elif name.endswith(('.pdf', '.doc', '.docx', '.txt', '.md', '.zip')):
            categories["documents"] += size
        else:
            categories["others"] += size

    return {
        "total": total,
        "categories": categories
    }


# ==================================
# FORMAT SIZE
# ==================================
def format_size(size):
    if size < 1024:
        return f"{size} B"

    elif size < 1024 * 1024:
        return f"{round(size / 1024, 2)} KB"

    elif size < 1024 * 1024 * 1024:
        return f"{round(size / (1024*1024), 2)} MB"

    else:
        return f"{round(size / (1024*1024*1024), 2)} GB"


# ==================================
# RENAME FILE
# ==================================
def rename_user_file(user_id, old_name, new_name):
    prefix = f"user_{user_id}/"
    old_prefix = f"{prefix}{old_name}"
    
    # Check if it's a folder or a single file
    # We do this by listing blobs with the old_name as prefix
    blobs = container_client.list_blobs(name_starts_with=old_prefix)
    
    found = False
    for blob in blobs:
        found = True
        # Calculate new blob name
        # If old_name was "folder", and blob was "user_1/folder/file.txt"
        # and new_name is "newfolder", new blob should be "user_1/newfolder/file.txt"
        
        # Actually, if it's a file, blob.name matches old_prefix exactly (or almost)
        # If it's a folder, blob.name starts with old_prefix/
        
        relative_path = blob.name.replace(old_prefix, "", 1)
        new_blob_name = f"{prefix}{new_name}{relative_path}"
        
        old_blob = container_client.get_blob_client(blob.name)
        new_blob = container_client.get_blob_client(new_blob_name)
        
        new_blob.start_copy_from_url(old_blob.url)
        old_blob.delete_blob()
    
    if not found:
        # Maybe it was an empty folder (only .folder marker) or something went wrong
        pass


# ==================================
# TRASH SYSTEM
# ==================================
def move_to_trash(user_id, filename):
    # Ensure we don't double .trash
    if filename.startswith(".trash/"):
        return
    rename_user_file(user_id, filename, f".trash/{filename}")

def restore_from_trash(user_id, filename):
    # Rename from .trash/filename to filename
    # Remove the .trash/ prefix
    original_name = filename.replace(".trash/", "", 1)
    rename_user_file(user_id, filename, original_name)

def get_trash_items(user_id):
    prefix = f"user_{user_id}/.trash/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    files = []
    for blob in blobs:
        name = blob.name.replace(f"user_{user_id}/", "")
        if not name or name.endswith("/.folder"):
            continue
            
        files.append({
            "name": name,
            "size": blob.size,
            "modified": blob.last_modified
        })
        
    return files

def empty_trash(user_id):
    prefix = f"user_{user_id}/.trash/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    for blob in blobs:
        delete_file(blob.name)


# ==================================
# DELETE FOLDER
# ==================================
def delete_folder(user_id, folder_path):
    prefix = f"user_{user_id}/{folder_path.strip('/')}/"

    blobs = container_client.list_blobs(
        name_starts_with=prefix
    )

    for blob in blobs:
        delete_file(blob.name)


# ==================================
# BREADCRUMB PARTS
# ==================================
def get_breadcrumbs(path):
    if not path:
        return []

    parts = path.split("/")

    crumbs = []

    current = ""

    for part in parts:
        current = f"{current}/{part}" if current else part

        crumbs.append({
            "name": part,
            "path": current
        })

    return crumbs

def auto_cleanup_trash(user_id):
    import datetime
    from azure.core.exceptions import ResourceNotFoundError
    
    prefix = f"user_{user_id}/.trash/"
    blobs = container_client.list_blobs(name_starts_with=prefix)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    deleted_count = 0
    
    for blob in blobs:
        # Check if older than 30 days
        diff = now - blob.last_modified
        if diff.days >= 30:
            try:
                delete_file(blob.name)
                deleted_count += 1
            except ResourceNotFoundError:
                pass
    
    return deleted_count