import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from base_sensor import BaseSensor

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

        self.base_nh3 = 0.1
        self.nh3_amp = 0.05

        # markov parameters
        self.temp_tau = 90.0      # min, larger = slower changes
        self.temp_sigma = 0.05
        self.temp_max_step = 0.3

        self.hum_tau = 120.0
        self.hum_sigma = 0.4
        self.hum_max_step = 1.5

        self._temp_state = None
        self._hum_state = None

    def _time_period(self, hour):
        if 6 <= hour < 12: return "morning"
        if 12 <= hour < 18: return "afternoon"
        if 18 <= hour < 24: return "evening"
        return "night"

    def _target_temp(self, hour):
        targets = {
            "morning": 27,
            "afternoon": 30.5,
            "evening": 29,
            "night": 26
        }
        return targets[self._time_period(hour)]

    def _target_hum(self, hour):
        targets = {
            "morning": 44,
            "afternoon": 50,
            "evening": 55,
            "night": 47
        }
        return targets[self._time_period(hour)]

    # for markovian property
    def _ou_step(self, prev, target, dt_min, tau, sigma, max_step):
        drift = (target - prev) * (dt_min / tau)
        noise = np.random.normal(0, sigma)
        proposed = prev + drift + noise
        delta = np.clip(proposed - prev, -max_step, max_step)
        return prev + delta

    def _init_env_state(self, start_time):
        h = start_time.hour
        self._temp_state = self._target_temp(h) + np.random.normal(0, 0.2)
        self._hum_state = self._target_hum(h) + np.random.normal(0, 1.0)

    def _update_env(self, ts):
        dt_min = self.frequency / 60.0
        h = ts.hour

        self._temp_state = self._ou_step(
            self._temp_state, self._target_temp(h),
            dt_min, self.temp_tau, self.temp_sigma, self.temp_max_step
        )
        self._hum_state = self._ou_step(
            self._hum_state, self._target_hum(h),
            dt_min, self.hum_tau, self.hum_sigma, self.hum_max_step
        )

        # clamp to plausible limits
        t = float(np.clip(self._temp_state, 20, 40))
        h = float(np.clip(self._hum_state, 20, 95))
        return round(t, 1), round(h, 1)

    def generate_reading(self, t):
        base = self.base_nh3 + self.nh3_amp * np.sin(t / 96)
        noise = np.random.normal(0, self.noise_level)
        spike = np.random.uniform(100, 700) if np.random.random() < self.anomaly_rate else 0
        nh3_value = base + noise + spike
        if self._temp_state is not None and self._hum_state is not None:
            # normalize to deviations from nominal values
            temp_dev = self._temp_state - 28    # baseline ~28°C
            hum_dev = self._hum_state - 50      # baseline ~50% RH

            # slight positive correlation
            nh3_value *= (1 + 0.005 * temp_dev + 0.002 * hum_dev)

        nh3_value = max(0.05, nh3_value)
        return round(nh3_value, 3)

    def generate_data(self, duration_minutes=1440, start_time=None):
        if start_time is None:
            start_time = datetime.now()

        num_points = int((duration_minutes * 60) / self.frequency)
        timestamps = [start_time + timedelta(seconds=i * self.frequency) for i in range(num_points)]

        # init smooth states
        if self._temp_state is None or self._hum_state is None:
            self._init_env_state(start_time)

        records = []
        for i, ts in enumerate(timestamps):
            nh3_value = self.generate_reading(i)
            temperature, humidity = self._update_env(ts)

            record = {
                "timestamp": ts,
                "sensor_type": self.type,
                "devEUI": self.devEUI,
                "battery": self.battery,
                "rssi": round(self._random_rssi(), 1),
                "snr": round(self._random_snr(), 1),
                "seqNumber": self.seqNumber,
                "temperature": temperature,
                "humidity": humidity,
                "nh3": nh3_value
            }
            self._increment_seq()
            records.append(record)

        return pd.DataFrame(records)
