import cv2
import mediapipe as mp
import numpy as np
import time
from deep_sort_realtime.deepsort_tracker import DeepSort

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Initialize DeepSORT Tracker
tracker = DeepSort(max_age=300)  # Allow tracking to persist for 10 seconds (300 frames at 30 FPS)

# Open Camera
cap = cv2.VideoCapture(0)

hand_tracked = False
hand_count = 0
last_seen_time = time.time()
tracked_hand_id = None
hand_visible = False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break
    
    # Flip the frame for better perspective
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    
    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    detections = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get bounding box around the detected hand
            x_min = min([lm.x for lm in hand_landmarks.landmark]) * w
            y_min = min([lm.y for lm in hand_landmarks.landmark]) * h
            x_max = max([lm.x for lm in hand_landmarks.landmark]) * w
            y_max = max([lm.y for lm in hand_landmarks.landmark]) * h
            
            # Ensure the bounding box forms a square
            box_size = max(int(x_max - x_min), int(y_max - y_min))
            x_min, y_min = max(0, int(x_min)), max(0, int(y_min))
            x_max, y_max = min(w, x_min + box_size), min(h, y_min + box_size)
            
            # Bounding box for tracking
            detection = [x_min, y_min, box_size, box_size, 0.9]
            detections.append(detection)
            
            # Draw square bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            print(f"Detected hand bounding box: {detection}")
    else:
        print("No hand detected")
    
    # Use DeepSORT tracking if a hand is detected
    if detections:
        print(f"Tracking detections (Before DeepSORT Call): {detections}")
        
        try:
            tracked_objects = tracker.update_tracks(detections, frame=frame)
            for track in tracked_objects:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                x, y, w, h = track.to_ltrb()
                
                # If a new hand appears after 10 seconds, increment the count
                current_time = time.time()
                if tracked_hand_id is None or (tracked_hand_id != track_id and not hand_visible):
                    hand_count += 1
                    tracked_hand_id = track_id
                    last_seen_time = current_time
                    hand_visible = True
                
                # Draw tracking bounding box on hand
                cv2.rectangle(frame, (int(x), int(y)), (int(w), int(h)), (255, 0, 0), 2)
                cv2.putText(frame, f'Hand ID: {track_id}', (int(x), int(y) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                print(f"Tracking hand ID: {track_id} at {x, y, w, h}")
                
        except Exception as e:
            print(f"Error in DeepSORT tracking: {e}")
    else:
        # Reset tracked hand ID if no hand is detected for more than 10 seconds
        if time.time() - last_seen_time > 10:
            tracked_hand_id = None
            hand_visible = False
    
    # Display hand count
    cv2.putText(frame, f'Hand Count: {hand_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Show Frame
    cv2.imshow("Hand Tracking", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()






# import cv2
# import mediapipe as mp
# import numpy as np
# import time
# from deep_sort_realtime.deepsort_tracker import DeepSort

# # Initialize MediaPipe Hand Detection
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)
# mp_draw = mp.solutions.drawing_utils

# # Initialize DeepSORT Tracker
# tracker = DeepSort(max_age=300)  # Allow tracking to persist for 10 seconds (300 frames at 30 FPS)

# # Open Camera
# cap = cv2.VideoCapture(0)

# hand_tracked = False
# hand_count = 0
# last_seen_time = time.time()
# tracked_hand_id = None

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame")
#         break
    
#     # Flip the frame for better perspective
#     frame = cv2.flip(frame, 1)
#     h, w, _ = frame.shape
    
#     # Convert to RGB for MediaPipe
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = hands.process(rgb_frame)
    
#     detections = []
#     if results.multi_hand_landmarks:
#         for hand_landmarks in results.multi_hand_landmarks:
#             # Get bounding box around the detected hand
#             x_min = min([lm.x for lm in hand_landmarks.landmark]) * w
#             y_min = min([lm.y for lm in hand_landmarks.landmark]) * h
#             x_max = max([lm.x for lm in hand_landmarks.landmark]) * w
#             y_max = max([lm.y for lm in hand_landmarks.landmark]) * h
            
#             # Ensure the bounding box forms a square
#             box_size = max(int(x_max - x_min), int(y_max - y_min))
#             x_min, y_min = max(0, int(x_min)), max(0, int(y_min))
#             x_max, y_max = min(w, x_min + box_size), min(h, y_min + box_size)
            
#             # Bounding box for tracking
#             detection = [x_min, y_min, box_size, box_size, 0.9]
#             detections.append(detection)
            
#             # Draw square bounding box
#             cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
#             mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#             print(f"Detected hand bounding box: {detection}")
#     else:
#         print("No hand detected")
    
#     # Use DeepSORT tracking if a hand is detected
#     if detections:
#         print(f"Tracking detections (Before DeepSORT Call): {detections}")
        
#         try:
#             tracked_objects = tracker.update_tracks(detections, frame=frame)
#             for track in tracked_objects:
#                 if not track.is_confirmed():
#                     continue
                
#                 track_id = track.track_id
#                 x, y, w, h = track.to_ltrb()
                
#                 # If a new hand appears after 10 seconds, increment the count
#                 current_time = time.time()
#                 if tracked_hand_id is None or (tracked_hand_id != track_id and current_time - last_seen_time > 10):
#                     hand_count += 1
#                     tracked_hand_id = track_id
#                     last_seen_time = current_time
                
#                 # Draw tracking bounding box on hand
#                 cv2.rectangle(frame, (int(x), int(y)), (int(w), int(h)), (255, 0, 0), 2)
#                 cv2.putText(frame, f'Hand ID: {track_id}', (int(x), int(y) - 10),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
#                 print(f"Tracking hand ID: {track_id} at {x, y, w, h}")
                
#         except Exception as e:
#             print(f"Error in DeepSORT tracking: {e}")
#     else:
#         # Reset tracked hand ID if no hand is detected for more than 10 seconds
#         if time.time() - last_seen_time > 10:
#             tracked_hand_id = None
    
#     # Display hand count
#     cv2.putText(frame, f'Hand Count: {hand_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
#     # Show Frame
#     cv2.imshow("Hand Tracking", frame)
    
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()





# import cv2
# import mediapipe as mp
# import numpy as np
# from deep_sort_realtime.deepsort_tracker import DeepSort

# # Initialize MediaPipe Hand Detection
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)
# mp_draw = mp.solutions.drawing_utils

# # Initialize DeepSORT Tracker
# tracker = DeepSort(max_age=30)  # Keep track of hands for longer duration

# # Open Camera
# cap = cv2.VideoCapture(0)

# hand_detected = False
# hand_count = 0

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame")
#         break
    
#     # Flip the frame for better perspective
#     frame = cv2.flip(frame, 1)
#     h, w, _ = frame.shape
    
#     # Convert to RGB for MediaPipe
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = hands.process(rgb_frame)
    
#     detections = []
#     if results.multi_hand_landmarks:
#         for hand_landmarks in results.multi_hand_landmarks:
#             # Get bounding box around the detected hand
#             x_min = min([lm.x for lm in hand_landmarks.landmark]) * w
#             y_min = min([lm.y for lm in hand_landmarks.landmark]) * h
#             x_max = max([lm.x for lm in hand_landmarks.landmark]) * w
#             y_max = max([lm.y for lm in hand_landmarks.landmark]) * h
            
#             # Ensure the bounding box has valid values
#             x_min, y_min = max(0, int(x_min)), max(0, int(y_min))
#             width, height = max(1, int(x_max - x_min)), max(1, int(y_max - y_min))

#             # Corrected bounding box structure
#             detection = [x_min, y_min, width, height, 0.9]
#             detections.append(detection)

#             mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#             print(f"Detected hand bounding box: {detection}")
#     else:
#         print("No hand detected")
    
#     # Use DeepSORT tracking if a hand is detected
#     if detections:
#         print(f"Tracking detections (Before DeepSORT Call): {detections}")
        
#         try:
#             tracked_objects = tracker.update_tracks(detections, frame=frame)
            
#             for track in tracked_objects:
#                 if not track.is_confirmed():
#                     continue
                
#                 track_id = track.track_id
#                 x, y, w, h = track.to_ltrb()
#                 cv2.rectangle(frame, (int(x), int(y)), (int(w), int(h)), (0, 255, 0), 2)
#                 cv2.putText(frame, f'Hand ID: {track_id}', (int(x), int(y) - 10),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
#                 print(f"Tracking hand ID: {track_id} at {x, y, w, h}")
                
#                 # Check for new hand detections
#                 if not hand_detected:
#                     hand_count += 1
#                     hand_detected = True
#         except Exception as e:
#             print(f"Error in DeepSORT tracking: {e}")
#     else:
#         hand_detected = False
    
#     # Display hand count
#     cv2.putText(frame, f'Hand Count: {hand_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
#     # Show Frame
#     cv2.imshow("Hand Tracking", frame)
    
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
