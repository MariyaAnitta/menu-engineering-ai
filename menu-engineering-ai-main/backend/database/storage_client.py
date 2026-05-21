import os
from configs.gemini_client import create_gemini_client

# Reuse the same credentials for GCS
_, credentials = create_gemini_client()

# Reusable Storage client instance (lazy loaded)
storage_client = None

def get_storage_client():
    """
    Returns the centralized Google Cloud Storage client instance (lazy loaded).
    """
    global storage_client
    if storage_client is None:
        if credentials is None:
            raise ValueError(
                "GCS credentials not initialized! "
                "Please ensure the GOOGLE_CREDS_JSON environment variable is set."
            )
        from google.cloud import storage
        storage_client = storage.Client(
            project=credentials.project_id,
            credentials=credentials
        )
    return storage_client

def upload_image_to_gcs(local_file_path: str, destination_blob_name: str):
    """
    Uploads a local image to a PRIVATE Google Cloud Storage bucket.
    Returns bucket and path metadata. 
    
    IMPORTANT: This implementation removed ALL public URL and ACL logic.
    Bucket: menu-engineering
    """
    bucket_name = "menu-engineering"
    
    try:
        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # Upload the file privately
        blob.upload_from_filename(local_file_path)

        # Return only private storage metadata
        return {
            "gcs_bucket": bucket_name,
            "gcs_path": destination_blob_name,
            "file_name": os.path.basename(local_file_path)
        }
    except Exception as e:
        print(f"GCS Upload Error: {e}")
        return None

