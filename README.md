# 10xStudio.AI - Menu Engineering & Visual Intelligence Suite

A professional, production-grade platform designed to revolutionize restaurant profitability through AI-driven menu engineering and visual auditing.

## 🚀 Overview

10xStudio.AI bridges the gap between business metrics and culinary aesthetics. It analyzes menu performance (Profit vs. Popularity) and automatically enhances or evaluates high-end food photography to drive revenue for your "Profit Hero" dishes.

**Key Features:**
- **Menu Engineering Matrix**: Categorize dishes into Stars, Plowhorses, Puzzles, and Duds based on sales data.
- **10x Visual Studio**: Transform amateur dish photos into professional, studio-quality images.
- **Visual Intelligence Hub**: Perform a 5-point quality audit on your dish photos, cross-referenced with your business performance data to identify revenue leakages.

## 📁 Project Structure

The project has been streamlined into a **Hybrid Architecture**:

*   **`/menu-engineering-ai-main/frontend`**: (Next.js) A modern React dashboard providing visual insights, audit results, and a menu engineering interface.
*   **`/menu-engineering-ai-main/backend`**: (FastAPI) The orchestration layer handling Excel processing, database synchronization, and AI pipeline management.
*   **Root Directory Python Scripts**: The AI engines explicitly called by the backend:
    *   `visual_intelligence.py`: Audits food photos against business performance metrics.
    *   `visual_processor_nano.py`: Generates professional variations of dish images.

*(Note: Legacy Vite files and Video Ad Studio modules have been permanently removed to streamline the focus on Menu Engineering).*

## 🛠️ Tech Stack

*   **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Framer Motion, Lucide.
*   **Backend**: Python 3.10+, FastAPI, Pandas.
*   **AI Engine**: Google Gemini 1.5 Flash, Vertex AI Imagen 3.
*   **Database & Storage**: 
    *   **Firestore**: Metadata persistence (Analyses, Audits, Selections).
    *   **GCS**: Scalable object storage for high-resolution culinary imagery.

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Node.js (v18+)
*   Python 3.10+
*   Google Cloud Project with Vertex AI enabled.

### 2. Environment Variables
Create a `.env` file in the root and backend folders based on the provided `.env.example`. 

**Critical keys needed:**
*   `GOOGLE_APPLICATION_CREDENTIALS` (Absolute path to your service account JSON)
*   `GEMINI_API_KEY` (If using Gemini directly)
*   *Note: Never commit your `.env` or `service-account.json` to version control.*

### 3. Backend Setup
```bash
cd menu-engineering-ai-main/backend
pip install -r requirements.txt
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend Setup
```bash
cd menu-engineering-ai-main/frontend
npm install
npm run dev -- -p 3005
```

## 🔒 Security Note
The `service-account.json` and `.env` files are excluded from this repository via `.gitignore`. You must recreate them locally after cloning the repository.

---
**Developed by 10xStudio Team**
