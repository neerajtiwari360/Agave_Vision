from flask import Flask, Response, render_template_string
import cv2
import time
import numpy as np
import subprocess

# Flask app setup
app = Flask(__name__)

# RTSP Stream Configuration
rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"

# Try using OpenCV with FFMPEG
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

def restart_stream():
    global cap
    cap.release()
    time.sleep(2)
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# HTML template for video stream
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Live Video Streaming</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; }
        h1 { color: #333; }
        img { max-width: 100%; height: auto; border: 5px solid #ccc; }
    </style>
</head>
<body>
    <h1>Live Video Streaming</h1>
    <div>
        <img src="{{ url_for('video_feed') }}" alt="Live Stream">
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

# Video streaming generator
def generate_frames():
    while True:
        if not cap.isOpened():
            restart_stream()
        success, frame = cap.read()
        if not success:
            restart_stream()
            continue
        
        # Resize frame to optimize performance
        frame = cv2.resize(frame, (640, 480))
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)



# import cv2

# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
# cap = cv2.VideoCapture(rtsp_url)

# if not cap.isOpened():
#     print("Error: Cannot open RTSP stream")
#     exit()

# # Retrieve original frame width and height
# original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# print(f"Original resolution: {original_width} x {original_height}")

# # Set window with half the original resolution
# half_width, half_height = original_width // 4, original_height // 4
# cv2.namedWindow('Reolink TrackMix RTSP Stream', cv2.WINDOW_NORMAL)
# cv2.resizeWindow('Reolink TrackMix RTSP Stream', half_width, half_height)

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Error: Can't receive frame (stream end?). Exiting ...")
#         break

#     # Resize frame to half the original dimensions for display
#     resized_frame = cv2.resize(frame, (half_width, half_height))

#     cv2.imshow('Reolink TrackMix RTSP Stream', resized_frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()






# import cv2

# # RTSP URL of your Reolink TrackMix camera
# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"

# # Start capturing video from RTSP stream
# cap = cv2.VideoCapture(rtsp_url)

# # Check if camera opened successfully
# if not cap.isOpened():
#     print("Error: Cannot open RTSP stream")
#     exit()

# while True:
#     ret, frame = cap.read()
    
#     # If frame is read correctly, ret is True
#     if not ret:
#         print("Error: Can't receive frame (stream end?). Exiting ...")
#         break
    
#     # Display the resulting frame
#     cv2.imshow('Reolink TrackMix RTSP Stream', frame)
    
#     # Exit streaming when user presses 'q'
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Release resources and close windows
# cap.release()
# cv2.destroyAllWindows()
