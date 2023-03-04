from arcade import Sprite

class Explosion(Sprite):
    def __init__(self, filename: str = None, starting_scale: float = 0.33, lifetime_seconds : float = 0.15, 
                    scale_increase_rate: float = 5.0, center_x: float = 0, center_y: float = 0):
        self.max_lifetime = lifetime_seconds
        self.elapsed_lifetime = 0.0
        self.scale_increase_rate = scale_increase_rate
        super().__init__(filename=filename, scale=starting_scale, center_x=center_x, center_y=center_y)

    def on_update(self, delta_time: float = 1 / 60):
        self.scale += self.scale_increase_rate * delta_time
        self.elapsed_lifetime += delta_time
        if self.elapsed_lifetime > self.max_lifetime:
            self.remove_from_sprite_lists()
        return super().on_update(delta_time)
