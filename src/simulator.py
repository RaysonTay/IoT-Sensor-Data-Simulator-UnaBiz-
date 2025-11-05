import pandas as pd
from datetime import datetime
from sensors.ammonia_sensor import AmmoniaSensor
from sensors.people_counter import PeopleCounterSensor
import os

class Simulator:
    """
    Manages and runs multiple IoT sensors together.
    Generates synchronized, realistic time-series data for testing and dashboards.
    """

    def __init__(self, duration_minutes=1440, start_time=None, output_dir="outputs"):
        self.duration_minutes = duration_minutes
        self.start_time = start_time if start_time else datetime.now()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)


        # Registry of all available sensor classes
        self.sensor_registry = {
            "ammonia": AmmoniaSensor,
            "people_counter_toilet": lambda **kwargs: PeopleCounterSensor(location="toilet", **kwargs),
            "people_counter_restaurant": lambda **kwargs: PeopleCounterSensor(location="restaurant", **kwargs),
            "people_counter_mall": lambda **kwargs: PeopleCounterSensor(location="mall", **kwargs),
            "people_counter_classroom": lambda **kwargs: PeopleCounterSensor(location="classroom", **kwargs),
        }

    def run_sensor(self, sensor_name, **kwargs):
        """Run one sensor and return its DataFrame."""
        if sensor_name not in self.sensor_registry:
            raise ValueError(f"Unknown sensor type: {sensor_name}")
        print(f"🟢 Running simulation for {sensor_name} ...")

        SensorClass = self.sensor_registry[sensor_name]
        sensor = SensorClass(seed=42, **kwargs)
        df = sensor.generate_data(duration_minutes=self.duration_minutes, start_time=self.start_time)

        # Save individual sensor output
        filename = f"{self.output_dir}/{sensor_name}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ {sensor_name} data saved to {filename}")
        return df

    def run_all(self, sensors_to_run):
        """
        Run multiple sensors and return a merged DataFrame.
        sensors_to_run: list of sensor names (must match registry keys)
        """
        all_dfs = []
        for name in sensors_to_run:
            df = self.run_sensor(name)
            all_dfs.append(df)

        # Merge all on timestamp (outer join)
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.sort_values("timestamp", inplace=True)
        combined.to_csv(f"{self.output_dir}/combined_simulation.csv", index=False)
        print(f"\n📁 Combined simulation saved to {self.output_dir}/combined_simulation.csv")
        return combined


if __name__ == "__main__":
    # Example run: 1 day of ammonia + toilet people counter
    sim = Simulator(duration_minutes=1440)
    combined_df = sim.run_all(["ammonia", "people_counter_toilet"])

    print("\nPreview of combined simulation:")
    print(combined_df.head(10))
