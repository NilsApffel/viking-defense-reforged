import arcade
from random import randint
from math import atan2, floor, pi, sqrt
from copy import copy, deepcopy
from pathfind import find_path

# there's probably a better way than gloabl variables to handle all this sizing...
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600
CELL_SIZE = 32
MAP_WIDTH = 480
MAP_HEIGHT = 480
CHIN_HEIGHT = SCREEN_HEIGHT-MAP_HEIGHT
INFO_BAR_HEIGHT = 20
ATK_BUTT_HEIGHT = CHIN_HEIGHT-INFO_BAR_HEIGHT
SHOP_ITEM_HEIGHT = 62
SHOP_ITEM_THUMB_SIZE = 40
SCREEN_TITLE = "Viking Defense Reforged v0.0.7 Dev"
SCALING = 1.0 # this does nothing as far as I can tell
SHOP_TOPS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k for k in range(0, 5)]
SHOP_BOTTOMS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k - SHOP_ITEM_HEIGHT for k in range(0, 5)]
MAP_TARGET_J = 7


class GridCell():
    def __init__(self, terrain_type: str = None, cellnum: int = -1) -> None:
        self.is_occupied = False
        if (terrain_type is None) or (terrain_type == "g") or (terrain_type == "ground"):
            self.terrain_type = "ground"
        elif (terrain_type == "s") or (terrain_type == "shallow"):
            self.terrain_type = "shallow"
        elif (terrain_type == "d") or (terrain_type == "deep"):
            self.terrain_type = "deep"
        else:
            raise ValueError("invalid terrain type: " + terrain_type)
        self.num = cellnum

    def __eq__(self, __o: object) -> bool:
        if __o == self.terrain_type:
            return True
        if __o == self.terrain_type[0]:
            return True
        return False


class Enemy(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, 
                    reward: float = 30, is_flying: bool = True, can_hide: bool = False):
        super().__init__(filename, scale)
        self.current_health = health
        self.max_health = health
        self.reward = reward
        self.priority = 800
        self.is_flying = is_flying
        self.is_hidden = False
        self.can_hide = can_hide

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
        self.current_health -= damage
        if self.current_health <= 0:
            self.remove_from_sprite_lists()
            return self.reward
        return 0


class FlyingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, reward: float = 30):
        super().__init__(filename=filename, scale=scale, health=health, reward=reward, is_flying=True)

    def on_update(self, delta_time: float = None):
        self.priority = self.center_y
        super().on_update(delta_time)


class Dragon(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/dragon.png", scale=0.5, health=10, reward=30)


class FloatingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, 
                    reward: float = 30, speed: float = 1, can_hide: bool = False):
        super().__init__(filename=filename, scale=scale, health=health, 
                            reward=reward, is_flying=False, can_hide=can_hide)
        self.path_to_follow = None
        self.next_path_step = 0
        self.speed = speed

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
                    reward: float = 30, speed: float = 1, sumberged_texture_filename: str = None):
        super().__init__(filename=filename, scale=scale, health=health, 
                            reward=reward, speed=speed, can_hide=True)
        self.append_texture(arcade.load_texture(sumberged_texture_filename))
        self.set_texture(0)


class TinyBoat(FloatingEnemy):
    def __init__(self):
        super().__init__(filename="images/boat.png", scale=0.4, health=15, reward=30)


class BigWhale(UnderwaterEnemy):
    def __init__(self):
        super().__init__(filename="images/whale.png", scale=1, health=50, 
                            reward=120, sumberged_texture_filename="images/whale_submerged2.png")


