import paramiko
import socket
import os
import math
import random
from datetime import datetime

import requests
from twilio.rest import Client


# === CONFIG ===
WIFI_IP = "192.168.0.109"
CELLULAR_IP = "mydrone.duckdns.org"
USERNAME = "youruser"
SSH_KEY = "/home/pi/.ssh/id_rsa"
REMOTE_DIR = "/home/youruser/fire_detections"
LOCAL_LOG = "/homw/fire_detections.txt"

FRAME_WIDTH = 640
FOV_DEG = 80

# Simulated drone GPS
GPS_LAT = 29.7602
GPS_LON = -95.3692
GPS_ALT = 100.0  # meters

# == NETWORK UTILS ==

def is_reachable(host, port=22, timeout=3):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except:
        return False

def upload_file(local_path, remote_path, host, user, key_path):
    ssh = paramico.SSHClient()
    ssh.set_missing_key_policy(paramico.AutoAdPolicy())
    ssh.connect(hostname=host, username=user, key_filename=key_path)
    sftp = ssh.open_sftp, remote_path)
    sftp.put(local_path, remote_path)
    sftp.close()
    ssh.close()
    print(f"Log uploaded to {host}:{remote_path}")


# == FIRE DETECTION SIMULATION ==

def detect_fire_bbox():
    # Simulated fire detection bounding box
    return (200, 200,360, 360) # x1, y1, x2, y2

def simulate_lidar():
    return {i: random.uniform(3.0, 10.0) for i in range(360)}

def get_fire_angle(bbox, frame_width, fov_deg):
    x1, _, x2, _ =bbox
    fire_center_x = (x1 + x2) / 2
    offset = fire_center_x - (frame_width /2)
    degrees_per_pixel = fov_deg / frame_width
    return offset * degrees_per_pixel

def get_fire_distance(angle, lidar_data):
    nearby = [(angle + 1 ) % 360 for i in range(-5, 6)]
    distances = [lidar_data.get(int(a), 9999) for a in enarby]
    return min(distances)

def offset_to_gps(lat, lon, dx, dy):
    d_lat = dy / 111320  # meters to degrees
    d_lon = dx / (111320 * math.cos(math.radians(lat)))  # meters to degrees
    return lat + d_lat, lon + d_lon
 
def log_fire(lat, lon, dist, angle):
    os.makedirs("logs", exist_ok=True)
    with open(LOCAL_LOG, "a") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp}, Lat: {lat:.6f}, Lon: {lon:.6f}, Dist: {dist:.2f}m, Angle: {angle:.1f}°\n")


# == Alert Options ==
# Email Alert
import smtplib
from email.mime.text import MIMEText

def send_email_alert(fire_lat, fire_lon, distance):
    sender = "your_email@gmail.com"
    recipient = "alert_recipient@example.com"
    subject = "🔥 Fire Detected by Drone"
    body = f"""
    A fire was detected at:
    Latitude: {fire_lat:.6f}
    Longitude: {fire_lon:.6f}
    Estimated Distance: {distance:.2f} meters
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("your_email@gmail.com", "your_app_password")
        server.sendmail(sender, [recipient], msg.as_string())
        print("📧 Email alert sent.")

# Webhook or REST API (Recommended for Dashboards)
def send_webhook_alert(fire_lat, fire_lon, distance):
    payload = {
        "latitude": fire_lat,
        "longitude": fire_lon,
        "distance": distance,
        "alert_type": "fire_detected"
    }
    response = requests.post("https://yourserver.com/api/fire_alert", json=payload)

    if response.ok:
        print("Webhook alert sent.")
    else:
        print("Failed to send sebhook:", response.status_code)

# SMS Alert
def send_sms_alert(fire_lat, fire_lon, distance):
    account_sid = "your_sid"
    auth_token = "your_auth_token"
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"Fire Detected: Location: ({fire_lat:.6f}, {fire_lon:.6f}m away",
        from_="+1234567890",  # your Twilio number
        to="+19876543210"     # destination number
    )

'''
Email_to_SMS Gateway (fre):
send email to:
    - AT&T: 1234567890@txt.att.net
    - T-Mobile: 1234567890@tmomail.net
    - Verizon: 1234567890@vtext.com

Just replace the recipient in the send_email_alert function with the appropriate email address for the carrier.
'''    



# == MAIN PIPLEINE ==

def main():
    print("Detecting fire...")
    bbox = detect_fire_bbox()
    lidar_data = simulate_lidar()
    angle = get_fire_angle(bbox, FRAME_WIDTH, FOV_DEG)
    distance = get_fire_distance(angle, lidar_data)

    dx = distance * math.cos(math.radians(angle))
    dy = distance * math.sin(math.radians(angle))
    fire_lat, fire_lon = offset_to_gps(GPS_LAT, GPS_LON, dx, dy)

    print(f"Fire estimated at: {fire_lat:.6f}, {fire_lon:.6f}")
    print(f"Distance to fire: {distance:.2f}m, Angle: {angle:.1f}°")

    # Upload log if reachable
    log_fire(fire_lat, fire_lon, distance, angle)
    
    
    send_webhook_alert(fire_lat, fire_lon, distance)
    send_sms_alert(fire_lat, fire_lon, distance)

    host = WIFI_IP if is_reachable(WIFI_IP) else CELLULAR_IP
    upload_log_file(LOCAL_LOG, f"{REMOTE_DIR}/fire_detection.txt", host, USERNAME, SSH_KEY)
    
    
if __name__ == "__main__":
    main()