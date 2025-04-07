import os
import requests
import time
from flask import Flask, Response, render_template_string, jsonify
import cv2
from datetime import datetime
from threading import Timer

app = Flask(__name__)

# RTSP Stream Configuration
rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
capture_api_url = "http://192.168.40.74/api.cgi?cmd=Snap&user=admin&password=AgaveNetworks123!"
ptz_api_url = "http://192.168.40.74/api.cgi?user=admin&password=AgaveNetworks123!"
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# Directory for storing captured images
IMAGE_DIR = "images"

# Ensure the images directory exists
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def restart_stream():
    global cap
    cap.release()
    time.sleep(2)
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# HTML template with white background and sky blue buttons
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reolink TrackMix Control</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            background-color: #ffffff; 
            color: #333333; 
            margin: 0; 
            padding: 0;
        }
        h1 { 
            color: #0077cc; 
            margin-top: 20px; 
            margin-bottom: 30px;
        }
        .container { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            flex-direction: column; 
            min-height: 100vh;
            padding: 20px;
            box-sizing: border-box;
        }
        .content { 
            display: flex; 
            align-items: center; 
            gap: 30px; 
            flex-wrap: wrap;
            justify-content: center;
        }
        .video-container { 
            border: 4px solid #e0e0e0; 
            border-radius: 8px; 
            padding: 5px; 
            background-color: #f5f5f5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        img { 
            max-width: 100%; 
            height: auto; 
            border-radius: 5px; 
            display: block;
        }
        .controls { 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            background: #f9f9f9; 
            padding: 20px; 
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        button { 
            padding: 12px 20px; 
            margin: 10px; 
            font-size: 16px; 
            font-weight: bold; 
            cursor: pointer; 
            border: none; 
            border-radius: 5px; 
            transition: all 0.3s ease; 
            width: 120px;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
        }
        .control-btn { 
            background-color: #4fc3f7; 
            color: #ffffff; 
        }
        .control-btn:hover { 
            background-color: #29b6f6; 
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }
        .capture-btn { 
            background-color: #66bb6a; 
            color: #ffffff; 
        }
        .capture-btn:hover { 
            background-color: #4caf50; 
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }
        .stop-btn { 
            background-color: #ef5350; 
            color: #ffffff; 
        }
        .stop-btn:hover { 
            background-color: #e53935; 
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }
        .ptz-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .ptz-btn {
            width: 80px;
            height: 80px;
            font-size: 24px;
        }
        .ptz-up { grid-column: 2; }
        .ptz-left { grid-column: 1; grid-row: 2; }
        .ptz-center { grid-column: 2; grid-row: 2; }
        .ptz-right { grid-column: 3; grid-row: 2; }
        .ptz-down { grid-column: 2; grid-row: 3; }
        footer {
            margin-top: 30px;
            color: #777;
            font-size: 14px;
        }
    </style>
    <script>
        function sendCommand(command) {
            fetch('/api/move/' + command, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        console.log(data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        function stopMovement() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        console.log(data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        function captureImage() {
            fetch('/api/capture', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    </script>
</head>
<body>
    <h1>Agave Networks Live Streaming..</h1>
    <div class="container">
        <div class="content">
            <div class="video-container">
                <img src="{{ url_for('video_feed') }}" alt="Live Stream">
            </div>
            <div class="controls">
                <div class="ptz-grid">
                    <button class="control-btn ptz-btn ptz-up" onclick="sendCommand('up')">↑</button>
                    <button class="control-btn ptz-btn ptz-left" onclick="sendCommand('left')">←</button>
                    <button class="control-btn ptz-btn ptz-center" onclick="stopMovement()">■</button>
                    <button class="control-btn ptz-btn ptz-right" onclick="sendCommand('right')">→</button>
                    <button class="control-btn ptz-btn ptz-down" onclick="sendCommand('down')">↓</button>
                </div>
                <button class="capture-btn" onclick="captureImage()">Take Picture</button>
                <button class="stop-btn" onclick="stopMovement()">Emergency Stop</button>
            </div>
        </div>
        <footer>
            Copyright © Agave Networks 2025
        </footer>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_frames():
    while True:
        if not cap.isOpened():
            restart_stream()
        success, frame = cap.read()
        if not success:
            restart_stream()
            continue
        
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

def send_ptz_command(direction):
    payload = [
        {
            "cmd": "PtzCtrl",
            "param": {
                "channel": 0,
                "op": direction,
                "speed": 3
            }
        }
    ]
    
    try:
        response = requests.post(ptz_api_url, json=payload, timeout=5)
        if response.status_code == 200:
            Timer(1.0, stop_camera_movement).start()
            return {"message": f"Moved {direction} successfully"}
        else:
            return {"error": f"Failed to move {direction}. Status code: {response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

def stop_camera_movement():
    stop_payload = [
        {
            "cmd": "PtzCtrl",
            "param": {
                "channel": 0,
                "op": "Stop"
            }
        }
    ]
    
    try:
        response = requests.post(ptz_api_url, json=stop_payload, timeout=5)
        if response.status_code == 200:
            print("Camera stopped successfully.")
            return True
        else:
            print(f"Stop failed. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Stop request failed: {str(e)}")
        return False

@app.route('/api/move/<direction>', methods=['POST'])
def move(direction):
    if direction in ['left', 'right', 'up', 'down']:
        result = send_ptz_command(direction)
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
    return jsonify({"error": "Invalid direction"}), 400

@app.route('/api/stop', methods=['POST'])
def stop():
    success = stop_camera_movement()
    if success:
        return jsonify({"message": "Camera stopped successfully."})
    else:
        return jsonify({"error": "Failed to stop camera."}), 400

@app.route('/api/capture', methods=['POST'])
def capture():
    try:
        response = requests.get(capture_api_url, timeout=5)
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(IMAGE_DIR, f"{timestamp}.png")
            
            with open(image_path, "wb") as f:
                f.write(response.content)

            return jsonify({
                "message": "Picture captured successfully!",
                "path": image_path,
                "timestamp": timestamp
            })
        else:
            return jsonify({
                "error": f"Failed to capture image. Camera returned status {response.status_code}"
            }), 400
    except requests.RequestException as e:
        return jsonify({
            "error": f"Request to camera failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)





# import os
# import requests
# import time
# from flask import Flask, Response, render_template_string, jsonify
# import cv2
# from datetime import datetime
# from threading import Timer

# app = Flask(__name__)

# # RTSP Stream Configuration
# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
# capture_api_url = "http://192.168.40.74/api.cgi?cmd=Snap&user=admin&password=AgaveNetworks123!"
# ptz_api_url = "http://192.168.40.74/api.cgi?user=admin&password=AgaveNetworks123!"
# cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # Directory for storing captured images
# IMAGE_DIR = "images"

# # Ensure the images directory exists
# if not os.path.exists(IMAGE_DIR):
#     os.makedirs(IMAGE_DIR)

# def restart_stream():
#     global cap
#     cap.release()
#     time.sleep(2)
#     cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # HTML template with UI
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1">
#     <title>Reolink TrackMix Control</title>
#     <style>
#         body { font-family: Arial, sans-serif; text-align: center; background-color: #2c3e50; color: #ecf0f1; margin: 0; }
#         h1 { color: #f39c12; margin-top: 20px; }
#         .container { display: flex; justify-content: center; align-items: center; flex-direction: column; height: 100vh; }
#         .content { display: flex; align-items: center; gap: 20px; }
#         .video-container { border: 8px solid #f39c12; border-radius: 10px; padding: 5px; background-color: #34495e; }
#         img { max-width: 100%; height: auto; border-radius: 5px; }
#         .controls { display: flex; flex-direction: column; align-items: center; background: #34495e; padding: 15px; border-radius: 10px; }
#         button { padding: 12px 20px; margin: 10px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; transition: 0.3s; width: 120px; }
#         .control-btn { background-color: #f39c12; color: #fff; }
#         .control-btn:hover { background-color: #e67e22; }
#         .capture-btn { background-color: #2ecc71; color: #fff; }
#         .capture-btn:hover { background-color: #27ae60; }
#         .stop-btn { background-color: #e74c3c; color: #fff; }
#         .stop-btn:hover { background-color: #c0392b; }
#         .ptz-grid {
#             display: grid;
#             grid-template-columns: repeat(3, 1fr);
#             gap: 10px;
#             margin-bottom: 15px;
#         }
#         .ptz-btn {
#             width: 80px;
#             height: 80px;
#             font-size: 24px;
#         }
#         .ptz-up { grid-column: 2; }
#         .ptz-left { grid-column: 1; grid-row: 2; }
#         .ptz-center { grid-column: 2; grid-row: 2; }
#         .ptz-right { grid-column: 3; grid-row: 2; }
#         .ptz-down { grid-column: 2; grid-row: 3; }
#     </style>
#     <script>
#         function sendCommand(command) {
#             fetch('/api/move/' + command, { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => {
#                     if (data.error) {
#                         alert('Error: ' + data.error);
#                     } else {
#                         console.log(data.message);
#                     }
#                 })
#                 .catch(error => console.error('Error:', error));
#         }

#         function stopMovement() {
#             fetch('/api/stop', { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => {
#                     if (data.error) {
#                         alert('Error: ' + data.error);
#                     } else {
#                         console.log(data.message);
#                     }
#                 })
#                 .catch(error => console.error('Error:', error));
#         }

#         function captureImage() {
#             fetch('/api/capture', { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => {
#                     if (data.error) {
#                         alert('Error: ' + data.error);
#                     } else {
#                         alert(data.message);
#                     }
#                 })
#                 .catch(error => console.error('Error:', error));
#         }
#     </script>
# </head>
# <body>
#     <h1>Reolink TrackMix Control Panel</h1>
#     <div class="container">
#         <div class="content">
#             <div class="video-container">
#                 <img src="{{ url_for('video_feed') }}" alt="Live Stream">
#             </div>
#             <div class="controls">
#                 <div class="ptz-grid">
#                     <button class="control-btn ptz-btn ptz-up" onclick="sendCommand('up')">↑</button>
#                     <button class="control-btn ptz-btn ptz-left" onclick="sendCommand('left')">←</button>
#                     <button class="control-btn ptz-btn ptz-center" onclick="stopMovement()">■</button>
#                     <button class="control-btn ptz-btn ptz-right" onclick="sendCommand('right')">→</button>
#                     <button class="control-btn ptz-btn ptz-down" onclick="sendCommand('down')">↓</button>
#                 </div>
#                 <button class="capture-btn" onclick="captureImage()">Take Picture</button>
#                 <button class="stop-btn" onclick="stopMovement()">Emergency Stop</button>
#             </div>
#         </div>
#     </div>
# </body>
# </html>
# """

# @app.route("/")
# def index():
#     return render_template_string(HTML_TEMPLATE)

# def generate_frames():
#     while True:
#         if not cap.isOpened():
#             restart_stream()
#         success, frame = cap.read()
#         if not success:
#             restart_stream()
#             continue
        
#         frame = cv2.resize(frame, (640, 480))
#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret:
#             continue
        
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# def send_ptz_command(direction):
#     payload = [
#         {
#             "cmd": "PtzCtrl",
#             "param": {
#                 "channel": 0,
#                 "op": direction,
#                 "speed": 3
#             }
#         }
#     ]
    
#     try:
#         response = requests.post(ptz_api_url, json=payload, timeout=5)
#         if response.status_code == 200:
#             Timer(1.0, stop_camera_movement).start()
#             return {"message": f"Moved {direction} successfully"}
#         else:
#             return {"error": f"Failed to move {direction}. Status code: {response.status_code}"}
#     except requests.RequestException as e:
#         return {"error": f"Request failed: {str(e)}"}

# def stop_camera_movement():
#     stop_payload = [
#         {
#             "cmd": "PtzCtrl",
#             "param": {
#                 "channel": 0,
#                 "op": "Stop"
#             }
#         }
#     ]
    
#     try:
#         response = requests.post(ptz_api_url, json=stop_payload, timeout=5)
#         if response.status_code == 200:
#             print("Camera stopped successfully.")
#             return True
#         else:
#             print(f"Stop failed. Status code: {response.status_code}")
#             return False
#     except requests.RequestException as e:
#         print(f"Stop request failed: {str(e)}")
#         return False

# @app.route('/api/move/<direction>', methods=['POST'])
# def move(direction):
#     if direction in ['left', 'right', 'up', 'down']:
#         result = send_ptz_command(direction)
#         if 'error' in result:
#             return jsonify(result), 400
#         return jsonify(result)
#     return jsonify({"error": "Invalid direction"}), 400

# @app.route('/api/stop', methods=['POST'])
# def stop():
#     success = stop_camera_movement()
#     if success:
#         return jsonify({"message": "Camera stopped successfully."})
#     else:
#         return jsonify({"error": "Failed to stop camera."}), 400

# @app.route('/api/capture', methods=['POST'])
# def capture():
#     try:
#         response = requests.get(capture_api_url, timeout=5)
#         if response.status_code == 200:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             image_path = os.path.join(IMAGE_DIR, f"{timestamp}.png")
            
#             with open(image_path, "wb") as f:
#                 f.write(response.content)

#             return jsonify({
#                 "message": "Picture captured successfully!",
#                 "path": image_path,
#                 "timestamp": timestamp
#             })
#         else:
#             return jsonify({
#                 "error": f"Failed to capture image. Camera returned status {response.status_code}"
#             }), 400
#     except requests.RequestException as e:
#         return jsonify({
#             "error": f"Request to camera failed: {str(e)}"
#         }), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)



# import os
# import requests
# import time
# from flask import Flask, Response, render_template_string, jsonify
# import cv2
# from datetime import datetime
# from threading import Timer

# app = Flask(__name__)

# # RTSP Stream Configuration
# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
# capture_api_url = "http://192.168.40.74/api.cgi?cmd=Snap&user=admin&password=AgaveNetworks123!"
# ptz_api_url = "http://192.168.40.74/api.cgi?cmd=PtzCtrl&user=admin&password=AgaveNetworks123!"
# cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # Directory for storing captured images
# IMAGE_DIR = "images"

# # Ensure the images directory exists
# if not os.path.exists(IMAGE_DIR):
#     os.makedirs(IMAGE_DIR)

# def restart_stream():
#     global cap
#     cap.release()
#     time.sleep(2)
#     cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # HTML template with UI
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1">
#     <title>Live Video Streaming</title>
#     <style>
#         body { font-family: Arial, sans-serif; text-align: center; background-color: #2c3e50; color: #ecf0f1; margin: 0; }
#         h1 { color: #f39c12; margin-top: 20px; }
#         .container { display: flex; justify-content: center; align-items: center; flex-direction: column; height: 100vh; }
#         .content { display: flex; align-items: center; gap: 20px; }
#         .video-container { border: 8px solid #f39c12; border-radius: 10px; padding: 5px; background-color: #34495e; }
#         img { max-width: 100%; height: auto; border-radius: 5px; }
#         .controls { display: flex; flex-direction: column; align-items: center; background: #34495e; padding: 15px; border-radius: 10px; }
#         button { padding: 12px 20px; margin: 10px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; transition: 0.3s; width: 120px; }
#         .control-btn { background-color: #f39c12; color: #fff; }
#         .control-btn:hover { background-color: #e67e22; }
#         .capture-btn { background-color: #2ecc71; color: #fff; }
#         .capture-btn:hover { background-color: #27ae60; }
#         .stop-btn { background-color: #e74c3c; color: #fff; }
#         .stop-btn:hover { background-color: #c0392b; }
#     </style>
#     <script>
#         function sendCommand(command) {
#             fetch('/api/move/' + command, { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => alert(data.message))
#                 .catch(error => console.error('Error:', error));
#         }

#         function stopMovement() {
#             fetch('/api/stop', { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => alert(data.message))
#                 .catch(error => console.error('Error:', error));
#         }
#     </script>
# </head>
# <body>
#     <h1>Live Video Streaming</h1>
#     <div class="container">
#         <div class="content">
#             <div class="video-container">
#                 <img src="{{ url_for('video_feed') }}" alt="Live Stream">
#             </div>
#             <div class="controls">
#                 <button class="control-btn" onclick="sendCommand('up')">Up</button>
#                 <button class="control-btn" onclick="sendCommand('left')">Left</button>
#                 <button class="control-btn" onclick="sendCommand('right')">Right</button>
#                 <button class="control-btn" onclick="sendCommand('down')">Down</button>
#                 <button class="capture-btn" onclick="sendCommand('capture')">Take Picture</button>
#                 <button class="stop-btn" onclick="stopMovement()">Stop Movement</button>
#             </div>
#         </div>
#     </div>
# </body>
# </html>
# """

# @app.route("/")
# def index():
#     return render_template_string(HTML_TEMPLATE)

# # Video streaming generator
# def generate_frames():
#     while True:
#         if not cap.isOpened():
#             restart_stream()
#         success, frame = cap.read()
#         if not success:
#             restart_stream()
#             continue
        
#         frame = cv2.resize(frame, (640, 480))
#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret:
#             continue
        
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# # Function to send PTZ movement command
# def send_ptz_command(direction):
#     payload = [
#         {
#             "cmd": "PtzCtrl",
#             "param": {
#                 "channel": 0,
#                 "op": direction,
#                 "speed": 3  # Set a speed value, for example 32
#             }
#         }
#     ]
    
#     try:
#         # Send the movement command to start moving
#         response = requests.post(ptz_api_url, json=payload, timeout=5)
#         if response.status_code == 200:
#             # Set up a Timer to stop the movement after 1 second
#             Timer(1.0, stop_camera_movement).start()  # Timer triggers stop after 1 second
#             return jsonify({"message": f"Moved {direction} successfully"})
#         else:
#             return jsonify({"error": f"Failed to move {direction}"}), 400
#     except requests.RequestException as e:
#         return jsonify({"error": f"Request failed: {str(e)}"}), 500

# # Function to stop the camera movement
# def stop_camera_movement():
#     stop_payload = [
#         {
#             "cmd": "PtzCtrl",
#             "param": {
#                 "channel": 0,
#                 "op": "Stop",  # Use the "Stop" operation to stop the camera
#                 "speed": 0
#             }
#         }
#     ]
    
#     try:
#         response = requests.post(ptz_api_url, json=stop_payload, timeout=5)
#         if response.status_code == 200:
#             print("Camera stopped successfully after 1 second.")
#     except requests.RequestException as e:
#         print(f"Failed to stop camera: {str(e)}")

# # API endpoint for PTZ movement
# @app.route('/api/move/<direction>', methods=['POST'])
# def move(direction):
#     if direction in ['left', 'right', 'up', 'down']:
#         return send_ptz_command(direction)
#     return jsonify({"error": "Invalid direction"}), 400

# # API endpoint for stopping the camera movement manually
# @app.route('/api/stop', methods=['POST'])
# def stop():
#     stop_camera_movement()
#     return jsonify({"message": "Camera stopped manually."})

# # API endpoint for capturing images
# @app.route('/api/capture', methods=['POST'])
# def capture():
#     try:
#         response = requests.get(capture_api_url, timeout=5)
#         if response.status_code == 200:
#             # Generate filename with timestamp
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             image_path = os.path.join(IMAGE_DIR, f"{timestamp}.png")
            
#             # Save image to local folder
#             with open(image_path, "wb") as f:
#                 f.write(response.content)

#             return jsonify({"message": "Picture taken successfully", "path": image_path})
#         else:
#             return jsonify({"error": "Failed to capture image"}), 400
#     except requests.RequestException as e:
#         return jsonify({"error": f"Request failed: {str(e)}"}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)










# import os
# import requests
# import time
# from flask import Flask, Response, render_template_string, jsonify
# import cv2
# from datetime import datetime

# app = Flask(__name__)

# # RTSP Stream Configuration
# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
# capture_api_url = "http://192.168.40.74/api.cgi?cmd=Snap&user=admin&password=AgaveNetworks123!"
# ptz_api_url = "http://192.168.40.74/api.cgi?cmd=PtzCtrl&user=admin&password=AgaveNetworks123!"
# cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # Directory for storing captured images
# IMAGE_DIR = "images"

# # Ensure the images directory exists
# if not os.path.exists(IMAGE_DIR):
#     os.makedirs(IMAGE_DIR)

# def restart_stream():
#     global cap
#     cap.release()
#     time.sleep(2)
#     cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # HTML template with UI
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1">
#     <title>Live Video Streaming</title>
#     <style>
#         body { font-family: Arial, sans-serif; text-align: center; background-color: #2c3e50; color: #ecf0f1; margin: 0; }
#         h1 { color: #f39c12; margin-top: 20px; }
#         .container { display: flex; justify-content: center; align-items: center; flex-direction: column; height: 100vh; }
#         .content { display: flex; align-items: center; gap: 20px; }
#         .video-container { border: 8px solid #f39c12; border-radius: 10px; padding: 5px; background-color: #34495e; }
#         img { max-width: 100%; height: auto; border-radius: 5px; }
#         .controls { display: flex; flex-direction: column; align-items: center; background: #34495e; padding: 15px; border-radius: 10px; }
#         button { padding: 12px 20px; margin: 10px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; transition: 0.3s; width: 120px; }
#         .control-btn { background-color: #f39c12; color: #fff; }
#         .control-btn:hover { background-color: #e67e22; }
#         .capture-btn { background-color: #2ecc71; color: #fff; }
#         .capture-btn:hover { background-color: #27ae60; }
#     </style>
#     <script>
#         function sendCommand(command) {
#             fetch('/api/move/' + command, { method: 'POST' })
#                 .then(response => response.json())
#                 .then(data => alert(data.message))
#                 .catch(error => console.error('Error:', error));
#         }
#     </script>
# </head>
# <body>
#     <h1>Live Video Streaming</h1>
#     <div class="container">
#         <div class="content">
#             <div class="video-container">
#                 <img src="{{ url_for('video_feed') }}" alt="Live Stream">
#             </div>
#             <div class="controls">
#                 <button class="control-btn" onclick="sendCommand('up')">Up</button>
#                 <button class="control-btn" onclick="sendCommand('left')">Left</button>
#                 <button class="control-btn" onclick="sendCommand('right')">Right</button>
#                 <button class="control-btn" onclick="sendCommand('down')">Down</button>
#                 <button class="capture-btn" onclick="sendCommand('capture')">Take Picture</button>
#             </div>
#         </div>
#     </div>
# </body>
# </html>
# """

# @app.route("/")
# def index():
#     return render_template_string(HTML_TEMPLATE)

# # Video streaming generator
# def generate_frames():
#     while True:
#         if not cap.isOpened():
#             restart_stream()
#         success, frame = cap.read()
#         if not success:
#             restart_stream()
#             continue
        
#         frame = cv2.resize(frame, (640, 480))
#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret:
#             continue
        
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# # Function to send PTZ movement command
# def send_ptz_command(direction):
#     payload = [
#         {
#             "cmd": "PtzCtrl",
#             "action": 0,
#             "param": {
#                 "channel": 0,
#                 "op": direction,
#                 "speed": 1
#             }
#         }
#     ]

#     try:
#         response = requests.post(ptz_api_url, json=payload, timeout=5)
#         if response.status_code == 200:
#             # Stop movement after a short delay
#             time.sleep(0.5)
#             stop_payload = [
#                 {
#                     "cmd": "PtzCtrl",
#                     "action": 0,
#                     "param": {
#                         "channel": 0,
#                         "op": "stop",
#                         "speed": 0
#                     }
#                 }
#             ]
#             requests.post(ptz_api_url, json=stop_payload, timeout=5)
#             return jsonify({"message": f"Moved {direction} successfully"})
#         else:
#             return jsonify({"error": f"Failed to move {direction}"}), 400
#     except requests.RequestException as e:
#         return jsonify({"error": f"Request failed: {str(e)}"}), 500

# # API endpoint for PTZ movement
# @app.route('/api/move/<direction>', methods=['POST'])
# def move(direction):
#     if direction in ['left', 'right', 'up', 'down']:
#         return send_ptz_command(direction)
#     return jsonify({"error": "Invalid direction"}), 400

# # API endpoint for capturing images
# @app.route('/api/capture', methods=['POST'])
# def capture():
#     try:
#         response = requests.get(capture_api_url, timeout=5)
#         if response.status_code == 200:
#             # Generate filename with timestamp
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             image_path = os.path.join(IMAGE_DIR, f"{timestamp}.png")
            
#             # Save image to local folder
#             with open(image_path, "wb") as f:
#                 f.write(response.content)

#             return jsonify({"message": "Picture taken successfully", "path": image_path})
#         else:
#             return jsonify({"error": "Failed to capture image"}), 400
#     except requests.RequestException as e:
#         return jsonify({"error": f"Request failed: {str(e)}"}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)












# from flask import Flask, Response, render_template_string
# import cv2
# import time
# import numpy as np
# import subprocess

# # Flask app setup
# app = Flask(__name__)

# # RTSP Stream Configuration
# rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"

# # Try using OpenCV with FFMPEG
# cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# def restart_stream():
#     global cap
#     cap.release()
#     time.sleep(2)
#     cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# # HTML template for video stream
# HTML_TEMPLATE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <title>Live Video Streaming</title>
#     <style>
#         body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; }
#         h1 { color: #333; }
#         img { max-width: 100%; height: auto; border: 5px solid #ccc; }
#     </style>
# </head>
# <body>
#     <h1>Live Video Streaming</h1>
#     <div>
#         <img src="{{ url_for('video_feed') }}" alt="Live Stream">
#     </div>
# </body>
# </html>
# """

# @app.route("/")
# def index():
#     return render_template_string(HTML_TEMPLATE)

# # Video streaming generator
# def generate_frames():
#     while True:
#         if not cap.isOpened():
#             restart_stream()
#         success, frame = cap.read()
#         if not success:
#             restart_stream()
#             continue
        
#         # Resize frame to optimize performance
#         frame = cv2.resize(frame, (640, 480))
#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret:
#             continue
        
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)



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
