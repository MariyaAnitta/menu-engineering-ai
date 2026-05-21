# Menu Engineering AI: Technical Architecture & Workflow Review

This report provides a comprehensive, production-grade technical architecture and workflow review of the **10xMenu.AI Menu Engineering Platform**. It details the core entry points, data flows, AI orchestration pipelines, database/storage configurations, runtime states, and current production features to prepare for a formal engineering code review.

---

## 🗺️ High-Level System Architecture

```mermaid
graph TB
    subgraph Frontend (Next.js & React)
        A[Navbar & Route Guard] --> B[Menu Engineering Landing]
        B --> C[DashboardShell]
        C --> D[VideoStudio & VisualModal]
        E[Admin Portal & AdminShell]
    end

    subgraph Backend API (FastAPI)
        F[server.py]
        G[runtime_config.py]
    end

    subgraph Core AI Orchestrators
        H[menu_engineering_workflow.py]
        I[insight_agent.py]
        J[cuisine_agent.py]
        K[image_generator.py]
    end

    subgraph Infrastructure & Storage
        L[db_provider.py]
        M[firestore_client.py]
        N[storage_client.py]
        O[Local Disk Storage]
        P[Google Cloud Storage]
    end

    C -->|Upload Spreadsheet| F
    C -->|Generate Image Preview| F
    E -->|Switch Provider / Query Stream| F
    
    F -->|Run Workflow| H
    H -->|Aggregate Data| L
    H -->|Query Gemini 2.5| I
    H -->|Classify Cuisine| J
    F -->|Generate Mock Visual| K
    
    L -->|Read / Write Metadata| M
    N -->|Private Cloud Upload| P
    K -->|Render Temp Assets| O
```

---

## 1. System Overview

### Primary Business Objective
The Menu Engineering AI platform maximizes restaurant profitability and operational intelligence by converting raw menu sales data into high-margin pricing designs. It dynamically identifies low-performing dishes, segments them into standard matrix classes (Stars, Plowhorses, Puzzles, Dogs), renders professional localized image previews using visual intelligence, and provides an executive administrative telemetry panel for runtime database configurations.

### Architectural Responsibilities

#### Frontend (Next.js/React & TypeScript)
*   **Decoupled State Management**: Houses the operational upload streams, dynamic filters, pagination offsets, and client-side view states.
*   **Media Composition Interface**: Runs localized canvas engines for previewing AI-generated dishes, selecting visual styles (Slate Hero, Classic Plate, etc.), and managing studio-level compositions.
*   **Theme Tokens & Boundaries**: Uses custom, unified theme styling matching modern dark-mode layouts, offering instant loading skeletons.

#### Backend (FastAPI & Uvicorn)
*   **Stateless Ingestion Pipeline**: Coordinates multipart spreadsheet parsing, data transformations, and numeric normalization without memory leaks.
*   **AI Cognitive Coordination**: Directs multi-modal Gemini API requests (`gemini-2.5-flash`, `gemini-2.5-flash-image`, `gemini-1.5-flash`) for structural cuisine profiling, executive operational summaries, and visual generation parameters.
*   **Multi-Provider Interface**: Abstracts standard database queries behind an interface contract (`DatabaseProvider`), dynamically dispatching queries at runtime to Firestore, Supabase, or PostgreSQL.

---

## 2. Frontend Entry Points & Navigation Flow

### Main Routes & Target Controllers

| Route Path | Associated Next.js Controller | Primary Responsibility |
| :--- | :--- | :--- |
| `/` | `frontend/app/page.tsx` | Main portal routing hub. |
| `/menu-engineering` | `frontend/app/menu-engineering/page.tsx` | Landing deck hosting the primary spreadsheet drag-and-drop ingestion boundary. |
| `/menu-engineering/dashboard` | `frontend/app/menu-engineering/dashboard/page.tsx` | Core operational workspace (`DashboardShell`) that orchestrates pricing filters, dishes tables, visual modals, and AI advice streams. |
| `/admin` | `frontend/app/admin/page.tsx` | Production monitoring workspace (`AdminShell`) exposing database provider configs, ingestion logs, and metrics telemetry. |

