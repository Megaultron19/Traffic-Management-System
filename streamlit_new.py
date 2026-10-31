import os
import tempfile

import pandas as pd
import streamlit as st

from process_video import process

OUT = "outputs"
VIDEO = os.path.join(OUT, "annotated.mp4")
DET_CSV = os.path.join(OUT, "detections.csv")
CROSS_CSV = os.path.join(OUT, "crossings.csv")

st.set_page_config(page_title="Traffic Analysis", page_icon="🚗", layout="wide")
st.title("🚗 Traffic Analysis Dashboard")

with st.sidebar:
    st.header("Process a video")
    upload = st.file_uploader("Video", type=["mp4", "avi", "mov", "mkv"])
    line = st.slider("Counting line (fraction of height)", 0.1, 0.9, 0.6, 0.05)
    conf = st.slider("Min confidence", 0.1, 0.9, 0.4, 0.05)
    if st.button("Run", disabled=upload is None, type="primary"):
        suffix = os.path.splitext(upload.name)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(upload.getbuffer())
        bar = st.progress(0.0, "Processing…")
        try:
            s = process(f.name, VIDEO, line_y_ratio=line, min_conf=conf,
                        progress=lambda i, n: bar.progress(min(i / n, 1.0) if n else 0.0,
                                                           f"Frame {i}/{n}"))
            st.success(f"Done: {s['counted']} vehicles counted in {s['seconds']}s")
        except Exception as e:
            st.error(str(e))
        finally:
            os.remove(f.name)

if not os.path.exists(DET_CSV):
    st.info("No results yet. Upload a video in the sidebar, or run "
            "`python process_video.py --input sample_videos/input.mp4`.")
    st.stop()

det = pd.read_csv(DET_CSV)
cross = pd.read_csv(CROSS_CSV) if os.path.exists(CROSS_CSV) else pd.DataFrame(
    columns=["frame", "timestamp", "track_id", "class", "direction"])

m = st.columns(4)
m[0].metric("Vehicles counted", len(cross))
m[1].metric("Down / Up", f"{(cross['direction'] == 'down').sum()} / "
                         f"{(cross['direction'] == 'up').sum()}")
m[2].metric("Unique vehicles tracked", det["track_id"].nunique())
m[3].metric("Avg confidence", f"{det['conf'].mean():.2f}" if len(det) else "–")

left, right = st.columns([2, 1])
with left:
    if os.path.exists(VIDEO):
        st.video(VIDEO)
    else:
        st.warning(f"Video not found: {VIDEO}")
with right:
    st.subheader("Counted by type")
    if len(cross):
        st.bar_chart(cross.groupby(["class", "direction"]).size().unstack(fill_value=0))
    else:
        st.caption("No line crossings.")
    st.subheader("Tracked by type")
    # Each track's most frequent class, so one vehicle counts once.
    st.bar_chart(det.groupby("track_id")["class"].agg(lambda c: c.mode()[0]).value_counts())

st.subheader("Traffic over time")
bin_s = st.select_slider("Bin size (s)", [1, 5, 10, 30, 60], value=10)
flow = det.assign(t=(det["timestamp"] // bin_s * bin_s).astype(int)) \
          .groupby("t")["track_id"].nunique().rename("vehicles in view")
st.line_chart(flow)

with st.expander("Raw data"):
    tab1, tab2 = st.tabs(["Crossings", "Detections"])
    tab1.dataframe(cross, width="stretch")
    tab2.dataframe(det, width="stretch")

d = st.columns(3)
if os.path.exists(VIDEO):
    with open(VIDEO, "rb") as f:
        d[0].download_button("📥 Video", f, "annotated_traffic.mp4", "video/mp4")
d[1].download_button("📥 Crossings CSV", cross.to_csv(index=False), "crossings.csv", "text/csv")
d[2].download_button("📥 Detections CSV", det.to_csv(index=False), "detections.csv", "text/csv")
