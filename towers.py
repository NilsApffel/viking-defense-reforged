from arcade import Sprite, Texture, draw_line, draw_scaled_texture_rectangle
from arcade.color import LIGHT_GRAY
from math import atan2, pi, sqrt, cos, sin, ceil
from random import random
from constants import MAP_WIDTH, SCREEN_HEIGHT, ASSETS, is_debug, ZAPS, PROJECTILES
from copy import deepcopy
from effects import SlowDown, Inflame, Freeze
from enemies import Enemy
from explosions import CatapultExplosion, GrowingExplosion
from projectiles import Projectile, Falcon, FlameParticle
from runes import Rune, MiniRune
from utils import normalize_tuple

class Tower(Sprite):
    def __init__(self, scale: float = 1, cooldown: float = 2, 
                    range: float = 100, damage: float = 5, 
                    name: str = None, description: str = None, can_see_types: list = None, 
                    has_rotating_top: bool = False, is_2x2: bool = False, 
                    constant_attack: bool = False, projectiles_are_homing: bool = False, 
                    animation_transition_times: list = None, texture: Texture = None):
        super().__init__(scale=scale, texture=texture)
        self.cooldown = cooldown
        self.cooldown_remaining = 0.0
        self.range = range
        self.damage = damage
        self.name = name
        if self.name is None:
            self.name = "Example Tower"
        self.description = description
        if self.description is None:
            self.description = "Generic Tower object. How do I make abstract classes again ?"
        self.can_see_types = can_see_types
        if can_see_types is None:
            self.can_see_types = []
        self.target = None
        self.target_x = MAP_WIDTH/2
        self.target_y = SCREEN_HEIGHT * 100000
        self.attack_animation_remaining = 0
        self.does_rotate = has_rotating_top
        self.is_2x2 = is_2x2
        self.do_constant_attack = constant_attack
        self.rune = None
        self.minirune = None
        self.projectiles_are_homing = projectiles_are_homing
        if animation_transition_times:
            self.animation_transition_times = animation_transition_times
            self.number_of_textures = len(self.animation_transition_times) - 1
            self.is_animated = (self.number_of_textures >= 2)
        else:
            self.animation_transition_times = []
            self.number_of_textures = 1
            self.is_animated = False
        self.animation_time = 0.0

    # this is a total hack, using it because creating a deepcopy of a shop's tower attribute to 
    # place it on the map doesn't work
    def make_another(self): 
        return Tower()

    def on_update(self, delta_time: float = 1 / 60):
        if self.does_rotate:
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            self.angle = atan2(-dx, dy)*180/pi

        # animation update, but only if needed
        if self.is_animated:
            old_time = self.animation_time
            new_time = old_time + delta_time
            # did we cross a threshold ? 
            for k, transition_time in enumerate(self.animation_transition_times):
                if old_time < transition_time <= new_time:
                    # we crossed a threshold, update my texture
                    new_texture_num = k % self.number_of_textures
                    self.set_texture(new_texture_num)
            self.animation_time = new_time
            if self.animation_time > self.animation_transition_times[-1]:
                self.animation_time -= self.animation_transition_times[-1]

        return super().on_update(delta_time)

    def can_see(self, enemy: Enemy):
        if enemy.center_y > SCREEN_HEIGHT:
            return False
        dx = self.center_x - enemy.center_x
        dy = self.center_y - enemy.center_y
        dist2 = dx*dx + dy*dy
        if dist2 > self.range**2:
            return False
        if enemy.is_flying and not ('flying' in self.can_see_types):
            return False
        if (not enemy.is_flying) and not ('floating' in self.can_see_types):
            return False
        if enemy.is_hidden and not ('underwater' in self.can_see_types):
            return False
        return True

    def aim_to(self, enemy: Enemy):
        self.target_x = enemy.center_x
        self.target_y = enemy.center_y
        self.target = enemy

    def attack(self, enemy: Enemy):
        """Tells the tower what enemy to attack, in order for it to draw its own animation, 
        and re-set its own cooldown. Returns instantaneous damage dealt to the enemy and any 
        new Projectile objects."""
        self.cooldown_remaining = self.cooldown
        self.target = enemy
        projectiles_created = []
        return self.damage, projectiles_created

    def draw_shoot_animation(self):
        pass

    def describe_damage(self):
        if self.do_constant_attack:
            return 'Damage: ' + str(round(self.damage, 2)) + ' per second\n'
        else:
            return 'Damage: ' + str(round(self.damage, 2)) + '\nReload: ' + str(round(self.cooldown, 2)) + ' seconds'

    def has_rune(self, rune_name: str):
        if self.rune is None:
            return False
        if (self.rune.name == rune_name) or rune_name == 'any':
            return True
        return False

    def set_rune(self, rune: Rune):
        if self.has_rune(rune.name):
            return 
        if (not (self.rune is None)):
            # we need to clear our current rune's effects
            clean_tower = self.make_another()
            self.cooldown = clean_tower.cooldown
            self.range = clean_tower.range
            self.damage = clean_tower.damage
            self.projectiles_are_homing = clean_tower.projectiles_are_homing
            self.minirune.remove_from_sprite_lists()
        self.rune = rune
        self.minirune = MiniRune(rune, center_x=self.center_x+10, center_y=self.center_y-10)
        if rune.name == 'raidho':
            self.projectiles_are_homing = True
        elif rune.name == 'hagalaz':
            self.damage *= 1.25
        elif rune.name == 'tiwaz':
            self.range *= 1.5
        elif rune.name == 'kenaz':
            self.damage *= 1.2
        elif rune.name == 'sowil':
            self.cooldown /= 2.00
            self.cooldown_remaining /= 2.00
            if self.do_constant_attack:
                self.damage *= 2.00
        return self.minirune

    def make_runed_projectile(self, projectile: Projectile):
        if self.has_rune('raidho'):
            projectile.has_static_target = False
            projectile.target = self.target
            projectile.is_retargeting = True
            projectile.parent_tower = self
        elif self.has_rune('kenaz'):
            if random() < 0.05:
                projectile.effects.append(Inflame())
        elif self.has_rune('isa'):
            if random() < 0.05:
                projectile.effects.append(Freeze())
        elif self.has_rune('sowil'):
            vx = projectile.velocity[0]
            vy = projectile.velocity[1]
            projectile.speed *= 2.00
            projectile.velocity = [vx*2.00, vy*2.00]
        elif self.has_rune('laguz'):
            projectile.num_secondary_projectiles += 1
        return projectile
    
    def remove_from_sprite_lists(self):
        if self.minirune:
            self.minirune.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()

