# repositories/document_repo.py
from cosmos_client import cosmos_manager
from repositories.repo import BaseRepository

class DocumentRepository(BaseRepository):
    def __init__(self):
        container = cosmos_manager.get_container("documents", partition_key="/user_id")
        super().__init__(container)