class Projectile(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, speed: float = 2.0,
                    center_x: float = 0, center_y: float = 0, angle: float = 0, angle_rate: float = 0,
                    target: Enemy = None, target_x: float = None, target_y: float = None, 
                    damage: float = 1, do_splash_damage: bool = False, splash_radius: float = 10):
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

        if not self.has_static_target:
            self.target_x = self.target.center_x
            self.target_y = self.target.center_y
        # calc velocity based on target
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        norm = sqrt(dx*dx + dy*dy)
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
                    name: str = None, description: str = None, can_see_types: list = None):
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
        self.animation_ontime_remaining = 0

    # this is a total hack, using it because creating a deepcopy of a shop's tower attribute to 
    # place it on the map doesn't work
    def make_another(self): 
        return Tower()

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
                            range=100, damage=5, name="Watchtower", 
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
        

class OakTreeTower(Tower):
    def __init__(self):
        super().__init__(filename="images/Oak_32x32_transparent.png", scale=1.0, cooldown=2.0, 
                            range=100, damage=5, name="Sacred Oak", 
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


class ShopItem():
    def __init__(self, is_unlocked: bool = False, is_unlockable: bool = False, thumbnail: str = None, 
                    scale: float = 1.0, cost: float = 100, tower: Tower = None) -> None:
        self.is_unlocked = is_unlocked
        self.is_unlockable = is_unlockable
        if thumbnail is None:
            thumbnail = "images/question.png"
        self.thumbnail = arcade.load_texture(thumbnail)
        self.scale = scale
        self.cost = cost
        self.tower = tower
        if self.tower is None:
            self.tower = InstaAirTower()
        self.actively_selected = False


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.ORANGE)

        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.paused = False
        self.assets = {"locked_shop_item" : arcade.load_texture("images/locked.png")}

    def setup(self):
        arcade.set_background_color(arcade.color.ORANGE)
        self.wave_number = 0
        self.money = 500
        self.population = 10
        self.wave_is_happening = False
        self.next_wave_duration = 4.0
        self.current_wave_time = 0.0
        self.is_air_wave = False
        self.paused = False
        self.load_shop_items() # first index is page, second is position in page
        self.current_shop_tab = 0
        self.shop_item_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.load_map("./files/map1.txt")

    def load_shop_items(self):
        self.shop_listlist = [[ # start Combat towers
                ShopItem(is_unlocked=True, is_unlockable=False, # real
                        thumbnail="images/tower_round_converted.png", scale = 0.3,
                        cost=100, tower=WatchTower()), 
                ShopItem(is_unlocked=False, is_unlockable=True, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=200, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=500, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=650, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1000, tower=Tower())
            ], [ # start Sacred towers
                ShopItem(is_unlocked=True, is_unlockable=False, 
                        thumbnail="images/simple_tree.png", scale = 0.3,
                        cost=120, tower=OakTreeTower()), 
                ShopItem(is_unlocked=False, is_unlockable=True, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=180, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=400, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=650, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1000, tower=Tower())
            ], [ # start Buildings
                ShopItem(is_unlocked=False, is_unlockable=True, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=300, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=500, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=700, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1200, tower=Tower()), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1500, tower=Tower())
            ]]

    def load_map(self, filename):
        with open(filename, mode="r") as mapfile:
            map_string_list = mapfile.readlines()
        map_listlist = []
        k = 0
        for map_rowstr in map_string_list:
            map_rowlist = []
            for map_char in map_rowstr.rstrip():
                map_rowlist.append(GridCell(terrain_type=map_char, cellnum=k))
                k = k + 1
            map_listlist.append(map_rowlist)
        # last row is all-water for enemy targeting reasons
        last_rowlist = []
        for m in range(k, k+len(map_rowlist)):
            last_rowlist.append(GridCell(terrain_type="shallow", cellnum=m))
        map_listlist.append(last_rowlist)
        self.map_cells = map_listlist

    def on_draw(self): 
        arcade.start_render()
        self.draw_map()
        self.towers_list.draw()
        self.enemies_list.draw()
        self.projectiles_list.draw()

        for enemy in self.enemies_list.sprite_list:
            enemy.draw_health_bar()
            
        for tower in self.towers_list.sprite_list:
            if tower.do_show_range and not self.paused:
                self.draw_range(tower)
            if tower.animation_ontime_remaining > 0:
                tower.draw_shoot_animation()

        if ((self.shop_item_selected and not self.paused) and 
                (self._mouse_x <= MAP_WIDTH and self._mouse_y >= CHIN_HEIGHT)):
            self.preview_tower_placement(
                x=self._mouse_x, 
                y=self._mouse_y, 
                tower_shopitem=self.shop_listlist[self.current_shop_tab][self.shop_item_selected-1]
            )

        self.draw_chin_menu()
        self.draw_shop()

        if self.paused: 
            self.draw_pause_menu()
    
    # draw sub-methods used to make self.on_draw more legible
    def draw_map(self):
        # individual cells
        for i in range(len(self.map_cells)):
            for j in range(len(self.map_cells[i])):
                l, r, t, b = cell_lrtb(i, j)
                c = cell_color(self.map_cells[i][j].terrain_type)
                arcade.draw_lrtb_rectangle_filled(left=l, right=r, top=t, bottom=b, color=c)

    def draw_range(self, tower):
        arcade.draw_circle_filled(
            center_x=tower.center_x,
            center_y=tower.center_y,
            radius=tower.range, 
            color=arcade.make_transparent_color(arcade.color.SKY_BLUE, transparency=32.0)
        )
        arcade.draw_circle_outline(
            center_x=tower.center_x,
            center_y=tower.center_y,
            radius=tower.range, 
            color=arcade.make_transparent_color(arcade.color.SKY_BLUE, transparency=128.0), 
            border_width=2
        )
        arcade.draw_circle_outline(
            center_x=tower.center_x,
            center_y=tower.center_y,
            radius=tower.range-15, 
            color=arcade.make_transparent_color(arcade.color.SKY_BLUE, transparency=128.0), 
            border_width=2
        )

    def preview_tower_placement(self, x: float, y: float, tower_shopitem: ShopItem):
        center_x, center_y = nearest_cell_centerxy(x, y)
        fake_tower = tower_shopitem.tower.make_another()
        fake_tower.center_x = center_x
        fake_tower.center_y = center_y
        i, j = nearest_cell_ij(x, y)
        left, right, top, bottom = cell_lrtb(i, j)
        is_spot_available = ((self.map_cells[i][j].terrain_type == "ground") and 
                                (not self.map_cells[i][j].is_occupied))
        if is_spot_available:
            outline_color = arcade.color.GREEN
        else:
            outline_color = arcade.color.RED
        arcade.draw_lrtb_rectangle_filled(
            left=left, right=right, top=top, bottom=bottom, color=outline_color
        )
        self.draw_range(fake_tower)
        fake_tower.draw()

    def draw_chin_menu(self):
        # Background
        arcade.draw_lrtb_rectangle_filled(
            left   = 0, 
            right  = MAP_WIDTH,
            top    = CHIN_HEIGHT,
            bottom = 0,
            color=arcade.color.ORANGE
        )
        # attack button
        arcade.draw_lrtb_rectangle_filled(
            left   = MAP_WIDTH - ATK_BUTT_HEIGHT, 
            right  = MAP_WIDTH,
            top    = CHIN_HEIGHT,
            bottom = INFO_BAR_HEIGHT,
            color=arcade.color.RED
        )
        arcade.draw_text(
            text="START\nNEXT\nWAVE",
            start_x = MAP_WIDTH - ATK_BUTT_HEIGHT,
            start_y = CHIN_HEIGHT - ATK_BUTT_HEIGHT/3,
            font_size = 14,
            width = ATK_BUTT_HEIGHT,
            align = "center"
        )
        # info bar
        arcade.draw_text(
            text="Population: " + str(self.population),
            start_x = MAP_WIDTH/2,
            start_y = 0,
            font_size = 14,
            width = MAP_WIDTH/4,
            align = "left"
        )
        arcade.draw_text(
            text="Money: " + str(self.money),
            start_x = MAP_WIDTH*0.75,
            start_y = 0,
            font_size = 14,
            width = MAP_WIDTH/4,
            align = "right"
        )

    def draw_shop(self): 
        # backround
        if self.current_shop_tab == 0:
            shop_background_color = arcade.color.ORANGE
        elif self.current_shop_tab == 1:
            shop_background_color = arcade.color.PALE_BLUE
        else:
            shop_background_color = arcade.color.SADDLE_BROWN
        arcade.draw_lrtb_rectangle_filled(
            left   = MAP_WIDTH, 
            right  = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = 0,
            color=shop_background_color
        )
        # shop tabs
        arcade.draw_lrtb_rectangle_filled( # combat towers
            left  = MAP_WIDTH,
            right = SCREEN_WIDTH - (SCREEN_WIDTH-MAP_WIDTH)*2/3,
            top    = SCREEN_HEIGHT,
            bottom = SCREEN_HEIGHT - INFO_BAR_HEIGHT,
            color = arcade.color.ORANGE
        )
        arcade.draw_text( 
            "COMBAT", 
            start_x = MAP_WIDTH + 0, 
            start_y = SCREEN_HEIGHT - 15, 
            color = arcade.color.WHITE, 
            font_size = 11,
            bold = True
        )
        arcade.draw_lrtb_rectangle_filled( # sacred towers
            left  = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*1/3,
            right = SCREEN_WIDTH - (SCREEN_WIDTH-MAP_WIDTH)*1/3,
            top    = SCREEN_HEIGHT,
            bottom = SCREEN_HEIGHT - INFO_BAR_HEIGHT,
            color = arcade.color.PALE_BLUE
        )
        arcade.draw_text( 
            "SACRED", 
            start_x = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*1/3 + 0, 
            start_y = SCREEN_HEIGHT - 15, 
            color = arcade.color.WHITE, 
            font_size = 11,
            bold = True
        )
        arcade.draw_lrtb_rectangle_filled( # buildings
            left  = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*2/3,
            right = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = SCREEN_HEIGHT - INFO_BAR_HEIGHT,
            color = arcade.color.SADDLE_BROWN
        )
        arcade.draw_text( 
            "BUILDING", 
            start_x = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*2/3 + 0, 
            start_y = SCREEN_HEIGHT - 15, 
            color = arcade.color.WHITE, 
            font_size = 11,
            bold = True
        )
        # empty shop slots
        for k in range(0, 5):
            # background
            arcade.draw_lrtb_rectangle_filled(
                left  = MAP_WIDTH + 3,
                right = SCREEN_WIDTH - 3,
                top    = SHOP_TOPS[k],
                bottom = SHOP_BOTTOMS[k],
                color = arcade.color.BEIGE
            )
            # shop item, if it should be there
            shop_item = (self.shop_listlist[self.current_shop_tab][k])
            if shop_item.is_unlocked:
                arcade.draw_scaled_texture_rectangle( # draw the thumbnail
                    center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 2, 
                    center_y = 7 + SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2,
                    texture = shop_item.thumbnail,
                    scale = shop_item.scale
                )
                arcade.draw_text( # tower name
                    shop_item.tower.name, 
                    start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                    start_y = SHOP_TOPS[k] - 15, 
                    color = arcade.color.PURPLE, 
                    font_size = 12,
                    bold = True
                )
                arcade.draw_text( # tower description
                    shop_item.tower.description, 
                    start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                    start_y = SHOP_TOPS[k] - 28, 
                    width = 100,
                    color = arcade.color.BLACK, 
                    font_size = 10,
                    multiline = True
                ) 
                arcade.draw_text( # tower price
                    str(shop_item.cost), 
                    start_x = MAP_WIDTH + 4, 
                    start_y = SHOP_BOTTOMS[k] + 10, 
                    color = arcade.color.BLACK, 
                    font_size = 12,
                    bold = True
                )
                if shop_item.actively_selected:
                    arcade.draw_lrtb_rectangle_outline(
                        left = MAP_WIDTH + 2,
                        right = SCREEN_WIDTH - 2,
                        top = SHOP_TOPS[k] + 2,
                        bottom = SHOP_BOTTOMS[k] - 2,
                        color = arcade.color.BLUE_GREEN,
                        border_width = 4
                    )
            elif shop_item.is_unlockable:
                arcade.draw_scaled_texture_rectangle( # draw the little lock
                    center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 2, 
                    center_y = 7 + SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2,
                    texture = self.assets["locked_shop_item"],
                    scale = 0.2
                )
                arcade.draw_text( # tower name
                    "Task: " + shop_item.tower.name, 
                    start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                    start_y = SHOP_TOPS[k] - 15, 
                    color = arcade.color.BLACK, 
                    font_size = 12,
                    bold = True
                )
                arcade.draw_text( # tower quest
                    "Not yet implemented", 
                    start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                    start_y = SHOP_TOPS[k] - 28, 
                    color = arcade.color.BLACK, 
                    font_size = 10,
                )
            else : 
                arcade.draw_scaled_texture_rectangle( # draw the little lock
                    center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 2, 
                    center_y = SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2,
                    texture = self.assets["locked_shop_item"],
                    scale = 0.2
                )
 
    def draw_pause_menu(self):
        arcade.draw_lrtb_rectangle_filled(
            left   = 0, 
            right  = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = 0,
            color=arcade.make_transparent_color(arcade.color.DIM_GRAY, transparency=128.0)
        )
        arcade.draw_lrtb_rectangle_filled(
            left   = self.width/2  - 100, 
            right  = self.width/2  + 100,
            top    = self.height/2 + 50,
            bottom = self.height/2 - 50,
            color=arcade.color.ASH_GREY
        )
        arcade.draw_text(
            text="Paused",
            start_x = self.width/2 - 100,
            start_y = self.height/2 + 10,
            font_size = 28,
            width = 200,
            align = "center"
        )
        arcade.draw_text(
            text="Press Esc to resume",
            start_x = self.width/2 - 100,
            start_y = self.height/2 - 10,
            font_size = 16,
            width = 200,
            align = "center"
        )

    def on_update(self, delta_time: float):
        if self.paused:
            return
        ret = super().on_update(delta_time)

        # check if any shop item is selected
        # NOTE this logic could be done somewhere else...
        self.shop_item_selected = 0
        for n, item in enumerate(self.shop_listlist[self.current_shop_tab]):
            if item.actively_selected:
                self.shop_item_selected = n+1

        # check for projectile impacts
        for proj in self.projectiles_list.sprite_list:
            dx = proj.target_x - proj.center_x
            dy = proj.target_y - proj.center_y
            dist_from_target = sqrt(dx*dx + dy*dy)
            if dist_from_target < proj.speed/2:
                self.perform_impact(proj)

        # check if any enemies get kills
        for enemy in self.enemies_list.sprite_list:
            if enemy.center_y <= CHIN_HEIGHT - 0.4*CELL_SIZE:
                self.population -= 1
                enemy.remove_from_sprite_lists()

        # wave time management
        if self.wave_is_happening:
            # print("Wave time : " + str(self.current_wave_time))
            self.current_wave_time += delta_time
            if self.current_wave_time > self.next_wave_duration:
                self.wave_is_happening = False
                arcade.unschedule(self.add_enemy)
                self.next_wave_duration += 3.0
                self.current_wave_time = 0.0
                # print("Next wave will last for " + str(self.next_wave_duration))

        # underwater enemy hiding
        for enemy in self.enemies_list:
            if enemy.can_hide:
                i, j = nearest_cell_ij(enemy.center_x, enemy.center_y)
                if self.map_cells[i][j].terrain_type == "deep":
                    enemy.is_hidden = True
                    enemy.set_texture(1)
                else:
                    enemy.is_hidden = False
                    enemy.set_texture(0)

        # tower attacks
        # sort enemies by increasing Y (low Y = high priority target)
        self.enemies_list.sort(key= lambda enmy : enmy.position[1])
        for tower in self.towers_list.sprite_list:
            if tower.cooldown_remaining <= 0: # ready to fire
                for enemy in self.enemies_list.sprite_list:
                    if tower.can_see(enemy): # an attack happens
                        dmg, projlist = tower.attack(enemy)
                        earnings = enemy.take_damage_give_money(dmg)
                        self.money += earnings
                        for proj in projlist:
                            self.projectiles_list.append(proj)
                            self.all_sprites.append(proj)
                        # we found something to shoot, stop looping through enemies
                        break
            else : # not ready to fire
                tower.cooldown_remaining -= delta_time
                if tower.cooldown_remaining < 0.0:
                    tower.cooldown_remaining = 0.0

        # move and delete sprites if needed
        self.enemies_list.update()
        self.enemies_list.on_update(delta_time) 
        self.towers_list.update()
        self.towers_list.on_update(delta_time)
        self.projectiles_list.update()
        self.projectiles_list.on_update(delta_time)
        return ret
    
    def perform_impact(self, projectile: Projectile):
        if projectile.do_splash_damage:
            for enemy in self.enemies_list.sprite_list:
                if arcade.get_distance_between_sprites(projectile, enemy) < projectile.splash_radius:
                    earnings = enemy.take_damage_give_money(damage=projectile.damage)
                    self.money += earnings
        else:
            if projectile.target is None:
                return
            earnings = projectile.target.take_damage_give_money(projectile.damage)
            self.money += earnings
        projectile.remove_from_sprite_lists()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            if self.paused:
                self.paused = False
                if self.wave_is_happening:
                    arcade.schedule(self.add_enemy, interval=2.0)
            else:
                self.paused = True
                if self.wave_is_happening:
                    arcade.unschedule(self.add_enemy)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.paused:
            return
        if (x > MAP_WIDTH) or (y < CHIN_HEIGHT): # we did not just place a tower
            self.unselect_all_shop_items()
        else: # we clicked inside the map
            # were we trying to place a new tower ?
            self.attempt_tower_place(x, y)  
        # Next Wave Start Button
        if (MAP_WIDTH-ATK_BUTT_HEIGHT < x < MAP_WIDTH) and (INFO_BAR_HEIGHT < y < CHIN_HEIGHT):
            if not self.wave_is_happening:
                self.wave_is_happening = True
                self.is_air_wave = randint(0, 1)
                arcade.schedule(self.add_enemy, interval=2.0)
        # Shop tab change
        elif (x > MAP_WIDTH) and (y >= SHOP_TOPS[0]): 
            if x <= MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)/3:
                self.current_shop_tab = 0
            elif x > SCREEN_WIDTH - (SCREEN_WIDTH-MAP_WIDTH)/3:
                self.current_shop_tab = 2
            else:
                self.current_shop_tab = 1
        # Shop item selection
        elif (x > MAP_WIDTH) and (y >= SHOP_BOTTOMS[-1]): 
            for k in range(0, 5):
                shop_item = self.shop_listlist[self.current_shop_tab][k]
                if SHOP_BOTTOMS[k] <= y <= SHOP_TOPS[k]:
                    shop_item.actively_selected = True

        return super().on_mouse_press(x, y, button, modifiers)

    def attempt_tower_place(self, x:float, y:float):
        # check if area is OK to place towers 
        i, j = nearest_cell_ij(x, y)
        center_x, center_y = nearest_cell_centerxy(x, y)
        is_spot_available = ((self.map_cells[i][j].terrain_type == "ground") and 
                                (not self.map_cells[i][j].is_occupied))
        if not is_spot_available:
            return

        # check if a tower is selected and is affordable
        for k in range(0, 5):
            shop_item = self.shop_listlist[self.current_shop_tab][k]
            is_item_buyable = (shop_item.actively_selected and self.money >= shop_item.cost)
            if is_item_buyable:
                self.money -= shop_item.cost
                new_tower = shop_item.tower.make_another()
                new_tower.center_x = center_x
                new_tower.center_y = center_y
                self.towers_list.append(new_tower)
                self.all_sprites.append(new_tower)
                self.unselect_all_shop_items()
                self.map_cells[i][j].is_occupied = True

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ret = super().on_mouse_motion(x, y, dx, dy)
        if not self.shop_item_selected:
            # loop over towers to show any relevant ranges
            for tower in self.towers_list.sprite_list:
                tower.do_show_range = ((tower.left < x < tower.right) and (tower.bottom < y < tower.top))
        return ret

    def add_enemy(self, delta_time : float):
        if self.is_air_wave:
            enemy = Dragon()
            enemy.bottom = SCREEN_HEIGHT
            enemy.left = randint(0, floor(MAP_WIDTH-enemy.width))
            enemy.velocity = (0, -1)
        else:
            if randint(0,1):
                enemy = BigWhale()
            else:
                enemy = TinyBoat()
            enemy.bottom = SCREEN_HEIGHT
            enemy.center_x, _ = cell_centerxy(i=0, j=4)
            enemy.velocity = (0, -1)
            enemy.calc_path(map=self.map_cells)
            # ANCHOR
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def unselect_all_shop_items(self):
        for m in range(0, 3):
            for shop_item in self.shop_listlist[m]:
                shop_item.actively_selected = False


