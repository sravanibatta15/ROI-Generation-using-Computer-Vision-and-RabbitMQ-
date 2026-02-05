import sys
import cv2
import json
import numpy as np
import pika
import base64
from datetime import datetime
from log_code import Logger
from display_manager import Display
from rabbitMq import MQ_SERVER
from config import RabbitMq
from model import YoloV7
from connection import CONNECTION
import warnings

warnings.filterwarnings('ignore')
logger = Logger.get_logs('consumer')


class RECIVER:
    def __init__(self):
        try:
            logger.info("Initializing receiver")

            self.rab = MQ_SERVER()
            self.host = RabbitMq['host']
            self.window_name = None
            self.win_names = []
            self.frame_id = 0

            self.load_datta = CONNECTION()
            self.yolo = YoloV7(r"C:\Users\sravs\Downloads\vedanta\best.pt")
            logger.info("YOLO model loaded successfully")

            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()

            # Raw frame queue
            self.channel.queue_declare(queue='frame_queue')
            self.channel.exchange_declare(exchange='frame_exchange', exchange_type='direct')

            # Raw frame to ROI queue
            self.channel.queue_declare(queue='frame_detect_queue')
            self.channel.exchange_declare(exchange='frame_detect_exchange', exchange_type='direct')
            self.channel.queue_bind(
                queue='frame_detect_queue',
                exchange='frame_detect_exchange',
                routing_key='frame.detect'
            )

            logger.info("Connected to RabbitMQ")

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def comsumer(self):
        try:
            logger.info("Starting consumer")

            self.channel.queue_bind(
                queue='frame_queue',
                exchange='frame_exchange',
                routing_key='#'
            )

            self.channel.basic_consume(
                queue='frame_queue',
                on_message_callback=self.frame_cap,
                auto_ack=True
            )

            self.channel.start_consuming()

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def frame_cap(self, channel, method, properties, body):
        try:
            self.frame_id += 1
            logger.info(f"[FRAME RECEIVED] frame_id={self.frame_id}")

            routing_key = method.routing_key
            self.th_id, self.cam_id, self.cam_name = routing_key.split("/")

            redis_data = self.load_datta.connecting_to_redis()
            usecase = redis_data[self.cam_name]['use_case']
            logger.info(f"usecase: {usecase}")

            self.window_name = f"{self.cam_id}|{self.th_id}|{self.cam_name}"
            if self.window_name not in self.win_names:
                self.win_names.append(self.window_name)

            if not body:
                logger.warning("[EMPTY FRAME BODY]")
                self.close_window(self.window_name)
                return

            # ===== Decode RAW frame =====
            frame = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                logger.error("[FRAME DECODE FAILED]")
                return

            # ===== Run YOLO (for local display/logging only) =====
            detections, _ = self.yolo.inference(frame)
            filtered_detections = [det for det in detections if det[0] in usecase]

            detection_payload = {
                "frame_id": self.frame_id,
                "thread_id": self.th_id,
                "cam_id": self.cam_id,
                "cam_name": self.cam_name,
                "timestamp": datetime.utcnow().isoformat(),
                "detections": []
            }

            for det in filtered_detections:
                cls_name, score, (x1, y1, x2, y2) = det
                detection_payload["detections"].append({
                    "class": cls_name,
                    "confidence": float(score),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })

            # ===== DO NOT draw boxes on frame =====
            # We keep frame RAW

            # ===== Send RAW frame only =====
            if usecase != ['person']:
                _, encoded = cv2.imencode('.jpg', frame)   # RAW frame
                frame_b64 = base64.b64encode(encoded).decode("utf-8")

                frame_detect_message = {
                    "meta": detection_payload,
                    "frame_b64": frame_b64
                }

                payload_bytes = json.dumps(frame_detect_message).encode("utf-8")

                self.channel.basic_publish(
                    exchange='frame_detect_exchange',
                    routing_key='frame.detect',
                    body=payload_bytes
                )

                logger.info(
                    f"[RAW FRAME SENT] frame_id={self.frame_id}, "
                    f"detections={len(detection_payload['detections'])}"
                )
            else:
                logger.info(
                    f"[SKIPPED SEND] frame_id={self.frame_id} because usecase={usecase}"
                )
                #===== Send RAW frame to SEGMENT queue if usecase == ['person'] =====
                # _, encoded = cv2.imencode('.jpg', frame)
                # frame_b64 = base64.b64encode(encoded).decode("utf-8")
                #
                # segment_message = {
                #     "meta": detection_payload,
                #     "frame_b64": frame_b64
                # }
                #
                # payload_bytes = json.dumps(segment_message).encode("utf-8")
                #
                # self.channel.basic_publish(
                #     exchange='frame_segment_exchange',
                #     routing_key='frame.segment',
                #     body=payload_bytes
                # )
                #
                # logger.info(f"[RAW FRAME SENT TO SEGMENT] frame_id={self.frame_id}")

            # ===== Local display WITH boxes (optional) =====
            Display.show_frame(
                self.window_name,
                frame.copy(),  # raw copy
                detections=filtered_detections,
                cam_name=self.cam_name
            )

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def close_window(self, wind_name):
        try:
            logger.info(f"[WINDOW CLOSED] {wind_name}")
            Display.close_win(wind_name)
            if wind_name in self.win_names:
                self.win_names.remove(wind_name)

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")


if __name__ == '__main__':
    obj = RECIVER()
    obj.comsumer()
