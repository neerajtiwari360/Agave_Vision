import cv2

rtsp_url = "rtsp://admin:AgaveNetworks123!@192.168.40.74:554//h264Preview_01_main"
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Error: Cannot open RTSP stream")
    exit()

# Retrieve original frame width and height
original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Original resolution: {original_width} x {original_height}")

# Set window with half the original resolution
half_width, half_height = original_width // 4, original_height // 4
cv2.namedWindow('Reolink TrackMix RTSP Stream', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Reolink TrackMix RTSP Stream', half_width, half_height)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Can't receive frame (stream end?). Exiting ...")
        break

    # Resize frame to half the original dimensions for display
    resized_frame = cv2.resize(frame, (half_width, half_height))

    cv2.imshow('Reolink TrackMix RTSP Stream', resized_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()






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
