import redis
import os
from dotenv import load_dotenv
load_dotenv()
redis_host=os.getenv("REDIS_HOST")
def get_redis_object():
    redis_pointer = redis.StrictRedis(host="localhost", port=6379, db=0)
    try:
        return redis_pointer
    except Exception as e:
        print(e)
    finally:
        redis_pointer.close()