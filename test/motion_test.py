import cv2
import numpy as np
import time

# Open video capture
cap = cv2.VideoCapture(0)

# Read initial frames
ret, frame1 = cap.read()
ret, frame2 = cap.read()

motion_detected = False
last_motion_time = time.time()

while cap.isOpened():
    # Compute frame difference
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    major_movement = False

    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Ignore small movements
            major_movement = True
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)

    current_time = time.time()

    # If movement detected, print once and update last motion time
    if major_movement:
        if not motion_detected:
            print("Motion detected!")
            motion_detected = True
        last_motion_time = current_time  # Reset timer on motion detection

    # If no movement for 5 seconds, print "No motion detected."
    elif motion_detected and (current_time - last_motion_time > 5):
        print("No motion detected.")
        motion_detected = False  # Reset motion flag

    # Show the video feed
    cv2.imshow("Motion Detection", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(10) == 27:  # Press 'ESC' to exit
        break

cap.release()
cv2.destroyAllWindows()






# import cv2
# import numpy as np

# # Open video capture
# cap = cv2.VideoCapture(0)

# # Read initial frames
# ret, frame1 = cap.read()
# ret, frame2 = cap.read()

# while cap.isOpened():
#     # Compute frame difference
#     diff = cv2.absdiff(frame1, frame2)
#     gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
#     blur = cv2.GaussianBlur(gray, (5, 5), 0)
#     _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

#     # Find contours
#     contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

#     major_movement = False

#     for contour in contours:
#         if cv2.contourArea(contour) > 500:  # Ignore small movements
#             major_movement = True
#             x, y, w, h = cv2.boundingRect(contour)
#             cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)

#     # Print motion status
#     if major_movement:
#         print("Motion detected!")
#     else:
#         print("No motion detected.")

#     # Show the video feed
#     cv2.imshow("Motion Detection", frame1)
#     frame1 = frame2
#     ret, frame2 = cap.read()

#     if cv2.waitKey(10) == 27:  # Press 'ESC' to exit
#         break

# cap.release()
# cv2.destroyAllWindows()
