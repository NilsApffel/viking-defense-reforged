import arcade
from random import randint, random
from math import floor, sqrt
import csv
from constants import *
from grid import *
from enemies import *
from towers import *

SCREEN_TITLE = "Viking Defense Reforged v0.1.0 Dev"


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


class Wave():
    def __init__(self, number, modifier, rank, type1, quant1, type2, quant2, type3, quant3) -> None:
        self.number = int(number)
        rnk = int(rank)
        try:
            q1 = int(quant1)
        except:
            q1 = 0
        try:
            q2 = int(quant2)
        except:
            q2 = 0
        try:
            q3 = int(quant3)
        except:
            q3 = 0
        
        self.enemies_list = []
        for k in range(q1):
            self.enemies_list.append((modifier, rnk, type1))
        for k in range(q2):
            self.enemies_list.append((modifier, rnk, type2))
        for k in range(q3):
            self.enemies_list.append((modifier, rnk, type3))
        
    def spawn(self, enemy_index: int) -> Enemy:
        enemy_type_name = self.enemies_list[enemy_index][2]
        if 'flying' in enemy_type_name:
            if 'tiny' in enemy_type_name:
                enemy = TinyBird()
            elif 'small' in enemy_type_name:
                enemy = SmallShip()
            elif 'medium' in enemy_type_name:
                enemy = MediumDragon()
            elif 'big' in enemy_type_name:
                enemy = BigDragon()
        else:
            if 'tiny' in enemy_type_name:
                enemy = TinyBoat()
            elif 'small' in enemy_type_name:
                enemy = SmallSnake()
            elif 'medium' in enemy_type_name:
                enemy = MediumBoat()
            elif 'big' in enemy_type_name:
                enemy = BigWhale()
        return enemy
        

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
        self.game_state = 'playing'
        self.wave_number = 0
        self.money = 500
        self.population = 10
        self.wave_is_happening = False
        self.enemies_left_to_spawn = 0
        self.next_enemy_index = 0
        self.current_wave_time = 0.0
        self.is_air_wave = False
        self.paused = False
        self.load_shop_items() # first index is page, second is position in page
        self.current_shop_tab = 0
        self.shop_item_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.load_map("./files/map1.txt")
        self.load_waves("./files/map1CampaignWaves.csv")

    def load_shop_items(self):
        self.shop_listlist = [[ # start Combat towers
                ShopItem(is_unlocked=True, is_unlockable=False, # real
                        thumbnail="images/tower_round_converted.png", scale = 0.3,
                        cost=100, tower=WatchTower()), 
                ShopItem(is_unlocked=True, is_unlockable=False, # real but should be locked
                        thumbnail="images/catapult_cool.png", scale = 0.6,
                        cost=200, tower=Catapult()), 
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

    def load_waves(self, filename):
        self.wave_list = []
        with open(filename, mode='r', newline='') as csvfile:
            wave_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            next(wave_reader) # skip header
            for row in wave_reader:
                self.wave_list.append(Wave(
                    number=row[0], 
                    modifier=row[1],
                    rank=row[2],
                    type1=row[3],
                    quant1=row[4],
                    type2=row[5], 
                    quant2=row[6], 
                    type3=row[7],
                    quant3=row[8]
                ))

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
                    width = 200,
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

        popup_color = arcade.color.ASH_GREY
        popup_title = 'Paused'
        popup_subtext = 'Press Esc to resume'
        if self.game_state == 'won':
            popup_color = arcade.color.FERN_GREEN
            popup_title = 'You Win !'
            popup_subtext = 'Waves survived: '+str(self.wave_number)
        elif self.game_state == 'lost':
            popup_color = arcade.color.DARK_RED
            popup_title = 'Game Over'
            popup_subtext = 'Waves survived: '+str(self.wave_number)

        arcade.draw_lrtb_rectangle_filled( # dim screen
            left   = 0, 
            right  = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = 0,
            color=arcade.make_transparent_color(arcade.color.DIM_GRAY, transparency=128.0)
        )
        arcade.draw_lrtb_rectangle_filled( # Message background
            left   = self.width/2  - 100, 
            right  = self.width/2  + 100,
            top    = self.height/2 + 50,
            bottom = self.height/2 - 50,
            color=popup_color
        )
        arcade.draw_text(
            text=popup_title,
            start_x = self.width/2 - 100,
            start_y = self.height/2 + 10,
            font_size = 28,
            width = 200,
            align = "center"
        )
        arcade.draw_text(
            text=popup_subtext,
            start_x = self.width/2 - 100,
            start_y = self.height/2 - 10,
            font_size = 16,
            width = 200,
            align = "center"
        )

    def on_update(self, delta_time: float):
        if self.paused or self.game_state == 'won' or self.game_state == 'lost':
            self.paused = True
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

        # wave management
        if self.wave_is_happening:
            self.current_wave_time += delta_time
            # spawn next enemy, if needed, and decrement enemies_left_to_spawn
            if self.enemies_left_to_spawn > 0:
                if random() < delta_time: # decide to spawn new enemy
                    new_enemy = self.wave_list[self.wave_number-1].spawn(self.next_enemy_index)
                    new_enemy.bottom = SCREEN_HEIGHT
                    new_enemy.velocity = (0, -1)
                    if new_enemy.is_flying:
                        new_enemy.left = randint(0, floor(MAP_WIDTH-new_enemy.width))
                    else:
                        new_enemy.center_x, _ = cell_centerxy(i=0, j=randint(0,4))
                        new_enemy.calc_path(map=self.map_cells)
                    self.enemies_list.append(new_enemy)
                    self.all_sprites.append(new_enemy)
                    self.enemies_left_to_spawn -= 1
                    self.next_enemy_index += 1
            # check if wave is over 
            elif self.enemies_left_to_spawn == 0 and len(self.enemies_list.sprite_list) == 0:
                self.wave_is_happening = False

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

        # check for loss condition
        if self.population <= 0:
            self.paused = True
            self.game_state = 'lost'
        # check for win condition
        elif self.wave_number >= len(self.wave_list) and not self.wave_is_happening:
            self.paused = True
            self.game_state = 'won'
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
            if self.paused and self.game_state == 'playing':
                self.paused = False
            else:
                self.paused = True

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
                self.current_wave_time = 0.0
                self.wave_number += 1
                self.enemies_left_to_spawn = len(self.wave_list[self.wave_number-1].enemies_list)
                self.next_enemy_index = 0
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

    def unselect_all_shop_items(self):
        for m in range(0, 3):
            for shop_item in self.shop_listlist[m]:
                shop_item.actively_selected = False


if __name__ == "__main__":
    app = GameWindow()
    app.setup()
    arcade.run()

# TODO next step :

# Roadmap items : 
# catapult visual improvements
# better tower targeting priorities that don't just rely on y-position
# find a bolder but narrower font for text
# vfx for exploding
# wave system compatible with infinite free-play
# next wave preview
# smoother trajectories for floating enemies
# shop challenges to unlock more towers
# massive texture overhaul
# 2x2 towers
# enchants
# special abilities
# floating enemies re-calc their path when a platform is placed
# info box with tower stats