import cv2

PORT = 8001

cap = cv2.VideoCapture(
    f"udp://0.0.0.0:{PORT}",
    cv2.CAP_FFMPEG
)

if not cap.isOpened():
    print("Failed to open video stream")
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    cv2.imshow("FFmpeg UDP Stream", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

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
