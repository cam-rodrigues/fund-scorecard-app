import csv
import os
from datetime import datetime

LOG_FILE = "audit_log.csv"

def log_action(user, action, details=""):
    timestamp = datetime.now().isoformat()
    log_entry = [timestamp, user, action, details]

    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User", "Action", "Details"])
        writer.writerow(log_entry)
