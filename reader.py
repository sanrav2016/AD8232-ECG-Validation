import serial
import time
import threading
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pylsl import StreamInfo, StreamOutlet, local_clock

# =======================
# USER CONFIG
# =======================
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
SAMPLE_RATE = 1000  # Hz
WINDOW_SECONDS = 10  # for display

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

            outlet.push_sample([value], timestamp=local_clock())

        except ValueError:
            pass
        except serial.SerialException as e:
            print("Serial error:", e)
            break

# =======================
# START SERIAL THREAD
# =======================
thread = threading.Thread(target=serial_reader, daemon=True)
thread.start()

# =======================
# REAL-TIME PLOT SETUP
# =======================
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=1)

ax.set_title("Real-Time ECG (Last 10 Seconds)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Amplitude")
ax.set_xlim(-WINDOW_SECONDS, 0)
ax.set_ylim(0, 4095)  # 🔧 adjust to your ECG scale
ax.grid(True)

def init():
    line.set_data([], [])
    return line,

def update(frame):
    if len(time_buffer) < 2:
        return line,

    t = np.array(time_buffer)
    y = np.array(ecg_buffer)

    # Convert to relative time (last 10 seconds)
    t = t - t[-1]

    line.set_data(t, y)
    return line,

ani = animation.FuncAnimation(
    fig,
    update,
    init_func=init,
    interval=30,   # ~33 FPS
    blit=True
)

print("Streaming ECG over LSL with real-time display. Close plot or Ctrl+C to stop.")
plt.show()
