import redis

Redis={
    'host':'localhost',
    'port':'6379',
    'db':0,
    'db1':1,
    'db2':2
}
redis_client=redis.StrictRedis(
    host=Redis['host'],
    port=Redis['port'],
    db=Redis['db'],
    decode_responses=True
)
redis_client_db1 = redis.StrictRedis(
    host=Redis['host'],
    port=Redis['port'],
    db=Redis['db1'],
    decode_responses=False
)
redis_client_db2 = redis.StrictRedis(
    host=Redis['host'],
    port=Redis['port'],
    db=Redis['db2'],
    decode_responses=False
)
RabbitMq={
    'host':'localhost',
    'port':'5672',
    'username':'guest'
}
json_path=r'C:\Users\sravs\Downloads\vedanta\camera_data.json'