import pika
import sys
from config import RabbitMq
from log_code import Logger
logger = Logger.get_logs('rabbitmq')
import warnings
warnings.filterwarnings('ignore')


class MQ_SERVER:
    def __init__(self):
        try:
            self.host = RabbitMq['host']
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()

            # ===== Existing setup =====
            self.channel.queue_declare(queue='frame_queue')
            self.channel.exchange_declare(exchange='frame_exchange', exchange_type='direct')

            self.channel.queue_declare(queue='detect_out')
            self.channel.queue_declare(queue='segment_out')
            self.channel.exchange_declare(exchange='detect_exchange', exchange_type='topic')

            self.channel.queue_bind(queue='detect_out',
                                    exchange='detect_exchange',
                                    routing_key="detect.#")
            self.channel.queue_bind(queue='segment_out',
                                    exchange='detect_exchange',
                                    routing_key="segment.#")

            # ===== frame_detect_queue setup =====
            self.channel.queue_declare(queue='frame_detect_queue')
            self.channel.exchange_declare(exchange='frame_detect_exchange', exchange_type='direct')

            self.frame_detect_routing_key = "frame.detect"

            self.channel.queue_bind(
                queue='frame_detect_queue',
                exchange='frame_detect_exchange',
                routing_key=self.frame_detect_routing_key
            )

            # ===== NEW: frame_segment_queue setup =====
            self.channel.queue_declare(queue='frame_segment_queue')
            self.channel.exchange_declare(exchange='frame_segment_exchange', exchange_type='direct')

            self.frame_segment_routing_key = "frame.segment"

            self.channel.queue_bind(
                queue='frame_segment_queue',
                exchange='frame_segment_exchange',
                routing_key=self.frame_segment_routing_key
            )

            logger.info("RabbitMQ setup completed successfully")

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def sent_frame(self, route_key, frame):
        try:
            logger.info('started..')
            self.channel.queue_bind(queue='frame_queue',
                                    exchange='frame_exchange',
                                    routing_key=route_key)
            self.channel.basic_publish(exchange='frame_exchange',
                                       routing_key=route_key,
                                       body=frame)

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def send_detect(self, frame, route_key):
        try:
            self.channel.basic_publish(exchange='detect_exchange',
                                       routing_key=route_key,
                                       body=frame)
            self.channel.basic_publish(exchange='detect_exchange',
                                       routing_key=route_key,
                                       body=frame)

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    # ===== Send to frame_detect_queue =====
    def send_frame_detect(self, frame):
        try:
            self.channel.basic_publish(
                exchange='frame_detect_exchange',
                routing_key=self.frame_detect_routing_key,
                body=frame
            )
            logger.info("Frame sent to frame_detect_queue")

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    # ===== NEW: Send to frame_segment_queue =====
    def send_frame_segment(self, frame):
        try:
            self.channel.basic_publish(
                exchange='frame_segment_exchange',
                routing_key=self.frame_segment_routing_key,
                body=frame
            )
            logger.info("Frame sent to frame_segment_queue")

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")
