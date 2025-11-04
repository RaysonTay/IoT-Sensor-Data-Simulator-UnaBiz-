from src.base_sensor import BaseSensor
import numpy as np
import pandas as pd

# Temporary subclass for testing purposes
class DummySensor(BaseSensor):
    def generate_reading(self, t):
        # Simulate a smooth oscillating value
        return np.sin(t / 5) * 10 + 50  # range roughly 40–60

def main():
    # Create a dummy sensor instance
    sensor = DummySensor(
        type="dummy",
        frequency=60,        # reading every 60 seconds
        noise_level=0.5,     # add a bit of Gaussian noise
        seed=42              # reproducible randomness
    )

    # Generate 30 minutes of readings
    df = sensor.generate_data(duration_minutes=30)

    # Display first few rows
    print(df.head())

    # Export to CSV
    df.to_csv("dummy_output.csv", index=False)
    # print("\nColumns in DataFrame:", df.columns.tolist())

    # print("\n✅ Dummy sensor data generated and saved as dummy_output.csv")

    # Optional: quick descriptive stats check
    # print("\nSummary statistics:")
    print(df[['rssi', 'snr', 'value']].describe())

if __name__ == "__main__":
    main()
