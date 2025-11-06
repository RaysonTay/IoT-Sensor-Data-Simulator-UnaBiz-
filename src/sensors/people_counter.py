import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.base_sensor import BaseSensor

class PeopleCounterSensor(BaseSensor):

    def __init__(self, devEUI=None, battery=100, seqNumber=0,
                 frequency=300, noise_level=0.5, anomaly_rate=0.01,
                 location="toilet", seed=None):
        # location: 'toilet'(default), 'restaurant', 'mall', or 'classroom'

        super().__init__(
            type=f"people_counter_{location}",
            devEUI=devEUI,
            battery=battery,
            seqNumber=seqNumber,
            frequency=frequency,
            noise_level=noise_level,
            anomaly_rate=anomaly_rate,
            seed=seed
        )

        self.location = location.lower()
        # occupancy logic
        self.current_occupancy = 0
        self.max_capacity = {
            "toilet": 10,
            "restaurant": 50,
            "mall": 200,
            "classroom": 30
        }.get(self.location, 10)

        self.cooldown_counter = 0  # for idle intervals
        self.activity_prob = {
            "toilet": 0.4,      # 40% chance of active period
            "restaurant": 0.6,  # more frequent activity
            "mall": 0.8,        # almost always active
            "classroom": 0.3    # short bursts, long idle gaps
        }.get(self.location, 0.5)

    def _get_time_period(self, hour):
        if 6 <= hour < 9:
            return "morning_peak"
        elif 12 <= hour < 14:
            return "lunch"
        elif 17 <= hour < 21:
            return "evening_peak"
        else:
            return "off_hours"

    def _people_flow_pattern(self, hour):

        period = self._get_time_period(hour)

        # base ranges by location & time
        location_patterns = {
            "toilet": {
                "morning_peak": (0, 5),
                "lunch": (0, 3),
                "evening_peak": (0, 5),
                "off_hours": (0, 1)
            },
            "restaurant": {
                "morning_peak": (0, 5),
                "lunch": (3, 10),
                "evening_peak": (5, 15),
                "off_hours": (0, 3)
            },
            "mall": {
                "morning_peak": (0, 15),
                "lunch": (5, 30),
                "evening_peak": (10, 40),
                "off_hours": (0, 10)
            },
            "classroom": {
                "morning_peak": (0, 25),
                "lunch": (0, 5),
                "evening_peak": (0, 25),
                "off_hours": (0, 3)
            }
        }

        loc = self.location if self.location in location_patterns else "toilet"
        low, high = location_patterns[loc][period]
        return np.random.uniform(low, high)

    def generate_data(self, duration_minutes=1440, start_time=None):
        if start_time is None:
            start_time = datetime.now()

        num_points = int((duration_minutes * 60) / self.frequency)
        timestamps = [start_time + timedelta(seconds=i * self.frequency) for i in range(num_points)]

        data = []
        for ts in timestamps:
            hour = ts.hour
            anomaly_triggered = False
            
            # burst activity logic
            if self.cooldown_counter > 0:
                period_in = period_out = 0
                self.cooldown_counter -= 1
            else:
                if np.random.random() < self.activity_prob:
                    # active; generate normally
                    period_in = np.random.poisson(self._people_flow_pattern(hour))
                    period_out = np.random.poisson(self._people_flow_pattern(hour))
                else:
                    # inactivity
                    self.cooldown_counter = np.random.randint(2, 6)  # 2–5 intervals of no movement
                    period_in = period_out = 0
            period_in = max(0, period_in)
            period_out = max(0, period_out)

            period_in = max(0, int(round(period_in + np.random.normal(0, self.noise_level))))
            period_out = max(0, int(round(period_out + np.random.normal(0, self.noise_level))))

            # anomalies
            if np.random.random() < self.anomaly_rate:
                anomaly_triggered = True
                anomaly_type = np.random.choice(["spike", "zero"])
                if anomaly_type == "spike":
                    multiplier = {
                        "toilet": 5,
                        "restaurant": 3,
                        "mall": 2,
                        "classroom": 4
                    }[self.location]
                    lam_in = max(1, self._people_flow_pattern(hour) * np.random.uniform(multiplier/2, multiplier))
                    lam_out = max(1, self._people_flow_pattern(hour) * np.random.uniform(multiplier/2, multiplier))
                    period_in = np.random.poisson(lam_in)
                    period_out = np.random.poisson(lam_out)
                else: # zero
                    period_in, period_out = 0, 0

            # prevent out > current occupancy unless anomaly
            if not anomaly_triggered and not np.isnan(period_out):
                period_out = min(period_out, self.current_occupancy)

            # update occupancy (ignore NaNs)
            if not np.isnan(period_in) and not np.isnan(period_out):
                self.current_occupancy += period_in - period_out
                self.current_occupancy = max(0, min(self.current_occupancy, self.max_capacity))

            record = {
                "timestamp": ts,
                "sensor_type": self.type,
                "devEUI": self.devEUI,
                "battery": self.battery,
                "rssi": round(self._random_rssi(), 1),
                "snr": round(self._random_snr(), 1),
                "seqNumber": self.seqNumber,
                "period_in": int(period_in) if not np.isnan(period_in) else np.nan,
                "period_out": int(period_out) if not np.isnan(period_out) else np.nan,
                "current_occupancy": int(self.current_occupancy),
                "location": self.location
            }
            self._increment_seq()
            data.append(record)

        return pd.DataFrame(data)
