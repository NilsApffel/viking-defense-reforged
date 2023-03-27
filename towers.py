from arcade import Sprite, draw_line, draw_scaled_texture_rectangle
from arcade.color import LIGHT_GRAY
from math import atan2, pi, sqrt
from random import random
from constants import MAP_WIDTH, SCREEN_HEIGHT, ASSETS, is_debug, ZAPS
from copy import deepcopy
from effects import SlowDown, Inflame, Freeze
from enemies import Enemy
from explosions import Explosion
from projectiles import Projectile, Falcon
from runes import Rune

class Tower(Sprite):
    def __init__(self, filename: str = None, scale: float = 1, cooldown: float = 2, 
                    range: float = 100, damage: float = 5, 
                    name: str = None, description: str = None, can_see_types: list = None, 
                    has_rotating_top: bool = False, is_2x2: bool = False, 
                    constant_attack: bool = False, projectiles_are_homing: bool = False):
        super().__init__(filename=filename, scale=scale)
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
        self.animation_ontime_remaining = 0
        self.does_rotate = has_rotating_top
        self.is_2x2 = is_2x2
        self.do_constant_attack = constant_attack
        self.rune = None
        self.projectiles_are_homing = projectiles_are_homing

    # this is a total hack, using it because creating a deepcopy of a shop's tower attribute to 
    # place it on the map doesn't work
    def make_another(self): 
        return Tower()

    def draw_runes(self):
        if self.rune is None:
            return
        if self.rune.name == 'raidho':
            draw_scaled_texture_rectangle(
                center_x=self.center_x+10,
                center_y=self.center_y-10,
                texture=ASSETS['raidho-r'],
                scale=1.0,
            )
        elif self.rune.name == 'hagalaz':
            draw_scaled_texture_rectangle(
                center_x=self.center_x+10,
                center_y=self.center_y-10,
                texture=ASSETS['hagalaz-h'],
                scale=1.0,
            )
        elif self.rune.name == 'tiwaz':
            draw_scaled_texture_rectangle(
                center_x=self.center_x+10,
                center_y=self.center_y-10,
                texture=ASSETS['tiwaz-t'],
                scale=1.0,
            )
        elif self.rune.name == 'kenaz':
            draw_scaled_texture_rectangle(
                center_x=self.center_x+10,
                center_y=self.center_y-10,
                texture=ASSETS['kenaz-c'],
                scale=1.0,
            )
        elif self.rune.name == 'isa':
            draw_scaled_texture_rectangle(
                center_x=self.center_x+10,
                center_y=self.center_y-10,
                texture=ASSETS['isa-i'],
                scale=1.0,
            )

    def on_update(self, delta_time: float = 1 / 60):
        if self.does_rotate:
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            self.angle = atan2(-dx, dy)*180/pi
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
            return 'Damage: ' + str(self.damage) + ' per second\n'
        else:
            return 'Damage: ' + str(self.damage) + '\nReload: ' + str(self.cooldown) + ' seconds'

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
        self.rune = rune
        if rune.name == 'raidho':
            self.projectiles_are_homing = True
        elif rune.name == 'hagalaz':
            self.damage *= 1.25
        elif rune.name == 'tiwaz':
            self.range *= 1.5
        elif rune.name == 'kenaz':
            self.damage *= 1.2

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
        return projectile

class InstaAirTower(Tower):
    def __init__(self):
        super().__init__(filename="images/tower_model_1E.png", scale=1.0, cooldown=2.0, 
                            range=100, damage=5, name="Arrow Tower", 
                            description="Fires at flying\nNever misses", 
                            can_see_types=['flying'])

    def make_another(self):
        return InstaAirTower()


class WatchTower(Tower):
    def __init__(self):
        super().__init__(filename="images/tower_model_1E.png", scale=1.0, cooldown=2.0, 
                            range=112, damage=5, name="Watchtower", 
                            description="Fires at floating\nNever misses", 
                            can_see_types=['floating'])

    def make_another(self):
        return WatchTower()

    def attack(self, enemy: Enemy):
        self.animation_ontime_remaining = 0.1
        self.enemy_x = enemy.center_x
        self.enemy_y = enemy.center_y
        return super().attack(enemy)

    def draw_shoot_animation(self):
        draw_line(
            start_x=self.center_x, 
            start_y=self.center_y, 
            end_x=self.enemy_x, 
            end_y=self.enemy_y, 
            color=LIGHT_GRAY, 
            line_width=2
        )

    def on_update(self, delta_time: float = 1 / 60):
        self.animation_ontime_remaining -= delta_time
        if self.animation_ontime_remaining < 0:
            self.animation_ontime_remaining = 0
        return super().on_update(delta_time)
        

