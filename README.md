# ROI-Generation-using-Computer-Vision-and-RabbitMQ
📌 Project Overview

This project implements a real-time, distributed computer vision pipeline that detects and segments objects from multiple video streams while focusing only on meaningful regions of each frame using a Region of Interest (ROI) strategy.

Instead of processing the entire frame, the system:
✔ Computes a fixed ROI on each camera feed
✔ Runs YOLOv7 only inside the ROI
✔ Filters irrelevant detections
✔ Stores results in Redis
✔ Uses RabbitMQ to decouple system components

This design improves:

Speed

Accuracy

Scalability

🧠 Key Features

✅ ROI-based detection & segmentation

✅ YOLOv7 for real-time inference

✅ RabbitMQ for async communication

✅ Redis for fast result storage

✅ Multi-camera support

✅ Multiprocessing + Multithreading

✅ Modular & scalable architecture



🧩 Tech Stack
Component -	Technology

Language -	Python

CV Framework -	OpenCV

DL Model -	YOLOv7

Messaging	- RabbitMQ

Storage - Redis

Processing -	Multiprocessing + Multithreading

Inference	- PyTorch


🎯 Object Classes Trained

Car

Truck

Person

Helmet

Jacket

Fire

Smoke

 Dataset & Training

 Total Images: 3,500

 Annotation Tool: LabelImg

 Model: YOLOv7

🎯 Output: best.pt trained weights

YOLO Format:

<class_id> <x_center> <y_center> <width> <height>
How the System Works (End-to-End)
1️⃣ Frame Capture

Reads frames from video streams using OpenCV.

Encodes and sends frames to RabbitMQ.

2️⃣ Detection

YOLOv7 detects objects.

Filters detections by camera use-case.

3️⃣ ROI Filtering

Keeps only objects inside ROI.

Crops ROI and stores in Redis DB1.

4️⃣ Segmentation

YOLOv7-Seg generates masks.

Applies segmentation only inside ROI.

5️⃣ Storage

Segmented ROI frames saved in Redis DB2.

⚙️ Installation
git clone https://github.com/your-username/roi-yolov7-video-analytics.git
cd roi-yolov7-video-analytics
pip install -r requirements.txt

▶️ Run the System

Make sure:
✔ Redis is running
✔ RabbitMQ is running

Then:

python main.py

🧪 Sample Output

Green bounding boxes inside ROI

Segmentation masks applied only in ROI

Real-time display & Redis storage

📈 Use Cases

Traffic Monitoring

Industrial Safety

Fire & Smoke Detection

PPE Compliance (Helmet/Jacket)

Smart Surveillance

🧾 Conclusion

This project demonstrates how ROI-based processing + distributed messaging + deep learning can be combined to build a high-performance real-time video analytics system.

The modular design allows:
✔ Easy scaling
✔ Multiple cameras
✔ Fast inference
✔ Clean data flow

🙋‍♀️ Author

B. Siva Sai Sravani

🎓 Data Science / AI-ML Engineer

📫 Email: sivasaisravani@gmail.com

🔗 GitHub: https://github.com/sravanibatta15

🔗 LinkedIn: https://www.linkedin.com/in/siva-sai-sravani/