class TowerBase(Tower):
    def __init__(self, scale: float = 1, name: str = None, texture: Texture = None):
        super().__init__(scale=scale, damage=0, range=0, cooldown=0,  name=name, texture=texture)

    def can_see(self, enemy: Enemy):
        return False


class WatchTower(Tower):
    def __init__(self):
        super().__init__(scale=1.0, cooldown=2.0, 
                            range=112, damage=5, name="Watchtower", 
                            description="Fires at floating\nNever misses", 
                            can_see_types=['floating'], 
                            animation_transition_times=[0.00, 0.08, 0.16, 0.24])
        self.append_texture(ASSETS['watchtower0'])
        self.append_texture(ASSETS['watchtower1'])
        self.append_texture(ASSETS['watchtower2'])
        self.set_texture(0)

    def make_another(self):
        return WatchTower()

    def attack(self, enemy: Enemy):
        self.attack_animation_remaining = 0.1
        self.enemy_x = enemy.center_x
        self.enemy_y = enemy.center_y
        return super().attack(enemy)

    def draw_shoot_animation(self):
        enemy_vector = (self.enemy_x-self.center_x, self.enemy_y-self.center_y)
        start_offset_x, start_offset_y = normalize_tuple(xytup=enemy_vector, new_length=11)
        draw_line(
            start_x=self.center_x + start_offset_x, 
            start_y=self.center_y + start_offset_y, 
            end_x=self.enemy_x, 
            end_y=self.enemy_y, 
            color=LIGHT_GRAY, 
            line_width=2
        )

    def on_update(self, delta_time: float = 1 / 60):
        self.attack_animation_remaining -= delta_time
        if self.attack_animation_remaining < 0:
            self.attack_animation_remaining = 0
        return super().on_update(delta_time)
        