class Catapult(Tower):
    def __init__(self):
        super().__init__(
            filename="images/catapult_top.png", 
            scale=1.0, 
            cooldown=3.5, 
            range=208, 
            damage=10, 
            name="Catapult", 
            description="Fires at Floating & Underwater\nUnhoming. Splash damage", 
            can_see_types=['floating', 'underwater'], 
            has_rotating_top=True
        )

    def make_another(self):
        return Catapult()

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        cannonball = Projectile(
            filename="images/cannonball.png", scale=0.3, speed=2.5, angle_rate=0,
            center_x=self.center_x, center_y=self.center_y, 
            target=None,
            target_x=enemy.center_x, target_y=enemy.center_y, 
            damage=self.damage, do_splash_damage=True, splash_radius=32, 
            impact_effect=Explosion(filename='./images/cannonball-explosion.png'), 
        )
        cannonball = self.make_runed_projectile(cannonball)
            
        return 0, [cannonball] # damage will be dealt by projectile

    # TODO : add an un-moving base
    # (bonus: use rotation to slightly adjust starting position of projectile)


class FalconCliff(Tower):
    def __init__(self):
        super().__init__(
            filename="images/falcon_cliff.png", 
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
        self.rune = rune
        if rune.name == 'raidho':
            self.projectiles_are_homing = True
        elif rune.name == 'hagalaz':
            self.damage *= 1.25
        elif rune.name == 'tiwaz':
            self.range *= 1.5
        elif rune.name == 'kenaz':
            self.damage *= 1.2

        self.falcon.set_rune(rune)

    def attack(self, enemy: Enemy):
        if self.can_see(enemy):
            return self.falcon.attack(enemy), [] # falcon attack should return the damage
        return 0, []
    
    def remove_from_sprite_lists(self):
        self.falcon.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()


class OakTreeTower(Tower):
    def __init__(self):
        super().__init__(filename="images/Oak_32x32_transparent.png", scale=1.0, cooldown=2.0, 
                            range=112, damage=5, name="Sacred Oak", 
                            description="Fires at flying\nHoming", 
                            can_see_types=['flying'], 
                            projectiles_are_homing=True)

    def make_another(self):
        return OakTreeTower()

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        leaf = Projectile(
            filename="images/leaf.png", scale=1.0, speed=2.0, angle_rate=360,
            center_x=self.center_x, center_y=self.center_y, 
            target=enemy, damage=self.damage
        )
        leaf = self.make_runed_projectile(leaf)
        return 0, [leaf] # damage will be dealt by projectile


class StoneHead(Tower):
    def __init__(self):
        super().__init__(filename='./images/stone_head_top.png', cooldown=3, 
                         range=112, damage=0, name='Stone Head', 
                         description="Fires at flying & floating\nHoming. Slows down enemies", 
                         can_see_types=['flying', 'floating'], has_rotating_top=True, 
                         projectiles_are_homing=True)
        
    def make_another(self):
        return StoneHead()
    
    def attack(self, enemy: Enemy):
        super().attack(enemy)
        wind_gust = Projectile(
            filename="images/wind-gust.png", scale=1.0, speed=2.0, angle_rate=0,
            center_x=self.center_x, center_y=self.center_y, 
            target=enemy, damage=self.damage, effects=[SlowDown()]
        )
        wind_gust = self.make_runed_projectile(wind_gust)
        return 0, [wind_gust] # effect will be dealt by projectile
        

class SparklingPillar(Tower):
    def __init__(self):
        super().__init__(filename='./images/sparkling_pillar.png', cooldown=0.3, 
                         range=75, damage=2, name='Sparkling Pillar', 
                         description="Fires at flying\nNever missies", 
                         can_see_types=['flying'], has_rotating_top=False)
        
    def make_another(self):
        return SparklingPillar()
    
    def attack(self, enemy: Enemy):
        self.animation_ontime_remaining = 0.05
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
        self.animation_ontime_remaining -= delta_time
        if self.animation_ontime_remaining < 0:
            self.animation_ontime_remaining = 0
        return super().on_update(delta_time)


class BigBuilding(Tower):
    def __init__(self, filename: str = None, scale: float = 1, cooldown: float = 120, 
                    name: str = None, description: str = None, 
                    unlocked_rune_indxs: list = None, 
                    unlocked_power_indxs: list = None):
        super().__init__(filename=filename, scale=scale, cooldown=cooldown, 
                            name=name, description=description, is_2x2=True)
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
        super().__init__(filename="images/TempleOfThor.png", scale=1.0, cooldown=120, 
                            name="Temple of Thor", 
                            description="Grants Mjolnir ability\nGrants Raidho rune", 
                            unlocked_rune_indxs=[0], 
                            unlocked_power_indxs=[0])

    def make_another(self):
        return TempleOfThor()
    

class Forge(BigBuilding):
    def __init__(self):
        super().__init__(filename="images/Forge-transparent.png", scale=1.0, cooldown=90, 
                            name="Forge", 
                            description="Grants Platform ability\nGrants Hagalaz rune", 
                            unlocked_rune_indxs=[1], 
                            unlocked_power_indxs=[1])

    def make_another(self):
        return Forge()


class TempleOfOdin(BigBuilding):
    def __init__(self):
        super().__init__(filename="images/TempleOfOdin.png", scale=1.0, cooldown=0, 
                            name="Temple of Odin", 
                            description="Grants Tiwaz, Kenaz and Isa runes", 
                            unlocked_rune_indxs=[2, 3, 4], 
                            unlocked_power_indxs=[])

    def make_another(self):
        return TempleOfOdin()
