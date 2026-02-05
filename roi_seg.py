import sys
import cv2
import json
import pika
import base64
import numpy as np
import warnings
from log_code import Logger
from config import RabbitMq, Redis
from seg import YOLOv7U7Seg  # Your segmentation model
import redis

warnings.filterwarnings("ignore")
logger = Logger.get_logs("roi_segment_consumer")


class ROI_SEGMENT_CONSUMER:
    def __init__(self):
        try:
            logger.info("Initializing ROI SEGMENT consumer")

            # RabbitMQ connection
            self.host = RabbitMq["host"]
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()

            # Queue + Exchange
            self.channel.queue_declare(queue="frame_segment_queue")
            self.channel.exchange_declare(exchange="frame_segment_exchange", exchange_type="direct")
            self.channel.queue_bind(
                queue="frame_segment_queue",
                exchange="frame_segment_exchange",
                routing_key="frame.segment"
            )

            # Segmentation model
            self.seg_model = YOLOv7U7Seg(weights="yolov7-seg.pt", device="cpu")

            # Redis DB2 for storing ROI frames
            self.redis_db1 = redis.StrictRedis(
                host=Redis["host"],
                port=Redis["port"],
                db=Redis["db2"],
                decode_responses=False
            )

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")

    def start(self):
        self.channel.basic_consume(
            queue="frame_segment_queue",
            on_message_callback=self.on_message,
            auto_ack=True
        )
        logger.info("ROI SEGMENT consumer started...")
        self.channel.start_consuming()

    # ---------------- ROI LOGIC ----------------
    @staticmethod
    def get_fixed_roi(frame_width, frame_height):
        roi_w = int(frame_width * 0.8)  # 80% of frame width
        roi_h = int(frame_height * 0.8)  # 80% of frame height
        cx = frame_width // 2
        cy = frame_height // 2
        x1 = max(0, cx - roi_w // 2)
        y1 = max(0, cy - roi_h // 2)
        x2 = min(frame_width, cx + roi_w // 2)
        y2 = min(frame_height, cy + roi_h // 2)
        return x1, y1, x2, y2

    # ---------------- MAIN CONSUMER ----------------
    def on_message(self, ch, method, props, body):
        try:
            data = json.loads(body.decode("utf-8"))
            meta = data["meta"]
            cam_id = meta["cam_id"]
            frame_b64 = data["frame_b64"]

            # Decode frame
            frame = cv2.imdecode(np.frombuffer(base64.b64decode(frame_b64), np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                logger.error(f"[ROI SEG] Failed to decode frame for cam_id={cam_id}")
                return

            h, w, _ = frame.shape
            rx1, ry1, rx2, ry2 = self.get_fixed_roi(w, h)

            # Draw ROI rectangle on original frame
            frame_with_roi = frame.copy()
            roi_color = (0, 255, 0)
            cv2.rectangle(frame_with_roi, (rx1, ry1), (rx2, ry2), roi_color, 2)
            cv2.putText(
                frame_with_roi,
                "ROI",
                (rx1, ry1 - 10 if ry1 - 10 > 10 else ry1 + 20),cv2.FONT_HERSHEY_SIMPLEX,0.7,roi_color,2,)

            # ---------------- SEGMENTATION ----------------
            # Only segment the ROI crop
            roi_frame = frame[ry1:ry2, rx1:rx2]
            segmented_roi = self.seg_model.infer_frame(roi_frame)  # Apply segmentation on ROI only

            # Place segmented ROI back into original frame
            result_frame = frame.copy()
            result_frame[ry1:ry2, rx1:rx2] = segmented_roi

            # ---------------- SAVE ROI CROP ----------------
            _, buffer = cv2.imencode(".jpg", segmented_roi)
            roi_b64 = base64.b64encode(buffer).decode("utf-8")
            redis_key = f"roi_frame:{cam_id}:{meta['frame_id']}"
            self.redis_db1.set(redis_key, roi_b64)
            logger.info(f"[REDIS DB2] ROI frame saved key={redis_key}")

            # ---------------- PUBLISH ----------------
            _, enc = cv2.imencode(".jpg", result_frame)
            out_b64 = base64.b64encode(enc).decode("utf-8")
            out_msg = {"meta": meta, "frame_b64": out_b64}
            self.channel.basic_publish(
                exchange="frame_segment_exchange",
                routing_key="frame.segment",
                body=json.dumps(out_msg).encode("utf-8")
            )

            # Display
            cv2.imshow(f"ROI SEG Cam {cam_id}", result_frame)
            cv2.waitKey(1)

        except Exception:
            exc_type, exc_msg, exc_line = sys.exc_info()
            logger.error(f"{exc_type} at {exc_line.tb_lineno} as {exc_msg}")


if __name__ == "__main__":
    ROI_SEGMENT_CONSUMER().start()
