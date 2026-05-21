from fastapi import FastAPI, UploadFile, File, Request, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from configs.settings import DEV_MODE
from workflows.menu_workflow import generate_menu
from workflows.menu_engineering_workflow import process_menu_engineering_file

from agents.cuisine_agent import suggest_dishes
from rag.pipelines.rag_pipeline import run_rag
from configs.gemini_client import gemini_client
from database.db_provider import get_database_provider
from database.storage_client import upload_image_to_gcs
from utils.json_utils import convert_numpy_types

import time
import pandas as pd
from io import BytesIO
import subprocess
import json
import os
import sys
import traceback
import logging
import uuid
from pathlib import Path

# -------------------------------
# Structured Logging Configuration
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("menu-ai-backend")

# -------------------------------
# Database Provider Initialization
# -------------------------------
from configs import runtime_config

logger.info(f"Initializing Database Provider: {runtime_config.DATABASE_PROVIDER}")
db_provider = get_database_provider(runtime_config.DATABASE_PROVIDER)
backend_audit_cache = {}

class DatabaseProviderRequest(BaseModel):
    provider: str

app = FastAPI(title="Menu Engineering AI Platform")

@app.get("/admin/database-provider")
def get_admin_database_provider():
    return {
        "provider": runtime_config.DATABASE_PROVIDER
    }

@app.post("/admin/database-provider")
def set_admin_database_provider(request: DatabaseProviderRequest):
    provider = request.provider.lower()
    if provider not in ["firebase", "supabase", "postgresql"]:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Unsupported database provider: {request.provider}"}
        )
    
    # Update runtime config
    runtime_config.DATABASE_PROVIDER = provider
    
    # Refresh active provider safely
    global db_provider
    try:
        db_provider = get_database_provider(provider)
        logger.info(f"Successfully switched database provider to: {provider}")
        return {
            "status": "success",
            "message": f"Database provider updated to {provider}",
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Error switching database provider: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to switch provider: {str(e)}"}
        )

@app.get("/admin/uploads")
def get_admin_uploads(limit: int = 5, start_after_id: Optional[str] = None):
    try:
        res = db_provider.get_uploads(limit=limit, start_after_id=start_after_id)
        return res
    except Exception as e:
        logger.error(f"Error in get_admin_uploads: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/admin/upload-details/{upload_id}")
def get_admin_upload_details(upload_id: str):
    try:
        details = db_provider.get_upload_details(upload_id)
        if not details:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Upload session {upload_id} not found"}
            )
        return details
    except Exception as e:
        logger.error(f"Error in get_admin_upload_details: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/admin/platform-metrics")
def get_admin_platform_metrics():
    logger.info("metrics fetch started")
    try:
        metrics = db_provider.get_platform_metrics()
        logger.info("firestore aggregation success")
    except Exception as e:
        logger.error(f"aggregation failure: {e}")
        metrics = {
            "total_uploads": 0,
            "total_dishes_processed": 0,
            "total_visual_audits": 0,
            "total_ai_insights": 0,
            "latest_file_name": "None",
            "latest_upload_timestamp": "None",
            "latest_upload_status": "None",
            "persisted_visual_assets": 0,
            "total_persisted_uploads": 0
        }
        
    metrics["active_database_provider"] = runtime_config.DATABASE_PROVIDER
    metrics["current_ai_models"] = {
        "insights_model": "gemini-2.5-flash",
        "vision_model": "gemini-2.0-flash"
    }
    
    logger.info("response returned")
    return metrics

print("SERVER FILE LOADED:", __file__)
# -------------------------------
# Enable CORS (for Next.js frontend)
# -------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL ERROR CAUGHT: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )


# -------------------------------
# Static images for menu
# -------------------------------

# Ensure directories exist at import-time before mounting
os.makedirs("localimages", exist_ok=True)
os.makedirs("localvideos", exist_ok=True)

app.mount("/images", StaticFiles(directory="localimages"), name="images")
app.mount("/videos", StaticFiles(directory="localvideos"), name="videos")


# -------------------------------
# Request model for dish suggestion
# -------------------------------

class RestaurantRequest(BaseModel):
    restaurantName: str
    details: str
    cuisine: str


# -------------------------------
# Endpoint: Suggest 20 dishes
# -------------------------------

