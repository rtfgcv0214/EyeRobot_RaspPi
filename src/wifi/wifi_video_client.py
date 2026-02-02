import subprocess

PC_IP = "192.168.0.99"   # PC의 Wi-Fi IP
PORT = 8001

cmd = [
    "gst-launch-1.0", # "-v", (for debugging)
    "v4l2src", "device=/dev/video0",
    "!", "image/jpeg,width=1280,height=720,framerate=10/1",
    "!", "rtpjpegpay",
    "!", "udpsink", f"host={PC_IP}", f"port={PORT}"
]

print("Starting GStreamer video sender...")
subprocess.run(cmd)
