from src.sensors.ammonia_sensor import AmmoniaSensor

def main():
    # Simulate 1 day with 2% anomaly rate
    sensor = AmmoniaSensor(frequency=900, anomaly_rate=0.02, seed=42)
    df = sensor.generate_data()
    print(df.head())
    print("\n✅ Generated ammonia sensor data with time-of-day temperature and 2% anomaly rate.")
    df.to_csv("ammonia_time_based.csv", index=False)

if __name__ == "__main__":
    main()
