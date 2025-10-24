try:
    from pymongo import MongoClient  # type: ignore
except ImportError:
    raise ImportError("pymongo is not installed. Install it with: pip install pymongo")


def get_database():
    CONNECTION_STRING = "mongodb://localhost:27017/"
    client = MongoClient(CONNECTION_STRING)
    db_name = "onboarding"
    if db_name not in client.list_database_names():
        client[db_name].command("ping")  # This will create the database if it doesn't exist
    return client[db_name]
    