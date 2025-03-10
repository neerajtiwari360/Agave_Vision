import cv2
from ultralytics import YOLO
# Load the trained YOLO model
model = YOLO(r'G:\My Drive\CODE\GITHUB\Vision-WorkFlow\model\best_model.pt')
# Start capturing video from the webcam (0 is usually the default camera)
cap = cv2.VideoCapture(0)
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break
    # Run inference on the current frame
    results = model.predict(frame)
    # Extract the image with predictions
    image_with_preds = results[0].plot()  # Get the first (and only) result
    # Convert image from RGB to BGR (for OpenCV display)
    image_bgr = cv2.cvtColor(image_with_preds, cv2.COLOR_RGB2BGR)
    # Display the resulting frame
    cv2.imshow('Webcam Live Feed', image_bgr)
    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()