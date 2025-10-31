# cosmos_client.py
import os
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "mydatabase")

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("Please set COSMOS_ENDPOINT and COSMOS_KEY in .env")

class CosmosDBManager:
    def __init__(self, endpoint, key, database_name):
        self.client = CosmosClient(endpoint, key)
        self.database_name = database_name
        self.database = self.client.create_database_if_not_exists(id=self.database_name)
        self.containers = {}

    def get_container(self, name, partition_key="/category"):
        if name not in self.containers:
            container = self.database.create_container_if_not_exists(
                id=name,
                partition_key=PartitionKey(path=partition_key),
                offer_throughput=400
            )
            self.containers[name] = container
        return self.containers[name]

# Singleton instance
cosmos_manager = CosmosDBManager(COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE)
