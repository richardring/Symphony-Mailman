from pymongo import MongoClient
import pymongo.errors

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

    def Test_Conn(self):
        retVal = False
        try:
            cache_item = self.user_cache.find_one()
            retVal = True
        except pymongo.errors.ConnectionFailure as conn_ex:
            exceptions.LogException(conn_ex)
        except pymongo.errors.ServerSelectionTimeoutError as timeout_ex:
            exceptions.LogException(timeout_ex)
        except Exception as ex:
            exceptions.LogException(ex)

        return retVal

    def Get_Id(self, email_address: str):
        cache_item = self.user_cache.find_one({'email_address': email_address})

        if cache_item:
            return cache_item['symphony_id'], cache_item['pretty_name']

        return '', ''

    def Delete_Id(self, id: str):
        self.user_cache.delete_one({'symphony_id': id})

    def Insert_Id(self, email_address: str, symphony_id: str, pod_id: str, pretty_name: str=''):
        cache_item = {
            'email_address': email_address,
            'symphony_id': symphony_id,
            'pod_id': pod_id,
            'pretty_name': pretty_name
        }

        result = self.user_cache.insert_one(cache_item)

    def Clear_All(self):
        self.user_cache.drop()