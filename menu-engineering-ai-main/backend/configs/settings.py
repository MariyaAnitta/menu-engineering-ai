import os
from dotenv import load_dotenv

load_dotenv()

# Vertex / Gemini models
EMBEDDING_MODEL = "text-embedding-004"
GENERATION_MODEL = "gemini-2.5-flash"

# Firestore vector collection
VECTOR_COLLECTION = "rag_chunks"

# Retrieval settings
TOP_K = 8

# Chunking configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Google service account key
GOOGLE_KEY_PATH = os.getenv("GOOGLE_KEY_PATH")

# Firestore database name
DATABASE_NAME = "nimesh-data"

# Vertex AI region
VERTEX_LOCATION = "us-central1"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = "menu-images"  # Change this to your actual bucket name

DEV_MODE = True             # local images instead of image generation
DEV_MODE_BATCH_RAG = False    # batch price lookup

# -----------------------------
# Image limits
# -----------------------------

DEV_IMAGE_LIMIT = 2
PROD_IMAGE_LIMIT = 10