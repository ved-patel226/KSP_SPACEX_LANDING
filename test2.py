import numpy as np
import matplotlib.pyplot as plt

# Constants
min_altitude = 0      # in meters
max_altitude = 10000  # in meters
max_speed = 1000       # in m/s

# Altitude range
h = np.linspace(min_altitude, max_altitude, 500)

# Equation
target_speed = max_speed * ((h - min_altitude) / (max_altitude - min_altitude))**1.5

# Plot
plt.plot(h, target_speed, label="Target Speed")
plt.xlabel("Altitude (m)")
plt.ylabel("Target Speed (m/s)")
plt.title("Target Speed vs. Altitude")
plt.grid(True)
plt.legend()
plt.show()
