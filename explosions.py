from arcade import Sprite, Texture, load_texture
from utils import AnimatedSprite

CATAPULT_EXPLOSIONS = [load_texture('./images/explosions/catapult'+str(k)+'.png') for k in range(6)]
MJOLNIR_EXPLOSIONS = [load_texture('./images/explosions/mjolnir'+str(k)+'.png') for k in range(15)]
AIR_EXPLOSIONS = [load_texture('./images/explosions/FlyerDeath'+str(k)+'.png') for k in range(10)]
WATER_EXPLOSIONS = [load_texture('./images/explosions/SwimmerDeath'+str(k)+'.png') for k in range(14)]
RUNE_EXPLOSION = load_texture('./images/explosions/rune_placement.png')

class GrowingExplosion(Sprite):
    def __init__(self, texture: Texture = None, starting_scale: float = 0.33, lifetime_seconds : float = 0.15, 
                    scale_increase_rate: float = 5.0, center_x: float = 0, center_y: float = 0, 
                    sound_name: str = None):
        self.max_lifetime = lifetime_seconds
        self.elapsed_lifetime = 0.0
        self.scale_increase_rate = scale_increase_rate
        super().__init__(scale=starting_scale, center_x=center_x, center_y=center_y, texture=texture)
        self.sound_name = sound_name

    def on_update(self, delta_time: float = 1 / 60):
        self.scale += self.scale_increase_rate * delta_time
        self.elapsed_lifetime += delta_time
        if self.elapsed_lifetime > self.max_lifetime:
            self.remove_from_sprite_lists()
        return super().on_update(delta_time)
    

class RuneApplyMarker(GrowingExplosion):
    def __init__(self, center_x: float = 0, center_y: float = 0):
        super().__init__(texture=RUNE_EXPLOSION, starting_scale=0.1, lifetime_seconds=0.25, 
                         scale_increase_rate=3.6, center_x=center_x, center_y=center_y)
    

class FramedExplosion(AnimatedSprite):
    def __init__(self, frames: list, frame_duration: float, scale: float = 1, 
                 center_x: float = 0, center_y: float = 0, angle: float = 0, 
                 sound_name: str = None):
        transition_times=[k*frame_duration for k in range(len(frames)+1)]
        transition_indxs = list(range(len(frames)))
        transition_indxs = transition_indxs + [transition_indxs[-1]]
        super().__init__(texture_list=frames, transition_times=transition_times, 
                         transition_indxs=transition_indxs, scale=scale, 
                         center_x=center_x, center_y=center_y, angle=angle)
        self.lifetime = transition_times[-1]
        self.sound_name = sound_name

    def on_update(self, delta_time: float = 1 / 60):
        new_time = self.animation_time + delta_time
        if new_time > self.lifetime:
            self.remove_from_sprite_lists()
            return
        return super().on_update(delta_time)


class CatapultExplosion(FramedExplosion):
    def __init__(self, scale: float = 1.0, speed_factor: float = 1.0, 
                 center_x: float = 0, center_y: float = 0):
        super().__init__(scale=scale, frames=CATAPULT_EXPLOSIONS, 
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04/speed_factor, 
                         sound_name='StoneHit')
        

class MjolnirExplosion(FramedExplosion):
    def __init__(self, center_x: float = 0, center_y: float = 0):
        super().__init__(frames=MJOLNIR_EXPLOSIONS, 
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04, sound_name='MjolnirExplosion')


class AirExplosion(FramedExplosion):
    def __init__(self, scale: float = 1, center_x: float = 0, center_y: float = 0):
        super().__init__(frames=AIR_EXPLOSIONS, scale=scale,
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04)


class WaterExplosion(FramedExplosion):
    def __init__(self, scale: float = 1, center_x: float = 0, center_y: float = 0):
        super().__init__(frames=WATER_EXPLOSIONS, scale=scale,
                         center_x=center_x, center_y=center_y, 
                         frame_duration=0.04)