### Visual Intelligence Navigation Flow
1.  **Ingestion Deck**: The user uploads an Excel menu dataset on the `/menu-engineering` route.
2.  **Redirect & Parsing**: If the upload parses successfully, the client is redirected to `/menu-engineering/dashboard`, pre-populating context variables and storing the active `upload_id` in React State.
3.  **Active Workspace**:
    *   **Data Analysis**: The user browses the [DishLevelTable](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/dashboard/DishLevelTable.tsx) to inspect margins, categorization (e.g. *Puzzles*), and AI-generated profitability advice.
    *   **Visual Generation**: Clicking **Generate AI Dish Visual** opens the [VisualModal](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/dashboard/VisualModal.tsx) for targeted dish image creations.
    *   **Selection & Render**: The modal calls `/generate-dish-preview` to generate local images, allows the user to browse styles (Slate, Retro, Minimalist), select the best design, and click **Save Selected Visual** to upload it securely to GCS and save metadata.

---

## 3. Backend Entry Points & Request Lifecycle

### API Server Configuration: `backend/api/server.py`
The FastAPI backend serves as the single orchestration server, initializing middleware, registering global exceptions, and declaring the database provider routers.

#### 1. Ingestion Endpoint: `POST /upload-menu`
*   Accepts raw spreadsheet files as multi-part form data.
*   Generates a cryptographically strong UUID (`upload_id`).
*   Saves the spreadsheet locally, parses the matrix, and triggers the `menu_engineering_workflow` async thread.
*   Persists raw results to `uploads_collection` and `dishes_collection`.

#### 2. Visual Intelligence Endpoint: `POST /generate-dish-preview`
*   Invokes `image_generator.py` to trigger local-first rendering steps.
*   Writes temporary generated assets into localized asset directories (`localimages/`).
*   Returns relative local image paths to the frontend client to keep the cloud architecture private.

#### 3. Visual Audit Persistence: `POST /save-selected-visual`
*   Transports the selected local disk image from `localimages/` to the secure, private GCS Bucket.
*   Writes structured metadata details to `visual_audits_collection` using the active database provider contract.

#### 4. Admin Telemetry & Configs:
*   `GET /admin/database-provider` & `POST /admin/database-provider`: Retrieves and updates the active runtime provider (`DATABASE_PROVIDER`).
*   `GET /admin/uploads`: Fetches a cursor-paginated page of recent spreadsheets.
*   `GET /admin/upload-details/{upload_id}`: Retrieves combined dishes, executive summaries, and visual audits for inspector side panels.
*   `GET /admin/platform-metrics`: Dynamically aggregates overall telemetry (Dishes, Audits, Uploads) and runtime environment specs.

---

## 4. End-to-End Workflow Mapping

### A. Spreadsheet Upload Workflow

```
[User Excel Upload]
       │
       ▼ (multipart/form-data)
[POST /upload-menu] ──► [Write Local Temporary File]
       │
       ▼ (UUID Ingestion ID Generation)
[Parse Excel Workbook] ──► [Normalize Dishes Data (Revenue, Profit, Margin)]
       │
       ▼
[Run Menu Engineering Matrix Calculations (Categorize: Puzzle/Star/Dog/Plowhorse)]
       │
       ▼
[Invoke cuisine_agent.py] ──► [Classify Restaurant Profile (e.g. Italian Bistro)]
       │
       ▼
[Invoke insight_agent.py] ──► [Request Gemini 2.5 Flash for Operational Insights]
       │
       ▼
[Save JSON Metadata to Uploads Collection]
       │
       ▼
[Bulk Insert Records to Dishes & AI Insights Collections]
       │
       ▼ (Return JSON Ingestion Response)
[Redirect User to Dashboard & Re-render React UI]
```

### B. Visual Intelligence Workflow

```
[Select Dish in Table] ──► [Open VisualModal] ──► [Choose Visual Composition Style]
       │
       ▼
[POST /generate-dish-preview]
       │
       ▼
[Trigger image_generator.py] ──► [Generate 3 Distinct Preview Assets on Local Disk]
       │
       ▼
[Return Local File Paths to Client] ──► [Render Previews Safely in React Canvas]
       │
       ▼ (User Chooses Preferred Dish Variant)
[POST /save-selected-visual]
       │
       ▼
[Read Image from Local Disk] ──► [Upload Securely to GCS Private Bucket]
       │
       ▼
[Write Metadata to visual_audits_collection (Incorporate GCS Path & Audit ID)]
       │
       ▼
[Update Dashboard UI Visual Badge Indicator]
```

---

## 5. Core Frontend Component Matrix

### 1. `DashboardShell`
*   **File Link**: [DashboardShell.tsx](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/dashboard/DashboardShell.tsx)
*   **Responsibility**: Core context and orchestrator of the entire workspace layout.
*   **State Ownership**: Stores the parsed menu items list (`dishes`), filter states (Stars, Dogs, etc.), selected dish IDs, active upload IDs, and the loaded AI executive summary.
*   **Backend Interaction**: Pulls parsed data and initiates spreadsheet re-runs.

