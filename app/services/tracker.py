class VehicleTracker:
    def __init__(self):
        self.last_center = None

    def update(self, det):
        if det is None:
            return None

        x1, y1, x2, y2 = det
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        center = (cx, cy)
        self.last_center = center
        return center
