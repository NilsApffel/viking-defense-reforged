from arcade import Sprite, Texture
from copy import deepcopy
from math import atan2, pi, sqrt, cos, sin
from random import random, randint
from constants import FLAMES, MAP_WIDTH, SCREEN_HEIGHT, CHIN_HEIGHT, is_debug, PROJECTILES, RAGE_PROJECTILES
from enemies import Enemy
from explosions import FramedExplosion
from runes import Rune

class Projectile(Sprite):
    def __init__(self, scale: float = 1, speed: float = 2.0,
                    center_x: float = 0, center_y: float = 0, angle: float = 0, angle_rate: float = 0,
                    target: Enemy = None, target_x: float = None, target_y: float = None, 
                    damage: float = 1, do_splash_damage: bool = False, splash_radius: float = 10, 
                    impact_effect: FramedExplosion = None, is_retargeting: bool = False, 
                    parent_tower: Sprite = None, effects: list = None, name: str = '', 
                    num_secondary_projectiles: int = 0, texture: Texture = None):
        super().__init__(scale=scale, center_x=center_x, 
                         center_y=center_y, angle=angle, texture=texture)
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
        if effects:
            self.effects = effects
        else:
            self.effects = []
        self.name = name
        self.num_secondary_projectiles = num_secondary_projectiles

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
                if self.name == 'flame_particle' and max(dx, dy) > 20:
                    dx += random()*32-8
                    dy += random()*32-8
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
        if self.angle_rate:
            self.angle += self.angle_rate*delta_time
        else:
            self.angle = atan2(self.velocity[1], self.velocity[0])*180/pi
        if ((self.center_x > MAP_WIDTH + 20) or (self.center_x < -20) or 
                (self.center_y > SCREEN_HEIGHT + 20) or (self.center_y < CHIN_HEIGHT - 20)):
            self.remove_from_sprite_lists()
        return super().on_update(delta_time)

    def make_secondaries(self, all_enemies: list, not_allowed_targets: list):
        '''After impacting the target, some projectiles launch fragments onto other enemies. 
        This function creates and returns those sub_projectiles.'''

        secondaries_list = []
        for k in range(self.num_secondary_projectiles):
            # pick a target
            chosen_enemy = None
            for enemy in all_enemies:
                dx = enemy.center_x - self.center_x
                dy = enemy.center_y - self.center_y
                dist2 = dx**2 + dy**2
                if dist2 < 10000 and not (enemy in not_allowed_targets):
                    # we found an enemy to shoot, stop looping through enemies and lets go shoot it
                    not_allowed_targets.append(enemy)
                    chosen_enemy = enemy
                    break
            if not chosen_enemy:
                # we did not find an enemy and the next sub-projectile won't either => exit sub creation loop
                break

            # make a copy of self but weaker and with no subs
            sub_proj = Projectile(
                scale=self.scale/2, speed=self.speed,
                center_x=self.center_x, center_y=self.center_y, angle_rate=self.angle_rate,
                target=chosen_enemy if self.target else None, 
                target_x=chosen_enemy.center_x, target_y=chosen_enemy.center_y, 
                damage=self.damage/2, do_splash_damage=self.do_splash_damage, 
                splash_radius=self.splash_radius/1.4, impact_effect=deepcopy(self.impact_effect), 
                is_retargeting=False, parent_tower=None, effects=deepcopy(self.effects), 
                name='sub-'+self.name, num_secondary_projectiles=0, 
                texture=self._texture 
            )
            for k in range(len(sub_proj.effects)):
                sub_proj.effects[k].duration_remaining /= 2
            secondaries_list.append(sub_proj)
        return secondaries_list