### 2. `DishLevelTable`
*   **File Link**: [DishLevelTable.tsx](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/dashboard/DishLevelTable.tsx)
*   **Responsibility**: Premium, high-density dashboard matrix representation.
*   **State Ownership**: Local table filtering, sorting column states, active row selections, and localized search inputs.
*   **Backend Interaction**: Directly triggers image generation processes on click.

### 3. `VisualModal`
*   **File Link**: [VisualModal.tsx](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/dashboard/VisualModal.tsx)
*   **Responsibility**: Generative workflow interface.
*   **State Ownership**: Selected design themes, loading spinner states, selected variant indexes, and temporary rendering image URLs.
*   **Backend Interaction**: Coordinates with `/generate-dish-preview` and `/save-selected-visual`.

### 4. `AdminShell`
*   **File Link**: [AdminShell.tsx](file:///d:/menu%20engineering%20verions/menu_studio_engg/10xStudio-AI/menu-engineering-ai-main/frontend/app/components/admin/AdminShell.tsx)
*   **Responsibility**: Enterprise administration console.
*   **State Ownership**: Stores paginated ingestion tables (`uploads`), inspector cache datasets, loading indicators, active database configurations, and database provider state.
*   **Backend Interaction**: Saves configuration changes, fetches dashboard statistics, and tracks database migration targets.

---

## 6. Core Backend Component Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Orchestration Layer                           │
├───────────────────┬───────────────────────────────────┬─────────────────┤
│ server.py         │ menu_engineering_workflow.py     │                 │
└───────────────────┴───────────────────────────────────┴─────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            AI Execution Layer                           │
├───────────────────┬───────────────────────────────────┬─────────────────┤
│ insight_agent.py  │ image_generator.py                │ cuisine_agent.py│
└───────────────────┴───────────────────────────────────┴─────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Infrastructure Layer                          │
├──────────────────┬───────────────────┬──────────────────┬───────────────┤
│ db_provider.py   │ firestore_client. │ storage_client.py│ runtime_      │
│                  │ py                │                  │ config.py     │
└──────────────────┴───────────────────┴──────────────────┴───────────────┘
```

### Infrastructure Layer Details
*   **`db_provider.py`**: Definitively decouples the database operations from raw Firebase calls. Serves as a dynamic interface pattern that selects active clients on-the-fly.
*   **`firestore_client.py`**: Initializes the Firestore client with service account credentials, handling pool management and secure document requests.
*   **`storage_client.py`**: hardens GCS access by enforcing strictly private permissions (stripping `make_public()` calls and ACL modifiers).
*   **`runtime_config.py`**: Hosts in-memory runtime variables (`DATABASE_PROVIDER = "firebase"`) allowing dynamic reconfiguration.

---

## 7. Database Architecture & Collections Rationale

```
  ┌───────────────────────┐          ┌───────────────────────┐
  │  uploads_collection   │          │  dishes_collection    │
  ├───────────────────────┤          ├───────────────────────┤
  │ PK: upload_id         │◄───┐     │ PK: dish_id           │
  │ file_name             │    │     │ FK: upload_id         │
  │ status                │    │     │ dish_name             │
  │ total_revenue         │    │     │ Category (Puzzle,Dog) │
  │ cuisine_category      │    │     │ profit_margin         │
  └───────────────────────┘    │     └───────────────────────┘
                               │
  ┌───────────────────────┐    │     ┌───────────────────────┐
  │ dashboard_ai_insights │◄───┼────►│  visual_audits_collection
  ├───────────────────────┤    │     ├───────────────────────┤
  │ PK: insight_id        │    │     │ PK: audit_id          │
  │ FK: upload_id         │◄───┘     │ FK: upload_id         │
  │ executive_summary     │          │ dish_name             │
  │ overall_profit_advice │          │ gcs_path              │
  └───────────────────────┘          └───────────────────────┘
```

### Collection Explanations

#### 1. `uploads_collection`
*   **Purpose**: Tracks high-level menu upload sessions.
*   **Primary Fields**: `upload_id` (PK), `file_name`, `status`, `uploaded_at`, `total_revenue`, `total_profit`, `cuisine_category`, `database_provider`.
*   **Why Separated**: Isolates session metadata from high-volume dish records to allow lightweight table loading and telemetry checks.

#### 2. `dishes_collection`
*   **Purpose**: Stores categorized menu item outputs.
*   **Primary Fields**: `dish_id` (PK), `upload_id` (FK), `dish_name`, `revenue`, `profit`, `profit_margin`, `category` (Star, Puzzle, Plowhorse, Dog).
*   **Why Separated**: Enables granular filtering, custom sorting, and per-dish visual intelligence matching.

#### 3. `dashboard_ai_insights_collection`
*   **Purpose**: Persists deep AI advice generated for an upload.
*   **Primary Fields**: `insight_id` (PK), `upload_id` (FK), `executive_summary`, `overall_profit_advice`, `generated_at`.
*   **Why Separated**: Keeps heavy text payloads decoupled from index queries, optimization parsing, and table lookups.

#### 4. `visual_audits_collection`
*   **Purpose**: Manages auditing trails of selected generated visual elements.
*   **Primary Fields**: `audit_id` (PK), `upload_id` (FK), `dish_name`, `style`, `gcs_path`, `local_path`, `created_at`.
*   **Why Separated**: Ensures that the generation history and cloud metadata are kept secure, keeping storage traces fully auditable.

---

## 8. Hardened Storage & Asset Rendering Flow

### 1. Local-First Rendering Sandbox
To optimize memory performance and cost, the application relies on a local-first file loop during generation:
1.  Calling `/generate-dish-preview` creates three image variants on local disk (`localimages/`).
2.  The React client previews these assets using standard, relative local paths.
3.  Because the browser reads from the local environment, the platform completely bypasses cloud charges during draft selections.

### 2. Private Google Cloud Storage Architecture
Security is enforced by making GCS access strictly private:
*   **Zero Public URLs**: Under `storage_client.py`, all public URL generation parameters and `blob.make_public()` modifiers are completely disabled.
*   **Metadata Integration**: When the user saves an image, the backend reads it from local disk, uploads it to GCS, and stores the internal GCS path (e.g. `gcs://menu-engineering-bucket/dish_audits/...`) inside Firestore.
*   **Asset Safety**: The actual cloud-based files are securely isolated from public web traffic, remaining fully protected inside the private environment.

---

## 9. Runtime Configuration & Provider Abstraction

The database access layer uses an interface-oriented provider pattern:

```
                  ┌──────────────────────┐
                  │   DatabaseProvider   │
                  │   (Abstract Class)   │
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
   ┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
   │FirebaseProvider │ │ Supabase │ │PostgreSQLProvider│
   └─────────────────┘ └──────────┘ └──────────────────┘
```

*   **Concrete Strategy Selection**: Files instantiate database calls via `get_database_provider()`, which reads the current active provider from memory (`runtime_config.py`).
*   **Runtime Switches**: An admin can toggle the selected provider dynamically in the UI. A `POST /admin/database-provider` call reconfigures `runtime_config.DATABASE_PROVIDER` in-memory.
*   **Seamless Extensibility**: Adding a new database client requires only implementing a concrete class extending `DatabaseProvider` without changing any endpoints or frontend code.

---

## 10. Operational Caching & High-Performance Features

The codebase uses a series of high-performance architectural patterns:
1.  **Dual-Tier UI Caching**: Caches paginated ingestion lists (`pagesCache`) and details lookups (`detailsCache`) in React memory to minimize database read overhead.
2.  **Telemetry Data Rollups**: The platform metrics route utilizes lightweight Firestore collection aggregations (`.count().get()`) rather than pulling complete tables, saving network bandwidth and query quotas.
3.  **Clean JSON Serialization**: Employs robust numeric parsing and timestamp serialization handlers to avoid floating-point errors.
4.  **Logging Traces**: Backend processing stages are completely traced using standardized structured logging headers (`Received menu engineering request...`, `Successfully uploaded...`), facilitating fast debugging.

---

## 11. Known Strengths & Future Scalability Opportunities

### Known Strengths
*   **Strong Decoupling**: Frontend canvas engines, backend servers, AI clients, and storage clients operate as independent modules.
*   **Strict Storage Controls**: The GCS storage bridge is completely secured, preventing data exposure.
*   **Interface-Driven DB Integration**: The database provider abstraction ensures the codebase is completely future-proof.

### Future Scalability Opportunities
*   **Authentication & Tenant Separation**: Integrating Auth0 or Firebase Auth for secure tenant routing.
*   **Enterprise Message Queue**: Offloading heavy AI operations (Gemini processing, image generation) to background task managers (Celery/Redis) rather than executing synchronously in API requests.
*   **Dynamic Cache Eviction**: Moving local caches to a centralized Redis system to share cached data across multiple application servers.
*   **Periodic Metrics Snapshots**: Writing cron-based daily snapshot metrics inside Firestore for fast analytical reports.
