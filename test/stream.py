import cv2
from flask import Flask, Response

app = Flask(__name__)

# 1. 카메라 연결 (0번이 안 되면 -1 또는 1로 바꿔보세요)
camera = cv2.VideoCapture(0)

# 2. 해상도 설정 (전송 속도를 위해 가볍게 시작)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    while True:
        # 카메라에서 프레임 읽기
        success, frame = camera.read()
        if not success:
            break
        else:
            # 3. 이미지를 JPG로 변환 (웹 전송용)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 4. 실시간 스트리밍 포맷으로 전송
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # 0.0.0.0 : 같은 와이파이 내의 모든 기기(맥북)에서 접속 허용
    print("=============================================")
    print("🎥 카메라 서버 시작! 맥북에서 아래 주소로 접속하세요:")
    print("   http://eye-rasp-1.local:5000")
    print("=============================================")
    app.run(host='0.0.0.0', port=5000)