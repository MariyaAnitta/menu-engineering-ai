# create_firestore_collections.py

from datetime import datetime
import uuid

from google.cloud import firestore

from configs.gemini_client import create_gemini_client
from configs.settings import DATABASE_NAME


# ==================================================
# FIRESTORE INITIALIZATION
# ==================================================

client, credentials = create_gemini_client()

db = firestore.Client(
    project=credentials.project_id,
    credentials=credentials,
    database=DATABASE_NAME
)


# ==================================================
# SHARED VALUES
# ==================================================

upload_id = str(uuid.uuid4())

file_name = "restaurant_menu.xlsx"

dish_id = str(uuid.uuid4())

audit_id = str(uuid.uuid4())

insight_id = str(uuid.uuid4())


# ==================================================
# 1. uploads_collection
# ==================================================

uploads_data = {

    "upload_id": upload_id,

    "file_name": file_name,

    "uploaded_at": datetime.utcnow().isoformat(),

    "row_count": 65,

    "status": "processed",

    "total_revenue": 250000,

    "total_profit": 120000
}

db.collection(
    "uploads_collection"
).document(upload_id).set(
    uploads_data
)

print("uploads_collection created")


# ==================================================
# 2. dishes_collection
# ==================================================

dish_data = {

    "dish_id": dish_id,

    "upload_id": upload_id,

    "file_name": file_name,

    "dish_name": "Chicken Machboos",

    "category": "Puzzle",

    "number_sold": 120,

    "revenue": 12000,

    "profit": 8000,

    "margin": 68.5,

    "food_cost_percent": 31
}

db.collection(
    "dishes_collection"
).document(dish_id).set(
    dish_data
)

print("dishes_collection created")


# ==================================================
# 3. dashboard_ai_insights_collection
# ==================================================

dashboard_ai_insights_data = {

    "insight_id": insight_id,

    "upload_id": upload_id,

    "file_name": file_name,

    "executive_summary":
        "High profitability opportunity identified.",

    "pricing_recommendations": [
        "Increase price of Chicken Machboos"
    ],

    "promotion_recommendations": [
        "Promote Lamb Harees"
    ],

    "bundle_opportunities": [
        "Tea + Dessert combo"
    ],

    "removal_recommendations": [
        "Consider removing low-margin items"
    ],

    "created_at": datetime.utcnow().isoformat()
}

db.collection(
    "dashboard_ai_insights_collection"
).document(insight_id).set(
    dashboard_ai_insights_data
)

print("dashboard_ai_insights_collection created")


# ==================================================
# 4. visual_audits_collection
# ==================================================

visual_audit_data = {

    "audit_id": audit_id,

    "upload_id": upload_id,

    "file_name": file_name,

    "dish_id": dish_id,

    "dish_name": "Chicken Machboos",

    "dish_category": "Puzzle",

    "visual_health_score": 8,

    "lighting_score": 9,

    "background_score": 8,

    "sharpness_score": 8,

    "plating_score": 7,

    "executive_summary":
        "Dish has strong hero potential.",

    "selected_style":
        "rustic_warmth",

    "selected_image": {

        "gcs_bucket":
            "menu-engineering",

        "gcs_path":
            "final-assets/chicken-machboos/hero.png",

        "public_url":
            "https://storage.googleapis.com/menu-engineering/final-assets/chicken-machboos/hero.png"
    },

    "created_at": datetime.utcnow().isoformat()
}

db.collection(
    "visual_audits_collection"
).document(audit_id).set(
    visual_audit_data
)

print("visual_audits_collection created")


# ==================================================
# SUCCESS
# ==================================================

print("\nAll Firestore collections created successfully.\n")