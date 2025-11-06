from mongodb import get_database

db = get_database()

if "users" not in db.list_collection_names():
    db.create_collection("users")
users = db['users']

if "loginlogs" not in db.list_collection_names():
    db.create_collection("loginlogs")
loginlogs = db['loginlogs']

if "documents" not in db.list_collection_names():
    db.create_collection("documents")
documents = db['documents']

def user_helper(user) -> dict:
    return {
    "id": str(user["_id"]),
    "username": user["username"],
    "password": user["password"],
    "status": user["status"]
    }

def log_helper(log) -> dict:
    return {
    "id": str(log["_id"]),
    "user_id": str(log["user_id"]),
    "time": log["time"],
    "action": log["action"]
    }

def document_helper(document) -> dict:
    return {
    "id": str(document["_id"]),
    "user_id":str(document["user_id"]),
    "path": document["path"],
    "blob_path": document["blob_path"],
    "title": document["title"],
    "tag": document["tag"],
    "data": document.get("data") or "",
    "edited_data": document.get("edited_data") or "",
    "status": document["status"]
    }

__all__ = ["users", "loginlogs", "documents", "user_helper", "document_helper", "log_helper"]