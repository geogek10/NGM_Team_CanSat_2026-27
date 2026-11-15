# 05 — Neural Networks & AI Training Pipeline
Training scripts and datasets for the 3 `.onnx` neural networks:
1. `GasSpecNet`: Deconvolves BME688 heater-sweep resistance from temperature/humidity/airflow to detect true VOC anomalies.
2. `HabitabilityNet`: Computes the **Habitability Index (`0-100%`)** from `[Temp, Press, Hum, Density, VOC Score, dP/dt, Alt]`.
3. `AeroHealthNet`: Evaluates propulsion health (IMU vibration, Bluejay eRPM, 4S 120C voltage sag) & Drone vs. Rover mobility advantage.
