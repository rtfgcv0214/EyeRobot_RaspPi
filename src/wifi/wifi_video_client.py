import subprocess
import argparse 

parser = argparse.ArgumentParser(description="WiFi Video Client using FFmpeg")
parser.add_argument("-i", "--ip",   type=str, default="192.168.0.99", \
                    help="IP address of the WiFi Video Server. seongho: 192.168.0.99, seohee: 192.168.0.171")
parser.add_argument("-p", "--port", type=int, default=8001,         help="Port number of the WiFi Video Server")
parser.add_argument("--fps",        type=int, default=20,           help="Frames per second for the video stream")
parser.add_argument("--size",       type=str, default="1280x720",   help="Resolution for the video stream")

"""
cmd = [
    "gst-launch-1.0", # "-v", (for debugging)
    "v4l2src", "device=/dev/video0",
    "!", "image/jpeg,width=1280,height=720,framerate=10/1",
    "!", "rtpjpegpay",
    "!", "udpsink", f"host={PC_IP}", f"port={PORT}"
]
"""

def main():
    args = parser.parse_args()

    cmd = [
        "ffmpeg",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(args.fps),
        "-video_size", args.size,
        "-i", "/dev/video0",

        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-probesize", "32",
        "-analyzeduration", "0",
        
        "-c:v", "copy",
        "-f", "mjpeg",
        f"udp://{args.ip}:{args.port}?pkt_size=1316"

    ]

    print("Starting FFmpeg video sender...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
