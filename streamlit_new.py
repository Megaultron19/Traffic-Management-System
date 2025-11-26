import streamlit as st
import pandas as pd
import os
st.set_page_config(page_title="Traffic Analysis", layout="wide")
st.markdown("""
    <h1 style='text-align: center; color: #1f77b4;'>
        🚗 Traffic Analysis Dashboard
    </h1>
    """, unsafe_allow_html=True)
st.markdown("---")
video_path = "outputs/annotated_web.mp4"
csv_path = "outputs/detections.csv"
col1, col2 = st.columns([2, 1])
with col1:
    st.header("📹 Annotated Video")
    
    if os.path.exists(video_path):
        try:
            video_file = open(video_path, 'rb')
            video_bytes = video_file.read()
            st.video(video_bytes)

            st.download_button(
                label="📥 Download Video",
                data=video_bytes,
                file_name="annotated_traffic.mp4",
                mime="video/mp4"
            )
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning(f"Video not found: {video_path}")
        st.info("Run: `python process_video_WORKING.py --input your_video.mp4`")
with col2:
    st.header("📊 Statistics")
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.metric("Total Detections", f"{len(df):,}")
        st.metric("Unique Vehicles", df['track_id'].nunique())
        st.markdown("---")

        st.subheader("Vehicle Types")
        vehicle_counts = df['class'].value_counts()
        for vehicle, count in vehicle_counts.items():
            st.write(f"**{vehicle}**: {count}")
        st.markdown("---")
        st.download_button(
            "📥 Download CSV",
            data=df.to_csv(index=False),
            file_name="detections.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"CSV not found: {csv_path}")
if os.path.exists(csv_path):
    st.markdown("---")
    st.header("📊 Visual Analysis")
    df = pd.read_csv(csv_path)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Detections by Vehicle Type")
        st.bar_chart(df['class'].value_counts())
    
    with chart_col2:
        st.subheader("Detections Over Time")
        df['time_bin'] = (df['timestamp'] // 10).astype(int) * 10
        time_data = df.groupby('time_bin')['track_id'].nunique()
        st.line_chart(time_data)
else:
    st.info("👆 No data available. Process a video first to see analysis.")
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "Smart Traffic Analysis System | Built with YOLOv8 & Streamlit"
    "</div>",
    unsafe_allow_html=True
)