class Falcon(Projectile):
    def __init__(self, parent_tower):
        super().__init__(texture=PROJECTILES['falcon'], speed=2.5, 
                         center_x=parent_tower.center_x, center_y=parent_tower.center_y, angle=90, 
                         target_x=parent_tower.center_x, target_y=parent_tower.center_y+100, 
                         damage=parent_tower.damage, is_retargeting=True, parent_tower=parent_tower, name='falcon')
        self.rune = None
        self.patrol_radius = 0.75*parent_tower.range
        self.latest_dt = 1/60
        
    def on_update(self, delta_time: float):
        # constants
        delta_alpha = 0.3 # radians
        self.latest_dt = delta_time

        # step 1 : choose a target Enemy (or None)
        self.target = self.parent_tower.target
        if self.target:
            if self.target.current_health <= 0.0 or not(self.parent_tower.can_see(self.target)):
                self.target = None
        
        # step 2 : select target coords
        if self.target:
            attack_radius = 20
            # 2.1A : get our current angle along the attack circle
            dx = self.center_x - self.target.center_x
            dy = self.center_y - self.target.center_y
            alpha = atan2(dy, dx) # radians
            # 2.2A : determine what point to target along the attack circle
            alpha_target = alpha + delta_alpha # radians
            # x_tgt = x_0 + r*cos(alpha)
            self.target_x = self.target.center_x + attack_radius*cos(alpha_target)
            self.target_y = self.target.center_y + attack_radius*sin(alpha_target)
        else:
            # 2.1B : get our current angle along the patrol circle
            dx = self.center_x - self.parent_tower.center_x
            dy = self.center_y - self.parent_tower.center_y
            alpha = atan2(dy, dx) # radians
            # 2.2B : determine what point to target along the patrol circle
            alpha_target = alpha + delta_alpha # radians
            # x_tgt = x_0 + r*cos(alpha)
            self.target_x = self.parent_tower.center_x + self.patrol_radius*cos(alpha_target)
            self.target_y = self.parent_tower.center_y + self.patrol_radius*sin(alpha_target)

        # step 3 : go towards coords
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        norm = sqrt(dx*dx + dy*dy)
        if norm == 0:
            norm = 0.001
        self.velocity = (self.speed*dx/norm, self.speed*dy/norm)
        self.angle = atan2(self.velocity[1], self.velocity[0])*180/pi

    def set_rune(self, rune: Rune):
        example = self.parent_tower.make_another().falcon
        self.damage = example.damage
        self.patrol_radius = example.patrol_radius
        self.rune = None
        if not rune:
            return
        if rune.name == 'hagalaz':
            self.damage *= 1.25
        elif rune.name == 'tiwaz':
            self.patrol_radius *= 1.5
        elif rune.name == 'kenaz':
            self.damage *= 1.2
        elif rune.name == 'sowil':
            self.damage *= 2.00
            vx = self.velocity[0]
            vy = self.velocity[1]
            self.speed *= 1.75
            self.velocity = [vx*1.75, vy*1.75]
        self.rune = rune

    def attack(self, enemy: Enemy) -> float:
        dx = self.center_x - enemy.center_x
        dy = self.center_y - enemy.center_y
        dist2 = dx**2 + dy**2
        if dist2 > 900: # 30px **2
            return 0
        damage = self.latest_dt*self.damage # damage = dt * dps
        return damage


class FlameParticle(Projectile):
    def __init__(self, tower_x: float, tower_y: float, tower_angle: float, enemy: Enemy, damage: float):
        # choose random coords near the "mouth" of the tower's nozzle
        r0 = 32
        theta = (tower_angle+90)*pi/180
        sigma_t = 6
        randsigned = random()*2 - 1
        dt = sigma_t*randsigned 
        dr = -16*(1-abs(dt)/sigma_t) # spawning "surface" is v-shaped along radial direction
        center_x = tower_x + r0*cos(theta) + dr*cos(theta) + dt*sin(theta)
        center_y = tower_y + r0*sin(theta) + dr*sin(theta) - dt*cos(theta)

        super().__init__(
            speed=3.0, scale=0.75, center_x=center_x, center_y=center_y, angle=0, angle_rate=0, 
            target=enemy, target_x=enemy.center_x, target_y=enemy.center_y, damage=damage, 
            do_splash_damage=False, is_retargeting=False, name='flame_particle', 
            texture=FLAMES[randint(0, 7)]
        )


class RageBlast(Projectile):
    def __init__(self, center_x: float = 0, center_y: float = 0, angle: float = 0, 
                 target: Enemy = None, damage: float = 30):
        super().__init__(scale=0.35, speed=5, center_x=center_x, center_y=center_y, angle=angle,
                         angle_rate=0, target=target, target_x=target.center_x, 
                         target_y=target.center_y, damage=damage, do_splash_damage=False, 
                         name='rage-bomb', num_secondary_projectiles=4, texture=PROJECTILES['stone_shard']
        )
        for tx in RAGE_PROJECTILES:
            self.append_texture(tx)
        self.set_texture(0)
        self.frame_indx = 0
        self.transition_times = [0.04*k for k in range(13)]
        self.transition_indxs = list(range(12)) + [0]
        self.animation_time = 0

    def on_update(self, delta_time: float):
        self.animation_time += delta_time
        # animation time cannot exceed return-to-zero time
        while self.animation_time  >= self.transition_times[-1]: 
            self.animation_time  -= self.transition_times[-1]
        # find the index of the texture we should be using from now on : 
        for (k, transition_k_time) in enumerate(self.transition_times):
            if self.animation_time < transition_k_time:
                # we haven't passed transition k yet, but it's the next one 
                new_frame_indx = self.transition_indxs[k-1]
                break
        # update the texture if needed
        if new_frame_indx != self.frame_indx:
            self.set_texture(new_frame_indx)
            self.frame_indx = new_frame_indx
        return super().on_update(delta_time)
    
    def make_secondaries(self, all_enemies: list, not_allowed_targets: list):
        # switch my texture so that the secondaries will also use this texture
        self._texture = PROJECTILES['stone_shard']
        self.scale = 0.5
        return super().make_secondaries(all_enemies, not_allowed_targets)
