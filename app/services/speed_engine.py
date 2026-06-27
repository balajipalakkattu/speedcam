import time
import math

class SpeedEngine:
    def __init__(self):
        self.last_center = None
        self.last_time = None
        self.meters_per_pixel = 0.05  # calibrate later

    def update(self, center):
        if center is None:
            return 0.0

        current_time = time.time()

        if self.last_center is None:
            self.last_center = center
            self.last_time = current_time
            return 0.0

        dx = abs(center[0] - self.last_center[0])
        dt = current_time - self.last_time

        self.last_center = center
        self.last_time = current_time

        if dt == 0:
            return 0.0

        meters = dx * self.meters_per_pixel
        speed_mps = meters / dt
        speed_mph = speed_mps * 2.23694

        return round(speed_mph, 2)