class Catapult(Tower):
    def __init__(self):
        super().__init__(
            texture=ASSETS['catapult_top'], 
            scale=0.8, 
            cooldown=3.5, 
            range=208, 
            damage=10, 
            name="Catapult", 
            description="Fires at Floating & Underwater\nUnhoming. Splash damage", 
            can_see_types=['floating', 'underwater'], 
            has_rotating_top=True
        )
        self.base_sprite = None

    def make_another(self):
        return Catapult()

    def make_base_tower(self):
        self.base_sprite = TowerBase(name='CatapultBase', texture=ASSETS['catapult_base'])
        self.base_sprite.center_x = self.center_x
        self.base_sprite.center_y = self.center_y
        return self.base_sprite

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        cannonball = Projectile(
            texture=PROJECTILES['cannonball'], scale=0.3, speed=2.5, angle_rate=0,
            center_x=self.center_x + 9*sin(self.angle*pi/180), 
            center_y=self.center_y - 9*cos(self.angle*pi/180), 
            target=None,
            target_x=enemy.center_x, target_y=enemy.center_y, 
            damage=self.damage, do_splash_damage=True, splash_radius=32, 
            impact_effect=CatapultExplosion(), 
        )
        cannonball = self.make_runed_projectile(cannonball)
            
        return 0, [cannonball] # damage will be dealt by projectile

    def remove_from_sprite_lists(self):
        self.base_sprite.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()
    

class FalconCliff(Tower):
    def __init__(self):
        super().__init__(
            texture=ASSETS['falcon_cliff'], 
            scale=1.0, 
            cooldown=0.1, 
            range=144, 
            damage=7.5, 
            name="Falcon Cliff", 
            description="Fires at Floating & Flying\nFalcon stays within range", 
            can_see_types=['floating', 'flying'], 
            constant_attack=True
        )
        self.falcon = Falcon(parent_tower=self)

    def make_another(self):
        return FalconCliff()

    def set_rune(self, rune: Rune):
        if self.has_rune(rune.name):
            return 
        if (not (self.rune is None)):
            # we need to clear our current rune's effects
            clean_tower = self.make_another()
            self.cooldown = clean_tower.cooldown
            self.range = clean_tower.range
            self.damage = clean_tower.damage
            self.projectiles_are_homing = clean_tower.projectiles_are_homing
            self.minirune.remove_from_sprite_lists()
        self.rune = rune
        self.minirune = MiniRune(rune, center_x=self.center_x+10, center_y=self.center_y-10)
        if rune.name == 'raidho':
            self.projectiles_are_homing = True
        elif rune.name == 'hagalaz':
            self.damage *= 1.25
        elif rune.name == 'tiwaz':
            self.range *= 1.5
        elif rune.name == 'kenaz':
            self.damage *= 1.2
        elif rune.name == 'sowil':
            self.damage *= 2.00

        self.falcon.set_rune(rune)
        return self.minirune

    def attack(self, enemy: Enemy):
        if self.can_see(enemy):
            return self.falcon.attack(enemy), [] # falcon attack should return the damage
        return 0, []
    
    def remove_from_sprite_lists(self):
        self.falcon.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()


class Bastion(Tower):
    def __init__(self):
        super().__init__(
            texture=ASSETS['bastion'], cooldown=5, range=48, damage=25, name='Bastion', 
            description='Fires at floating & underwater\nDamages all in range', 
            can_see_types=['floating', 'underwater'])
        self.splash_radius = 32
        self.explode_distance = 32

    def make_another(self):
        return Bastion()

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        explosives = []
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        theta_0 = atan2(dy, dx)
        for k in range(3):
            theta_k = theta_0 + 2*pi*k/3
            proj = Projectile(
                texture=PROJECTILES['cannonball'], scale=0.3, speed=2.5, angle_rate=0,
                center_x=self.center_x, center_y=self.center_y, target=None,
                target_x=self.center_x + self.explode_distance*cos(theta_k), 
                target_y=self.center_y + self.explode_distance*sin(theta_k), 
                damage=self.damage, do_splash_damage=True, splash_radius=self.splash_radius, 
                impact_effect=CatapultExplosion(scale=0.8, speed_factor=1.5), 
            )
            proj = self.make_runed_projectile(proj)
            explosives.append(proj)
            
        return 0, explosives # damage will be dealt by projectiles


