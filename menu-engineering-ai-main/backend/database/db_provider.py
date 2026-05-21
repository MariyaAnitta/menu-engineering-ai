import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from google.cloud.firestore import FieldFilter
from .firestore_client import get_db
from utils.json_utils import convert_numpy_types

class DatabaseProvider(ABC):
    @abstractmethod
    def save_file_metadata(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def save_menu_items(self, menu_items: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def save_dashboard_ai_insights(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def save_visual_audit(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def get_visual_audit(self, file_name: str, dish_name: str):
        pass

    @abstractmethod
    def get_uploads(self, limit: int = 5, start_after_id: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_upload_details(self, upload_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_platform_metrics(self) -> Dict[str, Any]:
        pass

class FirebaseProvider(DatabaseProvider):
    def __init__(self):
        self.db = get_db()

    def get_visual_audit(self, file_name: str, dish_name: str):
        """
        Retrieves visual audit for a specific dish and file from visual_audits_collection.
        """
        try:
            # We search by file_name and dish_name
            docs = self.db.collection("visual_audits_collection")\
                .where(filter=FieldFilter("file_name", "==", file_name))\
                .where(filter=FieldFilter("dish_name", "==", dish_name))\
                .limit(1).get()
            
            for doc in docs:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Firebase get_visual_audit error: {e}")
            return None

    def save_file_metadata(self, data: Dict[str, Any]):
        """
        Collection: uploads_collection
        """
        try:
            upload_id = data.get("upload_id")
            if not upload_id:
                return False
            doc_ref = self.db.collection("uploads_collection").document(upload_id)
            safe_data = convert_numpy_types(data)
            doc_ref.set(safe_data)
            return True
        except Exception as e:
            print(f"Firebase save_file_metadata error: {e}")
            return False

    def save_menu_items(self, menu_items: List[Dict[str, Any]]):
        """
        Collection: dishes_collection
        """
        try:
            batch = self.db.batch()
            safe_menu_items = convert_numpy_types(menu_items)
            for item in safe_menu_items:
                dish_id = item.get("dish_id")
                if not dish_id:
                    continue
                doc_ref = self.db.collection("dishes_collection").document(dish_id)
                batch.set(doc_ref, item)
            batch.commit()
            return True
        except Exception as e:
            print(f"Firebase save_menu_items error: {e}")
            return False

    def save_dashboard_ai_insights(self, data: Dict[str, Any]):
        """
        Collection: dashboard_ai_insights_collection
        """
        try:
            insight_id = data.get("insight_id")
            if not insight_id:
                return False
            doc_ref = self.db.collection("dashboard_ai_insights_collection").document(insight_id)
            safe_data = convert_numpy_types(data)
            doc_ref.set(safe_data)
            return True
        except Exception as e:
            print(f"Firebase save_dashboard_ai_insights error: {e}")
            return False

    def save_visual_audit(self, data: Dict[str, Any]):
        """
        Collection: visual_audits_collection
        """
        try:
            audit_id = data.get("audit_id")
            if not audit_id:
                return False
            doc_ref = self.db.collection("visual_audits_collection").document(audit_id)
            safe_data = convert_numpy_types(data)
            doc_ref.set(safe_data, merge=True)
            return True
        except Exception as e:
            print(f"Firebase save_visual_audit error: {e}")
            return False

    def get_uploads(self, limit: int = 5, start_after_id: str = None):
        """
        Fetch paginated uploads from uploads_collection, ordered by uploaded_at descending.
        """
        try:
            query = self.db.collection("uploads_collection").order_by("uploaded_at", direction="DESCENDING")
            if start_after_id:
                start_doc_ref = self.db.collection("uploads_collection").document(start_after_id)
                start_doc = start_doc_ref.get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            docs = query.limit(limit + 1).get()
            
            uploads_list = []
            for doc in docs[:limit]:
                d = doc.to_dict()
                upload_id = d.get("upload_id") or doc.id
                
                cuisine_category = d.get("cuisine_category")
                if not cuisine_category:
                    dish_docs = self.db.collection("dishes_collection")\
                        .where(filter=FieldFilter("upload_id", "==", upload_id))\
                        .limit(1).get()
                    for dd in dish_docs:
                        cuisine_category = dd.to_dict().get("category")
                
                uploads_list.append({
                    "upload_id": upload_id,
                    "file_name": d.get("file_name", "Unknown File"),
                    "status": d.get("status", "processed"),
                    "uploaded_at": d.get("uploaded_at", ""),
                    "dish_count": d.get("row_count") or d.get("dish_count") or 0,
                    "total_revenue": d.get("total_revenue", 0),
                    "cuisine_category": cuisine_category or "Uncategorized",
                    "database_provider": "firebase"
                })
                
            has_more = len(docs) > limit
            next_page_cursor = uploads_list[-1]["upload_id"] if uploads_list and has_more else None
            
            return {
                "uploads": uploads_list,
                "next_page_cursor": next_page_cursor,
                "has_more": has_more
            }
        except Exception as e:
            print(f"Firebase get_uploads error: {e}")
            return {
                "uploads": [],
                "next_page_cursor": None,
                "has_more": False
            }

    def get_upload_details(self, upload_id: str):
        """
        Fetch details from dishes_collection, dashboard_ai_insights_collection,
        and visual_audits_collection for the given upload_id.
        """
        try:
            upload_ref = self.db.collection("uploads_collection").document(upload_id)
            upload_doc = upload_ref.get()
            if not upload_doc.exists:
                return None
                
            upload_data = upload_doc.to_dict()
            
            dishes = self.db.collection("dishes_collection")\
                .where(filter=FieldFilter("upload_id", "==", upload_id)).get()
            dish_count = len(dishes)
            
            cuisine_category = upload_data.get("cuisine_category")
            if not cuisine_category and dishes:
                cuisine_category = dishes[0].to_dict().get("category")
                
            insight_docs = self.db.collection("dashboard_ai_insights_collection")\
                .where(filter=FieldFilter("upload_id", "==", upload_id))\
                .limit(1).get()
            
            ai_insight_summary = "No insights available."
            for doc in insight_docs:
                ai_insight_summary = doc.to_dict().get("executive_summary") or "No executive summary found."
                
            audit_docs = self.db.collection("visual_audits_collection")\
                .where(filter=FieldFilter("upload_id", "==", upload_id)).get()
            visual_audit_count = len(audit_docs)
            
            return {
                "upload_metadata": {
                    "upload_id": upload_id,
                    "file_name": upload_data.get("file_name", "Unknown File"),
                    "status": upload_data.get("status", "processed"),
                    "uploaded_at": upload_data.get("uploaded_at", ""),
                    "total_revenue": upload_data.get("total_revenue", 0),
                    "total_profit": upload_data.get("total_profit", 0)
                },
                "dish_count": dish_count,
                "ai_insight_summary": ai_insight_summary,
                "visual_audit_count": visual_audit_count,
                "total_revenue": upload_data.get("total_revenue", 0),
                "cuisine_category": cuisine_category or "Uncategorized",
                "processing_status": upload_data.get("status", "processed")
            }
        except Exception as e:
            print(f"Firebase get_upload_details error: {e}")
            return None

    def get_platform_metrics(self):
        """
        Aggregate platform metrics dynamically from Firestore collections.
        """
        try:
            total_uploads = self.db.collection("uploads_collection").count().get()[0][0].value
            total_dishes_processed = self.db.collection("dishes_collection").count().get()[0][0].value
            total_visual_audits = self.db.collection("visual_audits_collection").count().get()[0][0].value
            total_ai_insights = self.db.collection("dashboard_ai_insights_collection").count().get()[0][0].value
            
            latest_file_name = "None"
            latest_upload_timestamp = "None"
            latest_upload_status = "None"
            
            latest_docs = self.db.collection("uploads_collection").order_by("uploaded_at", direction="DESCENDING").limit(1).get()
            for doc in latest_docs:
                d = doc.to_dict()
                latest_file_name = d.get("file_name") or "Unknown"
                latest_upload_timestamp = d.get("uploaded_at") or "Unknown"
                latest_upload_status = d.get("status") or "processed"
            
            try:
                persisted_visual_assets = self.db.collection("visual_audits_collection")\
                    .order_by("gcs_path").count().get()[0][0].value
            except Exception:
                persisted_visual_assets = total_visual_audits
                
            total_persisted_uploads = self.db.collection("uploads_collection")\
                .where(filter=FieldFilter("status", "==", "processed")).count().get()[0][0].value
            
            return {
                "total_uploads": total_uploads,
                "total_dishes_processed": total_dishes_processed,
                "total_visual_audits": total_visual_audits,
                "total_ai_insights": total_ai_insights,
                "latest_file_name": latest_file_name,
                "latest_upload_timestamp": latest_upload_timestamp,
                "latest_upload_status": latest_upload_status,
                "persisted_visual_assets": persisted_visual_assets,
                "total_persisted_uploads": total_persisted_uploads
            }
        except Exception as e:
            print(f"Firebase get_platform_metrics error: {e}")
            return {
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

class SupabaseProvider(DatabaseProvider):
    # Placeholder for future Supabase implementation
    def save_file_metadata(self, data: Dict[str, Any]):
        print("SupabaseProvider: save_file_metadata (Not Implemented)")
        pass

    def save_menu_items(self, menu_items: List[Dict[str, Any]]):
        print("SupabaseProvider: save_menu_items (Not Implemented)")
        pass

    def save_dashboard_ai_insights(self, data: Dict[str, Any]):
        print("SupabaseProvider: save_dashboard_ai_insights (Not Implemented)")
        pass

    def save_visual_audit(self, data: Dict[str, Any]):
        print("SupabaseProvider: save_visual_audit (Not Implemented)")
        pass

    def get_visual_audit(self, file_name: str, dish_name: str):
        print("SupabaseProvider: get_visual_audit (Not Implemented)")
        return None

    def get_uploads(self, limit: int = 5, start_after_id: str = None):
        print("SupabaseProvider: get_uploads (Not Implemented)")
        return {"uploads": [], "next_page_cursor": None, "has_more": False}

    def get_upload_details(self, upload_id: str):
        print("SupabaseProvider: get_upload_details (Not Implemented)")
        return None

    def get_platform_metrics(self):
        print("SupabaseProvider: get_platform_metrics (Not Implemented)")
        return {
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

class PostgreSQLProvider(DatabaseProvider):
    # Placeholder for future PostgreSQL implementation
    def save_file_metadata(self, data: Dict[str, Any]):
        print("PostgreSQLProvider: save_file_metadata (Not Implemented)")
        pass

    def save_menu_items(self, menu_items: List[Dict[str, Any]]):
        print("PostgreSQLProvider: save_menu_items (Not Implemented)")
        pass

    def save_dashboard_ai_insights(self, data: Dict[str, Any]):
        print("PostgreSQLProvider: save_dashboard_ai_insights (Not Implemented)")
        pass

    def save_visual_audit(self, data: Dict[str, Any]):
        print("PostgreSQLProvider: save_visual_audit (Not Implemented)")
        pass

    def get_visual_audit(self, file_name: str, dish_name: str):
        print("PostgreSQLProvider: get_visual_audit (Not Implemented)")
        return None

    def get_uploads(self, limit: int = 5, start_after_id: str = None):
        print("PostgreSQLProvider: get_uploads (Not Implemented)")
        return {"uploads": [], "next_page_cursor": None, "has_more": False}

    def get_upload_details(self, upload_id: str):
        print("PostgreSQLProvider: get_upload_details (Not Implemented)")
        return None

    def get_platform_metrics(self):
        print("PostgreSQLProvider: get_platform_metrics (Not Implemented)")
        return {
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

def get_database_provider(provider: str = "firebase") -> DatabaseProvider:
    match provider.lower():
        case "firebase":
            return FirebaseProvider()
        case "supabase":
            return SupabaseProvider()
        case "postgresql":
            return PostgreSQLProvider()
        case _:
            raise ValueError(f"Unsupported database provider: {provider}")