# misc grid helper functions
def cell_lrtb(i: int, j: int):
    """Converts a cell's coordinates (as defined by its cell_listlist[i][j] indices)
    into on-screen coordinates of its left, right, top and bottom edges"""
    left = j * CELL_SIZE
    right = left + (CELL_SIZE-1)
    top = SCREEN_HEIGHT - (i * CELL_SIZE)
    bottom = top - (CELL_SIZE-1)
    return left, right, top, bottom

def cell_color(terrain_type:str):
    if (terrain_type == "ground") or (terrain_type == "g"):
        return arcade.color.BRONZE
    if (terrain_type == "shallow") or (terrain_type == "s"):
        return arcade.color.BLUE
    if (terrain_type == "deep") or (terrain_type == "d"):
        return arcade.color.DARK_BLUE
    return arcade.color.HOT_PINK # anime pigeon guy : is this error handling ? 

def nearest_cell_ij(x: float, y:float):
    j = int(x // CELL_SIZE)
    # y increases from CHIN_HEIGHT to SCREEN_HEIGHT along the upwards-vertical map axis
    # we need a variable that decreases along upwards-vertical axis, like i (column index) does.
    reverse_y = SCREEN_HEIGHT - y 
    i = int(reverse_y // CELL_SIZE)
    i = max(i, 0)
    j = max(j, 0)
    i = min(14, i)
    j = min(14, j)
    return i, j

def cell_centerxy(i: int, j:int):
    center_x = (j+0.5)*CELL_SIZE - 1
    center_y = SCREEN_HEIGHT - (i+0.5)*CELL_SIZE + 1
    return center_x, center_y

def nearest_cell_centerxy(x: float, y:float):
    i, j = nearest_cell_ij(x, y)
    return cell_centerxy(i, j)

def is_in_cell(sprite: arcade.Sprite, i: float, j:float):
    left, right, top, bottom = cell_lrtb(i, j)
    if left <= sprite.center_x < right:
        if bottom <= sprite.center_y < top:
            return True
    return False


if __name__ == "__main__":
    app = GameWindow()
    app.setup()
    arcade.run()

# TODO next step :

# Roadmap items : 
# vfx for exploding
# wave system overhaul
# next wave preview
# smoother trajectories for floating enemies
# shop challenges to unlock more towers
# massive texture overhaul
# 2x2 towers
# enchants
# special abilities
# floating enemies re-calc their path when a platform is placed
# info box with tower stats