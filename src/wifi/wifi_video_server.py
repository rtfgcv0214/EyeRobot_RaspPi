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