@app.post("/suggest-dishes")
def get_dishes(data: RestaurantRequest):
    print(f"DEBUG: Received suggest-dishes request for {data.cuisine}")

    # simulate AI processing delay in DEV mode
    if DEV_MODE:
        print("DEV MODE: Simulating dish recommendation generation...")
        # time.sleep(10) # Removed for faster testing

    if DEV_MODE:
        dishes = [
            "Harees",
            "Machboos",
            "Thareed",
            "Luqaimat",
            "Khameer",
            "Balaleet",
            "Aseeda",
            "Madrouba",
            "Ghuzi",
            "Saloona",
            "Markouka",
            "Batheeth",
            "Khubz Jabab",
            "Khubz Regag",
            "Farni",
            "Samak Mashwi",
            "Shuwaa",
            "Khabeesa",
            "Mhammar",
            "Jasheed"
        ]
    else:
        dishes = suggest_dishes(data.cuisine)

    return {
        "dishes": dishes
    }


# -------------------------------
# Request model for final menu
# -------------------------------

class MenuRequest(BaseModel):
    dishes: list[str]


# -------------------------------
# Endpoint: Generate final menu
# -------------------------------

@app.post("/generate-menu")
def generate_menu_api(data: MenuRequest):
    print(f"DEBUG: Received generate-menu request with {len(data.dishes)} dishes")

    dishes = data.dishes

    if len(dishes) != 10:
        return {
            "error": "Exactly 10 dishes required"
        }

    result = generate_menu(dishes)

    return {
        "menu": result
    }


# -------------------------------
# RAG Request model
# -------------------------------

class RagRequest(BaseModel):
    question: str


# -------------------------------
# Endpoint: RAG Chat
# -------------------------------

@app.post("/ask-rag")
def ask_rag(data: RagRequest):

    question = data.question

    prompt = f"""
You are a senior restaurant AI consultant named Neo.

Answer the user's question with practical, actionable advice.

Focus on:
- menu engineering
- pricing strategy
- cost control
- profitability
- customer behavior
- upselling and promotions


Rules:
- Do NOT use markdown formatting
- Do NOT use *, ** , any special characters .
- Use plain text only
- Keep answers clean and professional

Be concise, structured, and business-focused.Keep the response short and clear. Do not over-explain unless the user requests.
Be friendly and polite . Maintain the conversation flow as an expert assistant.

Question:
{question}
"""

    response = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return {
        "answer": response.text
    }
# -------------------------------
# Endpoint: Menu Engineering Upload
# -------------------------------

