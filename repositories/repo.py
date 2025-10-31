# repositories/base_repo.py
import uuid
from azure.cosmos import exceptions

class BaseRepository:
    def __init__(self, container):
        self.container = container
        self.partition_key_field = container._properties["partitionKey"]["paths"][0].lstrip("/")

    def create_item(self, item: dict):
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        if self.partition_key_field not in item:
            item[self.partition_key_field] = "default"
        return self.container.create_item(body=item)

    def get_item(self, item_id: str, partition_value: str):
        try:
            return self.container.read_item(item=item_id, partition_key=partition_value)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def list_items(self, query: str = "SELECT * FROM c"):
        return list(self.container.query_items(query=query, enable_cross_partition_query=True))

    def update_item(self, item_id: str, partition_value: str, new_data: dict):
        new_data["id"] = item_id
        new_data[self.partition_key_field] = partition_value
        try:
            return self.container.replace_item(item=item_id, body=new_data)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def delete_item(self, item_id: str, partition_value: str):
        try:
            self.container.delete_item(item=item_id, partition_key=partition_value)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
