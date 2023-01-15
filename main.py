import arcade
import random
import math as m
from copy import copy, deepcopy

# there's probably a better way than gloabl variables to handle all this sizing...
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600
MAP_WIDTH = 480
MAP_HEIGHT = 480
CHIN_HEIGHT = SCREEN_HEIGHT-MAP_HEIGHT
INFO_BAR_HEIGHT = 20
ATK_BUTT_HEIGHT = CHIN_HEIGHT-INFO_BAR_HEIGHT
SHOP_ITEM_HEIGHT = 62
SHOP_ITEM_THUMB_SIZE = 40
SCREEN_TITLE = "Viking Defense Reforged v0.0.2 Dev"
SCALING = 1.0 # this does nothing as far as I can tell
SHOP_TOPS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k for k in range(0, 5)]
SHOP_BOTTOMS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k - SHOP_ITEM_HEIGHT for k in range(0, 5)]

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        arcade.set_background_color(arcade.color.ORANGE)

        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.paused = False

        # first index is page, second is position in page
        self.shop_listlist = [[ShopItem()] * 5] * 3
        # TODO build out the actual shopitems
        # as long as there are empty/boilerplate shop items, the unlock progression will misbehave
        self.shop_listlist[0][0] = ShopItem(
            is_unlocked=True, 
            is_unlockable=False,
            thumbnail="images/tower_round_converted.png", 
            scale = 0.3,
            cost=100,
            tower=InstaAirTower()
        )
        self.shop_listlist[0][1].is_unlockable = True
        self.shop_listlist[1][0].is_unlockable = True
        self.shop_listlist[2][0].is_unlockable = True
        self.current_shop_tab = 0
        self.assets = {"locked_shop_item" : arcade.load_texture("images/locked.png")}

    def setup(self):
        arcade.set_background_color(arcade.color.ORANGE)

        first_tower = InstaAirTower()
        first_tower.center_y = SCREEN_HEIGHT / 2
        first_tower.center_x = MAP_WIDTH / 2
        self.towers_list.append(first_tower)
        self.all_sprites.append(first_tower) 
        self.wave_number = 0
        self.money = 500
        self.population = 10
        self.wave_is_happening = False
        self.next_wave_duration = 4.0
        self.current_wave_time = 0.0

    def on_draw(self): 
        # NOTE : consider moving much of this into methods to make it more readable/scrollable
        arcade.start_render()
        
        # Map
        arcade.draw_lrtb_rectangle_filled(
            left   = 0, 
            right  = MAP_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = CHIN_HEIGHT,
            color=arcade.color.NAVY_BLUE
        )

        self.all_sprites.draw()
        for enemy in self.enemies_list.sprite_list:
            enemy.draw_health_bar()
        for tower in self.towers_list.sprite_list:
            if tower.do_show_range:
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

        #chin and ear covers
        arcade.draw_lrtb_rectangle_filled(
            left   = 0, 
            right  = MAP_WIDTH,
            top    = CHIN_HEIGHT,
            bottom = 0,
            color=arcade.color.ORANGE
        )
        arcade.draw_lrtb_rectangle_filled(
            left   = MAP_WIDTH, 
            right  = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = 0,
            color=arcade.color.ORANGE
        )

        # Chin menu
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

        # side menu / shop
        # tabs are TODO
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
            shop_item = (self.shop_listlist[self.current_shop_tab][k]) # ANCHOR
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

        if self.paused: # Pause Window
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

        # check if any enemies get kills
        for enemy in self.enemies_list.sprite_list:
            if enemy.center_y < CHIN_HEIGHT - 0.5*enemy.height:
                self.population -= 1

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

        # tower attacks
        # sort enemies by increasing Y (low Y = high priority target)
        self.enemies_list.sort(key= lambda enmy : enmy.position[1])
        for tower in self.towers_list.sprite_list:
            if tower.cooldown_remaining <= 0: # ready to fire
                for enemy in self.enemies_list.sprite_list:
                    distance = arcade.sprite.get_distance_between_sprites(tower, enemy)
                    if distance <= tower.range: # an attack happens
                        tower.cooldown_remaining = tower.cooldown
                        enemy.current_health -= tower.damage
                        if enemy.current_health <= 0:
                            self.money += enemy.reward
                            enemy.remove_from_sprite_lists()
                        # we found something to shoot, stop looping through enemies
                        break
            else : # not ready to fire
                tower.cooldown_remaining -= delta_time
                if tower.cooldown_remaining < 0.0:
                    tower.cooldown_remaining = 0.0

        # move and delete spirtes if needed
        self.enemies_list.update()
        self.towers_list.update()
        return ret
    

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
        if (x > MAP_WIDTH) or (y < CHIN_HEIGHT): # we did not just place a tower
            self.unselect_all_shop_items()
        # Next Wave Start Button
        if (MAP_WIDTH-ATK_BUTT_HEIGHT < x < MAP_WIDTH) and (INFO_BAR_HEIGHT < y < CHIN_HEIGHT):
            if not self.wave_is_happening:
                self.wave_is_happening = True
                arcade.schedule(self.add_enemy, interval=2.0)
        # Shop item selection
        elif (x > MAP_WIDTH) and (y >= SHOP_BOTTOMS[-1]): 
            for k in range(0, 5):
                shop_item = self.shop_listlist[self.current_shop_tab][k]
                if SHOP_BOTTOMS[k] <= y <= SHOP_TOPS[k]:
                    shop_item.actively_selected = True

        return super().on_mouse_press(x, y, button, modifiers)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ret = super().on_mouse_motion(x, y, dx, dy)
        # loop over towers to show any relevant ranges
        for tower in self.towers_list.sprite_list:
            tower.do_show_range = ((tower.left < x < tower.right) and (tower.bottom < y < tower.top))
        return ret

    def add_enemy(self, delta_time : float):
        enemy = Dragon()
        enemy.bottom = SCREEN_HEIGHT
        enemy.left = random.randint(0, m.floor(MAP_WIDTH-enemy.width))
        enemy.velocity = (0, -1)
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def unselect_all_shop_items(self):
        for m in range(0, 3):
            for shop_item in self.shop_listlist[m]:
                shop_item.actively_selected = False


