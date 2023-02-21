import os, sys
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
import arcade
from random import randint, random
from math import floor, sqrt
from copy import deepcopy
import csv
from constants import *
from grid import *
from enemies import *
from towers import *
from waves import Wave
from shop import ShopItem
from abilities import *

SCREEN_TITLE = "Viking Defense Reforged v0.2.6 Dev"


def init_outlined_text(text, start_x, start_y, font_size=13, font_name="impact"):
    """Creates and returns a list of 5 arcade.Text objects with the given properties. 
    When drawn together, these 5 objects create an outlined text effect."""
    black = arcade.color.BLACK
    text_objects_list = [
        arcade.Text(text, start_x=start_x-1, start_y=start_y, font_size=font_size, 
                        font_name=font_name, color=black), 
        arcade.Text(text, start_x=start_x+1, start_y=start_y, font_size=font_size, 
                        font_name=font_name, color=black),
        arcade.Text(text, start_x=start_x, start_y=start_y-1, font_size=font_size, 
                        font_name=font_name, color=black),
        arcade.Text(text, start_x=start_x, start_y=start_y+1, font_size=font_size, 
                        font_name=font_name, color=black),
        arcade.Text(text, start_x=start_x, start_y=start_y, font_size=font_size, 
                        font_name=font_name)]
    return text_objects_list

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.ORANGE)
        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.effects_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.paused = False
        self.assets = {
            "locked_shop_item" : arcade.load_texture("images/locked.png"), 
            "attack_button" : arcade.load_texture('./images/NextWaveButton.png'),
            "attack_button_lit" : arcade.load_texture('./images/NextWaveButtonLit.png'),
            "attack_button_grey" : arcade.load_texture('./images/NextWaveButtonGrey.png'),
            "level_select_screen" : arcade.load_texture('./images/LevelSelectBlank.png'),
            "abilities_bar" : arcade.load_texture('./images/Abilities.png')
        }
        self.read_score_file()
        self.init_text()
        self.abilities_list = [SellTowerAbility(), MjolnirAbility(), None, None, None]

    def read_score_file(self):
        self.best_waves = []
        maps_unlocked = 0
        if not os.path.exists(SCORE_FILE):
            # print(SCORE_FILE, "does not appear to exist, assuming this is a new install of the game")
            self.maps_beaten = 0
            self.best_waves = [0] * 5
            return
        with open(SCORE_FILE, mode='r') as scorefile:
            score_reader = csv.reader(scorefile, delimiter=',', quotechar='|')
            next(score_reader) # skip header
            for map_data in score_reader:
                is_map_unlocked = (map_data[1] == "True")
                most_waves_survived = int(map_data[3])
                self.best_waves.append(most_waves_survived)
                if is_map_unlocked:
                    maps_unlocked += 1
        self.maps_beaten = maps_unlocked - 1

    def setup(self, map_number: int = 1):
        arcade.set_background_color(arcade.color.ORANGE)
        self.map_number = map_number
        self.read_score_file()
        self.wave_is_happening = False
        self.hover_target = '' # used to store what UI element is being moused over, if any
        if map_number == 0: # level select screen
            self.game_state = 'level select'
            self.paused = True
            return
        self.game_state = 'playing'
        self.wave_number = 0
        self.money = 500
        self.population = 10
        self.enemies_left_to_spawn = 0
        self.next_enemy_index = 0
        self.is_air_wave = False
        self.paused = False
        self.load_shop_items() # first index is page, second is position in page
        self.current_shop_tab = 0
        self.shop_item_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.ability_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.abilities_unlocked = [True, False, False, False, False]
        self.load_map("./files/map"+str(map_number)+".txt")
        self.load_waves("./files/map"+str(map_number)+"CampaignWaves.csv")
        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.effects_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()

    def load_shop_items(self):
        self.shop_listlist = [[ # start Combat towers
                ShopItem(is_unlocked=True, is_unlockable=False, 
                        thumbnail="images/tower_round_converted.png", scale = 0.3,
                        cost=100, tower=WatchTower()), 
                ShopItem(is_unlocked=False, is_unlockable=True, # real
                        thumbnail="images/catapult_cool.png", scale = 1,
                        cost=200, tower=Catapult(), quest="Destroy 10 enemies", 
                        quest_thresh=10, quest_var_name="enemies killed"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=500, tower=Tower(), quest="Destroy 25 flying enemies", 
                        quest_thresh=25, quest_var_name="flying enemies killed"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=650, tower=Tower(), quest="Place 10 platforms", 
                        quest_thresh=10, quest_var_name="platforms placed"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1000, tower=Tower(), quest="Inflame 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies inflamed")
            ], [ # start Sacred towers
                ShopItem(is_unlocked=True, is_unlockable=False, 
                        thumbnail="images/simple_tree.png", scale = 0.3,
                        cost=120, tower=OakTreeTower()), 
                ShopItem(is_unlocked=False, is_unlockable=True, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=180, tower=Tower(), quest="Plant 5 Sacred Oaks", 
                        quest_thresh=5, quest_var_name="current oaks"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=400, tower=Tower(), quest="Destroy 4 enemies with 1 mjolnir", 
                        quest_thresh=4, quest_var_name="max mjolnir kills"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=650, tower=Tower(), quest="Destroy 3 submerged enemies", 
                        quest_thresh=3, quest_var_name="submerged enemies killed"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1000, tower=Tower(), quest="Freeze 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies frozen")
            ], [ # start Buildings
                ShopItem(is_unlocked=False, is_unlockable=True, # real
                        thumbnail="images/ThorTempleThumb.png", scale = 1,
                        cost=300, tower=TempleOfThor(), quest="Destroy 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies killed"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=500, tower=Tower(), quest="Build 15 structures", 
                        quest_thresh=15, quest_var_name="current structures"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=700, tower=Tower(), quest="Enchant 12 towers with runes", 
                        quest_thresh=12, quest_var_name="current enchanted towers"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1200, tower=Tower(), quest="Reach 3000 gold", 
                        quest_thresh=3000, quest_var_name="current gold"), 
                ShopItem(is_unlocked=False, is_unlockable=False, # placeholder
                        thumbnail="images/question.png", scale = 0.3,
                        cost=1500, tower=Tower(), quest="Build 3 temples", 
                        quest_thresh=3, quest_var_name="current temples")
            ]]
        
        self.quest_tracker = {
            "enemies killed": 0, "flying enemies killed": 0, "submerged enemies killed": 0,
            "enemies inflamed": 0, "enemies frozen": 0, "platforms placed": 0,
            "max mjolnir kills": 0, "current oaks": 0, "current temples": 0, 
            "current structures": 0, "current enchanted towers": 0, "current gold": 0, 
            "_" : None # tracker used for pre-unlocked towers
        }

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

        # check which cells are safe for spawning floating enemies
        self.spawnable_cell_js = []
        for j in range(len(self.map_cells[0])):
            if ((self.map_cells[0][j].terrain_type == "shallow") or 
                (self.map_cells[0][j].terrain_type == "deep")):
                self.spawnable_cell_js.append(j)

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

    def init_text(self):
        """Initializes all text objects in order to avoid ever using draw_text, which has 
        terrible performance"""

        # 1. Permanently static text using outlined font
        combat_tab = init_outlined_text(
            "COMBAT", 
            start_x = MAP_WIDTH + 6, 
            start_y = SCREEN_HEIGHT - 19, 
            font_size = 13,
            font_name="impact"
        )
        sacred_tab = init_outlined_text(
            "SACRED", 
            start_x = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*1/3 + 8, 
            start_y = SCREEN_HEIGHT - 19, 
            font_size = 13,
            font_name="impact"
        )
        building_tab = init_outlined_text(
            "BUILDING", 
            start_x = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*2/3 + 3, 
            start_y = SCREEN_HEIGHT - 19, 
            font_size = 13,
            font_name="impact"
        )
        activities_title = init_outlined_text(
            text = "ABILITIES",
            font_name= "impact",
            start_x = MAP_WIDTH + 80,
            start_y= 48,
            font_size = 13
        )
        self.multi_layer_text = {"combat_tab": combat_tab, 
                                    "sacred_tab": sacred_tab,
                                    "building_tab": building_tab,
                                    "abilities_title": activities_title}
        
        # 2. Info box text
        title_text = arcade.Text(
            '', 
            start_x = MAP_WIDTH + 14, 
            start_y = SHOP_BOTTOMS[-1] - 88, 
            color = arcade.color.PURPLE, 
            font_size = 12,
            bold = True
        )
        stats_text = arcade.Text(
            '', 
            start_x = MAP_WIDTH + 14, 
            start_y = SHOP_BOTTOMS[-1] - 104, 
            width = SCREEN_WIDTH - MAP_WIDTH - 28,
            color = arcade.color.BLACK, 
            font_size = 12,
            multiline = True, 
            font_name="Agency FB" 
        ) 
        description_text = arcade.Text( 
            '', 
            start_x = MAP_WIDTH + 14, 
            start_y = SHOP_BOTTOMS[-1] - 146, 
            width = SCREEN_WIDTH - MAP_WIDTH - 28,
            color = arcade.color.BLACK, 
            font_size = 12,
            multiline = True, 
            font_name="Agency FB" 
        ) 
        self.info_box_text = [title_text, stats_text, description_text]

        # 3. Next wave previews
        self.wave_previews_text = []
        for k in range(2):
            wave_title = arcade.Text(
                text = '',
                start_x = 17+(WAVE_VIEWER_WIDTH+15)*k,
                start_y = CHIN_HEIGHT - 28,
                color = arcade.color.PURPLE,
                font_size = 11,
                width = WAVE_VIEWER_WIDTH,
                bold = True, 
                # font_name = "Agency FB" 
            )
            wave_content = arcade.Text(
                text = '',
                start_x = 17+(WAVE_VIEWER_WIDTH+15)*k,
                start_y = CHIN_HEIGHT - 45,
                color = arcade.color.BLACK,
                font_size = 10,
                width = WAVE_VIEWER_WIDTH,
                bold = True,
                multiline = True,
                # font_name = "Agency FB" 
            )
            self.wave_previews_text.append([wave_title, wave_content])

        # 4. Misc chin menu items
        self.population_counter_text = arcade.Text(
            text="Population: " ,
            start_x = MAP_WIDTH/2,
            start_y = 3,
            font_size = 14,
            width = MAP_WIDTH/4,
            align = "left"
        )
        self.money_counter_text = arcade.Text(
            text="Money: ",
            start_x = MAP_WIDTH*0.75,
            start_y = 3,
            font_size = 14,
            width = MAP_WIDTH/4,
            align = "right"
        )

        # 5. Shop
        self.shop_text = []
        for k in range(5):
            name = arcade.Text(
                '', 
                start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                start_y = SHOP_TOPS[k] - 15, 
                color = arcade.color.PURPLE, 
                font_size = 12,
                bold = True
            )
            description = arcade.Text(
                '', 
                start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 4, 
                start_y = SHOP_TOPS[k] - 34, 
                width = 200,
                color = arcade.color.BLACK, 
                font_size = 12,
                multiline = True, 
                # may require using e.g. arcade.load_font('./agencyfb.ttf') 
                # for cross-platform compatibility
                font_name="Agency FB" 
            ) 
            price = arcade.Text(
                '', 
                start_x = MAP_WIDTH + 4, 
                start_y = SHOP_BOTTOMS[k] + 10, 
                color = arcade.color.BLACK, 
                font_size = 12,
                bold = True
            )
            quest_progress = arcade.Text( 
                '', 
                start_x = MAP_WIDTH + 100, 
                start_y = SHOP_BOTTOMS[k] + 4, 
                color = arcade.color.BLACK, 
                font_size = 12,
                bold = True, 
                align="right", 
                width=115
            )
            self.shop_text.append({'name': name, 'description': description, 
                                   'price': price, 'quest progress': quest_progress})

    def on_draw(self): 
        arcade.start_render()
        if self.game_state == 'level select':
            self.draw_level_select()
            return   
        self.draw_map()
        self.towers_list.draw()
        self.enemies_list.draw()
        self.projectiles_list.draw()

        for enemy in self.enemies_list.sprite_list:
            enemy.draw_effects()
            enemy.draw_health_bar()
            
        if not self.paused:
            for k, tower in enumerate(self.towers_list.sprite_list):
                if self.hover_target == "tower:"+str(k):
                    self.draw_range(tower)
                if tower.animation_ontime_remaining > 0:
                    tower.draw_shoot_animation()

        self.effects_list.draw()

        if ((not self.paused) and (self._mouse_x <= MAP_WIDTH and self._mouse_y >= CHIN_HEIGHT)):
            if self.shop_item_selected:
                self.preview_tower_placement(
                    x=self._mouse_x, 
                    y=self._mouse_y, 
                    tower_shopitem=self.shop_listlist[self.current_shop_tab][self.shop_item_selected-1]
                )
            elif self.ability_selected:
                k = self.ability_selected - 1
                self.abilities_list[k].preview(x=self._mouse_x, y=self._mouse_y)

        self.draw_chin_menu()
        self.draw_shop()
        self.draw_info_box()
        self.draw_abilities_bar()

        if self.paused: 
            self.draw_pause_menu()
    
    # draw sub-methods used to make self.on_draw more legible
    def draw_map(self):
        # individual cells
        for i in range(len(self.map_cells)-1):
            for j in range(len(self.map_cells[i])):
                l, r, t, b = cell_lrtb(i, j)
                c = cell_color(self.map_cells[i][j].terrain_type)
                arcade.draw_lrtb_rectangle_filled(left=l, right=r, top=t, bottom=b, color=c)

    def draw_range(self, tower):
        if tower.is_2x2:
            return
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

        if fake_tower.is_2x2:
            fake_tower.center_x += CELL_SIZE/2
            fake_tower.center_y -= CELL_SIZE/2
            right += CELL_SIZE
            bottom -= CELL_SIZE
            for ii in range(i, i+2):
                for jj in range(j, j+2):
                    if ((0 <= ii <= 14) and (0 <= jj <= 14)):
                        if ((self.map_cells[ii][jj].terrain_type != "ground") or 
                                (self.map_cells[ii][jj].is_occupied)):
                            is_spot_available = False
                    else:
                        is_spot_available = False  
            
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
        # Wave previews
        for k in range(2):
            # background 
            arcade.draw_lrtb_rectangle_filled(
                left   = 15+(WAVE_VIEWER_WIDTH+15)*k, 
                right  = 15+(WAVE_VIEWER_WIDTH+15)*k + WAVE_VIEWER_WIDTH,
                top    = CHIN_HEIGHT - 10,
                bottom = INFO_BAR_HEIGHT + 2,
                color=arcade.color.BEIGE
            )
            # add preview of waves, if there are still waves left
            if self.wave_number+1-k < len(self.wave_list):
                self.wave_previews_text[k][0].text = 'Attack #'+str(self.wave_number+2-k)+'/'+str(len(self.wave_list))
                self.wave_previews_text[k][1].text = self.wave_list[self.wave_number+1-k].describe()
            else:
                self.wave_previews_text[k][0].text = ''
                self.wave_previews_text[k][1].text = ''
            for txt in self.wave_previews_text[k]:
                txt.draw()
                
        # attack button
        texture = self.assets['attack_button']
        if self.wave_is_happening:
            texture = self.assets['attack_button_grey']
        elif self.hover_target == 'attack_button' and not self.paused:
            texture = self.assets['attack_button_lit']
        arcade.draw_scaled_texture_rectangle(
            center_x = MAP_WIDTH - 5 - ATK_BUTT_HEIGHT/2,
            center_y = INFO_BAR_HEIGHT + 2 + ATK_BUTT_HEIGHT/2,
            scale = 1.0,
            texture = texture
        )
        # info bar
        self.population_counter_text.text = "Population: " + str(self.population)
        self.population_counter_text.draw()
        self.money_counter_text.text = "Money: " + str(self.money)
        self.money_counter_text.draw()

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
        arcade.draw_lrtb_rectangle_filled( # sacred towers
            left  = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*1/3,
            right = SCREEN_WIDTH - (SCREEN_WIDTH-MAP_WIDTH)*1/3,
            top    = SCREEN_HEIGHT,
            bottom = SCREEN_HEIGHT - INFO_BAR_HEIGHT,
            color = arcade.color.PALE_BLUE
        )
        arcade.draw_lrtb_rectangle_filled( # buildings
            left  = MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)*2/3,
            right = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = SCREEN_HEIGHT - INFO_BAR_HEIGHT,
            color = arcade.color.SADDLE_BROWN
        )
        for txt in self.multi_layer_text['combat_tab']:
            txt.draw()
        for txt in self.multi_layer_text['sacred_tab']:
            txt.draw()
        for txt in self.multi_layer_text['building_tab']:
            txt.draw()

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
                    center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 2 + 0.5, 
                    center_y = 7 + SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2 + 0.5,
                    texture = shop_item.thumbnail,
                    scale = shop_item.scale
                )
                self.shop_text[k]['name'].text = shop_item.tower.name
                self.shop_text[k]['description'].text = shop_item.tower.description
                self.shop_text[k]['price'].text = str(shop_item.cost)
                self.shop_text[k]['quest progress'].text = ''
                for txt in self.shop_text[k].values():
                    txt.draw()
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
                self.shop_text[k]['name'].text = "Task: " + shop_item.tower.name
                self.shop_text[k]['description'].text = shop_item.quest
                self.shop_text[k]['price'].text = ''
                self.shop_text[k]['quest progress'].text = str(shop_item.quest_progress) + '/' + str(shop_item.quest_thresh)
                for txt in self.shop_text[k].values():
                    txt.draw()
            else : 
                arcade.draw_scaled_texture_rectangle( # draw the little lock
                    center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 2, 
                    center_y = SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2,
                    texture = self.assets["locked_shop_item"],
                    scale = 0.2
                )
 
    def draw_info_box(self):
        arcade.draw_lrtb_rectangle_filled( # background
            left = MAP_WIDTH + 12,
            right = SCREEN_WIDTH - 12,
            top = SHOP_BOTTOMS[-1] - 68,
            bottom = SHOP_BOTTOMS[-1] - 172, 
            color = arcade.color.BEIGE
        )
        # shop item, if relevant
        if 'shop' in self.hover_target:
            k = int(self.hover_target.split(':')[-1])
            if k < 9:
                tower = self.shop_listlist[self.current_shop_tab][k].tower
                self.info_box_text[0].text = tower.name
                self.info_box_text[1].text = tower.describe_damage()
                self.info_box_text[2].text = tower.description
        elif 'tower' in self.hover_target:
            k = int(self.hover_target.split(':')[-1])
            tower = self.towers_list.sprite_list[k]
            self.info_box_text[0].text = tower.name
            self.info_box_text[1].text = tower.describe_damage()
            self.info_box_text[2].text = tower.description
        elif 'ability' in self.hover_target:
            k = int(self.hover_target.split(':')[-1])
            self.info_box_text[0].text = ABILITY_NAMES[k]
            self.info_box_text[1].text = ABILITY_DESCRIPTIONS[k]
            self.info_box_text[2].text = ''
        else:
            self.info_box_text[0].text = ''
            self.info_box_text[1].text = ''
            self.info_box_text[2].text = ''

        for txt in self.info_box_text:
            txt.draw()
        
    def draw_abilities_bar(self):
        arcade.draw_scaled_texture_rectangle(
            center_x = floor((SCREEN_WIDTH - MAP_WIDTH) / 2) + MAP_WIDTH + 0.5,
            center_y = 24.5,
            texture = self.assets["abilities_bar"],
            scale = 1.0 
        )
        for txt in self.multi_layer_text['abilities_title']:
            txt.draw()

        for k in range(5):
            if self.abilities_unlocked[k]:
                self.abilities_list[k].draw_icon(
                    x = MAP_WIDTH + 7 + k*42 + 20.5,
                    y = 24.5
                )

        # test of the lrtb coords of different ability buttons
        if self.ability_selected > 0:
            k = self.ability_selected - 1
            arcade.draw_lrtb_rectangle_outline(
                left = MAP_WIDTH + 7 + k*42,
                right = MAP_WIDTH + 7 + k*42 + 40,
                top = 44,
                bottom = 4,
                color = arcade.color.BLUE,
                border_width = 2
            )

    def draw_pause_menu(self):

        popup_color = arcade.color.ASH_GREY
        popup_title = 'Paused'
        popup_subtext = 'Press Esc to resume'
        popup_subsubtext = 'Press SPACE to exit'
        if self.game_state == 'won':
            popup_color = arcade.color.FERN_GREEN
            popup_title = 'You Win !'
            popup_subtext = 'Waves survived: '+str(self.wave_number)
        elif self.game_state == 'lost':
            popup_color = arcade.color.DARK_RED
            popup_title = 'Game Over'
            popup_subtext = 'Waves survived: '+str(self.wave_number-1)

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
            start_x = self.width/2 - 125,
            start_y = self.height/2 - 15,
            font_size = 16,
            width = 250,
            align = "center"
        )
        arcade.draw_text(
            text=popup_subsubtext,
            start_x = self.width/2 - 100,
            start_y = self.height/2 - 35,
            font_size = 12,
            width = 200,
            align = "center", 
            italic = True
        )

    def draw_level_select(self):
        arcade.draw_scaled_texture_rectangle(
            center_x=SCREEN_WIDTH/2, 
            center_y=SCREEN_HEIGHT/2,
            texture=self.assets["level_select_screen"], 
            scale=1.0
        ) 
        for k in range(5):
            campaign_mode_label = "LOCKED"
            if k <= self.maps_beaten:
                campaign_mode_label = "PLAY"
            else:
                arcade.draw_lrtb_rectangle_filled(
                    left = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + 5,
                    right= LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH - 2,
                    top=435,
                    bottom= 320, 
                    color=arcade.make_transparent_color(arcade.color.DIM_GRAY, transparency=230.0)
                )
            if ("start campaign" in self.hover_target) and (self.hover_target[-1] == str(k+1)):
                arcade.draw_lrtb_rectangle_outline(
                    left = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k,
                    right= LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH,
                    top=313,
                    bottom= 278, 
                    color=arcade.color.BLACK,
                    border_width=3
                )
            arcade.draw_text(
                text = campaign_mode_label, 
                start_x = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k,
                start_y = 284,
                color = arcade.color.BLACK,
                font_size = 20,
                width = LEVEL_WIDTH,
                align = "center", 
                bold = True
            )
            arcade.draw_text(
                text = "Waves survived:\n" + str(self.best_waves[k]), 
                start_x = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k,
                start_y = 215,
                color = arcade.color.BLACK,
                font_size = 11,
                width = LEVEL_WIDTH,
                align = "center", 
                bold = True, 
                multiline = True
            )
                
    def on_update(self, delta_time: float):
        if is_debug and not self.paused:
            pass

        if self.paused or self.game_state == 'won' or self.game_state == 'lost':
            self.paused = True
            return
        ret = super().on_update(delta_time)

        # check if any shop item is selected
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

        self.perform_enemy_actions()
        self.perform_tower_attacks(delta_time=delta_time)
        self.update_wave_progress(delta_time=delta_time)
        self.update_quests()
        self.update_abilities(delta_time=delta_time)

        # move and delete sprites if needed
        self.enemies_list.update()
        self.enemies_list.on_update(delta_time) 
        self.towers_list.update()
        self.towers_list.on_update(delta_time)
        self.projectiles_list.update()
        self.projectiles_list.on_update(delta_time)
        self.effects_list.update()
        self.effects_list.on_update(delta_time)

        # check for loss condition
        if self.population <= 0:
            self.paused = True
            self.game_state = 'lost'
            self.update_score_file(self.map_number, self.wave_number-1, did_win=False)
        # check for win condition
        elif self.wave_number >= len(self.wave_list) and not self.wave_is_happening:
            self.paused = True
            self.game_state = 'won'
            self.update_score_file(self.map_number, self.wave_number, did_win=True)

        return ret
    
    def update_abilities(self, delta_time: float):
        # update cooldowns
        for ability in self.abilities_list:
            if not (ability is None):
                ability.on_update(delta_time)
        # update unlocks
        thor_temples = 0
        for tower in self.towers_list.sprite_list:
            if tower.name == "Temple of Thor":
                thor_temples += 1
        self.abilities_unlocked[1] = (thor_temples > 0) or is_debug

    def perform_enemy_actions(self):
        # check if any enemies get kills
        for enemy in self.enemies_list.sprite_list:
            if enemy.center_y <= CHIN_HEIGHT - 0.4*CELL_SIZE:
                self.population -= 1
                enemy.remove_from_sprite_lists()

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
    
    def update_wave_progress(self, delta_time: float):
        if self.wave_is_happening:
            # spawn next enemy, if needed, and decrement enemies_left_to_spawn
            if self.enemies_left_to_spawn > 0:
                if random() < delta_time: # decide to spawn new enemy
                    new_enemy = self.wave_list[self.wave_number-1].spawn(self.next_enemy_index)
                    new_enemy.bottom = SCREEN_HEIGHT
                    if new_enemy.is_flying:
                        new_enemy.left = randint(0, floor(MAP_WIDTH-new_enemy.width))
                    else:
                        test_j = 99
                        while not (test_j in self.spawnable_cell_js):
                            test_j = randint(0, len(self.map_cells[0]))
                        new_enemy.center_x, _ = cell_centerxy(i=0, j=test_j)
                        new_enemy.calc_path(map=self.map_cells)
                    self.enemies_list.append(new_enemy)
                    self.all_sprites.append(new_enemy)
                    self.enemies_left_to_spawn -= 1
                    self.next_enemy_index += 1
            # check if wave is over 
            elif self.enemies_left_to_spawn == 0 and len(self.enemies_list.sprite_list) == 0:
                self.wave_is_happening = False

    def perform_tower_attacks(self, delta_time: float):
        # sort enemies by increasing priority (low priority will be attacked first)
        self.enemies_list.sort(key= lambda enmy : enmy.priority)
        for tower in self.towers_list.sprite_list:  
            for enemy in self.enemies_list.sprite_list:
                if tower.can_see(enemy): 
                    # we found something to target, stop looping through enemies
                    tower.aim_to(enemy)
                    if tower.cooldown_remaining <= 0: # ready to fire
                        # an attack happens
                        dmg, projlist = tower.attack(enemy)
                        earnings = enemy.take_damage_give_money(dmg)
                        self.money += earnings
                        # deal with projectiles created by tower.attack()
                        for proj in projlist: 
                            self.projectiles_list.append(proj)
                            self.all_sprites.append(proj)
                        # increment quest trackers
                        if earnings > 0:
                            self.quest_tracker["enemies killed"] += 1
                            if enemy.is_flying:
                                self.quest_tracker["flying enemies killed"] += 1
                            elif enemy.is_hidden:
                                self.quest_tracker["submerged enemies killed"] += 1
                    else : # not ready to fire
                        tower.cooldown_remaining -= delta_time
                        if tower.cooldown_remaining < 0.0:
                            tower.cooldown_remaining = 0.0
                    break # only do this for the first enemy each tower can see
            else: # tower did not see any enemy (break was not reached)
                tower.cooldown_remaining -= delta_time
                if tower.cooldown_remaining < 0.0:
                    tower.cooldown_remaining = 0.0

    def perform_impact(self, projectile: Projectile):
        if projectile.do_splash_damage:
            projectile_kills = 0
            current_enemies = len(self.enemies_list.sprite_list)
            for k in range(current_enemies):
                enemy = self.enemies_list.sprite_list[current_enemies-1-k]
                dx = (enemy.center_x-projectile.target_x)
                dy = (enemy.center_y-projectile.target_y)
                dist = sqrt(dx**2 + dy**2)
                if dist <= projectile.splash_radius:
                    earnings = enemy.take_damage_give_money(damage=projectile.damage)
                    self.money += earnings
                    # increment quest trackers
                    if earnings > 0:
                        projectile_kills += 1
                        self.quest_tracker["enemies killed"] += 1
                        if enemy.is_flying:
                            self.quest_tracker["flying enemies killed"] += 1
                        elif enemy.is_hidden:
                            self.quest_tracker["submerged enemies killed"] += 1
            if projectile.damage == 100: # this is a mjolnir
                if projectile_kills > self.quest_tracker["max mjolnir kills"]:
                    self.quest_tracker["max mjolnir kills"] = projectile_kills
        else:
            if projectile.target is None:
                return
            earnings = projectile.target.take_damage_give_money(projectile.damage)
            self.money += earnings
            # increment quest trackers
            if earnings > 0:
                self.quest_tracker["enemies killed"] += 1
                if projectile.target.is_flying:
                    self.quest_tracker["flying enemies killed"] += 1
                elif projectile.target.is_hidden:
                    self.quest_tracker["submerged enemies killed"] += 1
        if not (projectile.impact_effect is None):
            explosion = deepcopy(projectile.impact_effect)
            explosion.center_x = projectile.target_x
            explosion.center_y = projectile.target_y
            self.effects_list.append(explosion)
            self.all_sprites.append(explosion)
        projectile.remove_from_sprite_lists()

    def update_score_file(self, map_number: int, waves_survived: int, did_win: bool):
        # read the entire file
        scores_listlist = []
        file_to_open = SCORE_FILE
        if not os.path.exists(SCORE_FILE):
            print(SCORE_FILE, "does not appear to exist, will create a new one")
            # read the score file that is inside the executable (corresponding to a brand new game)
            file_to_open = "./files/scores.csv"
        
        with open(file_to_open, mode='r') as scorefile:
            score_reader = csv.reader(scorefile, delimiter=',', quotechar='|')
            for map_data in score_reader:
                scores_listlist.append(map_data)

        # overwrite the relevant waves_survived, and possibly the is_unlocked of the next map
        if waves_survived > int(scores_listlist[map_number][3]):
            scores_listlist[map_number][3] = str(waves_survived)
        if did_win:
            scores_listlist[map_number][2] = True
            if map_number < len(scores_listlist)-1:
                scores_listlist[map_number+1][1] = True

        if not os.path.isdir(SCORE_FOLDER):
            os.makedirs(SCORE_FOLDER)
        # write file
        with open(SCORE_FILE, mode='w') as scorefile:
            score_writer = csv.writer(scorefile, delimiter=',', quotechar='|', lineterminator='\n')
            score_writer.writerows(scores_listlist)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            if self.paused and self.game_state == 'playing':
                self.paused = False
            else:
                self.paused = True
        elif self.paused and symbol == arcade.key.SPACE: 
            # return to level select
            self.setup(map_number=0)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        # 0. Deal with level selection and paused state
        if self.game_state == 'level select':
            # check if we pressed a "play" button for any map
            if 278 <= y <= 313:
                for k in range(5):
                    left  = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k
                    right = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH
                    if left <= x <= right: 
                        if k <= self.maps_beaten:
                            self.setup(map_number=k+1) 
                            return super().on_mouse_press(x, y, button, modifiers)
        if self.paused:
            return
        
        # 1. Deal with tower placement and abilities
        if (x > MAP_WIDTH) or (y < CHIN_HEIGHT): # we did not just place a tower
            self.unselect_all_items()
        else: # we clicked inside the map
            # were we trying to place / sell a tower ?
            if not self.ability_selected:
                self.attempt_tower_place(x, y)  
            elif self.ability_selected == 1:
                self.attempt_tower_sell(x, y)
            elif self.ability_selected == 2:
                if self.abilities_list[1].cooldown_remaining <= 0.01:
                    mjolnir = self.abilities_list[1].trigger(x, y)
                    self.projectiles_list.append(mjolnir)
                    self.all_sprites.append(mjolnir)
                    self.ability_selected = 0
            
        # 2. Deal with button clicks 
        # 2.1 Next Wave Start Button
        if (MAP_WIDTH-ATK_BUTT_HEIGHT-5 < x < MAP_WIDTH-5) and (INFO_BAR_HEIGHT+2 < y < CHIN_HEIGHT-10):
            if not self.wave_is_happening:
                self.wave_is_happening = True
                self.wave_number += 1
                self.enemies_left_to_spawn = len(self.wave_list[self.wave_number-1].enemies_list)
                self.next_enemy_index = 0
        # 2.2 Shop tab change
        elif (x > MAP_WIDTH) and (y >= SHOP_TOPS[0]): 
            if x <= MAP_WIDTH + (SCREEN_WIDTH-MAP_WIDTH)/3:
                self.current_shop_tab = 0
            elif x > SCREEN_WIDTH - (SCREEN_WIDTH-MAP_WIDTH)/3:
                self.current_shop_tab = 2
            else:
                self.current_shop_tab = 1
        # 2.3 Shop item selection
        elif (x > MAP_WIDTH) and (y >= SHOP_BOTTOMS[-1]): 
            for k in range(0, 5):
                shop_item = self.shop_listlist[self.current_shop_tab][k]
                if SHOP_BOTTOMS[k] <= y <= SHOP_TOPS[k]:
                    if shop_item.is_unlocked:
                        shop_item.actively_selected = True
        # 2.4 Ability selection 
        elif (MAP_WIDTH < x) and (4 <= y <= 44): 
            for k in range(0, 5):
                left = MAP_WIDTH + 7 + k*42
                right = MAP_WIDTH + 7 + k*42 + 40
                if left <= x <= right:
                    if self.abilities_unlocked[k] and self.abilities_list[k].cooldown_remaining < 0.01:
                        self.ability_selected = k+1

        return super().on_mouse_press(x, y, button, modifiers)

    def attempt_tower_place(self, x:float, y:float):
        # check if a tower is selected and is affordable
        is_item_buyable = False
        for k in range(0, 5):
            shop_item = self.shop_listlist[self.current_shop_tab][k]
            is_item_buyable = (shop_item.actively_selected and self.money >= shop_item.cost)
            if is_item_buyable:
                break
        if not is_item_buyable:
            return
        # if we reach this line, then there exists a selected, affordable ShopItem named shop_item
                
        # check if area is OK to place towers 
        i, j = nearest_cell_ij(x, y)
        center_x, center_y = nearest_cell_centerxy(x, y)
        is_spot_available = ((self.map_cells[i][j].terrain_type == "ground") and 
                                (not self.map_cells[i][j].is_occupied))
        if shop_item.tower.is_2x2: # additional checks for large towers
            center_x += CELL_SIZE/2
            center_y -= CELL_SIZE/2
            for ii in range(i, i+2):
                for jj in range(j, j+2):
                    if ((0 <= ii <= 14) and (0 <= jj <= 14)):
                        if ((self.map_cells[ii][jj].terrain_type != "ground") or 
                                (self.map_cells[ii][jj].is_occupied)):
                            is_spot_available = False
                    else:
                        is_spot_available = False 
        if not is_spot_available:
            return
        # if we reach this line, it means shop_item is a selected and affordable tower that is
        # hovering over an available location
        
        # buy and place the shop_item
        self.money -= shop_item.cost
        new_tower = shop_item.tower.make_another()
        new_tower.center_x = center_x
        new_tower.center_y = center_y
        self.towers_list.append(new_tower)
        self.all_sprites.append(new_tower)
        self.map_cells[i][j].is_occupied = True
        if new_tower.is_2x2:
            self.map_cells[i+1][j].is_occupied = True
            self.map_cells[i][j+1].is_occupied = True
            self.map_cells[i+1][j+1].is_occupied = True

    def attempt_tower_sell(self, x: float, y: float):
        i, j = nearest_cell_ij(x, y)
        if not self.map_cells[i][j].is_occupied:
            return
        
        # if we reach this line, then the cell is occupied by a 1x1 or 2x2 tower
        for tower in self.towers_list.sprite_list:
            if tower.is_2x2: # we'll deal with 2x2 towers later
                continue
            ti, tj = nearest_cell_ij(tower.center_x, tower.center_y)
            if (i == ti) and (j == tj):
                # found the tower
                price = self.find_tower_price(tower.name)
                self.money += int(floor(price/2))
                self.map_cells[i][j].is_occupied = False
                tower.remove_from_sprite_lists()
                return
            
        # if we reach this line, then the cell is occupied by a 2x2 tower
        for tower in self.towers_list.sprite_list:
            if not tower.is_2x2:
                continue
            ti, tj = nearest_cell_ij(tower.center_x-CELL_SIZE/2, tower.center_y+CELL_SIZE/2)
            if (ti <= i <= ti+1) and (tj <= j <= tj+1):
                # found the tower
                price = self.find_tower_price(tower.name)
                self.money += int(floor(price/2))
                self.map_cells[ti][tj].is_occupied = False
                self.map_cells[ti+1][tj].is_occupied = False
                self.map_cells[ti][tj+1].is_occupied = False
                self.map_cells[ti+1][tj+1].is_occupied = False
                tower.remove_from_sprite_lists()
                return

    def find_tower_price(self, tower_name):
        for shop_list in self.shop_listlist:
            for shop_item in shop_list:
                if shop_item.tower.name == tower_name:
                    return shop_item.cost

    def update_quests(self):
        # 1. update the state-based quests in the self.quest_tracker
        # (event-based quests are updated wherever the relevant events happen)
        temples = 0
        oaks = 0
        for tower in self.towers_list.sprite_list:
            if "temple" in tower.name.lower():
                temples += 1
            elif tower.name == "Sacred Oak":
                oaks += 1
        self.quest_tracker["current oaks"] = oaks
        self.quest_tracker["current_temples"] = temples
        self.quest_tracker["current structures"] = len(self.towers_list.sprite_list)
        self.quest_tracker["current gold"] = self.money

        # 2. use self.quest_tracker to update each shopitem and perform unlocks
        for shop_list in self.shop_listlist:
            for k, shop_item in enumerate(shop_list):
                if shop_item.is_unlockable:
                    shop_item.quest_progress = self.quest_tracker[shop_item.quest_var_name]
                    if ((shop_item.quest_progress >= shop_item.quest_thresh) and 
                        not(shop_item.tower.name == "Example Tower")):
                        shop_item.is_unlocked = True
                        shop_item.is_unlockable = False
                        if k < len(shop_list) - 1: # there exists a next item
                            shop_list[k+1].is_unlockable = True

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ret = super().on_mouse_motion(x, y, dx, dy)
        self.hover_target = ''

        # 0. Deal with level select screen
        if self.game_state == "level select":
            # check if we are over a "play" button for any map
            if 278 <= y <= 313:
                for k in range(5):
                    left  = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k
                    right = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH
                    if left <= x <= right: 
                        if k <= self.maps_beaten:
                            self.hover_target = "start campaign " + str(k+1)
            return ret

        # 1. Are we hovering over a shop item ?
        if (x > MAP_WIDTH) and (y >= SHOP_BOTTOMS[-1]): 
            for k in range(0, 5):
                shop_item = self.shop_listlist[self.current_shop_tab][k]
                if SHOP_BOTTOMS[k] <= y <= SHOP_TOPS[k]:
                    if shop_item.is_unlockable or shop_item.is_unlocked:
                        self.hover_target = 'shop:' + str(self.current_shop_tab) + ':' + str(k)
                        return ret
        
        # 2. Are we hovering over an ability ?
        if (MAP_WIDTH < x) and (4 <= y <= 44):
            for k in range(5):
                left = MAP_WIDTH + 7 + k*42
                right = MAP_WIDTH + 7 + k*42 + 40
                if left <= x <= right:
                    if self.abilities_unlocked[k]:
                        self.hover_target = 'ability:' + str(k)
                        return ret
                
        # 3. Are we hovering over the attack button ?
        if (MAP_WIDTH-ATK_BUTT_HEIGHT-5 < x < MAP_WIDTH-5) and (INFO_BAR_HEIGHT+2 < y < CHIN_HEIGHT-10):
            self.hover_target = 'attack_button'
            return ret

        # 4. Is there a shopitem or ability previously selected ?
        if 0 < self.shop_item_selected < 9:
            self.hover_target = 'shop:' + str(self.current_shop_tab) + ':' + str(self.shop_item_selected-1)
            return ret
        if 0 < self.ability_selected < 9:
            self.hover_target = 'ability:' + str(self.ability_selected-1)
            return ret
        
        # 5. Are we mousing over a tower sprite on the map ?
        if (x < MAP_WIDTH) and (CHIN_HEIGHT < y):
            for k, tower in enumerate(self.towers_list.sprite_list):
                if ((tower.left < x < tower.right) and (tower.bottom < y < tower.top)):
                    self.hover_target = 'tower:'+str(k)
                    return ret
                
        return ret

    def unselect_all_items(self):
        for m in range(0, 3):
            for shop_item in self.shop_listlist[m]:
                shop_item.actively_selected = False
        self.ability_selected = 0
        self.shop_item_selected = 0


if __name__ == "__main__":
    app = GameWindow()
    app.setup(map_number=0)
    arcade.run()

# TODO next step : 

# Roadmap items : 
# high quality mjolnir explosion
# abilities and shop items get highlighted on mouse-over
# score calculation
# vfx for enemies exploding
# wave system compatible with infinite free-play
# free-play mode
# smoother trajectories for floating enemies
# more maps
# more towers
# massive texture overhaul
# enchants
# platform ability
# floating enemies re-calc their path when a platform is placed
