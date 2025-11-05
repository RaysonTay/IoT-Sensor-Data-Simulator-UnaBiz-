import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_random_devEUI():
    return ''.join(random.choice('0123456789abcdef') for _ in range(16))

class BaseSensor:
    def __init__(self, type, devEUI=None, battery=100, seqNumber=0, seed=None, frequency=300, noise_level=0.0, anomaly_rate=0.01):
        self.type = type
        self.devEUI = devEUI if devEUI else generate_random_devEUI()
        self.battery = battery
        self.seqNumber = seqNumber
        self.frequency = frequency # default 5min = 300s
        self.noise_level = noise_level
        self.anomaly_rate = anomaly_rate
        if seed is not None:
            np.random.seed(seed)
        self.battery_drain_rate = 100 / (3 * 365 * 24 * (3600 / self.frequency))  # ~3-year life

    
    def _random_rssi(self, anomaly=False):
        if np.random.random() < self.anomaly_rate:
            return np.random.uniform(-80, -60)
        return np.random.normal(-25, 5) # mean -25dBm, stddev 5dBm (from real data)

    def _random_snr(self, anomaly=False):
        if np.random.random() < self.anomaly_rate:
            return np.random.uniform(-10, 0)
        return np.random.normal(13.5, 1.5) # mean 13.5dB, stddev 1.5dB (from real data)

    def _increment_seq(self):
        self.seqNumber = (self.seqNumber + 1) % 65536

    def generate_reading(self, t):
        # to be overidden
        raise NotImplementedError("Subclasses must implement generate_reading()")

    def generate_data(self, duration_minutes=60, start_time=None):
        # generate time-series data for the given duration.
        if start_time is None:
            start_time = datetime.now() # defaults to now
        
        num_points = int((duration_minutes * 60) / self.frequency)
        timestamps = [start_time + timedelta(seconds=i * self.frequency) for i in range(num_points)]
        readings = []
        for t in range(num_points):
            val = self.generate_reading(t)
            if not np.isnan(val):
                self.battery = max(0, self.battery - np.random.normal(self.battery_drain_rate, self.battery_drain_rate * 0.1))

            record = {
                "timestamp": timestamps[t],
                "sensor_type": self.type,
                "devEUI": self.devEUI,
                "battery": round(self.battery, 2),
                "rssi": round(self._random_rssi(), 1),
                "snr": round(self._random_snr(), 1),
                "seqNumber": self.seqNumber,
                "value": val
            }
            self._increment_seq()
            readings.append(record)

        return pd.DataFrame(readings)
