import sys
import cv2
import json
import pika
import base64
import numpy as np
import redis
from log_code import Logger
from config import RabbitMq, Redis
import warnings

warnings.filterwarnings("ignore")
logger = Logger.get_logs("roi_detect")


class ROI_CONSUMER:
    def __init__(self):
        try:
            logger.info("Initializing ROI consumer")

            # RabbitMQ
            self.host = RabbitMq["host"]
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()

            # Queue + Exchange
            self.channel.queue_declare(queue="frame_detect_queue")
            self.channel.exchange_declare(exchange="frame_detect_exchange", exchange_type="direct")
            self.channel.queue_bind(
                queue="frame_detect_queue",
                exchange="frame_detect_exchange",
                routing_key="frame.detect"
            )

            # Store ROI per camera
            self.roi_coords = {}

            # 🔗 Redis DB1 connection (for ROI frames)
            self.redis_db1 = redis.StrictRedis(
                host=Redis["host"],
                port=Redis["port"],
                db=Redis["db1"],
                decode_responses=False   # must be False for binary/image data
            )

            logger.info("Connected to RabbitMQ + Redis DB1 (ROI storage)")

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def start(self):
        try:
            logger.info("Starting ROI consumer...")

            self.channel.basic_consume(
                queue="frame_detect_queue",
                on_message_callback=self.on_message,
                auto_ack=True
            )

            self.channel.start_consuming()

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    # ---------------- ROI LOGIC ----------------
    def get_fixed_roi(self, frame_width, frame_height):
        roi_w = int(frame_width * 0.5)
        roi_h = int(frame_height * 0.6)

        cx = frame_width // 2
        cy = frame_height // 2

        x1 = cx - roi_w // 2
        y1 = cy - roi_h // 2
        x2 = cx + roi_w // 2
        y2 = cy + roi_h // 2

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame_width, x2)
        y2 = min(frame_height, y2)

        return x1, y1, x2, y2

    def normalize_bbox(self, bbox):
        x1, y1, x2, y2 = bbox
        if x2 < x1 or y2 < y1:
            w = x2
            h = y2
            x2 = x1 + w
            y2 = y1 + h
        return int(x1), int(y1), int(x2), int(y2)

    def is_bbox_inside_roi(self, bbox, roi):
        bx1, by1, bx2, by2 = self.normalize_bbox(bbox)
        rx1, ry1, rx2, ry2 = roi
        return (bx1 >= rx1 and by1 >= ry1 and bx2 <= rx2 and by2 <= ry2)

    # ---------------- MAIN CONSUMER ----------------
    def on_message(self, ch, method, properties, body):
        try:
            data = json.loads(body.decode("utf-8"))

            meta = data["meta"]
            frame_b64 = data["frame_b64"]
            cam_id = meta["cam_id"]

            # Decode frame
            frame_bytes = base64.b64decode(frame_b64)
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)

            if frame is None:
                logger.error("[ROI] Failed to decode frame")
                return

            h, w, _ = frame.shape

            # Set ROI once per camera
            if cam_id not in self.roi_coords:
                self.roi_coords[cam_id] = self.get_fixed_roi(w, h)
                rx1, ry1, rx2, ry2 = self.roi_coords[cam_id]
                logger.info(f"FIXED ROI SET cam_id={cam_id} x1={rx1}, y1={ry1}, x2={rx2}, y2={ry2}")

            rx1, ry1, rx2, ry2 = self.roi_coords[cam_id]

            # Draw ROI
            roi_color = (0, 0, 255)
            cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), roi_color, 2)
            cv2.putText(frame, "ROI",
                        (rx1, ry1 - 10 if ry1 - 10 > 10 else ry1 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, roi_color, 2)

            # 🎯 Process ONLY detections inside ROI
            for det in meta["detections"]:
                cls_name = det["class"]
                conf = det["confidence"]
                bbox = det["bbox"]

                inside = self.is_bbox_inside_roi(bbox, self.roi_coords[cam_id])

                if not inside:
                    logger.info(f"[ROI MISS] cam_id={cam_id} class={cls_name} conf={conf:.2f} bbox={bbox}")
                    continue

                logger.info(f"[ROI HIT] cam_id={cam_id} class={cls_name} conf={conf:.2f} bbox={bbox}")

                x1, y1, x2, y2 = self.normalize_bbox(bbox)
                color = (0, 255, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{cls_name} {conf:.2f}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # 💾 SAVE ROI CROP → Redis DB1
            roi_crop = frame[ry1:ry2, rx1:rx2]
            _, buffer = cv2.imencode(".jpg", roi_crop)
            roi_b64 = base64.b64encode(buffer).decode("utf-8")

            redis_key = f"roi_frame:{cam_id}:{meta['frame_id']}"
            self.redis_db1.set(redis_key, roi_b64)

            logger.info(f"[REDIS DB1] ROI frame saved key={redis_key}")

            cv2.imshow(f"ROI Consumer - Cam {cam_id}", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                cv2.destroyAllWindows()
                sys.exit(0)

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")


if __name__ == "__main__":
    obj = ROI_CONSUMER()
    obj.start()
