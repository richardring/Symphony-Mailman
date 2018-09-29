import botlog as log
import config
import email_server.caching.cache_mongo as mongo
import email_server.caching.cache_sqlite as sqlite

CacheEnabled = True

if config.CacheType == 'sqlite':
    User_Cache = sqlite.UserCache(config.CacheConfigs['sqlite'])
    User_Cache.Clear_All()
elif config.CacheType == 'mongodb':
    User_Cache = mongo.UserCache(config.CacheConfigs['mongodb'])
    log.LogConsoleInfoVerbose('Testing connection to MongoDB...')
    CacheEnabled = User_Cache.Test_Conn()
    suc = 'succeeded!' if CacheEnabled else 'failed :('
    log.LogConsoleInfoVerbose('Connection test ' + suc)
    log.LogConsoleInfoVerbose('Clearing Cache...')
    User_Cache.Clear_All()