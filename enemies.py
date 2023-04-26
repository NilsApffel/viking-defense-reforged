from arcade import Sprite, SpriteSolidColor, SpriteList, draw_scaled_texture_rectangle, load_texture
from arcade.color import RED, GREEN
from math import sqrt, atan2, pi
from constants import MAP_TARGET_J, ICE_SHIELD_TEXTURE, FIRE_SHIELD_TEXTURE, REGEN_TEXTURE, HBAR_HEIGHT, HBAR_WIDTH_FACTOR, is_debug
from effects import Effect
from grid import *
from pathfind import find_path

class Enemy(Sprite):
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
        self.temporary_effects = SpriteList()
        self.greenbar = SpriteSolidColor(width=round(HBAR_WIDTH_FACTOR*self.max_health), height=HBAR_HEIGHT, color=GREEN)
        self.redbar = SpriteSolidColor(width=1, height=HBAR_HEIGHT, color=RED)
        self.redbar.visible = False
        self.buff_sprite = None

    def take_damage_give_money(self, damage: float):
        starting_health = self.current_health
        if 'shield' in self.modifier.lower():
            self.current_health -= damage/2 
        else:
            self.current_health -= damage
        if self.current_health <= 0:
            for eff in self.temporary_effects:
                eff.remove_from_sprite_lists()
            self.remove_from_sprite_lists()
            if damage > 0 and starting_health > 0:
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

        if old_modifier != modifier:
            if self.buff_sprite:
                self.buff_sprite.remove_from_sprite_lists()
                self.buff_sprite = None

        if ('fast' in modifier) and not ('fast' in old_modifier):
            self.speed *= 1.5
            self.velocity = (self.velocity[0]*1.5, self.velocity[1]*1.5)
        elif ('fast' in old_modifier) and not ('fast' in modifier):
            self.speed /= 1.5
            self.velocity = (self.velocity[0]/1.5, self.velocity[1]/1.5)
        if ('regen' in modifier) and not ('regen' in old_modifier):
            self.regen_rate = 5 # hit points per second
        elif ('regen' in old_modifier) and not ('regen' in modifier):
            self.regen_rate = 0

        effect_texture = None
        if 'ice shield' in self.modifier:
            effect_texture = ICE_SHIELD_TEXTURE
        elif 'fire shield' in self.modifier:
            effect_texture = FIRE_SHIELD_TEXTURE
        elif 'regen' in self.modifier:
            effect_texture = REGEN_TEXTURE
        if self.is_flying:
            shield_size = max(self.width, self.height*0.6) + 4
            vertical_offset = 2
        else:
            shield_size = max(self.width, self.height) + 4
            vertical_offset = 0
        shield_scale = shield_size / 64

        if effect_texture:
            self.buff_sprite = Sprite(
                center_x=self.center_x, 
                center_y=self.center_y + vertical_offset, 
                texture=effect_texture, 
                scale=shield_scale
            )

    def on_update(self, delta_time: float = 1 / 60):
        if 'regen' in self.modifier.lower():
            self.current_health += self.regen_rate * delta_time
            self.current_health = min(self.current_health, self.max_health)

        # go through effects in reverse order because some of them might get removed in this loop
        n = len(self.temporary_effects)
        for k in range(n):
            effect = self.temporary_effects[n-k-1]
            effect.center_x = self.center_x
            effect.center_y = self.center_y
            self.velocity = (effect.speed_multiplier*self.velocity[0], 
                             effect.speed_multiplier*self.velocity[1])
            effect.on_update(delta_time)
            if effect.duration_remaining <= 0:
                effect.remove_from_sprite_lists()
        if self.buff_sprite:
            self.buff_sprite.center_x = self.center_x
            self.buff_sprite.center_y = self.center_y
        self.update_health_bar()
        return super().on_update(delta_time)
    
    def update_health_bar(self):
        full_width = round(self.max_health*HBAR_WIDTH_FACTOR)
        green_width = round(self.current_health*HBAR_WIDTH_FACTOR)
        red_width = full_width - green_width
        if red_width >= 1: #Workaround for Sprites not supporting zero width
            self.redbar.width = red_width
            self.redbar.visible = True
        else:
            self.redbar.width = 1
            self.redbar.visible = False
        self.redbar.center_x = self.center_x + full_width/2 - red_width/2
        self.redbar.center_y = self.top + HBAR_HEIGHT/2

        if green_width >= 1: #Workaround for Sprites not supporting zero width
            self.greenbar.width = green_width
            self.greenbar.visible = True
        else:
            self.greenbar.width = 1
            self.greenbar.visible = False
        self.greenbar.center_x = self.center_x - full_width/2 + green_width/2
        self.greenbar.center_y = self.top + HBAR_HEIGHT/2

    def set_effect(self, effect: Effect) -> bool:
        """Attempts to set the effect on the enemy. Returns True only if the effect 
        was added and was not already present."""
        # check if effect cannot be added
        if self.current_health <= 0:
            return False
        if ('ice shield' in self.modifier) and (effect.name == 'freeze'):
            return False
        if ('fire shield' in self.modifier) and (effect.name == 'inflame'):
            return False
        
        # check if effect is already present
        for eff in self.temporary_effects.sprite_list:
            if eff.name == effect.name:
                eff.duration_remaining = effect.duration
                return False
            
        # add effect
        effect.scale = 1.2*max(self.width, self.height)/50
        self.temporary_effects.append(effect)
        return True # 1 new effect added

    def remove_from_sprite_lists(self):
        self.greenbar.remove_from_sprite_lists()
        self.redbar.remove_from_sprite_lists()
        for eff in self.temporary_effects:
            eff.remove_from_sprite_lists()
        if self.buff_sprite:
            self.buff_sprite.remove_from_sprite_lists()
        return super().remove_from_sprite_lists()

class FlyingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, reward: float = 30):
        super().__init__(filename=filename, scale=scale, health=health, reward=reward, is_flying=True)

    def on_update(self, delta_time: float = None):
        priority_millions = round(self.priority/1000000)
        self.priority = self.center_y + priority_millions*1000000
        self.velocity = (0, -self.speed)
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
        # Priority mostly depends on how many steps are left on the path to your target.
        # If your priority is lower than other enemies', towers will try to shoot you first.
        # Priority millions does not change over time except through the Command ability
        priority_millions = round(self.priority/1000000)
        new_priority = self.center_y + 1000 * (len(self.path_to_follow) - self.next_path_step)
        self.priority = new_priority + priority_millions*1000000
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
        self.append_texture(load_texture(sumberged_texture_filename))
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
