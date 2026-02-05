import cv2
import signal
import sys
import argparse

parser = argparse.ArgumentParser(description="WiFi Video Server using FFmpeg")
parser.add_argument("-p", "--port", type=int, default=8001, help="Port to listen on for incoming video stream")
parser.add_argument("-d", "--display", action="store_true", help="Display the video stream in a window")
parser.add_argument("-f", "--save_file", type=str, default="", help="File path to save the incoming video stream")


cap: cv2.VideoCapture | None = None
writer: cv2.VideoWriter | None = None


def cleanup(signum=None, frame=None):
    global cap, writer

    print("Cleaning up...")

    if cap is not None:
        cap.release()

    if writer is not None:
        writer.release()

    cv2.destroyAllWindows()
    sys.exit(0)

def main():
    global cap, writer
    args = parser.parse_args()

    port = args.port
    display = args.display
    save_path = args.save_file

    cap = cv2.VideoCapture(
    f"udp://0.0.0.0:{port}?overrun_nonfatal=1&fifo_size=50000000",
    cv2.CAP_FFMPEG
    )

    if not cap.isOpened():
        print("Failed to open video stream")
        cleanup()
    
    if save_path:
        if not save_path.endswith('.avi'):
            save_path += '.avi'

        w = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 1:
            fps = 20
        fourcc = cv2.VideoWriter.fourcc(*'MJPG')
        
        print(f"Opening video writer ({w}x{h} @ {fps} FPS) save to: {save_path}")
        writer = cv2.VideoWriter(save_path, fourcc, fps, (w, h))

        if not writer.isOpened():
            print('Failed to open video writer')
            cleanup()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        ret, frame = cap.read()
        if not ret:
            cv2.waitKey(10)
            continue
        
        if display:
            cv2.imshow("FFmpeg UDP Stream", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cleanup()
        
        if writer is not None:
            writer.write(frame)

if __name__ == "__main__":
    main()

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
