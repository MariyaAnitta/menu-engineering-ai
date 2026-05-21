import os
import json
from google import genai
from google.oauth2 import service_account


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Check for environment variable (useful for production / Render deployments)
google_creds_json = os.getenv("GOOGLE_CREDS_JSON")

credentials = None
project_id = None

if google_creds_json:
    try:
        creds_info = json.loads(google_creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project_id = credentials.project_id
        print("Successfully loaded Google credentials from environment variable GOOGLE_CREDS_JSON")
    except Exception as e:
        print(f"Error loading credentials from GOOGLE_CREDS_JSON env var: {e}")
else:
    SERVICE_ACCOUNT_FILE = os.path.join(
        BASE_DIR,
        "configs",
        "tenxds-agents-idp-b7d6f705f5c1.json"
    )
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            project_id = credentials.project_id
            print(f"Successfully loaded Google credentials from file: {SERVICE_ACCOUNT_FILE}")
        except Exception as e:
            print(f"Error loading credentials from file {SERVICE_ACCOUNT_FILE}: {e}")
    else:
        print(f"Warning: Credentials file {SERVICE_ACCOUNT_FILE} not found. Local Google service account credentials missing.")

if credentials:
    gemini_client = genai.Client(
        vertexai=True,
        credentials=credentials,
        project=project_id,
        location="us-central1"
    )
else:
    gemini_client = None
    print("Warning: gemini_client set to None because Google credentials are not available.")

def create_gemini_client():
    return gemini_client, credentials