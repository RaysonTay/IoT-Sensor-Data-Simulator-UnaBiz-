from src.base_sensor import BaseSensor
import numpy as np

# Define a quick dummy subclass to test functionality
class DummySensor(BaseSensor):
    def generate_reading(self, t):
        # Example pattern: sinusoidal oscillation + baseline
        return np.sin(t / 10) + 10

def main():
    # Instantiate dummy sensor
    sensor = DummySensor(type="dummy", devEUI="dummy", battery=100, rssi=0.1, seqNumber=0.1, snr=0.1, frequency=15, noise_level=0.2, seed=42)

    # Generate 30 minutes of data (30 readings if frequency = 60s)
    df = sensor.generate_data(duration_minutes=30)

    # Print the first few rows
    print(df.head())

    # Save to CSV to confirm export
    df.to_csv("dummy_output.csv", index=False)
    print("\n✅ Data generated and saved as dummy_output.csv")

if __name__ == "__main__":
    main()
