from pymongo import MongoClient

import botlog as log
from email_server.caching.cache import Cache
import exceptions


class UserCache(Cache):
    def __init__(self, cache_config):
        super().__init__(cache_config)

        self._cache_config = cache_config
        self.mongo_client = None
        self.mongo_db = None
        self.user_cache = None

        self.Get_Connection()

    def Get_Connection(self):
        self.mongo_client = MongoClient(self._cache_config['conn_str'], serverSelectionTimeoutMS=10)
        self.mongo_db = self.mongo_client[self._cache_config['db_name']]
        self.user_cache = self.mongo_db['user_cache']

    def Get_Id(self, email_address: str) -> str:
        cache_item = self.user_cache.find_one({'email_address': email_address})

        if cache_item:
            return cache_item['symphony_id']

        return ''

    def Delete_Id(self, id: str):
        self.user_cache.delete_one({'symphony_id': id})

    def Insert_Id(self, email_address: str, symphony_id: str, pod_id: str):
        cache_item = {
            'email_address': email_address,
            'symphony_id': symphony_id,
            'pod_id': pod_id
        }

        result = self.user_cache.insert_one(cache_item)

    def Clear_All(self):
        self.user_cache.drop()