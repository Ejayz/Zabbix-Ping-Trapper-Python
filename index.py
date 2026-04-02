from zabbix_utils import Sender
from datetime import datetime
import time
from icmplib import ping
from threading import Thread

sender = Sender(server="172.20.1.1", port=10051)

TARGETS = {
    "1.1.1.1": ("Trapper.Ping.Cloudflare", "Trapper.PacketLoss.Cloudflare"),
    "8.8.8.8": ("Trapper.Ping.Google", "Trapper.PacketLoss.Google"),
    "9.9.9.9": ("Trapper.Ping.Cloud9", "Trapper.PacketLoss.Cloud9"),
}


def compute_packet_loss(samples):
    if len(samples) == 0:
        return 0.0
    loss = (1 - (sum(samples) / len(samples))) * 100
    return round(loss, 2)


def worker(target, latency_key, loss_key):
    samples = []
    counter = 0

    # Align start to exact second
    while True:
        now = time.time()
        sleep_time = 1 - (now % 1)
        time.sleep(sleep_time)
        break

    while True:
        start_time = time.time()
        zeroed_time = datetime.now().replace(microsecond=0)
        ts_now = zeroed_time.timestamp()

        try:
            result = ping(target, count=1, timeout=1)
            success = 1 if result.is_alive else 0
            latency = result.avg_rtt if result.is_alive else 0
        except:
            success = 0
            latency = 0

        samples.append(success)
        counter += 1

        # --- SEND LATENCY EVERY SECOND ---
        sender.send_value("isp-core", latency_key, latency, ts_now)

        print(f"[{zeroed_time}] {target} latency={latency} ms")

        # --- EVERY 60 SAMPLES → SEND PACKET LOSS ---
        if counter >= 60:
            packet_loss = compute_packet_loss(samples)

            # timestamp = start of window
            ts_window_start = ts_now - 59

            sender.send_value(
                "isp-core",
                loss_key,
                packet_loss,
                ts_window_start
            )

            print(
                f"[PACKET LOSS] {target} = {packet_loss}% "
                f"(ts={datetime.fromtimestamp(ts_window_start)})"
            )

            # reset
            samples = []
            counter = 0

        # maintain 1-second interval precisely
        elapsed = time.time() - start_time
        sleep_remaining = max(0, 1 - elapsed)
        time.sleep(sleep_remaining)


# --- START ALL THREADS AT SAME TIME ---
threads = []

# Global alignment before starting all threads
now = time.time()
sleep_time = 1 - (now % 1)
time.sleep(sleep_time)

for target, (latency_key, loss_key) in TARGETS.items():
    t = Thread(target=worker, args=(target, latency_key, loss_key), daemon=True)
    t.start()
    threads.append(t)

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    print("Stopped.")


######## Rollling seconds in this area
# from zabbix_utils import Sender
# from datetime import datetime
# import time
# from icmplib import ping
# from threading import Thread
# from collections import deque

# sender = Sender(server="172.20.1.1", port=10051)

# TARGETS = {
#     "1.1.1.1": ("Trapper.Ping.Cloudflare", "Trapper.PacketLoss.Cloudflare"),
#     "8.8.8.8": ("Trapper.Ping.Google", "Trapper.PacketLoss.Google"),
#     "9.9.9.9": ("Trapper.Ping.Cloud9", "Trapper.PacketLoss.Cloud9"),
# }


# def compute_packet_loss(samples):
#     if len(samples) == 0:
#         return 0.0
#     loss = (1 - (sum(samples) / len(samples))) * 100
#     return round(loss, 2)


# def worker(target, latency_key, loss_key):
#     # rolling buffer (last 60 seconds)
#     samples = deque(maxlen=60)

#     # align start
#     while True:
#         now = time.time()
#         sleep_time = 1 - (now % 1)
#         time.sleep(sleep_time)
#         break

#     while True:
#         start_time = time.time()
#         zeroed_time = datetime.now().replace(microsecond=0)
#         ts_now = zeroed_time.timestamp()

#         try:
#             result = ping(target, count=1, timeout=1)
#             success = 1 if result.is_alive else 0
#             latency = result.avg_rtt if result.is_alive else 0
#         except:
#             success = 0
#             latency = 0

#         # store result
#         samples.append(success)

#         # compute rolling packet loss
#         packet_loss = compute_packet_loss(samples)

#         # --- SEND LATENCY ---
#         sender.send_value("isp-core", latency_key, latency, ts_now)

#         # --- SEND PACKET LOSS EVERY SECOND ---
#         sender.send_value("isp-core", loss_key, packet_loss, ts_now)

#         print(
#             f"[{zeroed_time}] {target} "
#             f"latency={latency} ms | loss={packet_loss}% "
#             f"(samples={len(samples)})"
#         )

#         # keep exact 1-second interval
#         elapsed = time.time() - start_time
#         sleep_remaining = max(0, 1 - elapsed)
#         time.sleep(sleep_remaining)


# # --- START ALL THREADS ---
# threads = []

# # global alignment
# now = time.time()
# sleep_time = 1 - (now % 1)
# time.sleep(sleep_time)

# for target, (latency_key, loss_key) in TARGETS.items():
#     t = Thread(target=worker, args=(target, latency_key, loss_key), daemon=True)
#     t.start()
#     threads.append(t)

# # keep alive
# try:
#     while True:
#         time.sleep(1)
# except (KeyboardInterrupt, SystemExit):
#     print("Stopped.")