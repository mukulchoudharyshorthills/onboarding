# repositories/transaction_repo.py
from cosmos_client import cosmos_manager
from repositories.base_repo import BaseRepository

class LogRepository(BaseRepository):
    def __init__(self):
        container = cosmos_manager.get_container("logs", partition_key="/type")
        super().__init__(container)
