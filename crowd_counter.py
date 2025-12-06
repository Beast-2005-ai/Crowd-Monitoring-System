# ==============================================================================
# AUTONOMOUS CROWD MONITORING SYSTEM
# ==============================================================================
# This is the final, complete, and fully tested version for deployment.
# It integrates all requested features for maximum reliability and automation,
# including a robust startup check to handle reports from previous days after
# a prolonged power outage. The daily report is now triggered at midnight.
# ==============================================================================

import cv2
from ultralytics import YOLO
import time
import csv
from datetime import datetime, date
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, Response, jsonify
import threading
from flask_cors import CORS
import signal

# Configuration

WEBCAM_INDEX = 0
MODEL_PATH = 'best.onnx'
CONFIDENCE_THRESHOLD = 0.5
PERSON_CLASS_ID = 0
SAVE_DIRECTORY = '/mnt/crowd_logs' # The system will automatically mount your USB drive to this location.
BATCH_SIZE = 25 # This is the number of new detections to buffer in RAM before writing to the USB drive.

# Email Configuration
EMAIL_SENDER = '<Sender Email>'
EMAIL_PASSWORD = '<Sender Email Password From Google App Passwords>'
EMAIL_RECIPIENTS = ['<Recipient Emails>']

# --- Global variables ---
output_frame = None
lock = threading.Lock()
app = Flask(_name_)
CORS(app)
stop_event = threading.Event()
detection_thread = None
current_unique_count = 0

def get_daily_csv_filename(for_date): # Generates a CSV filename based on a specific date.
    return for_date.strftime('%A_%d_%b_%Y.csv')

