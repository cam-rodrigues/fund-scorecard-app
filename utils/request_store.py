import csv
import os
from datetime import datetime

REQUESTS_FILE = "user_requests.csv"

def save_request(description: str, email: str = "") -> None:
    """Append a user feature request to the CSV log."""
    entry = [datetime.now().isoformat(), description.strip(), email.strip()]
    file_exists = os.path.isfile(REQUESTS_FILE)
    with open(REQUESTS_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Description", "Email"])
        writer.writerow(entry)