@app.post("/analyze-menu-engineering")
async def analyze_menu_engineering(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload Excel file → Run menu engineering → Save Persistence (Production Schema)
    """
    logger.info(f"Received menu engineering request for file: {file.filename}")

    if not file.filename.lower().endswith(".xlsx"):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        return {"status": "error", "message": "Only .xlsx files are supported"}

    # Sanitize and generate unique temp filename
    safe_filename = Path(file.filename).name
    upload_id = str(uuid.uuid4())
    temp_file_path = f"temp_{upload_id[:8]}_{safe_filename}"
    
    try:
        logger.info(f"Processing Excel content for {safe_filename} (Upload ID: {upload_id})")
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        required_columns = ["Menu Item Name", "Number Sold", "Item Cost", "Item Price"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns in upload: {missing_columns}")
            return {"status": "error", "message": f"Missing required columns: {', '.join(missing_columns)}"}

        df.to_excel(temp_file_path, index=False)
        
        logger.info(f"Running Menu Engineering Workflow for {temp_file_path}")
        dashboard_response = process_menu_engineering_file(temp_file_path)

        # -----------------------------------
        # Production Persistence Logic
        # -----------------------------------
        uploaded_at = time.strftime('%Y-%m-%d %H:%M:%S')
        summary = dashboard_response.get("summary", {})
        ai_insights = dashboard_response.get("ai_insights", {})

        # 1. Save Upload Session
        logger.info(f"Saving upload metadata for upload_id: {upload_id}")
        meta_success = db_provider.save_file_metadata({
            "upload_id": upload_id,
            "file_name": safe_filename,
            "uploaded_at": uploaded_at,
            "row_count": len(df),
            "status": "processed",
            "total_revenue": summary.get("total_revenue"),
            "total_profit": summary.get("total_profit")
        })
        if meta_success:
            logger.info(f"Successfully saved upload metadata: {upload_id}")
        else:
            logger.error(f"Failed to save upload metadata: {upload_id}")

        # 2. Save Analyzed Dishes with unique dish_ids
        dish_level_data = dashboard_response.get("dish_level_data", [])
        dishes_to_save = []
        dish_id_map = {} # Map dish_name to dish_id for frontend tracking

        for item in dish_level_data:
            d_id = str(uuid.uuid4())
            dish_name = item.get("dish_name")
            dish_id_map[dish_name] = d_id
            
            dishes_to_save.append({
                "dish_id": d_id,
                "upload_id": upload_id,
                "file_name": safe_filename,
                "dish_name": dish_name,
                "category": item.get("category"),
                "number_sold": item.get("number_sold"),
                "revenue": item.get("revenue"),
                "profit": item.get("profit"),
                "margin": item.get("profit_margin"),
                "food_cost_percent": item.get("item_cost_percent", 0) # Mapping to schema
            })
        
        logger.info(f"Saving {len(dishes_to_save)} dishes for upload_id: {upload_id}")
        dishes_success = db_provider.save_menu_items(dishes_to_save)
        if dishes_success:
            logger.info(f"Successfully saved dishes for upload_id: {upload_id}")
        else:
            logger.error(f"Failed to save dishes for upload_id: {upload_id}")

        # 3. Save Executive AI Insights
        insight_id = str(uuid.uuid4())
        logger.info(f"Saving AI insights for upload_id: {upload_id}")
        insights_success = db_provider.save_dashboard_ai_insights({
            "insight_id": insight_id,
            "upload_id": upload_id,
            "file_name": safe_filename,
            "executive_summary": ai_insights.get("executive_summary"),
            "pricing_recommendations": ai_insights.get("pricing_recommendation", []),
            "promotion_recommendations": ai_insights.get("promotion_recommendation", []),
            "bundle_opportunities": ai_insights.get("bundle_opportunities", []),
            "removal_recommendations": ai_insights.get("removal_recommendations", []),
            "created_at": uploaded_at
        })
        if insights_success:
            logger.info(f"Successfully saved AI insights for upload_id: {upload_id}")
        else:
            logger.error(f"Failed to save AI insights for upload_id: {upload_id}")

        # Inject IDs into response for frontend
        dashboard_response["upload_id"] = upload_id
        dashboard_response["dish_id_map"] = dish_id_map

        safe_response = convert_numpy_types(
            dashboard_response
        )

        return safe_response

    except Exception as e:
        logger.exception(f"Critical error in menu engineering: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            background_tasks.add_task(os.remove, temp_file_path)
            logger.info(f"Queued cleanup for {temp_file_path}")

# -------------------------------
# Endpoint: Visual Creation Layer
# -------------------------------
@app.post("/process-visual-creation")
async def process_visual_creation(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dish_name: str = Form(...)
):
    """
    Generate professional styles using Gemini Nano Subprocess.
    PREVIEW ONLY: Does not upload to GCS or save to Firestore.
    """
    logger.info(f"Visual Creation (Preview) request for {dish_name}")
    os.makedirs("localimages", exist_ok=True)
    
    # Secure, unique filename for original
    safe_name = Path(file.filename).name
    unique_id = str(uuid.uuid4())[:8]
    original_filename = f"original_{unique_id}_{safe_name}"
    original_path = os.path.join("localimages", original_filename)
    
    with open(original_path, "wb") as f:
        f.write(await file.read())
        
    output_dir = "localimages"
    script_path = os.path.abspath("../../visual_processor_nano.py")
    
    try:
        logger.info(f"Executing Visual Processor subprocess for {dish_name}")
        result = subprocess.run(
            [sys.executable, script_path, os.path.abspath(original_path), os.path.abspath(output_dir)],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Visual Processor Script Error: {result.stderr}")
            return {"status": "error", "message": result.stderr}
            
        local_result = json.loads(result.stdout)
        
        if not local_result.get("success"):
            logger.error(f"AI Generation reported failure: {local_result.get('error')}")
            return {"status": "error", "message": local_result.get("error", "AI generation failed")}

        # Return standardized local preview metadata to frontend
        results_list = []
        ai_results = local_result.get("results", [])
        
        for res in ai_results:
            style_name = res.get("style")
            local_filename = res.get("filename")
            results_list.append({
                "style_name": style_name,
                "preview_image_url": f"/images/{local_filename}",
                "local_image_path": os.path.join(output_dir, local_filename)
            })
            
        # Cleanup local original image after processing (styles remain for preview)
        if os.path.exists(original_path):
            background_tasks.add_task(os.remove, original_path)

        logger.info(f"Visual Creation complete for {dish_name}. Preview styles: {len(results_list)}")
        return {
            "success": True, 
            "results": results_list
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Visual Processor timeout for {dish_name}")
        return {"status": "error", "message": "Visual processing timed out after 300s"}
    except Exception as e:
        logger.exception(f"Error in visual creation for {dish_name}: {str(e)}")
        return {"status": "error", "message": str(e)}

# -------------------------------
# Endpoint: Visual Intelligence Layer
# -------------------------------

@app.post("/analyze-visual-intelligence")
async def analyze_visual_intelligence_api(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    dish_name: str = Form(...),
    orders: float = Form(...),
    margin: float = Form(...),
    views: float = Form(...),
    revenue: str = Form(...),
    rating: float = Form(...),
    avg_orders: float = Form(...),
    avg_views: float = Form(...),
    image_url: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None)
):
    """
    Perform visual quality audit.
    PREVIEW ONLY: Does not save to Firestore.
    """
    logger.info(f"Visual Intelligence Audit request for {dish_name}")
    os.makedirs("localimages", exist_ok=True)
    image_path = None
    
    try:
        if file:
            original_safe_name = Path(file.filename).name
            unique_id = str(uuid.uuid4())[:8]
            image_path = f"localimages/audit_{unique_id}_{original_safe_name}"
            with open(image_path, "wb") as f:
                f.write(await file.read())
        elif image_url:
            # Handle relative and absolute local paths
            if "/images/" in image_url:
                filename = image_url.split("/")[-1]
                image_path = os.path.join("localimages", filename)
            else:
                logger.info(f"Downloading cloud image for audit: {image_url}")
                import requests
                response = requests.get(image_url, stream=True, timeout=30)
                if response.status_code == 200:
                    unique_id = str(uuid.uuid4())[:8]
                    image_path = f"localimages/cloud_audit_{unique_id}.png"
                    with open(image_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    return {"status": "error", "message": f"Failed to download cloud image: {response.status_code}"}
        
        if not image_path or not os.path.exists(image_path):
            return {"status": "error", "message": "No image found for analysis"}
            
        script_path = os.path.abspath("../../visual_intelligence.py")
        
        result = subprocess.run(
            [sys.executable, script_path, os.path.abspath(image_path), dish_name, str(orders), str(margin), str(views), revenue, str(rating), str(avg_orders), str(avg_views)],
            capture_output=True, 
            text=True,
            env=os.environ.copy(),
            timeout=300
        )
        
        if result.returncode != 0:
            logger.error(f"Visual Intelligence Script Error: {result.stderr}")
            return {"status": "error", "message": result.stderr}
            
        return json.loads(result.stdout)

    except Exception as e:
        logger.exception(f"Error in visual intelligence for {dish_name}: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Only cleanup if it was a temporary audit-specific upload
        if image_path and "audit_" in image_path and os.path.exists(image_path):
            background_tasks.add_task(os.remove, image_path)

@app.post("/save-selected-visual")
async def save_selected_visual(
    background_tasks: BackgroundTasks,
    upload_id: str = Form(...),
    file_name: str = Form(...),
    dish_id: str = Form(...),
    dish_name: str = Form(...),
    dish_category: str = Form(...),
    selected_style: str = Form(...),
    local_image_path: str = Form(...),
    visual_health_score: float = Form(...),
    lighting_score: float = Form(...),
    background_score: float = Form(...),
    sharpness_score: float = Form(...),
    plating_score: float = Form(...),
    executive_summary: str = Form(...)
):
    """
    FINAL PERSISTENCE: Uploads selected style to GCS and saves to visual_audits_collection.
    """
    logger.info(f"Saving selected visual for {dish_name} (Style: {selected_style})")
    
    if not os.path.exists(local_image_path):
        logger.error(f"Local image not found for persistence: {local_image_path}")
        return {"status": "error", "message": "Local preview image has expired or not found"}

    try:
        # 1. Upload ONLY selected image to GCS
        filename = os.path.basename(local_image_path)
        gcs_path = f"final-assets/{dish_name.replace(' ', '_').lower()}/{filename}"
        
        logger.info(f"Uploading final asset to GCS: {gcs_path}")
        gcs_metadata = upload_image_to_gcs(local_image_path, gcs_path)
        
        if not gcs_metadata:
            logger.error(f"GCS upload failed for dish: {dish_name}")
            return {"status": "error", "message": "Failed to upload image to Cloud Storage"}
            
        logger.info("Successfully uploaded selected image to GCS")

        # 2. Save metadata to visual_audits_collection (Private GCS Metadata)
        audit_id = str(uuid.uuid4())
        audit_data = {
            "audit_id": audit_id,
            "upload_id": upload_id,
            "file_name": file_name,
            "dish_id": dish_id,
            "dish_name": dish_name,
            "dish_category": dish_category,
            "visual_health_score": visual_health_score,
            "lighting_score": lighting_score,
            "background_score": background_score,
            "sharpness_score": sharpness_score,
            "plating_score": plating_score,
            "executive_summary": executive_summary,
            "selected_style": selected_style,
            "selected_image": {
                "gcs_bucket": gcs_metadata["gcs_bucket"],
                "gcs_path": gcs_metadata["gcs_path"],
                "file_name": gcs_metadata["file_name"]
            },
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Inject GCS metadata flat fields required for the firestore query and mapping
        audit_data["gcs_bucket"] = gcs_metadata["gcs_bucket"]
        audit_data["gcs_path"] = gcs_metadata["gcs_path"]
        audit_data["selected_image_file_name"] = gcs_metadata["file_name"]

        logger.info(f"Persisting GCS metadata for audit_id: {audit_id}")
        logger.info(f"Saving visual audit for dish: {dish_name}")
        success = db_provider.save_visual_audit(audit_data)
        if success:
            logger.info(f"Successfully persisted final visual audit: {audit_id}")
            logger.info(f"GCS metadata successfully stored for audit_id: {audit_id}")
        else:
            logger.error(f"Failed to save visual audit: {dish_name}")
            return {"status": "error", "message": "Failed to save visual audit metadata"}
        
        # Cleanup local image after successful cloud persistence
        background_tasks.add_task(os.remove, local_image_path)
        
        # Invalidate backend audit cache to ensure fresh fetch
        cache_key = f"{file_name or 'manual_upload'}:{dish_name}"
        if cache_key in backend_audit_cache:
            del backend_audit_cache[cache_key]
        
        return {
            "status": "success",
            "audit_id": audit_id,
            "gcs_bucket": gcs_metadata["gcs_bucket"],
            "gcs_path": gcs_metadata["gcs_path"],
            "file_name": gcs_metadata["file_name"]
        }

    except Exception as e:
        logger.exception(f"Error saving selected visual: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/get-dish-audit/{dish_name}")
async def get_dish_audit(dish_name: str, file_name: Optional[str] = None):
    """
    Retrieve existing visual audit and image data for a specific dish.
    """
    logger.info(f"Fetching visual audit for dish: {dish_name}")
    try:
        cache_key = f"{file_name or 'manual_upload'}:{dish_name}"
        if cache_key in backend_audit_cache:
            logger.info(f"Returning cached visual audit for dish: {dish_name}")
            return backend_audit_cache[cache_key]

        audit = db_provider.get_visual_audit(file_name or "manual_upload", dish_name)
        if audit:
            logger.info(f"Successfully retrieved visual audit for dish: {dish_name}")
            backend_audit_cache[cache_key] = audit
            return audit
        else:
            logger.info(f"No visual audit found for dish: {dish_name}")
            return {"status": "not_found", "message": "No audit found for this dish"}
    except Exception as e:
        logger.error(f"Error fetching visual audit for dish {dish_name}: {str(e)}")
        return {"status": "error", "message": str(e)}




# -------------------------------
# Health check
# -------------------------------

@app.get("/")
def home():
    return {
        "status": "Menu AI Backend Running"
    }