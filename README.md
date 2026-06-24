# MarineSpillPredict-Deep-Learning-based-Oil-Spill-Detection-System
## 🚀 Key Features

- Developed an **AI-based oil spill detection system** using **U-Net, DeepLabV3+, and a Hybrid Segmentation Model** for pixel-level segmentation of oil spills in **Synthetic Aperture Radar (SAR)** images.

- Designed and implemented a **data preprocessing pipeline** including image resizing, normalization, noise reduction, and data augmentation to improve model generalization.

- Trained and evaluated deep learning models on multiple public datasets, including:
  - Kaggle Oil Spill Dataset
  - M4D/ITI SAR Dataset
  - SOS SAR Dataset

- Achieved high segmentation performance, with **DeepLabV3+ obtaining an F1-Score of 95.8% and Recall of 96.1%** for accurate oil spill detection.

- Implemented a **hybrid ensemble approach** by combining predictions from U-Net and DeepLabV3+ to enhance structural consistency and reduce false detections.

- Evaluated model performance using standard segmentation metrics:
  - Precision
  - Recall
  - F1-Score
  - Intersection over Union (IoU)
  - Pixel Accuracy

- Developed an **automated alert generation system** to notify users upon oil spill detection, enabling faster environmental monitoring and emergency response.

- Built a scalable framework capable of supporting:
  - Real-time maritime surveillance
  - Environmental monitoring
  - Marine disaster management applications
 
  ## 🛠️ Tech Stack

- Python
- TensorFlow & Keras
- OpenCV
- NumPy & Scikit-learn
- Deep Learning
- Computer Vision
- Image Segmentation
- Synthetic Aperture Radar (SAR) Imagery
