import sys
import os
import pika
import cv2
import numpy as np
from seg import YOLOv7U7Seg
from log_code import Logger
from config import RabbitMq
from rabbitMq import MQ_SERVER
from display_manager import Display
from connection import CONNECTION

logger = Logger.get_logs("SEG_SERVER")

class SegmentServer:
    def __init__(self):
        try:
            os.environ["YOLOv7_IGNORE_GIT"] = "1"
            self.rab = MQ_SERVER()
            self.host = RabbitMq["host"]
            self.usecases = {}

            logger.info("Loading segmentation model...")
            self.seg = YOLOv7U7Seg(weights="yolov7-seg.pt",
                device="cpu")
            logger.info("Connecting to RabbitMQ...")
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange="frame_exchange", exchange_type="direct")
            self.channel.queue_declare(queue="frame_queue")
            logger.info("SEGMENTATION SERVER READY")


        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def callback(self, ch, method, properties, body):
        try:
            _, cam_id, cam_name = method.routing_key.split("/")
            win_name = f"{cam_name} | SEG | CAM {cam_id}"

            if not body:
                Display.close_win(win_name)
                return
            frame = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
            # fetch usecases
            if cam_name not in self.usecases:
                redis_data = CONNECTION().connecting_to_redis()
                self.usecases[cam_name] = redis_data[cam_name]["use_case"]

            uc = self.usecases[cam_name]
            if "person" in uc:
                self.seg.infer_frame_roi(frame,classes=[0],win_name=win_name)

                route_key = f"segment.{_}.{cam_id}"
                _, encode = cv2.imencode('.jpg', frame)
                frame_byte = encode.tobytes()
                self.rab.send_detect(frame_byte, route_key)


        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def start(self):
        try:
            self.channel.queue_bind(queue="frame_queue", exchange="frame_exchange", routing_key="#")
            self.channel.basic_consume(queue="frame_queue", on_message_callback=self.callback, auto_ack=True)

            logger.info("SEGMENTATION SERVER RUNNING...")
            self.channel.start_consuming()
        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")


if __name__ == "__main__":
    SegmentServer().start()
