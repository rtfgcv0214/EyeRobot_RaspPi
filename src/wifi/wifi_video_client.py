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
    "-input_format", "mjpeg",
    "-thread_queue_size", "1",

    "-framerate", "20",
    "-video_size", "1280x720",
    "-i", "/dev/video0",
    
    "-c:v", "mjpeg",
    "-q:v", "5",
    "-an",
    "-f", "mjpeg",
    f"udp://{PC_IP}:{PORT}?pkt_size=1400"

]

print("Starting FFmpeg video sender...")
subprocess.run(cmd)
