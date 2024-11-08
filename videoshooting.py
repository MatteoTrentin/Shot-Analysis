import math
import cv2
import mediapipe as mp

# Set up pose detector and video capture
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
cap = cv2.VideoCapture("C:\\Users\\mtren\\Downloads\\output_shot_analysis.avi")

# Get video properties for output
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Define the codec and create VideoWriter object to save output
out = cv2.VideoWriter('output_shot_analysis.avi', cv2.VideoWriter_fourcc(*'XVID'), fps, (frame_width, frame_height))

def calculate_angle(a, b, c):
    radians = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

follow_through_frames = 0          # Counter to verify follow-through hold
follow_through_cooldown = 0        # Cooldown timer after follow-through detection
cooldown_duration = fps * 1.5      # Keep follow-through for 1.5 seconds

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert to RGB for MediaPipe and process
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.pose_landmarks:
        # Draw pose landmarks on the video
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # Get landmarks for shoulder, elbow, and wrist
        landmarks = results.pose_landmarks.landmark
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        # Calculate angles
        shoulder_elbow = calculate_angle(shoulder, elbow, wrist)
        elbow_wrist = calculate_angle(elbow, wrist, shoulder)

        # Check phase feedback, with cooldown for follow-through phase
        if follow_through_cooldown > 0:
            # Keep displaying follow-through during cooldown period
            cv2.putText(image, "Follow-Through Phase: Fully extend wrist and elbow.", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            follow_through_cooldown -= 1  # Decrement cooldown timer

        elif shoulder_elbow < 100:  # Preparation phase
            cv2.putText(image, "Preparation Phase: Bend elbow to 90-100 degrees.", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            follow_through_frames = 0  # Reset follow-through counter

        elif 100 <= shoulder_elbow < 160 and elbow_wrist < 150:  # Release phase
            cv2.putText(image, "Release Phase: Smoothly extend elbow and wrist.", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            follow_through_frames = 0  # Reset follow-through counter
            
        elif shoulder_elbow > 160 and wrist.y < shoulder.y and wrist.y < elbow.y:
            # Checking if wrist is higher than both shoulder and elbow
            follow_through_frames += 1  # Increment follow-through detection frames
            if follow_through_frames >= fps // 4:  # Hold follow-through for at least a fraction of a second
                cv2.putText(image, "Follow-Through Phase: Fully extend wrist and elbow.", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                follow_through_cooldown = cooldown_duration  # Activate cooldown timer
        else:
            follow_through_frames = 0  # Reset if conditions are not met

    # Write the frame to the output video
    out.write(image)
    
    # Display the result (optional for real-time viewing)
    cv2.imshow("Shooting Form Analysis", image)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

# Print message when saving is complete
print("The output video has been saved as 'output_shot_analysis.avi'.")
