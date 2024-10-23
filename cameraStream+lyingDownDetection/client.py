import socket
import cv2
import struct
import numpy as np
import mediapipe as mp
import threading

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))
# Initialize Mediapipe Pose class and drawing utilities
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
imagestack = []
prev_im = cv2.imread("load.jpg")
# Function to check if person is lying down
def is_lying_down(landmarks):
    # Extract the y-coordinates of important body points
    points_of_interest = ['LEFT_SHOULDER', 'RIGHT_SHOULDER', 'LEFT_HIP', 'RIGHT_HIP', 'LEFT_KNEE', 'RIGHT_KNEE', 'LEFT_ANKLE', 'RIGHT_ANKLE']
    y_coords = [landmarks[mp_pose.PoseLandmark[point].value].y for point in points_of_interest]

    # Calculate the range of the y-coordinates
    y_range = np.ptp(y_coords)  # Peak-to-peak (max - min)

    # Set a threshold to determine if the person is lying down
    # If y_range is small (points are close on the y-axis), the person is lying down
    return y_range < 0.2  # Adjust threshold as needed
def image_processing(image2):
    try:
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            # Convert the frame to RGB as Mediapipe requires
            image_rgb = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False  # Improve performance

            # Make pose detection
            results = pose.process(image_rgb)

            # Draw pose landmarks on the image
            image_rgb.flags.writeable = True
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image_bgr, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2)
                )

                # Check if person is lying down
                if is_lying_down(results.pose_landmarks.landmark):
                    cv2.putText(image_bgr, "Lying Down", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                else:
                    cv2.putText(image_bgr, "Not Lying Down", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                # Show the image with pose landmarks
                #cv2.imshow('Pose Estimation', image_bgr)
                imagestack.append(image_bgr)
    except Exception as e:
        print(e)

def main():
    global prev_im
    data = b""
    try:
        while True:
            data = b""
            # Retrieve message size
            data_size = client_socket.recv(4)
            if not data_size:
                break
            frame_size = struct.unpack(">I", data_size)[0]
            #print(frame_size)
            # Retrieve the actual frame data
            while len(data) < frame_size:
                packet = client_socket.recv(frame_size - len(data))
                if not packet:
                    return None
                data += packet
            print(f"Expected frame size: {frame_size}, Received data size: {len(data)}")


            # Convert frame_data into a numpy array and decode it
            frame_array = np.frombuffer(data, dtype=np.uint8)
            image = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            print(image)

            # If the image is None, the frame was corrupted
            if image is None:
                print("Failed to decode image")
                continue
            if len(image.shape) == 2:  # Grayscale image (2D array)
                print("Image is grayscale, converting to BGR")
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

            image = image.astype(np.uint8)
            if np.array_equal(prev_im, image):
                continue
            threading.Thread(target=image_processing, args=(image,)).start()
            prev_im = image
            try:
                if imagestack:  # Check if there's an image in the stack
                    cv2.imshow("Processed Image", imagestack[0])
                    imagestack.pop(0)
            except Exception as e:
                print(e)
            # Break the loop on 'q' key press
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
    finally:
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()