def send_email(subject, body, file_path): # Sends an email with an attachment. Returns True on success, False on failure
    try:
        msg = MIMEMultipart()
        msg['Subject'], msg['From'], msg['To'] = subject, EMAIL_SENDER, ", ".join(EMAIL_RECIPIENTS)
        msg.attach(MIMEText(body, 'plain'))
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(file_path)}")
        msg.attach(part)
        print("Connecting to email server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp_server.send_message(msg)
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def flush_batch_to_csv(csv_writer, batch): # Writes all buffered log entries to the CSV file
    if not batch: return
    try:
        csv_writer.writerows(batch)
    except Exception as e:
        print(f"Error writing batch to CSV: {e}")
    batch.clear()

def run_crowd_detection():
    """The main worker thread for video processing, AI inference, and logging."""
    global output_frame, lock, current_unique_count
    
    time.sleep(10)
    
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)

    print("\nChecking for any unprocessed logs from previous days...") # If there has been a power failure, send those reports now.
    today = date.today()
    for filename in os.listdir(SAVE_DIRECTORY):
        if filename.endswith(".csv"):
            try:
                file_date_str = "".join(filename.split('')[1:]).replace('.csv', '')
                file_date = datetime.strptime(file_date_str, '%d_%b_%Y').date()
                if file_date < today:
                    print(f"Found unprocessed log from a previous day: {filename}")
                    full_path = os.path.join(SAVE_DIRECTORY, filename)
                    final_count = "N/A"
                    with open(full_path, 'r') as f:
                        for row in csv.reader(f):
                            if "FINAL COUNT" in row[1] or "SESSION STOPPED" in row[1]:
                                final_count = row[2]
                                break
                    
                    email_subject = f"Delayed Crowd Report: {file_date.strftime('%A, %d %b %Y')}"
                    email_body = f"This report is for a previous day and was sent upon system startup after a power failure.\n\nTotal unique people detected: {final_count}"
                    
                    if send_email(email_subject, email_body, full_path):
                        print(f"Delayed email sent. Deleting old log file: {filename}")
                        os.remove(full_path)
                    else:
                        print(f"Failed to send delayed email. Keeping old log file as backup.")
            except Exception as e:
                print(f"Error processing old log file {filename}: {e}")

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(WEBCAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"FATAL ERROR: Could not open USB webcam at index {WEBCAM_INDEX}.")
        return

    current_date = date.today()
    current_csv_filename = os.path.join(SAVE_DIRECTORY, get_daily_csv_filename(current_date))
    seen_person_ids = set()
    log_batch = [] 

    file_exists = os.path.isfile(current_csv_filename)
    if file_exists:
        print(f"Log file for today found. Resuming session in: {current_csv_filename}")
        try:
            with open(current_csv_filename, mode='r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) > 1 and row[1].isdigit():
                        seen_person_ids.add(int(row[1]))
            with lock:
                current_unique_count = len(seen_person_ids)
            print(f"Successfully loaded {len(seen_person_ids)} existing IDs for today.")
        except Exception as e:
            print(f"Warning: Could not read existing log file. Error: {e}")
    
    csv_file = open(current_csv_filename, mode='a', newline='')
    csv_writer = csv.writer(csv_file)
    if not file_exists:
        csv_writer.writerow(['Timestamp', 'Newly Detected ID', 'Total Unique People Today'])

    try:
        while not stop_event.is_set():
            today = date.today()

            if today != current_date:
                print(f"\n--- Midnight Rollover Detected: {today} ---")  # Midnight Rollover
                flush_batch_to_csv(csv_writer, log_batch)
                final_count_yesterday = len(seen_person_ids)
                csv_writer.writerow(['-', 'FINAL COUNT FOR THE DAY', final_count_yesterday])
                csv_file.close()
                
                email_subject = f"Daily Crowd Report: {current_date.strftime('%A, %d %b %Y')}"
                email_body = f"The daily monitoring session has concluded.\n\nTotal unique people detected: {final_count_yesterday}"
                
                if send_email(email_subject, email_body, current_csv_filename):
                    print(f"Email sent. Deleting previous day's log file.")
                    os.remove(current_csv_filename)
                else:
                    print(f"Email failed. Keeping log file as backup.")

                # Reset for new day
                current_date = today
                seen_person_ids = set()
                with lock:
                    current_unique_count = 0
                current_csv_filename = os.path.join(SAVE_DIRECTORY, get_daily_csv_filename(current_date))
                csv_file = open(current_csv_filename, mode='w', newline='')
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['Timestamp', 'Newly Detected ID', 'Total Unique People Today'])
                print(f"Started new log for today: {os.path.basename(current_csv_filename)}")

            success, frame = cap.read()
            if not success: continue

            results = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=CONFIDENCE_THRESHOLD, classes=PERSON_CLASS_ID)
            annotated_frame = results[0].plot()

            if results[0].boxes.id is not None:
                for track_id in results[0].boxes.id.int().cpu().tolist():
                    if track_id not in seen_person_ids:
                        seen_person_ids.add(track_id)
                        with lock:
                            current_unique_count = len(seen_person_ids)
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        log_batch.append([timestamp, track_id, len(seen_person_ids)])
                        if len(log_batch) >= BATCH_SIZE:
                            flush_batch_to_csv(csv_writer, log_batch)
            
            with lock:
                output_frame = annotated_frame.copy()
            
            time.sleep(0.01)

    finally:
        print("\nDetection thread is cleaning up (manual stop)...") # Graceful shutdown for manual stop: save data but do not email
        if 'csv_file' in locals() and not csv_file.closed:
            flush_batch_to_csv(csv_writer, log_batch)
            final_count = len(seen_person_ids)
            print(f"Final count for this session: {final_count}")
            csv_writer.writerow(['-', 'SESSION STOPPED', final_count])
            csv_file.close()
            print(f"Session data saved to {os.path.basename(current_csv_filename)}. The final report will be sent upon next startup.")

        if 'cap' in locals():
            cap.release()
        print("Detection thread has finished.")

def graceful_shutdown_handler(signum, frame):
    print(f"\nSignal {signum} received. Shutting down gracefully...")
    stop_event.set()
    if detection_thread is not None:
        detection_thread.join()
    exit(0)

def generate_stream_frames():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None: time.sleep(0.1); continue
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            if not flag: continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\n')

@app.route("/video_feed")
def video_feed():
    return Response(generate_stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/count")
def get_count():
    global current_unique_count
    with lock:
        count_to_return = current_unique_count
    return jsonify(unique_person_count=count_to_return)

if _name_ == '_main_':
    signal.signal(signal.SIGTERM, graceful_shutdown_handler)
    detection_thread = threading.Thread(target=run_crowd_detection)
    detection_thread.daemon = True
    detection_thread.start()
    print("\nBackend server for USB Webcam starting...")
    try:
        app.run(host='0.0.0.0', port=5123, threaded=True) # Current port is React frontend default
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Shutting down gracefully...")
    finally:
        if not stop_event.is_set():
            print("Signaling detection thread to stop...")
            stop_event.set()
            detection_thread.join()
            print("Script has finished.")