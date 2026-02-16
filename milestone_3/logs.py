# milestone_3/logs.py

from datetime import datetime

LOG_FILE = "milestone_3/access.log"

def log_access(username: str, role: str, query: str, confidence: float):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = f'{timestamp} {username} {role} "{query}" {confidence}\n'

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)
