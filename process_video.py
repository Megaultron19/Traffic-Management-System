import argparse
import os
import shutil
import sqlite3
import subprocess
import time

import cv2
import pandas as pd

VEHICLES = {"car", "truck", "bus", "motorcycle", "bicycle"}
DET_COLS = ["frame", "timestamp", "track_id", "class", "conf", "x1", "y1", "x2", "y2"]
CROSS_COLS = ["frame", "timestamp", "track_id", "class", "direction"]


def crossing(prev_y, y, line_y):
    """Direction a centroid moved across the line between two frames, or None."""
    if prev_y < line_y <= y:
        return "down"
    if prev_y >= line_y > y:
        return "up"
    return None


def to_web_mp4(src, dst):
    """Re-encode to H.264 so browsers can play it; fall back to the raw file."""
    if shutil.which("ffmpeg"):
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
             "-vcodec", "libx264", "-pix_fmt", "yuv420p", dst])
        if r.returncode == 0:
            os.remove(src)
            return
    os.replace(src, dst)


def process(input_path, output="outputs/annotated.mp4", model_path="yolov8n.pt",
            imgsz=640, line_y_ratio=0.6, min_conf=0.4, progress=None):
    """Detect, track and count vehicles. Returns summary dict.

    progress: optional callback(frame_idx, total_frames).
    """
    from ultralytics import YOLO  # slow import; keep `crossing` testable without it

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Video not found: {input_path}")
    out_dir = os.path.dirname(output) or "."
    os.makedirs(out_dir, exist_ok=True)

    model = YOLO(model_path)
    class_ids = [i for i, n in model.names.items() if n in VEHICLES]

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    line_y = int(h * line_y_ratio)

    raw = output + ".raw.mp4"
    writer = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    detections, crossings = [], []
    last_y = {}  # track_id -> previous centroid y
    counted = set()  # count each track once; box jitter at the line would double count
    counts = {"up": 0, "down": 0}
    frame_idx = 0
    start = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        ts = frame_idx / fps

        res = model.track(frame, persist=True, imgsz=imgsz, conf=min_conf,
                          classes=class_ids, tracker="bytetrack.yaml", verbose=False)[0]
        b = res.boxes
        if b.id is not None:
            for (x1, y1, x2, y2), tid, cls, conf in zip(
                    b.xyxy.int().tolist(), b.id.int().tolist(),
                    b.cls.int().tolist(), b.conf.tolist()):
                label = model.names[cls]
                detections.append([frame_idx, ts, tid, label, conf, x1, y1, x2, y2])

                cy = (y1 + y2) // 2
                d = crossing(last_y[tid], cy, line_y) if tid in last_y and tid not in counted else None
                last_y[tid] = cy
                if d:
                    counted.add(tid)
                    counts[d] += 1
                    crossings.append([frame_idx, ts, tid, label, d])

                color = (0, 200, 255) if d else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"#{tid} {label} {conf:.2f}", (x1, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.line(frame, (0, line_y), (w, line_y), (0, 0, 255), 3)
        cv2.putText(frame, f"Down: {counts['down']}  Up: {counts['up']}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
        writer.write(frame)

        if progress:
            progress(frame_idx, total)
        elif frame_idx % 30 == 0:
            pct = frame_idx / total * 100 if total else 0
            print(f"{pct:5.1f}%  frame {frame_idx}/{total}  counted {sum(counts.values())}")

    cap.release()
    writer.release()
    to_web_mp4(raw, output)

    det_df = pd.DataFrame(detections, columns=DET_COLS)
    cross_df = pd.DataFrame(crossings, columns=CROSS_COLS)
    det_df.to_csv(os.path.join(out_dir, "detections.csv"), index=False)
    cross_df.to_csv(os.path.join(out_dir, "crossings.csv"), index=False)
    # Fresh DB per run so results from different videos don't mix.
    with sqlite3.connect(os.path.join(out_dir, "traffic.db")) as conn:
        det_df.to_sql("detections", conn, if_exists="replace", index=False)
        cross_df.to_sql("crossings", conn, if_exists="replace", index=False)

    elapsed = time.time() - start
    return {
        "frames": frame_idx,
        "detections": len(det_df),
        "tracked": det_df["track_id"].nunique(),
        "counted": len(cross_df),
        **counts,
        "seconds": round(elapsed, 1),
        "fps": round(frame_idx / elapsed, 1) if elapsed else 0,
        "output": output,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Vehicle detection, tracking and line counting")
    p.add_argument("--input", required=True, help="Input video path")
    p.add_argument("--output", default="outputs/annotated.mp4", help="Annotated output video")
    p.add_argument("--model", default="yolov8n.pt", help="YOLO weights")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--line_y_ratio", type=float, default=0.6,
                   help="Counting line height as fraction of frame (0=top, 1=bottom)")
    p.add_argument("--min_conf", type=float, default=0.4, help="Min detection confidence")
    a = p.parse_args()
    summary = process(a.input, a.output, a.model, a.imgsz, a.line_y_ratio, a.min_conf)
    for k, v in summary.items():
        print(f"{k:>11}: {v}")
