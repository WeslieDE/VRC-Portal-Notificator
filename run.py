import os
import time
import re
from pathlib import Path
from datetime import datetime
from collections import deque
from plyer import notification

# ==============================
# CONFIG
# ==============================
WINDOW_SECONDS = 10
TRIGGER_COUNT = 5
CHECK_INTERVAL = 0.1

# ==============================
# REGEX (exakt deine Messages)
# ==============================
PORTAL_REGEX = re.compile(
    r"\[PortalManager\] Received portal destroy event\.|\[Behaviour\] Portal can't be configured because API didn't give back the full ID\."
)

# ==============================
# Logdatei finden
# ==============================
def get_latest_log_file():
    base_path = Path(os.getenv("USERPROFILE")) / "AppData/LocalLow/VRChat/VRChat"
    logs = list(base_path.glob("output_log_*.txt"))
    if not logs:
        return None
    return max(logs, key=lambda f: f.stat().st_mtime)

# ==============================
# Watcher
# ==============================
def watch_log():
    print("👀 VRChat Portal Error Watcher gestartet")

    timestamps = deque()
    alert_sent = False
    current_log_name = None

    while True:
        log_path = get_latest_log_file()
        if not log_path:
            print("❌ Keine Logdatei gefunden")
            time.sleep(5)
            continue

        if log_path.name != current_log_name:
            current_log_name = log_path.name
            print(f"📄 Logdatei: {current_log_name}")

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(CHECK_INTERVAL)

                    new_log = get_latest_log_file()
                    if new_log and new_log.name != current_log_name:
                        break
                    continue

                if PORTAL_REGEX.search(line):
                    now = datetime.now()
                    timestamps.append(now)

                    # Alte Einträge entfernen
                    while timestamps and (now - timestamps[0]).total_seconds() > WINDOW_SECONDS:
                        timestamps.popleft()

                    # Trigger
                    if len(timestamps) >= TRIGGER_COUNT and not alert_sent:
                        alert_sent = True

                        notification.notify(
                            title="VRChat Portal Fehler",
                            message="⚠️ ALARM: Portal-Fehler!",
                            timeout=3
                        )

                        print("⚠️ ALARM: Portal-Fehler!")

                # Reset nach Ruhephase
                if alert_sent and timestamps:
                    if (datetime.now() - timestamps[-1]).total_seconds() > WINDOW_SECONDS:
                        timestamps.clear()
                        alert_sent = False
                        print("🟢 Portal-Fehler zurückgesetzt")

# ==============================
# START
# ==============================
if __name__ == "__main__":
    try:
        watch_log()
    except KeyboardInterrupt:
        print("👋 Beendet")
