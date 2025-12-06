Autonomous Crowd Monitoring System
1. Project Overview
This project implements a fully autonomous, real-time crowd detection and counting system designed for deployment on a Raspberry Pi 5. It uses a custom-trained YOLOv8 AI model to detect people in a live video feed and the ByteTrack algorithm to assign unique IDs, enabling an accurate count of unique visitors throughout the day.

Key Features:

Edge AI: Runs efficiently on a Raspberry Pi 5 using a quantized (FP16) ONNX model.

Autonomous Operation: Starts automatically on boot, runs 24/7, and recovers from power outages without data loss.

Hardware Protection: Utilizes batched writing and external USB storage to minimize SD card wear.

Automated Reporting: Generates a daily CSV log of unique footfall and emails it to designated recipients at midnight.

Remote Monitoring: Hosts a secure web dashboard for viewing the live video feed and real-time count from any device on the local network.

2. Hardware Requirements
Computer: Raspberry Pi 5 (4GB or 8GB recommended)

Power Supply: Official Raspberry Pi 27W USB-C Power Supply (5.1V, 5A) - Critical for stability.

Storage:

microSD Card (32GB+, High Endurance recommended) for the OS.

USB Pendrive (64GB+) for storing log data.

Camera: USB Webcam or Ethernet/IP Camera (RTSP stream supported).

Cooling: Active cooling case with fan (official case recommended) + optional external airflow.

3. Software Architecture
Backend (Python)
The core logic runs as a system service (crowd-monitor.service) on the Raspberry Pi.

Framework: Flask (for the web server).

AI Engine: Ultralytics YOLOv8 (running via ONNX Runtime).

Tracking: ByteTrack.

Data Management: Custom logic for batched CSV logging, daily rollover, and email automation.

Frontend (React.js)
A modern, dark-themed dashboard for monitoring the system.

Framework: React + Vite.

Styling: Tailwind CSS.

Features: Live video stream display, real-time connection status, and simulated terminal logs.

4. Installation & Setup
Prerequisites
Raspberry Pi 5 running Raspberry Pi OS (64-bit).

Python 3.10 installed (recommended via pyenv).

Enabled SSH and VNC interfaces.

Step 1: Clone the Repository
Bash

git clone <your-repo-url>
cd crowd-monitoring-system
Step 2: Install Dependencies
Create a virtual environment and install the required Python libraries.

Bash

# Navigate to the backend directory
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Step 3: Configure USB Storage
Format your USB drive to ext4.

Create a mount point: sudo mkdir /mnt/crowd_logs

Edit /etc/fstab to auto-mount the drive on boot using its UUID.

Set permissions: sudo chown -R user:user /mnt/crowd_logs

Step 4: Setup Automation (Systemd & Cron)
Systemd Service: Copy the provided crowd-monitor.service file to /etc/systemd/system/.

Update paths in the file to match your user and project location.

Enable the service: sudo systemctl enable crowd-monitor.service

Daily Reboot: Add a cron job to reboot the Pi daily at 2:00 AM for long-term stability.

Run crontab -e and add: 0 2 * * * /sbin/reboot

5. Usage
Deployment
Once installed, the system is fully autonomous.

Power On: Plug in the Raspberry Pi.

Auto-Start: The monitoring service starts automatically after boot.

Verify: Check the status via SSH: sudo systemctl status crowd-monitor.service

Monitoring Dashboard
To view the live feed:

Ensure your laptop is on the same Wi-Fi network as the Pi.

Run the React frontend on your laptop (or host it on the Pi).

Enter the Pi's IP address in the dashboard to connect.

Data Retrieval
Daily Reports: Check your email inbox for the automated daily report (sent at midnight).

Manual Access: Connect to the Pi via SFTP or plug the USB drive into your computer to access the raw CSV logs in /mnt/crowd_logs.

6. Performance
Inference Speed: ~160ms per frame (~6 FPS) on Raspberry Pi 5 using quantized YOLOv8 Nano.

Accuracy: * Precision: 87.6%

Recall: 80.1%

mAP @ 50%: 52.5%

Power Consumption: Optimized for stability with the official 27W power supply.

7. Project Structure
├── backend/
│   ├── crowd_counter.py        # Main application logic
│   ├── yolov8n.onnx            # Quantized AI model
│   ├── requirements.txt        # Python dependencies
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Dashboard UI logic
│   │   └── ...
│   └── package.json
└── README.md
8. Troubleshooting
Service Fails to Start: Check logs with journalctl -u crowd-monitor.service -f.

Camera Timeout: Ensure you are using the official 27W power supply. Low voltage causes USB peripherals to disconnect.

Incorrect Time in Logs: Verify the Pi's timezone is set to your local time (sudo raspi-config).
