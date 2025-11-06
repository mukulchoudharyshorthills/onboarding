try:
    from pymongo import MongoClient  # type: ignore
except ImportError:
    raise ImportError("pymongo is not installed. Install it with: pip install pymongo")
import os

def get_database():
    CONNECTION_STRING = os.getenv('COSMOS_URL')
    client = MongoClient(CONNECTION_STRING)
    db_name = os.getenv('COSMOS_DATABASE')
    if db_name not in client.list_database_names():
        client[db_name].command("ping")  # This will create the database if it doesn't exist
    return client[db_name]
    