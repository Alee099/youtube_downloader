import streamlit as st
from pytubefix import YouTube
import os
import subprocess
import time

def download_video(yt, selected_stream):
    st.info(f"Downloading video: {selected_stream.resolution} at {selected_stream.fps}fps")
    video_path = selected_stream.download(filename='video.mp4')

    st.info("Downloading audio...")
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
    audio_path = audio_stream.download(filename='audio.mp4')

    output_filename = yt.title.replace(" ", "_") + f"_{selected_stream.resolution}_{selected_stream.fps}fps.mp4"

    st.info("Merging video and audio with ffmpeg...")
    subprocess.call([
        'ffmpeg', '-y',
        '-i', 'video.mp4',
        '-i', 'audio.mp4',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_filename
    ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    os.remove("video.mp4")
    os.remove("audio.mp4")
    time.sleep(1)  

    return output_filename

def download_audio_only(yt):
    st.info("Downloading audio only...")
    audio = yt.streams.filter(only_audio=True).first()
    out_path = audio.download()
    base, _ = os.path.splitext(out_path)
    new_file = base + '.mp3'
    os.rename(out_path, new_file)
    time.sleep(1)
    return new_file


st.title("🎬 YouTube Video & Audio Downloader")

url = st.text_input(" Enter YouTube Video URL:")
if url:
    try:
        yt = YouTube(url)
        st.success(f" Fetched: {yt.title}")
        choice = st.radio(" Choose what to download:", ['Video', 'Audio only'])

        if choice == 'Video':
            streams = yt.streams.filter(file_extension='mp4', only_video=True).order_by('resolution').desc()
            unique_streams = {}
            for stream in streams:
                if stream.resolution not in unique_streams or stream.filesize > unique_streams[stream.resolution].filesize:
                    unique_streams[stream.resolution] = stream

            res_options = [f"{res} - {s.fps}fps - {round(s.filesize / (1024*1024), 2)} MB"
                           for res, s in unique_streams.items()]
            selected_option = st.selectbox(" Select resolution:", res_options)
            selected_stream = list(unique_streams.values())[res_options.index(selected_option)]

            if st.button("⬇ Download Video"):
                output = download_video(yt, selected_stream)
                st.success(f" Download complete: {output}")
                with open(output, "rb") as f:
                    st.download_button(" Click to Download", f, file_name=output)

        else:
            if st.button(" Download Audio"):
                output = download_audio_only(yt)
                st.success(f"Audio downloaded: {output}")
                with open(output, "rb") as f:
                    st.download_button(" Click to Download", f, file_name=output)

    except Exception as e:
        st.error(f" Error: {e}")
