# Smart Traffic Management System

Vehicle detection, tracking and counting from video using YOLOv8 + ByteTrack, with a Streamlit dashboard.

## Features

- Detects cars, trucks, buses, motorcycles and bicycles (YOLOv8)
- Persistent vehicle IDs via ByteTrack (built into Ultralytics)
- Counts vehicles crossing a horizontal line, by direction (up / down), each vehicle once
- Annotated output video, re-encoded to H.264 so it plays in the browser
- Results saved to CSV and SQLite
- Dashboard: upload & process videos, counts by type and direction, traffic over time, downloads

## Install

Requires Python 3.10+ and FFmpeg (optional, for browser-playable video).

```bash
git clone https://github.com/Megaultron19/Traffic-Management-System.git
cd Traffic-Management-System
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

FFmpeg: `winget install ffmpeg` / `brew install ffmpeg` / `sudo apt install ffmpeg`.

## Usage

Dashboard (upload a video from the sidebar and click **Run**):

```bash
streamlit run streamlit_new.py
```

Command line:

```bash
unzip sample_videos.zip
python process_video.py --input sample_videos/input.mp4
```

| Option | Default | Meaning |
|---|---|---|
| `--input` | required | Input video |
| `--output` | `outputs/annotated.mp4` | Annotated video |
| `--model` | `yolov8n.pt` | YOLO weights (e.g. `yolov8s.pt` for accuracy) |
| `--imgsz` | `640` | Inference size |
| `--line_y_ratio` | `0.6` | Counting line height (0 = top, 1 = bottom) |
| `--min_conf` | `0.4` | Minimum detection confidence |

## Outputs (`outputs/`)

| File | Contents |
|---|---|
| `annotated.mp4` | Boxes, track IDs, counting line, live up/down counts |
| `detections.csv` | Every detection: frame, timestamp, track_id, class, conf, x1, y1, x2, y2 |
| `crossings.csv` | Every counted vehicle: frame, timestamp, track_id, class, direction |
| `traffic.db` | SQLite with `detections` and `crossings` tables (rebuilt each run) |

## Tests

```bash
python test_counting.py
```

## Roadmap

Speed estimation, heatmaps, RTSP/webcam input, multi-camera support.

## Author

Harshit Singh — GitHub: [Megaultron19](https://github.com/Megaultron19)

*For academic/demo purposes. No biometric data stored or transmitted.*
