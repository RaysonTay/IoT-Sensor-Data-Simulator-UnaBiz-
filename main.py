from src.sensors.people_counter import PeopleCounterSensor

def main():
    # Test the sensor for each location type
    for loc in ["toilet"]:
        print(f"\n--- Simulating {loc.upper()} ---")
        
        # Create one sensor instance per location
        sensor = PeopleCounterSensor(
            location=loc,
            frequency=300,        # 5-minute intervals
            anomaly_rate=0.02,    # 2% anomalies
            seed=42
        )
        
        # Generate 1 day (24h) of data
        df = sensor.generate_data(duration_minutes=1440)
        
        # Print a preview
        print(df.head(10))
        print(f"\nSummary for {loc}:")
        print(df[['period_in', 'period_out', 'current_occupancy']].describe())
        
        # Save to CSV
        filename = f"people_counter_{loc}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Saved {filename}")

if __name__ == "__main__":
    main()
