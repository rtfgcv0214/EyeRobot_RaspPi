import cv2
import signal
import sys

PORT = 8001

cap = cv2.VideoCapture(
    f"udp://0.0.0.0:{PORT}?overrun_nonfatal=1&fifo_size=50000000",
    cv2.CAP_FFMPEG
)

if not cap.isOpened():
    print("Failed to open video stream")
    sys.exit(1)

def cleanup(signum=None, frame=None):
    print("Cleaning up...")
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    cv2.imshow("FFmpeg UDP Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cleanup()

"""
import subprocess

PORT = 8001

cmd = [
    "gst-launch-1.0", # "-v", (for debugging)
    "udpsrc", f"port={PORT}",
    "caps=application/x-rtp,media=video,encoding-name=JPEG,payload=26",
    "!", "rtpjpegdepay",
    "!", "jpegdec",
    "!", "videoconvert",
    "!", "autovideosink"
]

subprocess.run(cmd)
"""
