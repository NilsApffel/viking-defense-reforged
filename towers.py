import arcade
from copy import deepcopy
from enemies import *

class Explosion(arcade.Sprite):
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


class Projectile(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, speed: float = 2.0,
                    center_x: float = 0, center_y: float = 0, angle: float = 0, angle_rate: float = 0,
                    target: Enemy = None, target_x: float = None, target_y: float = None, 
                    damage: float = 1, do_splash_damage: bool = False, splash_radius: float = 10, 
                    impact_effect: Explosion = None):
        super().__init__(filename=filename, scale=scale, center_x=center_x, center_y=center_y, angle=angle)
        self.speed = speed
        self.angle_rate = angle_rate
        self.target = target
        self.target_x = target_x
        self.target_y = target_y
        self.can_be_deleted = False
        self.has_static_target = (target is None)
        self.damage = damage
        self.do_splash_damage = do_splash_damage
        self.splash_radius = splash_radius
        self.impact_effect = impact_effect

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
            if self.target.current_health > 0:
                self.target_x = self.target.center_x
                self.target_y = self.target.center_y
                # calc velocity based on target
                dx = self.target_x - self.center_x
                dy = self.target_y - self.center_y
                norm = sqrt(dx*dx + dy*dy)
                if norm == 0:
                    norm = 0.001
                self.velocity = (self.speed*dx/norm, self.speed*dy/norm)
            else:
                self.target=None
                self.has_static_target = True
        self.angle += self.angle_rate*delta_time
        # print(norm, "away from target with speed", self.velocity)
        if ((self.center_x > MAP_WIDTH + 20) or (self.center_x < -20) or 
                (self.center_y > SCREEN_HEIGHT + 20) or (self.center_y < CHIN_HEIGHT - 20)):
            self.remove_from_sprite_lists()
        return super().on_update(delta_time)


class Tower(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, cooldown: float = 2, 
                    range: float = 100, damage: float = 5, do_show_range: bool = False, 
                    name: str = None, description: str = None, can_see_types: list = None, 
                    has_rotating_top: bool = False, is_2x2: bool = False):
        super().__init__(filename=filename, scale=scale)
        self.cooldown = cooldown
        self.cooldown_remaining = 0.0
        self.range = range
        self.damage = damage
        self.do_show_range = False
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

    # this is a total hack, using it because creating a deepcopy of a shop's tower attribute to 
    # place it on the map doesn't work
    def make_another(self): 
        return Tower()

    def on_update(self, delta_time: float = 1 / 60):
        if self.does_rotate:
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            self.angle = atan2(-dx, dy)*180/pi
        return super().on_update(delta_time)

    def can_see(self, enemy: Enemy):
        distance = arcade.sprite.get_distance_between_sprites(self, enemy)
        if distance > self.range:
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
        arcade.draw_line(
            start_x=self.center_x, 
            start_y=self.center_y, 
            end_x=self.enemy_x, 
            end_y=self.enemy_y, 
            color=arcade.color.LIGHT_GRAY, 
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
            target_x=enemy.center_x, target_y=enemy.center_y, 
            damage=self.damage, do_splash_damage=True, splash_radius=32, 
            impact_effect=Explosion(filename='./images/cannonball-explosion.png')
        )
        return 0, [cannonball] # damage will be dealt by projectile

    # TODO : add rotation of top of the tower, an un-moving base, 
    # and tracking enemy via top rotation using on_update.
    # (bonus: use rotation to slightly adjust starting position of projectile)


class OakTreeTower(Tower):
    def __init__(self):
        super().__init__(filename="images/Oak_32x32_transparent.png", scale=1.0, cooldown=2.0, 
                            range=112, damage=5, name="Sacred Oak", 
                            description="Fires at flying\nHoming", 
                            can_see_types=['flying'])

    def make_another(self):
        return OakTreeTower()

    def attack(self, enemy: Enemy):
        super().attack(enemy)
        leaf = Projectile(
            filename="images/leaf.png", scale=1.0, speed=2.0, angle_rate=360,
            center_x=self.center_x, center_y=self.center_y, 
            target=enemy, damage=self.damage
        )
        return 0, [leaf] # damage will be dealt by projectile


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
        

class TempleOfThor(BigBuilding):
    def __init__(self):
        super().__init__(filename="images/TempleOfThor.png", scale=1.0, cooldown=120, 
                            name="Temple of Thor", 
                            description="Grants Mjolnir ability\nGrants Raidho rune", 
                            unlocked_rune_indxs=[0], 
                            unlocked_power_indxs=[0])

    def make_another(self):
        return TempleOfThor()
    