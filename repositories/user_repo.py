# repositories/user_repo.py
from cosmos_client import cosmos_manager
from repositories.repo import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        container = cosmos_manager.get_container("users", partition_key="/username")
        super().__init__(container)
