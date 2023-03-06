from arcade import Sprite
from math import sqrt
from constants import MAP_WIDTH, SCREEN_HEIGHT, CHIN_HEIGHT, is_debug
from enemies import Enemy
from explosions import Explosion

class Projectile(Sprite):
    def __init__(self, filename: str = None, scale: float = 1, speed: float = 2.0,
                    center_x: float = 0, center_y: float = 0, angle: float = 0, angle_rate: float = 0,
                    target: Enemy = None, target_x: float = None, target_y: float = None, 
                    damage: float = 1, do_splash_damage: bool = False, splash_radius: float = 10, 
                    impact_effect: Explosion = None, is_retargeting: bool = False, 
                    parent_tower: Sprite = None):
        super().__init__(filename=filename, scale=scale, center_x=center_x, center_y=center_y, angle=angle)
        self.speed = speed
        self.angle_rate = angle_rate
        self.target = target
        self.target_x = target_x
        self.target_y = target_y
        self.has_static_target = (target is None)
        self.damage = damage
        self.do_splash_damage = do_splash_damage
        self.splash_radius = splash_radius
        self.impact_effect = impact_effect
        self.is_retargeting = (is_retargeting and not (parent_tower is None))
        self.parent_tower = parent_tower

        if not self.has_static_target:
            self.target_x = self.target.center_x
            self.target_y = self.target.center_y
        # calc velocity based on target
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        norm = sqrt(dx*dx + dy*dy)
        if norm == 0:
            norm = 0.001
        self.velocity = (self.speed*dx/norm, self.speed*dy/norm)

    def on_update(self, delta_time: float):
        if not self.has_static_target:
            if (not (self.target is None)) and (self.target.current_health > 0):
                self.target_x = self.target.center_x
                self.target_y = self.target.center_y
                # accelerate towards target and lose some speed
                dx = self.target_x - self.center_x
                dy = self.target_y - self.center_y
                norm = sqrt(dx*dx + dy*dy)
                if norm == 0:
                    norm = 0.001
                force_x = self.speed*dx/norm
                force_y = self.speed*dy/norm
                vx = self.velocity[0]
                vy = self.velocity[1]
                self.velocity = (0.67*vx+0.33*force_x, 0.67*vy + 0.33*force_y)
            else: # target is dead or nonexistent
                if self.is_retargeting:
                    # are we still within range of our tower ?
                    dx = self.center_x - self.parent_tower.center_x
                    dy = self.center_y - self.parent_tower.center_y
                    dist2 = dx*dx + dy*dy
                    if dist2 < self.parent_tower.range**2:
                        self.target = self.parent_tower.target
                else:
                    self.target=None
                    self.has_static_target = True
        self.angle += self.angle_rate*delta_time
        if ((self.center_x > MAP_WIDTH + 20) or (self.center_x < -20) or 
                (self.center_y > SCREEN_HEIGHT + 20) or (self.center_y < CHIN_HEIGHT - 20)):
            self.remove_from_sprite_lists()
        return super().on_update(delta_time)
