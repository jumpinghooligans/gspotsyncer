from boto.dynamodb2.fields import HashKey,RangeKey
from boto.dynamodb2.table import Table

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

DYNAMO_TABLES = [
    Table('users', schema=[HashKey('username')]),
    Table('playlists', schema=[HashKey('username')])
]