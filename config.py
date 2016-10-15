WTF_CSRF_ENABLED = True
SECRET_KEY = 'csrf-key'

MONGO_HOST = 'mongo'
MONGO_DBNAME = 'gspotsyncer'

TEST_MONGO_HOST = 'mongo'
TEST_MONGO_DBNAME = 'gspotsyncer_test'

SPOTIFY_CLIENT_ID = 'spotify-client-id'
SPOTIFY_CLIENT_SECRET = 'spotify-client-secret'

CACHE_TYPE = 'memcached'
CACHE_MEMCACHED_SERVERS = ['memcached']

TEMPLATES_AUTO_RELOAD = True

SESSION_COOKIE_DOMAIN='.gspotsyncer.com'