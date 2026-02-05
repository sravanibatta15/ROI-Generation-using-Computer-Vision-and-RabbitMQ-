import json
import sys
from config import redis_client, json_path
from log_code import Logger

logger = Logger.get_logs('connection')
class  CONNECTION:

    def connecting_to_redis(self):
        try:
            key = "camera_config"

            with open(json_path, "r") as f:
                file_data = json.load(f)
            redis_value = redis_client.get(key)

            if redis_value is None:
                logger.info("No data found in Redis. Writing JSON file data to Redis.")
                redis_client.set(key, json.dumps(file_data))
                logger.info(f'data dumped:{file_data}')
                return file_data

            logger.info("Data found in Redis. Loading from Redis.")
            logger.info(f'data found:{json.loads(redis_value)}')
            return json.loads(redis_value)
        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
