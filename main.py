from src.base_sensor import BaseSensor
import numpy as np

class DummySensor(BaseSensor):
    def generate_reading(self, t):
        return np.sin(t / 10) + 10  # just a test pattern

sensor = DummySensor("001", "dummy", frequency=60, noise_level=0.2)
df = sensor.generate_data(duration_minutes=30)
print(df.head())
