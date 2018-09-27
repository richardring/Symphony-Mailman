import config
import email_server.caching.cache_mongo as mongo
import email_server.caching.cache_sqlite as sqlite

if config.CacheType == 'sqlite':
    User_Cache = sqlite.UserCache(config.CacheConfigs['sqlite'])
elif config.CacheType == 'mongodb':
    User_Cache = mongo.UserCache(config.CacheConfigs['mongodb'])