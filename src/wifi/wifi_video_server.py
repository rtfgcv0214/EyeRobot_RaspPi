import subprocess

PC_IP = "10.207.112.114"   # PC의 Wi-Fi IP
PORT = 8001

cmd = [
    "gst-launch-1.0",
    "v4l2src", "device=/dev/video0",
    "!",
    "image/jpeg,width=1280,height=720,framerate=10/1",
    "!",
    "rtpjpegpay",
    "!",
    f"udpsink host={PC_IP} port={PORT}"
]

print("Starting GStreamer video sender...")
subprocess.run(cmd)
