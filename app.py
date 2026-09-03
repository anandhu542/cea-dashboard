"""
CEA Dashboard — Raspberry Pi backend
-------------------------------------
Reads one JSON line per cycle from the ATmega2560 over USB serial
and serves the latest reading to a browser dashboard.

Mega2560 -> USB cable -> Raspberry Pi 4B
On the Pi, the Mega usually shows up as /dev/ttyACM0 (sometimes
/dev/ttyACM1 if something else is plugged in). Run:
    ls /dev/ttyACM* /dev/ttyUSB*
to confirm, and update SERIAL_PORT below if needed.

Run:
    python3 app.py
Then open, from any device on the same network:
    http://<raspberry-pi-ip>:5000
"""

import json
import threading
import time
from datetime import datetime

import serial
from flask import Flask, jsonify, render_template

# ---------------- Configuration ----------------
SERIAL_PORT = "/dev/ttyUSB0"   # change if your Mega enumerates differently
BAUD_RATE = 115200              # must match Serial.begin() in the .ino
RECONNECT_DELAY = 3             # seconds to wait before retrying a lost connection

app = Flask(__name__)

# Shared state between the serial-reader thread and the Flask routes
latest_data = {}
data_lock = threading.Lock()
connection_status = {"connected": False, "last_update": None}


def serial_reader():
    """Background thread: continuously reads JSON lines from the Mega
    and keeps latest_data up to date. Reconnects automatically if the
    USB connection drops."""
    global latest_data, connection_status

    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                print(f"[serial] connected on {SERIAL_PORT}")
                connection_status["connected"] = True
                # Let the Mega finish its boot/reset after the port opens
                time.sleep(2)
                ser.reset_input_buffer()

                while True:
                    raw_line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw_line:
                        continue
                    try:
                        parsed = json.loads(raw_line)
                    except json.JSONDecodeError:
                        # Ignore boot messages / partial lines that aren't JSON
                        continue

                    with data_lock:
                        latest_data = parsed
                        connection_status["last_update"] = datetime.now().isoformat()

        except serial.SerialException as e:
            print(f"[serial] error: {e} — retrying in {RECONNECT_DELAY}s")
            connection_status["connected"] = False
            time.sleep(RECONNECT_DELAY)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    with data_lock:
        payload = dict(latest_data)
        payload["_connected"] = connection_status["connected"]
        payload["_last_update"] = connection_status["last_update"]
    return jsonify(payload)


if __name__ == "__main__":
    reader_thread = threading.Thread(target=serial_reader, daemon=True)
    reader_thread.start()

    # host="0.0.0.0" makes it reachable from other devices on the LAN
    app.run(host="0.0.0.0", port=5000, debug=False)
