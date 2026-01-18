import serial
import time
import threading
import collections
import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

# =======================
# USER CONFIG
# =======================
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
WINDOW_SECONDS = 5
SAMPLE_RATE = 1000  # Hz

# =======================
# BUFFER SETUP
# =======================
max_samples = WINDOW_SECONDS * SAMPLE_RATE
ecg_buffer = collections.deque(maxlen=max_samples)
time_buffer = collections.deque(maxlen=max_samples)

start_time = time.time()

# =======================
# LSL STREAM SETUP
# =======================
info = StreamInfo(
    name="ECG_Stream",
    type="ECG",
    channel_count=1,
    nominal_srate=SAMPLE_RATE,
    channel_format="float32",
    source_id="ecg_serial_001"
)

# Optional: add channel metadata
ch = info.desc().append_child("channels").append_child("channel")
ch.append_child_value("label", "ECG")
ch.append_child_value("unit", "uV")
ch.append_child_value("type", "ECG")

outlet = StreamOutlet(info)

print("LSL stream started: ECG_Stream")

# =======================
# SERIAL READER THREAD
# =======================
def serial_reader():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Connected to", SERIAL_PORT)

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue

            value = float(line)

            t = time.time() - start_time
            ecg_buffer.append(value)
            time_buffer.append(t)

            # Push to LSL with precise timestamp
            outlet.push_sample([value], timestamp=local_clock())

        except ValueError:
            pass  # ignore malformed lines
        except serial.SerialException as e:
            print("Serial error:", e)
            break

# =======================
# START THREAD
# =======================
thread = threading.Thread(target=serial_reader, daemon=True)
thread.start()

# =======================
# KEEP MAIN THREAD ALIVE
# =======================
print("Streaming ECG over LSL. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping stream.")