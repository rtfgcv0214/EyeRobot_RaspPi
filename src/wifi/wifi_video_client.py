import subprocess

PC_IP = "192.168.0.99"   # PC의 Wi-Fi IP
PORT = 8001

"""
cmd = [
    "gst-launch-1.0", # "-v", (for debugging)
    "v4l2src", "device=/dev/video0",
    "!", "image/jpeg,width=1280,height=720,framerate=10/1",
    "!", "rtpjpegpay",
    "!", "udpsink", f"host={PC_IP}", f"port={PORT}"
]
"""

cmd = [
    "ffmpeg",
    "-f", "v4l2",
    "-framerate", "10",
    "-video_size", "1280x720",
    "-i", "/dev/video0",
    "-vcodec", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-pix_fmt", "yuv420p",
    "-f", "mpegts",
    f"udp://{PC_IP}:{PORT}"
]

print("Starting FFmpeg video sender...")
subprocess.run(cmd)
