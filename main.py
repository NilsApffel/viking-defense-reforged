import arcade
import random
import math as m

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600
MAP_WIDTH = 500
MAP_HEIGHT = 500
CHIN_HEIGHT = SCREEN_HEIGHT-MAP_HEIGHT
INFO_BAR_HEIGHT = 20
ATK_BUTT_HEIGHT = CHIN_HEIGHT-INFO_BAR_HEIGHT
SCREEN_TITLE = "Viking Defense Reforged v0.0.1 Dev"
RADIUS = 150
SCALING = 1.0 # this does nothing as far as I can tell

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        arcade.set_background_color(arcade.color.ORANGE)

        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.paused = False

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

        if self.paused: # Pause Window
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
                    if distance <= tower.range:
                        tower.cooldown_remaining = tower.cooldown
                        # instakill 
                        # self.money += enemy.reward
                        # enemy.remove_from_sprite_lists()
                        # not instakill
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
        # Next Wave Start Button
        if (MAP_WIDTH-ATK_BUTT_HEIGHT < x < MAP_WIDTH) and (INFO_BAR_HEIGHT < y < CHIN_HEIGHT):
            if not self.wave_is_happening:
                self.wave_is_happening = True
                arcade.schedule(self.add_enemy, interval=2.0)

        return super().on_mouse_press(x, y, button, modifiers)

    def add_enemy(self, delta_time : float):
        enemy = Dragon()
        enemy.bottom = SCREEN_HEIGHT
        enemy.left = random.randint(0, m.floor(MAP_WIDTH-enemy.width))
        enemy.velocity = (0, -1)
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)


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
    def __init__(self, filename: str = None, scale: float = 1, cooldown: float = 2, range: float = 100, damage: float = 5):
        super().__init__(filename=filename, scale=scale)
        self.cooldown = cooldown
        self.cooldown_remaining = 0.0
        self.range = range
        self.damage = damage

class InstaAirTower(Tower):
    def __init__(self):
        super().__init__(filename="images/tower_round_converted.png", scale=0.5, cooldown=1.0, range=100, damage=1)


if __name__ == "__main__":
    app = GameWindow()
    app.setup()
    arcade.run()

# TODO
# Roadmap : 
# vfx for shooting and exploding
# hover over tower to see range
# shop texture
# place more towers
# map split into blocks which each have a type (land, water, deepwater) and occupancy state
# map texture and associated properties
# next wave preview
# wave system overhaul
# projectiles
# floating enemies with land collision and path-finding