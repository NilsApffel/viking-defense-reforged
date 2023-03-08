from arcade import Sprite

class Effect(Sprite):
    def __init__(self, filename: str = None, damage_per_second: float = 0, 
                 speed_multiplier: float = 1, duration: float = 3, angle_rate: float=720):
        super().__init__(filename=filename, scale=1)
        self.damage_per_second = damage_per_second
        self.speed_multiplier = speed_multiplier
        self.angle_rate = angle_rate
        self.duration = duration
        self.duration_remaining = duration

    def on_update(self, delta_time: float = 1 / 60):
        self.duration_remaining -= delta_time
        self.angle += self.angle_rate*delta_time
        return super().on_update(delta_time)

class SlowDown(Effect):
    def __init__(self):
        super().__init__(filename='./images/slowdown.png', damage_per_second=0, 
                         speed_multiplier=0.5, duration=5, angle_rate=720)
