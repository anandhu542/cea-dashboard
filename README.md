# CEA Dashboard — ATmega2560 + Raspberry Pi 4B

Shows live sensor/actuator data from the Mega2560 in a browser, served
from the Pi.

## How it works
- The Mega2560 prints one compact JSON line per 800ms cycle over USB
  Serial (`sendJSON()` in the .ino).
- The Pi runs `app.py`, which reads that serial port in a background
  thread and keeps the latest reading in memory.
- A Flask web server serves `index.html`, which polls `/data` every
  2 seconds and updates the page — no page reloads.

## 1. Wiring
Just a single USB cable: Mega2560's USB port → Raspberry Pi 4B USB
port. No extra electronics needed — the Mega's own USB-serial chip
handles this.

## 2. Find the serial port on the Pi
```bash
ls /dev/ttyACM* /dev/ttyUSB*
```
It's almost always `/dev/ttyACM0` for a Mega2560. If you have other
USB-serial devices plugged in, check which one is the Mega:
```bash
dmesg | grep -i tty
```
Update `SERIAL_PORT` in `app.py` if it's different.

### Permissions
Your user needs access to the serial port:
```bash
sudo usermod -a -G dialout $USER
```
Log out and back in (or reboot) for this to take effect.

## 3. Install dependencies on the Pi
```bash
sudo apt update
sudo apt install python3-pip python3-venv -y
cd pi_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Run it
```bash
python3 app.py
```
Then, from any device on the same Wi-Fi/LAN, open:
```
http://<raspberry-pi-ip>:5000
```
Find the Pi's IP with `hostname -I` on the Pi itself.

## 5. (Optional) Auto-start on boot
Copy the service file and enable it:
```bash
sudo cp cea-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cea-dashboard
sudo systemctl start cea-dashboard
```
Check status/logs:
```bash
sudo systemctl status cea-dashboard
journalctl -u cea-dashboard -f
```
Note: if you used a venv, change `ExecStart` in the service file to
point at `venv/bin/python3` instead of the system Python.

## Notes
- If the Mega resets when the port opens (normal for Arduino boards
  over USB), `app.py` already waits 2 seconds after connecting before
  reading, so you won't see garbled boot-time serial noise.
- The dashboard auto-reconnects if the USB cable is unplugged and
  replugged — no restart needed.
- To view this from outside your home network, you'd need port
  forwarding or a remote-access tool (e.g. Tailscale) — happy to help
  set that up if you want it.
