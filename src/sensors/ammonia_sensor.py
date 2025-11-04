import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.base_sensor import BaseSensor

class AmmoniaSensor(BaseSensor):

    def __init__(self, devEUI=None, battery=100, seqNumber=0,
                 frequency=300, noise_level=0.01, anomaly_rate=0.01, seed=None):
        super().__init__(
            type="ammonia",
            devEUI=devEUI,
            battery=battery,
            seqNumber=seqNumber,
            frequency=frequency,
            noise_level=noise_level,
            anomaly_rate=anomaly_rate,
            seed=seed
        )
        self.base_nh3 = 0.1  # typical ppm
        self.nh3_amp = 0.05  # small daily variation

    def _get_time_period(self, hour):
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 24:
            return "evening"
        else:
            return "night"

    def _temp_by_time(self, hour): # based on real data ranges
        ranges = {
            "morning": (26, 28),
            "afternoon": (29, 32),
            "evening": (28, 30),
            "night": (25, 27)
        }
        period = self._get_time_period(hour)
        return np.random.uniform(*ranges[period])

    def _humidity_by_time(self, hour):  # based on real data ranges
        ranges = {
            "morning": (40, 48),
            "afternoon": (45, 55),
            "evening": (48, 60),
            "night": (42, 52)
        }
        period = self._get_time_period(hour)
        return np.random.uniform(*ranges[period])

    def generate_reading(self, t):

        base = self.base_nh3 + self.nh3_amp * np.sin(t / 96)
        noise = np.random.normal(0, self.noise_level)

        # spike anomaly
        if np.random.random() < self.anomaly_rate:
            spike = np.random.uniform(100, 700)
        else:
            spike = 0

        nh3_value = max(0.05, base + noise + spike)
        return round(nh3_value, 3)

    def generate_data(self, duration_minutes=1440, start_time=None):
        if start_time is None:
            start_time = datetime.now()

        num_points = int((duration_minutes * 60) / self.frequency)
        timestamps = [start_time + timedelta(seconds=i * self.frequency) for i in range(num_points)]

        records = []
        for t in range(num_points):
            nh3_value = self.generate_reading(t)
            ts = timestamps[t]
            hour = ts.hour

            record = {
                "timestamp": ts,
                "sensor_type": self.type,
                "devEUI": self.devEUI,
                "battery": self.battery,
                "rssi": round(self._random_rssi(), 1),
                "snr": round(self._random_snr(), 1),
                "seqNumber": self.seqNumber,
                "temperature": round(self._temp_by_time(hour), 1),
                "humidity": round(self._humidity_by_time(hour), 1),
                "nh3": nh3_value
            }
            self._increment_seq()
            records.append(record)

        return pd.DataFrame(records)
