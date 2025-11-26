import argparse
import os
import cv2
import time
import pandas as pd
import sqlite3
from ultralytics import YOLO
from math import hypot
class CentroidTracker:
    def __init__(self, max_distance=50):
        self.next_id = 1
        self.objects = {}
        self.max_distance = max_distance
        self.counted_ids = set()

    def update(self, detections):
        new_centroids = []
        boxes = []
        for (x1, y1, x2, y2) in detections:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            new_centroids.append((cx, cy))
            boxes.append((x1, y1, x2, y2))

        if len(self.objects) == 0:
            result = []
            for cent, box in zip(new_centroids, boxes):
                oid = self.next_id
                self.objects[oid] = cent
                self.next_id += 1
                result.append((oid, box))
            return result
        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())
        matches = {}
        used_new = set()
        
        for i, new_c in enumerate(new_centroids):
            best_id = None
            best_dist = self.max_distance + 1
            for oid, old_c in zip(object_ids, object_centroids):
                d = hypot(new_c[0] - old_c[0], new_c[1] - old_c[1])
                if d < best_dist:
                    best_dist = d
                    best_id = oid
            if best_id is not None and best_dist <= self.max_distance:
                matches[best_id] = (new_c, boxes[i])
                used_new.add(i)

        for oid, (cent, box) in matches.items():
            self.objects[oid] = cent

        for i, (cent, box) in enumerate(zip(new_centroids, boxes)):
            if i in used_new:
                continue
            oid = self.next_id
            self.objects[oid] = cent
            self.next_id += 1
            matches[oid] = (cent, box)

        return [(oid, matches[oid][1]) for oid in matches]
def main(args):
    os.makedirs("outputs", exist_ok=True)
    if not os.path.exists(args.input):
        print(f"ERROR: Video not found: {args.input}")
        return
    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print("ERROR: Cannot open video")
        return  
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video: {width}x{height}, {fps:.1f} FPS, {total_frames} frames\n")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))
    tracker = CentroidTracker(max_distance=60)
    conn = sqlite3.connect('outputs/traffic.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        frame INTEGER, timestamp REAL, track_id INTEGER,
        class TEXT, conf REAL,
        x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER
    )''')
    conn.commit()

    csv_rows = []
    total_counts = 0
    frame_idx = 0
    start_time = time.time()
    line_y = int(height * args.line_y_ratio)
    vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
    print("Processing frames...")
    print("=" * 60)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_idx += 1
        ts = frame_idx / fps
        results = model.predict(frame, imgsz=args.imgsz, verbose=False)[0]
        
        boxes = []
        classes = []
        confs = []
        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, confidence, class_id = result
            class_name = model.names[int(class_id)]
            
            if frame_idx <= 3:
                print(f"Frame {frame_idx}: {class_name} ({confidence:.2f})")
            
            if class_name.lower() in vehicle_classes and confidence >= args.min_conf:
                boxes.append((int(x1), int(y1), int(x2), int(y2)))
                classes.append(class_name)
                confs.append(confidence)

        tracked = tracker.update(boxes)
        for idx, (tid, bbox) in enumerate(tracked):
            label = classes[idx]
            conf = confs[idx]
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID:{tid} {label} {conf:.2f}', 
                       (x1, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            cur.execute('''INSERT INTO detections 
                        (frame, timestamp, track_id, class, conf, x1, y1, x2, y2) 
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                       (frame_idx, ts, tid, label, conf, x1, y1, x2, y2))
            csv_rows.append({
                'frame': frame_idx, 'timestamp': ts, 'track_id': tid, 
                'class': label, 'conf': conf, 
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
            })
            centroid = tracker.objects.get(tid)
            if centroid and tid not in tracker.counted_ids:
                if centroid[1] > line_y:
                    tracker.counted_ids.add(tid)
                    total_counts += 1
        cv2.line(frame, (0, line_y), (width, line_y), (0,0,255), 3)
        cv2.putText(frame, f'Count: {total_counts}', (10, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,255), 3)
        cv2.putText(frame, f'Frame: {frame_idx}/{total_frames}', (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        out.write(frame)

        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames * 100) if total_frames > 0 else 0
            print(f"Progress: {progress:.1f}% | Detections: {len(csv_rows)}")

        if frame_idx % 200 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    out.release()
    cap.release()

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    if len(csv_rows) > 0:
        pd.DataFrame(csv_rows).to_csv('outputs/detections.csv', index=False)
        print(f"✓ SUCCESS!")
        print(f"  Frames processed: {frame_idx}")
        print(f"  Detections found: {len(csv_rows)}")
        print(f"  Vehicles counted: {total_counts}")
        print(f"  Time: {elapsed:.1f}s ({frame_idx/elapsed:.1f} FPS)")
    else:
        print("No detections found!")
        pd.DataFrame(columns=['frame','timestamp','track_id','class','conf',
                             'x1','y1','x2','y2']).to_csv('outputs/detections.csv', index=False)
    
    print(f"\nOutput files:")
    print(f"   Video: {args.output}")
    print(f"   CSV:   outputs/detections.csv")
    print(f"   DB:    outputs/traffic.db")
    print("=" * 60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video path')
    parser.add_argument('--output', default='outputs/annotated.mp4', help='Output video')
    parser.add_argument('--model', default='yolov8n.pt', help='YOLO model')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size')
    parser.add_argument('--line_y_ratio', type=float, default=0.75, help='Line position')
    parser.add_argument('--min_conf', type=float, default=0.5, help='Min confidence')
    args = parser.parse_args()
    main(args)