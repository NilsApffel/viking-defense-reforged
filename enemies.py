import arcade
from math import sqrt, atan2, pi
from grid import *
from pathfind import find_path

class Enemy(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, speed: float = 0.8,
                    reward: float = 30, is_flying: bool = True, can_hide: bool = False):
        super().__init__(filename, scale)
        self.current_health = health
        self.max_health = health
        self.reward = reward
        self.priority = 800
        self.is_flying = is_flying
        self.is_hidden = False
        self.can_hide = can_hide
        self.rank = 1
        self.modifier = ''
        self.regen_rate = 0.0
        self.speed = speed
        self.velocity = (0, -speed)

    def draw_health_bar(self):
        barheight = 4
        barwidth = self.max_health
        arcade.draw_lrtb_rectangle_filled(
            left  = self.center_x - barwidth/2 + barwidth*(self.current_health/self.max_health),
            right = self.center_x + barwidth/2,
            top = self.top + barheight, 
            bottom = self.top, 
            color=arcade.color.RED)
        arcade.draw_lrtb_rectangle_filled(
            left  = self.center_x - barwidth/2,
            right = self.center_x - barwidth/2 + barwidth*(self.current_health/self.max_health),
            top = self.top + barheight, 
            bottom = self.top, 
            color=arcade.color.GREEN)

    def take_damage_give_money(self, damage: float):
        if 'shield' in self.modifier.lower():
            self.current_health -= damage/2 
        else:
            self.current_health -= damage
        if self.current_health <= 0:
            self.remove_from_sprite_lists()
            return self.reward
        return 0
    
    def set_rank(self, rank:int):
        old_rank = self.rank
        self.rank = rank
        self.max_health *= rank/old_rank
        self.current_health *= rank/old_rank

    def set_modifier(self, modifier: str):
        old_modifier = self.modifier
        self.modifier = modifier
        if ('fast' in modifier) and not ('fast' in old_modifier):
            self.speed *= 1.5
            self.velocity = (self.velocity[0]*1.5, self.velocity[1]*1.5)
        if ('regen' in modifier) and not ('regen' in old_modifier):
            self.regen_rate = self.max_health / 60

    def on_update(self, delta_time: float = 1 / 60):
        if 'regen' in self.modifier.lower():
            self.current_health += self.regen_rate * delta_time
            self.current_health = min(self.current_health, self.max_health)
        return super().on_update(delta_time)

class FlyingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, reward: float = 30):
        super().__init__(filename=filename, scale=scale, health=health, reward=reward, is_flying=True)

    def on_update(self, delta_time: float = None):
        self.priority = self.center_y
        super().on_update(delta_time)


class TinyBird(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/TinyBird.png", scale=1.0, health=10, reward=30)


class SmallShip(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/SmallShip.png", scale=1.0, health=20, reward=60)


class MediumDragon(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/MediumDragon.png", scale=1.0, health=30, reward=100)


class BigDragon(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/BigDragon.png", scale=1.0, health=70, reward=150)


class FloatingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, 
                    reward: float = 30, speed: float = 0.8, can_hide: bool = False):
        super().__init__(filename=filename, scale=scale, health=health, speed=speed,
                            reward=reward, is_flying=False, can_hide=can_hide)
        self.path_to_follow = None
        self.next_path_step = 0

    def on_update(self, delta_time: float=None):
        # follow path steps
        (i, j) = nearest_cell_ij(self.center_x, self.center_y)
        if is_in_cell(self, i,j) and ((i,j) in self.path_to_follow):
            self.next_path_step = self.path_to_follow.index((i,j))+1
        # target next path step
        if self.next_path_step < len(self.path_to_follow):
            target_i, target_j = self.path_to_follow[self.next_path_step]
            target_x, target_y = cell_centerxy(target_i, target_j)
            dx = target_x - self.center_x
            dy = target_y - self.center_y
            norm = sqrt(dx*dx + dy*dy)
            if norm == 0:
                norm = 0.001
            self.velocity = (self.speed*dx/norm, self.speed*dy/norm)
            self.angle = atan2(self.velocity[1], self.velocity[0])*180/pi
        # set own targeting priority vis-a-vis towers
        # priority mostly depends on how many steps are left on the path to your target
        # if your priority is lower than other enemies', towers will try to shoot you first
        self.priority = self.center_y + 1000 * (len(self.path_to_follow) - self.next_path_step)
        super().on_update(delta_time)

    def calc_path(self, map):
        """Updates the enemy's internal path_to_follow variable, which is an ordered list of 
        what cells to go to reach the exit, using a-star pathfinding."""
        i, j = nearest_cell_ij(self.center_x, self.center_y)
        target_i = 15
        target_j = MAP_TARGET_J
        new_path = find_path(start_cell=(i,j), target_cell=(target_i, target_j), map=map)
        self.path_to_follow = new_path
        self.next_path_step = 0


class UnderwaterEnemy(FloatingEnemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, 
                    reward: float = 30, speed: float = 0.8, sumberged_texture_filename: str = None):
        super().__init__(filename=filename, scale=scale, health=health, 
                            reward=reward, speed=speed, can_hide=True)
        self.append_texture(arcade.load_texture(sumberged_texture_filename))
        self.set_texture(0)


class TinyBoat(FloatingEnemy):
    def __init__(self):
        super().__init__(filename="images/boat.png", scale=0.3, health=15, reward=30)


class SmallSnake(UnderwaterEnemy):
    def __init__(self):
        super().__init__(filename="images/SmallSnake.png", scale=1.0, health=25, 
                            reward=60, sumberged_texture_filename="images/SmallSnakeUnderwater.png")


class MediumBoat(FloatingEnemy):
    def __init__(self):
        super().__init__(filename="images/MediumBoat.png", scale=1.0, health=50, reward=100)


class BigWhale(UnderwaterEnemy):
    def __init__(self):
        super().__init__(filename="images/BigWhale.png", scale=1.0, health=80, 
                            reward=150, sumberged_texture_filename="images/BigWhaleUnderwater.png")
