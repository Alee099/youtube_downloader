import streamlit as st
from pytubefix import YouTube
import os
import subprocess
import time

st.set_page_config(page_title="YouTube Downloader", layout="wide")
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        .stApp {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }
        .title {
            color: #ff4b4b;
            font-size: 3.5rem;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            text-align: center;
            color: #6c757d;
            margin-bottom: 3rem;
            font-size: 1.25rem;
        }
        .block {
            background-color: #ffffff;
            padding: 2.5rem 2rem;
            border-radius: 18px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.06);
        }
        .stRadio > div {
            flex-direction: row !important;
        }
        .stButton button {
            background-color: #ff4b4b;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
        }
        .stButton button:hover {
            background-color: #e63e3e;
        }
        input[type="text"] {
            font-size: 1.1rem;
        }
        .stSelectbox {
            font-size: 1.1rem;
        }
        /* Make the app full screen with some padding */
        .stProgress {
            margin: 0 5%;
        }
    </style>
""", unsafe_allow_html=True)
def download_video_with_process_progress(yt, selected_stream):
    progress = st.progress(0.0, text="🕐 Preparing to download...")

    video_path = "video.mp4"
    audio_path = "audio.mp4"

    time.sleep(0.1)

    # Step 1: Download video
    progress.progress(0.1, text="📥 Downloading video stream...")
    selected_stream.download(filename=video_path)
    progress.progress(0.4, text="✅ Video downloaded.")

    # Step 2: Download audio
    progress.progress(0.45, text="🎧 Downloading audio stream...")
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
    audio_stream.download(filename=audio_path)
    progress.progress(0.75, text="✅ Audio downloaded.")

    # Step 3: Merge audio + video
    progress.progress(0.8, text="🛠️ Merging video and audio...")
    output_filename = yt.title.replace(" ", "_") + f"_{selected_stream.resolution}_{selected_stream.fps}fps.mp4"

    video_codec = selected_stream.codecs[0] if selected_stream.codecs else ""
    resolution = int(selected_stream.resolution.replace("p", ""))

    
    if resolution > 1080 or 'avc1' not in video_codec:
        st.warning("High-resolution video — merging may take longer.")

    if resolution <= 1080 and 'avc1' in video_codec:
        merge_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            output_filename
        ]
    else:
        merge_cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-c:a', 'aac',
            output_filename
        ]

    subprocess.call(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    os.remove(video_path)
    os.remove(audio_path)

    progress.progress(1.0, text="✅ Done! Video is ready.")
    return output_filename

def download_audio_only_with_progress(yt):
    st.info("🎧 Downloading audio...")
    audio = yt.streams.filter(only_audio=True).first()
    total_size = audio.filesize
    bytes_downloaded = 0

    progress = st.progress(0, text="🎧 Downloading audio...")

    def on_audio_progress(stream, chunk, bytes_remaining):
        nonlocal bytes_downloaded
        bytes_downloaded = total_size - bytes_remaining
        percent = int((bytes_downloaded / total_size) * 100)
        mb_done = round(bytes_downloaded / (1024 * 1024), 2)
        mb_total = round(total_size / (1024 * 1024), 2)
        progress.progress(percent, text=f"🎧 Downloading audio... {mb_done}/{mb_total} MB")

    yt.register_on_progress_callback(on_audio_progress)
    out_path = audio.download()
    yt.register_on_progress_callback(None)

    base, _ = os.path.splitext(out_path)
    new_file = base + '.mp3'
    os.rename(out_path, new_file)
    time.sleep(1)
    return new_file

#  UI Content 
st.markdown('<div class="title">🎬 YouTube Video Downloader</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Download HD Videos or MP3s instantly</div>', unsafe_allow_html=True)

with st.container():
    with st.container():
        st.markdown('<div class="block">', unsafe_allow_html=True)

        url = st.text_input("🔗 Paste YouTube Video URL here:")
        if url:
            try:
                yt = YouTube(url)
                st.success(f"🎉 Video Fetched: {yt.title}")
                choice = st.radio("What would you like to download?", ['Video', 'Audio only'])

                if choice == 'Video':
                    streams = yt.streams.filter(file_extension='mp4', only_video=True).order_by('resolution').desc()
                    unique_streams = {}
                    for stream in streams:
                        if stream.resolution not in unique_streams or stream.filesize > unique_streams[stream.resolution].filesize:
                            unique_streams[stream.resolution] = stream

                    res_options = [f"{res} - {s.fps}fps - {round(s.filesize / (1024*1024), 2)} MB"
                                   for res, s in unique_streams.items()]
                    selected_option = st.selectbox("🖥️ Select video quality:", res_options)
                    selected_stream = list(unique_streams.values())[res_options.index(selected_option)]

                    if st.button("⬇ Download Video"):
                        output = download_video_with_process_progress(yt, selected_stream)

                        st.success("✅ Video downloaded successfully!")
                        st.video(output)

                else:
                    if st.button("🎧 Download Audio"):
                        output = download_audio_only_with_progress(yt)
                        st.success("✅ Audio downloaded successfully!")
                        st.audio(output)

            except Exception as e:
                st.error(f" Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