class GreekFire(Tower):
    def __init__(self):
        super().__init__(
            texture=ASSETS['greek_fire_top'], 
            cooldown=0.001, 
            range=150, 
            damage=30, 
            name='Greek Fire', 
            description='Fires at floating\nContinuous fire', 
            can_see_types=['floating'], 
            has_rotating_top=True, 
            constant_attack=True, 
            projectiles_are_homing=True)
        self.latest_dt = 0.017
        self.particles_per_second = 60*10
        self.effect_probability_per_second = 0.05
        self.effect_probability_per_particle = 1-(1-self.effect_probability_per_second)**(1.0/self.particles_per_second)
        self.base_sprite = None

    def make_another(self):
        return GreekFire()

    def make_runed_projectile(self, projectile: Projectile):
        if self.has_rune('kenaz'):
            if random() < self.effect_probability_per_particle:
                projectile.effects.append(Inflame())
        elif self.has_rune('isa'):
            if random() < self.effect_probability_per_particle:
                projectile.effects.append(Freeze())
        else:
            return super().make_runed_projectile(projectile)
        return projectile

    def make_base_tower(self):
        self.base_sprite = TowerBase(name='GreekFireBase', texture=ASSETS['greek_fire_base'])
        self.base_sprite.center_x = self.center_x
        self.base_sprite.center_y = self.center_y
        return self.base_sprite

    def on_update(self, delta_time: float = 1 / 60):
        self.latest_dt = delta_time
        return super().on_update(delta_time)
    
    def attack(self, enemy: Enemy):
        super().attack(enemy)
        flame_particles = []
        n_particles = ceil(self.particles_per_second*self.latest_dt)
        n_particles = max (1, n_particles) # guarantee we always create at least 1 particle
        total_dmg = self.damage * self.latest_dt
        dmg_per_particle = total_dmg / n_particles
        for k in range(n_particles):
            particle = FlameParticle(
                tower_x=self.center_x, 
                tower_y=self.center_y,
                tower_angle=self.angle,
                enemy=enemy,
                damage=dmg_per_particle
            )
            flame_particles.append(self.make_runed_projectile(particle))

        return 0, flame_particles

    def remove_from_sprite_lists(self):
        self.base_sprite.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()

class OakTreeTower(Tower):
    def __init__(self):
        super().__init__(texture=ASSETS['sacred_oak'], scale=1.0, cooldown=2.0, 
                            range=112, damage=5, name="Sacred Oak", 
                            description="Fires at flying\nHoming", 
                            can_see_types=['flying'], 
                            projectiles_are_homing=True)

    def make_another(self):
        return OakTreeTower()

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        leaf = Projectile(
            texture=PROJECTILES['leaf'], scale=1.0, speed=2.0, angle_rate=360,
            center_x=self.center_x, center_y=self.center_y, 
            target=enemy, damage=self.damage
        )
        leaf = self.make_runed_projectile(leaf)
        return 0, [leaf] # damage will be dealt by projectile


class StoneHead(Tower):
    def __init__(self):
        super().__init__(texture=ASSETS['stone_head_top'], cooldown=3, 
                         range=112, damage=0, name='Stone Head', 
                         description="Fires at flying & floating\nHoming. Slows down enemies", 
                         can_see_types=['flying', 'floating'], has_rotating_top=True, 
                         projectiles_are_homing=True)
        self.base_sprite = None
        
    def make_another(self):
        return StoneHead()
    
    def make_base_tower(self):
        self.base_sprite = TowerBase(name='StoneHeadBase', texture=ASSETS['stone_head_base'])
        self.base_sprite.center_x = self.center_x
        self.base_sprite.center_y = self.center_y
        return self.base_sprite
    
    def attack(self, enemy: Enemy):
        super().attack(enemy)
        enemy_vector = (enemy.center_x-self.center_x, enemy.center_y-self.center_y)
        start_offset_x, start_offset_y = normalize_tuple(xytup=enemy_vector, new_length=13)
        wind_gust = Projectile(
            texture=PROJECTILES['wind_gust'], scale=1.0, speed=2.0, angle_rate=0,
            center_x=self.center_x+start_offset_x, 
            center_y=self.center_y+start_offset_y, 
            target=enemy, damage=self.damage, effects=[SlowDown()]
        )
        wind_gust = self.make_runed_projectile(wind_gust)
        return 0, [wind_gust] # effect will be dealt by projectile

    def remove_from_sprite_lists(self):
        self.base_sprite.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()       


