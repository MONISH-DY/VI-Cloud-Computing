from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError

from config import Config
import mimetypes


# ======================================
# CONNECTION
# ======================================
blob_service_client = BlobServiceClient.from_connection_string(
    Config.AZURE_CONNECTION_STRING
)

container_client = blob_service_client.get_container_client(
    Config.CONTAINER_NAME
)


# ======================================
# UPLOAD
# ======================================
def upload_file(blob_name, file):
    blob_client = container_client.get_blob_client(blob_name)

    content_type = guess_content_type(blob_name)

    blob_client.upload_blob(
        file,
        overwrite=True,
        content_settings=ContentSettings(
            content_type=content_type
        )
    )


# ======================================
# DOWNLOAD
# ======================================
def download_file(blob_name):
    blob_client = container_client.get_blob_client(blob_name)

    return blob_client.download_blob().readall()


# ======================================
# DELETE
# ======================================
def delete_file(blob_name):
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()

    except ResourceNotFoundError:
        pass


# ======================================
# EXISTS
# ======================================
def file_exists(blob_name):
    blob_client = container_client.get_blob_client(blob_name)

    return blob_client.exists()


# ======================================
# GET MIME TYPE
# ======================================
def guess_content_type(filename):
    content_type, _ = mimetypes.guess_type(filename)

    if content_type:
        return content_type

    return "application/octet-stream"


# ======================================
# PREVIEW FILE
# ======================================
def get_file_stream(blob_name):
    blob_client = container_client.get_blob_client(blob_name)

    data = blob_client.download_blob().readall()

    return data


# ======================================
# GET FILE URL (optional)
# ======================================
def get_blob_url(blob_name):
    blob_client = container_client.get_blob_client(blob_name)

    return blob_client.url