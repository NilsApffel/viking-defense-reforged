from arcade import Sprite
from random import randint

class Effect(Sprite):
    def __init__(self, name, filename: str = None, damage_per_second: float = 0, 
                 speed_multiplier: float = 1, duration: float = 3, 
                 angle_rate: float=720, angle: float=0):
        super().__init__(filename=filename, scale=1)
        self.name = name
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
        super().__init__(name='slowdown', filename='./images/slowdown.png', damage_per_second=0, 
                         speed_multiplier=0.6, duration=5, angle_rate=720)

       
class Inflame(Effect):
    def __init__(self):
        super().__init__(name='inflame', filename='./images/inflame-2.png', 
                         damage_per_second=5, duration=3, angle_rate=360)


class Freeze(Effect):
    def __init__(self):
        super().__init__(name='freeze', filename='./images/freeze.png', 
                         speed_multiplier=0, duration=3, angle_rate=0, angle=randint(0, 359))