class SparklingPillar(Tower):
    def __init__(self):
        super().__init__(texture=ASSETS['sparkling_pillar'], cooldown=0.3, 
                         range=75, damage=2, name='Sparkling Pillar', 
                         description="Fires at flying\nNever missies", 
                         can_see_types=['flying'], has_rotating_top=False)
        
    def make_another(self):
        return SparklingPillar()
    
    def attack(self, enemy: Enemy):
        self.attack_animation_remaining = 0.05
        self.enemy_x = enemy.center_x
        self.enemy_y = enemy.center_y
        return super().attack(enemy)
    
    def draw_shoot_animation(self):
        cx = (self.center_x + self.enemy_x)/2
        cy = (self.center_y + self.enemy_y)/2
        dx = self.enemy_x - self.center_x
        dy = self.enemy_y - self.center_y
        zap_num = round(sqrt(dx**2 + dy**2)/10)*10
        if zap_num > 0:
            ZAPS['zap-'+str(zap_num)].draw_scaled(
                center_x=cx, 
                center_y=cy, 
                angle=atan2(dy, dx)*180/pi
            )

    def on_update(self, delta_time: float = 1 / 60):
        self.attack_animation_remaining -= delta_time
        if self.attack_animation_remaining < 0:
            self.attack_animation_remaining = 0
        return super().on_update(delta_time)


class QuarryOfRage(Tower):
    def __init__(self):
        super().__init__(texture=ASSETS['quarry_of_rage'], cooldown=4.0, 
                         range=208, damage=30, name='Quarry Of Rage', 
                         description='Fires at floating\nHoming. Fragmentation blast', 
                         can_see_types=['floating'], projectiles_are_homing=True)
    
    def make_another(self):
        return QuarryOfRage()
    
    def attack(self, enemy: Enemy):
        super().attack(enemy)
        bomb = Projectile(
            texture=PROJECTILES['bomb'], scale=0.3, speed=5, angle_rate=0,
            center_x=self.center_x, center_y=self.center_y, 
            target=enemy, target_x=enemy.center_x, target_y=enemy.center_y, 
            damage=self.damage, do_splash_damage=False, 
            name='rage-bomb', num_secondary_projectiles=4
        )
        bomb = self.make_runed_projectile(bomb)
            
        return 0, [bomb] # damage will be dealt by projectile


class SanctumOfTempest(Tower):
    def __init__(self):
        super().__init__(cooldown=0.5, 
                         range=96, damage=10, name='Sanctum of Tempest', 
                         description="Fires at flying & floating\nEach 5th hit amplified", 
                         can_see_types=["floating", "flying"])
        self.hit_counter = 0
        for k in range(5):
            self.append_texture(ASSETS['sanctum'+str(k)])
        self.set_texture(0)

    def make_another(self):
        return SanctumOfTempest()
    
    def attack(self, enemy: Enemy):
        self.hit_counter = self.hit_counter + 1
        self.hit_counter = self.hit_counter % 5
        if self.hit_counter != 0:
            self.attack_animation_remaining = 0.1
            self.enemy_x = enemy.center_x
            self.enemy_y = enemy.center_y
            self.set_texture(self.hit_counter)
            return super().attack(enemy)
        else:
            # Special AoE giant hit
            blast_effect = GrowingExplosion(
                texture=ASSETS['zap_blast'], starting_scale=0.1, 
                lifetime_seconds=0.15, 
                scale_increase_rate = 10 if self.has_rune('tiwaz') else 6, 
            )
            blast_effect.angle = random()*2*pi
            zap_blast = Projectile(
                texture=PROJECTILES['cannonball'], scale=0.1, speed=0,
                center_x=self.center_x, center_y=self.center_y, 
                target_x=self.center_x, target_y=self.center_y, 
                damage=self.damage, do_splash_damage=True, 
                splash_radius=self.range, impact_effect=blast_effect, 
                name='zap blast'
            )
            if (not self.has_rune('raidho')) and (not self.has_rune('laguz')):
                zap_blast = self.make_runed_projectile(zap_blast)
            self.set_texture(self.hit_counter)
            self.cooldown_remaining = self.cooldown
            return 0, [zap_blast]
        
    def on_update(self, delta_time: float = 1 / 60):
        self.attack_animation_remaining -= delta_time
        if self.attack_animation_remaining < 0:
            self.attack_animation_remaining = 0
        return super().on_update(delta_time)
    
    def draw_shoot_animation(self):
        cx = (self.center_x + self.enemy_x)/2
        cy = (self.center_y + self.enemy_y)/2
        dx = self.enemy_x - self.center_x
        dy = self.enemy_y - self.center_y
        zap_num = round(sqrt(dx**2 + dy**2)/10)*10
        if zap_num > 0:
            ZAPS['zap-'+str(zap_num)].draw_scaled(
                center_x=cx, 
                center_y=cy, 
                angle=atan2(dy, dx)*180/pi
            )


