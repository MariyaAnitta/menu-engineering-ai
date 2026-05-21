import os
from configs.gemini_client import create_gemini_client
from configs.settings import DATABASE_NAME

# Initialize the Gemini client and credentials from the shared config
# We reuse the same service account credentials for Firestore and Gemini
client, credentials = create_gemini_client()

# Reusable Firestore client instance (lazy loaded)
db = None

def get_db():
    """
    Returns the centralized Firestore client instance (lazy loaded).
    """
    global db
    if db is None:
        if credentials is None:
            raise ValueError(
                "Firebase/Firestore credentials not initialized! "
                "Please ensure the GOOGLE_CREDS_JSON environment variable is set."
            )
        from google.cloud import firestore
        db = firestore.Client(
            project=credentials.project_id,
            credentials=credentials,
            database=DATABASE_NAME
        )
    return db