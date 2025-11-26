# Smart Traffic Management System

A real-time traffic monitoring and analysis system powered by YOLOv8 for vehicle detection, tracking, and counting. Features an interactive Streamlit dashboard for visualization and analysis.

🎯 Features

Vehicle Detection: Detects cars, trucks, buses, motorcycles, and bicycles using YOLOv8

Object Tracking: Custom centroid-based tracking algorithm for persistent vehicle IDs

Vehicle Counting: Counts vehicles crossing a designated line with no duplicates

Annotated Video Output: Generates videos with bounding boxes, IDs, and confidence scores

Data Export: Saves detections to CSV and SQLite database

Interactive Dashboard: Beautiful Streamlit web interface with charts and analytics

Real-time Processing: Efficient video processing with progress tracking

🛠️ Installation

Prerequisites


Python 3.10 or higher

FFmpeg (for video conversion)

Step 1: Clone the Repository

bashgit clone https://github.com/yourusername/traffic-management-system.git

cd traffic-management-system

Step 2: Create Virtual Environment

bash# Using conda (recommended)

conda create -n traffic python=3.11 -y

conda activate traffic

Or using venv

python -m venv venv

source venv/bin/activate  # Linux/Mac

venv\Scripts\activate     # Windows

Step 3: Install Dependencies

bashpip install -r requirements.txt

Step 4: Install FFmpeg

bash# Windows (using winget)

winget install ffmpeg


Or using conda

conda install -c conda-forge ffmpeg

Linux
sudo apt install ffmpeg

Mac
brew install ffmpeg


📦 Requirements

Create a requirements.txt file with:

ultralytics>=8.0.0

opencv-python>=4.8.0

pandas>=2.0.0

numpy>=1.24.0

streamlit>=1.28.0

plotly>=5.17.0

pillow>=10.0.0


🚀 Quick Start

1. Process a Video
   
bashpython process_video.py --input sample_videos/input.mp4 --output outputs/annotated_.mp4

Options:

--input: Path to input video (required)

--output: Path to output video (default: outputs/annotated.mp4)


3. Convert Video to Web Format
   
bashffmpeg -i outputs/annotated.mp4 -vcodec libx264 -pix_fmt yuv420p outputs/annotated_web.mp4

5. Launch Dashboard
   
bashstreamlit run streamlit_new.py

The dashboard will open in your browser at http://localhost:8501



📊 Output Files

1. Annotated Video

Bounding boxes around detected vehicles

Vehicle IDs and class labels

Confidence scores

Counting line visualization

Real-time vehicle count


2. CSV File (outputs/detections.csv)
   
Contains all detections with:

Frame number

Timestamp

Track ID

Vehicle class

Confidence score

Bounding box coordinates (x1, y1, x2, y2)


3. SQLite Database (outputs/traffic.db)

Structured database with the same information for SQL queries


🎨 Dashboard Features

Video Playback

Play annotated video directly in browser

Download option for offline viewing

Statistics Panel

Total detections count,
Unique vehicles tracked,
Average confidence score,
Vehicle type breakdown.

Visual Analytics

Bar Chart: Detections by vehicle type

Line Chart: Vehicle count over time

Data Table: Filterable detection records

🐛 Troubleshooting
Video Won't Play in Dashboard

Problem: Black screen or "Video not found"

Solution:

bash# Convert to web-compatible format

ffmpeg -i outputs/annotated.mp4 -vcodec libx264 -pix_fmt yuv420p outputs/annotated_web.mp4

GPU highly recommended for real-time processing.

🤝 Contributing

Contributions are welcome! Please follow these steps:

Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📝 Future Enhancements

 Speed estimation using pixel-to-meter calibration
 
 Multi-directional counting (bidirectional traffic)
 
 Violation detection (wrong-way, speeding)
 
 Heatmap generation for traffic density
 
 Real-time streaming support (RTSP/webcam)
 
 Advanced tracking (DeepSORT, ByteTrack)
 
 Email/SMS alerts for specific events
 
 Multi-camera support
 
 Cloud deployment options
 

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments

Ultralytics YOLOv8 - Object detection

OpenCV - Computer vision library

Streamlit - Dashboard framework

Plotly - Interactive charts


Disclaimer

For academic/demo purposes only

Not intended for production

No biometric data stored or transmitted

👨‍💻 Authors

Harshit Singh

GitHub: Megaultron19 

Email: harshitkatiyar2003@gmail.com