class BigBuilding(Tower):
    def __init__(self, scale: float = 1, cooldown: float = 120, 
                    name: str = None, description: str = None, 
                    unlocked_rune_indxs: list = None, 
                    unlocked_power_indxs: list = None, 
                    animation_transition_times: list = None, 
                    texture: Texture = None):
        super().__init__(scale=scale, cooldown=cooldown, 
                            name=name, description=description, is_2x2=True, 
                            animation_transition_times=animation_transition_times, 
                            texture=texture)
        if unlocked_rune_indxs is None:
            self.unlocked_rune_indxs = []
        else:
            self.unlocked_rune_indxs = deepcopy(unlocked_rune_indxs)
        if unlocked_power_indxs is None:
            self.unlocked_power_indxs = []
        else:
            self.unlocked_power_indxs = deepcopy(unlocked_power_indxs)

    def describe_damage(self):
        return ''
        

class TempleOfThor(BigBuilding):
    def __init__(self):
        super().__init__(texture=ASSETS['temple_of_thor'], scale=1.0, cooldown=120, 
                            name="Temple of Thor", 
                            description="Grants Mjolnir ability\nGrants Raidho rune", 
                            unlocked_rune_indxs=[0], 
                            unlocked_power_indxs=[1])

    def make_another(self):
        return TempleOfThor()
    

class Forge(BigBuilding):
    def __init__(self):
        super().__init__(scale=1.0, cooldown=90, 
                            name="Forge", 
                            description="Grants Platform ability\nGrants Hagalaz rune", 
                            unlocked_rune_indxs=[1], 
                            unlocked_power_indxs=[2], 
                            animation_transition_times=[0.00, 0.08, 0.16, 0.24])
        self.append_texture(ASSETS['forge0'])
        self.append_texture(ASSETS['forge1'])
        self.append_texture(ASSETS['forge2'])
        self.set_texture(0)

    def make_another(self):
        return Forge()


class TempleOfOdin(BigBuilding):
    def __init__(self):
        super().__init__(texture=ASSETS['temple_of_odin'], scale=1.0, cooldown=0, 
                            name="Temple of Odin", 
                            description="Grants Tiwaz, Kenaz and Isa runes", 
                            unlocked_rune_indxs=[2, 3, 4], 
                            unlocked_power_indxs=[])

    def make_another(self):
        return TempleOfOdin()


class ChamberOfTheChief(BigBuilding):
    def __init__(self):
        super().__init__(texture=ASSETS['chamber_of_the_chief'], cooldown=60, 
                         name='Chamber of the Chief', 
                         description='Grants Command ability\nGrants Sowil rune', 
                         unlocked_rune_indxs=[5], unlocked_power_indxs=[3])
        
    def make_another(self):
        return ChamberOfTheChief()


class TempleOfFreyr(BigBuilding):
    def __init__(self):
        super().__init__(texture=ASSETS['temple_of_freyr'], cooldown=120, 
                         name='Temple of Freyr', 
                         description='Grants Harvest ability\nGrants Laguz rune', 
                         unlocked_rune_indxs=[6], unlocked_power_indxs=[4])
    
    def make_another(self):
        return TempleOfFreyr()
