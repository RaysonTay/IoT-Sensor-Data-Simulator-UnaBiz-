import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_random_devEUI():
    return ''.join(random.choice('0123456789abcdef') for _ in range(16))

class BaseSensor:
    def __init__(self, type, devEUI=None, battery=100, seqNumber=0, seed=None, frequency=900, noise_level=0.0):
        self.type = type
        self.devEUI = devEUI if devEUI else generate_random_devEUI()
        self.battery = battery
        self.seqNumber = seqNumber
        self.frequency = frequency # default 5min = 900s
        self.noise_level = noise_level
        if seed is not None:
            np.random.seed(seed)
    
    def _random_rssi(self):
        return np.random.uniform(-110, -40)

    def _random_snr(self):
        return np.random.uniform(-10, 15)

    def _increment_seq(self):
        self.seqNumber = (self.seqNumber + 1) % 65536

    def generate_reading(self, t):
        # to be overidden
        raise NotImplementedError("Subclasses must implement generate_reading()")

    def generate_data(self, duration_minutes=60, start_time=None):
        # generate time-series data for the given duration.
        # Returns pd.DataFrame with columns: ['timestamp', 'sensor_type', 'value']
        if start_time is None:
            start_time = datetime.now() # defaults to now

        num_points = int((duration_minutes * 60) / self.frequency)
        timestamps = [start_time + timedelta(seconds=i * self.frequency) for i in range(num_points)]
        values = [self.generate_reading(t) for t in range(num_points)]

        # optional Gaussian noise
        if self.noise_level > 0:
            noise = np.random.normal(0, self.noise_level, len(values))
            values = np.array(values) + noise

        return pd.DataFrame({
            "timestamp": timestamps,
            "sensor_type": self.type,
            "value": values
        })
