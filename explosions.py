from arcade import Sprite, load_texture
from math import floor

CATAPULT_EXPLOSIONS = [load_texture('./images/explosions/catapult'+str(k)+'.png') for k in range(6)]
MJOLNIR_EXPLOSIONS = [load_texture('./images/explosions/mjolnir'+str(k)+'.png') for k in range(15)]


class GrowingExplosion(Sprite):
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
    

class FramedExplosion(Sprite):
    def __init__(self, frames: list, scale: float = 1, center_x: float = 0, center_y: float = 0, 
                 frame_duration: float = None, total_duration: float = None):
        super().__init__(scale=scale, center_x=center_x, center_y=center_y)
        for frame in frames:
            self.append_texture(frame)
        self.num_frames = len(frames)
        self.set_texture(0)
        if frame_duration:
            self.frame_duration = frame_duration
            self.total_duration = frame_duration * self.num_frames
        elif total_duration:
            self.total_duration = total_duration
            self.frame_duration = total_duration / self.num_frames
        else:
            self.frame_duration = 0.04
            self.total_duration = 0.04 * self.num_frames
        self.animation_time = 0

    def on_update(self, delta_time: float = 1 / 60):
        old_time = self.animation_time
        new_time = self.animation_time + delta_time
        if new_time > self.total_duration:
            self.remove_from_sprite_lists()
            return
        old_frame_num = floor(old_time / self.frame_duration)
        new_frame_num = floor(new_time / self.frame_duration)
        if old_frame_num != new_frame_num:
            self.set_texture(new_frame_num)
        self.animation_time = new_time
        return super().on_update(delta_time)


class CatapultExplosion(FramedExplosion):
    def __init__(self, scale: float = 1.0, speed_factor: float = 1.0, 
                 center_x: float = 0, center_y: float = 0):
        super().__init__(scale=scale, frames=CATAPULT_EXPLOSIONS, 
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04/speed_factor)
        

class MjolnirExplosion(FramedExplosion):
    def __init__(self, center_x: float = 0, center_y: float = 0):
        super().__init__(frames=MJOLNIR_EXPLOSIONS, 
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04)