class Enemy(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, reward: float = 30):
        super().__init__(filename, scale)
        self.current_health = health
        self.max_health = health
        self.reward = reward

    def draw_health_bar(self):
        barheight = 4
        barwidth = self.max_health * 4
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

    def update(self):
        if self.center_y < CHIN_HEIGHT - 0.5*self.height:
            self.remove_from_sprite_lists()
        super().update()


class FlyingEnemy(Enemy):
    def __init__(self, filename: str = None, scale: float = 1, health: float = 4, reward: float = 30):
        super().__init__(filename=filename, scale=scale, health=health, reward=reward)


class Dragon(FlyingEnemy):
    def __init__(self):
        super().__init__(filename="images/dragon.png", scale=0.5, health=4, reward=30)


class Tower(arcade.Sprite):
    def __init__(self, filename: str = None, scale: float = 1, cooldown: float = 2, 
                    range: float = 100, damage: float = 5, do_show_range: bool = False, 
                    name: str = None, description: str = None):
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


class InstaAirTower(Tower):
    def __init__(self):
        super().__init__(filename="images/tower_round_converted.png", scale=0.5, cooldown=1.0, 
                            range=100, damage=1, name="Arrow Tower", 
                            description="Fires at flying\nNever misses")


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


if __name__ == "__main__":
    app = GameWindow()
    app.setup()
    arcade.run()

# TODO next step : ability to buy and place more towers

# Roadmap items : 
# vfx for shooting and exploding
# shop tabs
# map split into blocks which each have a type (land, water, deepwater) and occupancy state
# map texture and associated properties
# towers clip to blocks
# wave system overhaul
# next wave preview
# projectiles
# floating enemies with land collision and path-finding
# make tower sprites square and top-viewed
# shop challenges to unlock more towers
# massive texture overhaul
# enchants
# special abilities
# info box with tower stats