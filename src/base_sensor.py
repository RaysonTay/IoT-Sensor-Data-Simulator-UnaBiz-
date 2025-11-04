import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class BaseSensor:
    def __init__(self, type, devEUI, rssi, seqnumber, snr, seed, frequency=15, noise_level=0.0):
        self.type = type
        self.devEUI = devEUI
        self.rssi = rssi
        self.seqNumber = seqnumber
        self.snr = snr
        self.frequency = frequency
        self.noise_level = noise_level
        if seed is not None:
            np.random.seed(seed)

    def generate_reading(self, t):
        # to be overidden
        raise NotImplementedError("Subclasses must implement generate_reading()")

    def generate_data(self, duration_minutes=60, start_time=None):
        # generate time-series data for the given duration.
        # Returns pd.DataFrame with columns: ['timestamp', 'sensor_id', 'value']
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
            "sensor_name": self.type,
            "value": values
        })
