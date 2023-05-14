import csv, os, sys
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
import arcade
from copy import deepcopy
from math import floor, atan2, pi
from random import randint, random
from abilities import MjolnirAbility, SellTowerAbility, PlatformAbility, CommandAbility, HarvestAbility
from constants import *
from enemies import Enemy
from explosions import AirExplosion, WaterExplosion
from grid import *
from projectiles import Projectile
from runes import Raidho, Hagalaz, Tiwaz, Kenaz, Isa, Sowil, Laguz
from shop import ShopItem
from towers import (Tower, WatchTower, Catapult, FalconCliff, Bastion, GreekFire,
                    OakTreeTower, StoneHead, SparklingPillar, QuarryOfRage, SanctumOfTempest,
                    TempleOfThor, Forge, TempleOfOdin, ChamberOfTheChief, TempleOfFreyr)
from utils import timestr
from waves import Wave, WaveMaker


SCREEN_TITLE = "Viking Defense Reforged v0.7.3 Dev"


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
        arcade.set_background_color((255, 255, 255))
        self.enemies_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.effects_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()
        self.map_shape_list = arcade.ShapeElementList()
        self.platforms = arcade.SpriteList()
        self.all_health_bars = arcade.SpriteList()
        self.enemy_effects = arcade.SpriteList()
        self.gui_elements = arcade.SpriteList()
        self.paused = False
        self.assets = {
            "attack_button" : arcade.load_texture('./images/NextWaveButton.png'),
            "attack_button_lit" : arcade.load_texture('./images/NextWaveButtonLit.png'),
            "attack_button_grey" : arcade.load_texture('./images/NextWaveButtonGrey.png'),
            "level_select_screen" : arcade.load_texture('./images/LevelSelectBlank.png'),
            'info_box' : arcade.load_texture('./images/info_box.png'),
            'chin_menu' : arcade.load_texture('./images/chin_menu.png'),
            'shop_buildings' : arcade.load_texture('./images/shop_buildings.png'),
            'shop_combat' : arcade.load_texture('./images/shop_combat.png'),
            'shop_sacred' : arcade.load_texture('./images/shop_sacred.png'),
        }
        self.read_score_file()
        self.abilities_list = [SellTowerAbility(), MjolnirAbility(), PlatformAbility(), CommandAbility(), HarvestAbility()]
        self.runes_list = [Raidho(), Hagalaz(), Tiwaz(), Kenaz(), Isa(), Sowil(), Laguz()]
        if is_debug:
            self.perf_graph = arcade.PerfGraph(width=80, height=80, background_color=TRANSPARENT_BLACK)
            self.perf_graph.center_x = 40
            self.perf_graph.center_y = SCREEN_HEIGHT - 40

        self.range_preview = arcade.Sprite()
        self.range_preview.append_texture(load_texture('./images/TowerRange.png'))
        self.range_preview.append_texture(load_texture('./images/AbilityRange.png'))
        self.range_preview.set_texture(0)
        self.water_shimmer_ind = 0 
        self.water_shimmer_timer = 0.04

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
        if self.best_waves[-1] >= 70:
            self.maps_beaten += 1

    def setup(self, map_number: int = 1, is_freeplay: bool = False):
        self.map_number = map_number
        self.map_water_static = None
        self.map_water_animation = None
        self.map_land = None
        self.is_freeplay = is_freeplay
        self.read_score_file()
        self.wave_is_happening = False
        if self.is_freeplay:
            self.wave_maker = WaveMaker()
        else:
            self.wave_maker = None
        self.hover_target = '' # used to store what UI element is being moused over, if any
        if map_number == 0: # level select screen
            self.game_state = 'level select'
            self.paused = True
            return
        self.game_state = 'playing'
        self.wave_number = 0
        self.money = 500 + 1500*is_debug
        self.population = 10
        self.enemies_left_to_spawn = 0
        self.next_enemy_index = 0
        self.is_air_wave = False
        self.time_to_next_spawn = 1.0
        self.paused = False
        self.load_shop_items() # first index is page, second is position in page
        self.current_shop_tab = 0
        self.shop_item_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.rune_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.ability_selected = 0 # 0 if none selected, otherwise index+1 of selection
        self.runes_unlocked = [False, False, False, False, False, False, False]
        self.abilities_unlocked = [True, False, False, False, False]
        self.map_shape_list = arcade.ShapeElementList()
        self.load_map("./files/map"+str(map_number)+".txt")
        self.load_waves("./files/map"+str(map_number)+"CampaignWaves.csv")
        self.platforms = arcade.SpriteList()
        self.all_health_bars = arcade.SpriteList()
        self.enemy_effects = arcade.SpriteList()
        self.enemies_list = arcade.SpriteList()
        self.swimmers_list = arcade.SpriteList()
        self.flyers_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.projectiles_list = arcade.SpriteList()
        self.effects_list = arcade.SpriteList()
        self.water_explosions_list = arcade.SpriteList()
        self.init_gui_elements()
        self.all_sprites = arcade.SpriteList()    
        self.time_to_next_wave = 75 if self.map_number < 5 else 60 # seconds
        self.init_text()

    def load_shop_items(self):
        self.shop_listlist = [[ # start Combat towers
                ShopItem(is_unlocked=True, is_unlockable=False, 
                        thumbnail="images/WatchtowerThumb.png",
                        cost=100, tower=WatchTower()), 
                ShopItem(is_unlocked=is_debug, is_unlockable=True,
                        thumbnail="images/catapult_cool.png",
                        cost=200, tower=Catapult(), quest="Destroy 10 enemies", 
                        quest_thresh=10, quest_var_name="enemies killed"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False, 
                        thumbnail="images/FalconCliffThumb.png",
                        cost=500, tower=FalconCliff(), quest="Destroy 25 flying enemies", 
                        quest_thresh=25, quest_var_name="flying enemies killed"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False,
                        thumbnail="images/BastionThumb.png",
                        cost=650, tower=Bastion(), quest="Place 10 platforms", 
                        quest_thresh=10, quest_var_name="platforms placed"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False, 
                        thumbnail="images/GreekFireThumb.png",
                        cost=1000, tower=GreekFire(), quest="Inflame 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies inflamed")
            ], [ # start Sacred towers
                ShopItem(is_unlocked=True, is_unlockable=False, 
                        thumbnail="images/SacredOakThumb.png",
                        cost=120, tower=OakTreeTower()), 
                ShopItem(is_unlocked=is_debug, is_unlockable=True, 
                        thumbnail="images/StoneHeadThumb.png",
                        cost=180, tower=StoneHead(), quest="Plant 5 Sacred Oaks", 
                        quest_thresh=5, quest_var_name="current oaks"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False, 
                        thumbnail="images/SparklingPillarThumb.png",
                        cost=400, tower=SparklingPillar(), quest="Destroy 4 enemies with 1\nmjolnir", 
                        quest_thresh=4, quest_var_name="max mjolnir kills"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False,
                        thumbnail="images/QuarryOfRageThumb.png",
                        cost=650, tower=QuarryOfRage(), quest="Destroy 3 submerged enemies", 
                        quest_thresh=3, quest_var_name="submerged enemies killed"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False,
                        thumbnail="images/SanctumOfTempestThumb.png",
                        cost=1000, tower=SanctumOfTempest(), quest="Freeze 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies frozen")
            ], [ # start Buildings
                ShopItem(is_unlocked=is_debug, is_unlockable=True,
                        thumbnail="images/ThorTempleThumb.png",
                        cost=300, tower=TempleOfThor(), quest="Destroy 20 enemies", 
                        quest_thresh=20, quest_var_name="enemies killed"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False,
                        thumbnail="images/ForgeThumb.png",
                        cost=500, tower=Forge(), quest="Build 15 structures", 
                        quest_thresh=15, quest_var_name="current structures"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False,
                        thumbnail="images/OdinTempleThumb.png",
                        cost=700, tower=TempleOfOdin(), quest="Enchant 12 towers with runes", 
                        quest_thresh=12, quest_var_name="current enchanted towers"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False, 
                        thumbnail="images/ChamberChiefThumb.png",
                        cost=1200, tower=ChamberOfTheChief(), quest="Reach 3000 gold", 
                        quest_thresh=3000, quest_var_name="current gold"), 
                ShopItem(is_unlocked=is_debug, is_unlockable=False, 
                        thumbnail="images/FreyrTempleThumb.png",
                        cost=1500, tower=TempleOfFreyr(), quest="Build 3 temples", 
                        quest_thresh=3, quest_var_name="current_temples")
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

        # Create the objects needed to quickly draw the map from scratch
        # see https://api.arcade.academy/en/latest/examples/shape_list_demo.html#shape-list-demo
        points_list = []
        colors_list = []
        for i in range(len(self.map_cells)-1):
            for j in range(len(self.map_cells[i])):
                l, r, t, b = cell_lrtb(i, j)
                c = cell_color(self.map_cells[i][j].terrain_type)
                points_list.append((l,t))
                points_list.append((r+1,t))
                points_list.append((r+1,b-1))
                points_list.append((l,b-1))
                for m in range(4):
                    colors_list.append(c)
        shape = arcade.create_rectangles_filled_with_colors(points_list, colors_list)
        self.map_shape_list.append(shape)

        # load the map image, if it exists
        if self.map_number > 0:
            self.map_water_animation = arcade.Sprite(
                center_x=MAP_WIDTH/2,
                center_y=CHIN_HEIGHT+MAP_HEIGHT/2
            )
            for k in range(24):
                self.map_water_animation.append_texture(arcade.load_texture('./images/water_shimmer/'+str(k+1)+'.png'))
            self.map_water_animation.set_texture(0)

            self.map_water_static = arcade.Sprite(
                center_x=MAP_WIDTH/2,
                center_y=CHIN_HEIGHT+MAP_HEIGHT/2,
                texture=arcade.load_texture('./images/map'+str(self.map_number)+'-water.png')
            )

            self.map_land = arcade.Sprite(
                center_x=MAP_WIDTH/2,
                center_y=CHIN_HEIGHT+MAP_HEIGHT/2,
                texture=arcade.load_texture('./images/map'+str(self.map_number)+'LandOnly.png')
            )
        self.water_shimmer_ind = 0 
        self.water_shimmer_timer = 0.04

        self.abilities_list[2] = PlatformAbility(map_reference=self.map_cells)

    def load_waves(self, filename):
        self.wave_list = []
        if self.is_freeplay:
            for k in range(4):
                self.wave_list.append(self.wave_maker.make_wave())
        else:
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
            text="10" ,
            start_x = MAP_WIDTH*0.5,
            start_y = 4,
            font_size = 14,
            width = MAP_WIDTH*0.2,
            align = "right"
        )
        self.money_counter_text = arcade.Text(
            text="500",
            start_x = MAP_WIDTH*0.75,
            start_y = 3,
            font_size = 14,
            width = MAP_WIDTH*0.22,
            align = "right"
        )

        # 5. Shop
        self.shop_text = []
        for k in range(5):
            name = arcade.Text(
                '', 
                start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 10, 
                start_y = SHOP_TOPS[k] - 15, 
                color = arcade.color.PURPLE, 
                font_size = 12,
                bold = True
            )
            description = arcade.Text(
                '', 
                start_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE + 11, 
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
                start_x = MAP_WIDTH + 11, 
                start_y = SHOP_BOTTOMS[k] + 7, 
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

    def init_gui_elements(self):
        """creates the SpriteList containing almost all parts of the gui (shop, corner menu, chin menu). 
        Speeds up future draw operations on these parts, which will be stored in the SpriteList self.gui_elements"""
        self.gui_elements = arcade.SpriteList()

        # 1. Backgrounds
        chin_background = arcade.Sprite(
            center_x=MAP_WIDTH/2,
            center_y=CHIN_HEIGHT/2,
            texture=self.assets['chin_menu']
        )
        corner_background = arcade.Sprite(
            center_x = MAP_WIDTH + SHOP_WIDTH/2,
            center_y = (SCREEN_HEIGHT-SHOP_HEIGHT)/2,
            texture = self.assets["info_box"]
        )
        self.shop_background = arcade.Sprite(
            center_x = MAP_WIDTH + SHOP_WIDTH/2,
            center_y = SCREEN_HEIGHT - SHOP_HEIGHT/2
        )
        self.shop_background.append_texture(self.assets['shop_combat'])
        self.shop_background.append_texture(self.assets['shop_sacred'])
        self.shop_background.append_texture(self.assets['shop_buildings'])
        self.shop_background.set_texture(texture_no=0)
        self.gui_elements.extend([chin_background, corner_background, self.shop_background])

        # 2. Attack button
        self.attack_button = arcade.Sprite(
            center_x = MAP_WIDTH - 5 - ATK_BUTT_HEIGHT/2,
            center_y = INFO_BAR_HEIGHT + 2 + ATK_BUTT_HEIGHT/2,
        )
        self.attack_button.append_texture(self.assets['attack_button'])
        self.attack_button.append_texture(self.assets['attack_button_lit'])
        self.attack_button.append_texture(self.assets['attack_button_grey'])
        self.attack_button.set_texture(texture_no=0)
        self.gui_elements.append(self.attack_button)
        
        # 3. Shop items
        for tab in range(len(self.shop_listlist)):
            for k in range(len(self.shop_listlist[tab])):
                self.shop_listlist[tab][k].center_x = MAP_WIDTH + SHOP_ITEM_THUMB_SIZE/2 + 4.5
                self.shop_listlist[tab][k].center_y = SHOP_TOPS[k] - SHOP_ITEM_HEIGHT/2 + 10.5
                self.gui_elements.append(self.shop_listlist[tab][k])

        # 4. Abilities bar
        self.ability_icons = []
        for k in range(5):
            ability_icon = arcade.Sprite(
                center_x = MAP_WIDTH + k*42 + 28.5,
                center_y = 25.5,
                texture=self.abilities_list[k].icon
            )
            ability_icon.visible = self.abilities_unlocked[k]
            self.ability_icons.append(ability_icon)
            self.gui_elements.append(ability_icon)

        # 5. Runes bar
        self.rune_icons = []
        for k in range(7):
            rune_icon = arcade.Sprite(
                center_x = MAP_WIDTH + k*30 + 20.5,
                center_y = 193.5,
                texture=self.runes_list[k].extended_icon
            )
            rune_icon.visible = self.runes_unlocked[k]
            self.rune_icons.append(rune_icon)
            self.gui_elements.append(rune_icon)

        # 6. Chin menu buttons
        self.pause_button = arcade.Sprite(
            filename='./images/pause-button.png',
            center_x = 83,
            center_y = 12,
        )
        self.gui_elements.append(self.pause_button)
        self.exit_button = arcade.Sprite(
            filename='./images/exit-button.png',
            center_x = 25.5,
            center_y = 12,
        )
        self.gui_elements.append(self.exit_button)

        # 7. Splash screens (drawn separately, on top of everything)
        self.pause_splash = arcade.Sprite(
            filename='./images/pause-menu.png',
            center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT/2,
        )
        self.exit_splash = arcade.Sprite(
            filename='./images/confirm-exit.png',
            center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT/2,
        )
        self.win_splash = arcade.Sprite(
            filename='./images/win-screen.png',
            center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT/2,
        )
        self.lose_splash = arcade.Sprite(
            filename='./images/lose-splash.png',
            center_x=SCREEN_WIDTH/2,
            center_y=SCREEN_HEIGHT/2,
        )

    def on_draw(self): 
        arcade.start_render()
        if self.game_state == 'level select':
            self.draw_level_select()
            return  
         
        self.draw_map_background()
        self.water_explosions_list.draw()
        self.swimmers_list.draw()
        self.draw_map_land()

        self.towers_list.draw()
        for tower in self.towers_list.sprite_list:
            tower.draw_runes()

        self.flyers_list.draw()
        self.enemy_effects.draw()
        self.all_health_bars.draw()

        # clears the buffer to make sure projectiles are properly rendered
        self.ctx.flush() 
        self.projectiles_list.draw()

        if not self.paused:
            for k, tower in enumerate(self.towers_list.sprite_list):
                if self.hover_target == "tower:"+str(k):
                    self.draw_range(tower)
                if tower.attack_animation_remaining > 0:
                    tower.draw_shoot_animation()
            self.ctx.flush()

        self.effects_list.draw()

        if ((not self.paused) and (self._mouse_x <= MAP_WIDTH and self._mouse_y >= CHIN_HEIGHT)):
            if self.shop_item_selected:
                self.preview_tower_placement(
                    x=self._mouse_x, 
                    y=self._mouse_y, 
                    tower_shopitem=self.shop_listlist[self.current_shop_tab][self.shop_item_selected-1]
                )
            elif self.rune_selected:
                k = self.rune_selected - 1
                self.runes_list[k].preview(x=self._mouse_x, y=self._mouse_y)
            elif self.ability_selected:
                k = self.ability_selected - 1
                if self.abilities_list[k].has_range:
                    self.preview_ability_range(
                        x=self._mouse_x, 
                        y=self._mouse_y, 
                        ability_range=self.abilities_list[k].range
                    )
                self.abilities_list[k].preview(x=self._mouse_x, y=self._mouse_y)

        self.gui_elements.draw()
        self.draw_chin_menu()
        self.draw_shop()
        self.draw_corner_menu()

        if self.paused: 
            self.draw_pause_menu()
        if is_debug:
            self.perf_graph.draw()
    
    # draw sub-methods used to make self.on_draw more legible
    def draw_map_background(self):
        if self.map_number > 0:
            self.map_water_static.draw()
            self.map_water_animation.draw(blend_function=(self.ctx.DST_COLOR, self.ctx.SRC_COLOR))
        else:
            # draw the map using colored rectangles representing terrain type of each cell
            self.map_shape_list.draw()

    def draw_map_land(self):
        if self.map_number > 0:
            self.map_land.draw()
        self.platforms.draw()

    def draw_range(self, tower):
        if tower.is_2x2:
            return
        self.range_preview.set_texture(0)
        self.range_preview.center_x = tower.center_x
        self.range_preview.center_y = tower.center_y
        self.range_preview.scale = tower.range/137.0
        self.range_preview.draw()
        self.range_preview.angle -= 0.5 # degrees

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
        if fake_tower.does_rotate:
            fake_tower.make_base_tower().draw()
        fake_tower.draw()

    def preview_ability_range(self, x:float, y:float, ability_range: float):
        self.range_preview.set_texture(1)
        self.range_preview.center_x = x
        self.range_preview.center_y = y
        self.range_preview.scale = ability_range/137.0
        self.range_preview.draw()
        self.range_preview.angle -= 0.5 # degrees

    def draw_chin_menu(self):
        # Background and attack button are Sprites in the gui_elements list, already drawn

        # Wave previews
        for k in range(2):
            # add preview of waves, if there are still waves left
            if self.wave_number+1-k < len(self.wave_list):
                if self.is_freeplay:
                    self.wave_previews_text[k][0].text = 'Attack #'+str(self.wave_number+2-k)
                else:
                    self.wave_previews_text[k][0].text = 'Attack #'+str(self.wave_number+2-k)+'/'+str(len(self.wave_list))
                self.wave_previews_text[k][1].text = self.wave_list[self.wave_number+1-k].describe()
                if k==1 and not self.wave_is_happening:
                   mins_left = str(int(self.time_to_next_wave//60))
                   secs_left = str(int(self.time_to_next_wave) % 60)
                   time_left = mins_left+':'+secs_left if len(secs_left)==2 else mins_left+':0'+secs_left
                   self.wave_previews_text[k][0].text += ' : in ' + time_left
            else:
                self.wave_previews_text[k][0].text = ''
                self.wave_previews_text[k][1].text = ''
            for txt in self.wave_previews_text[k]:
                txt.draw()
                
        # attack button (update only, it already got drawn)
        if self.wave_is_happening:
            self.attack_button.set_texture(texture_no=2) # grey
        elif self.hover_target == 'attack_button' and not self.paused:
            self.attack_button.set_texture(texture_no=1) # lit
        else:
            self.attack_button.set_texture(texture_no=0) # normal

        # info bar
        self.population_counter_text.text = str(self.population)
        self.population_counter_text.draw()
        self.money_counter_text.text = str(floor(self.money))
        self.money_counter_text.draw()

    def draw_shop(self): 
        # background
        self.shop_background.set_texture(self.current_shop_tab)

        for tab in range(len(self.shop_listlist)):
            for k in range(len(self.shop_listlist[tab])):
                self.shop_listlist[tab][k].visible = (self.current_shop_tab == tab) and self.shop_listlist[tab][k].is_unlocked

        for k in range(0, 5):
            # shop item, if it should be there
            shop_item = (self.shop_listlist[self.current_shop_tab][k])
            if shop_item.is_unlocked:
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
                self.shop_text[k]['name'].text = "Task: " + shop_item.tower.name
                self.shop_text[k]['description'].text = shop_item.quest
                self.shop_text[k]['price'].text = ''
                self.shop_text[k]['quest progress'].text = str(floor(shop_item.quest_progress)) + '/' + str(shop_item.quest_thresh)
                for txt in self.shop_text[k].values():
                    txt.draw()
 
    def draw_corner_menu(self):
        # 1. Runes bar
        for k in range(7):
            self.rune_icons[k].visible = self.runes_unlocked[k]
        if self.rune_selected > 0:
            k = self.rune_selected - 1
            arcade.draw_lrtb_rectangle_outline(
                left = MAP_WIDTH + 5 + k*30,
                right = MAP_WIDTH + 5 + k*30 + 29,
                top = 215,
                bottom = 186,
                color = arcade.color.BLUE,
                border_width = 2
            )

        # 2. Info Box
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
            if not (tower.rune is None):
                tower.rune.draw_icon(x=SCREEN_WIDTH-30, y=SHOP_BOTTOMS[-1]-86)
        elif 'rune' in self.hover_target:
            k = int(self.hover_target.split(':')[-1])
            self.info_box_text[0].text = RUNE_NAMES[k]
            self.info_box_text[1].text = RUNE_DESCRIPTIONS[k]
            self.info_box_text[2].text = ''
        elif 'ability' in self.hover_target:
            k = int(self.hover_target.split(':')[-1])
            self.info_box_text[0].text = ABILITY_NAMES[k]
            self.info_box_text[1].text = ABILITY_DESCRIPTIONS[k] + timestr(self.abilities_list[k].cooldown)
            self.info_box_text[2].text = ''
        elif is_debug:
            self.info_box_text[0].text = self.hover_target
            self.info_box_text[1].text = ''
            self.info_box_text[2].text = ''
        else:
            self.info_box_text[0].text = ''
            self.info_box_text[1].text = ''
            self.info_box_text[2].text = ''
        for txt in self.info_box_text:
            txt.draw()
    
        # 3. Abilities bar
        for k in range(5):
            self.ability_icons[k].visible = self.abilities_unlocked[k]
            if self.abilities_list[k].cooldown_remaining > 0.01:
                self.abilities_list[k].draw_cooldown(
                    x = MAP_WIDTH + 27 + k*42,
                    y=24
                )
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
        arcade.draw_lrtb_rectangle_filled( # dim screen
            left   = 0, 
            right  = SCREEN_WIDTH,
            top    = SCREEN_HEIGHT,
            bottom = 0,
            color=arcade.make_transparent_color(arcade.color.DIM_GRAY, transparency=128.0)
        )
        if self.game_state == 'playing' and self.paused:
            self.pause_splash.draw()
            return
        elif self.game_state == 'exit confirmation':
            self.exit_splash.draw()
            return
        elif self.game_state == 'won':
            self.win_splash.draw()
            return
        elif self.game_state == 'lost':
            self.lose_splash.draw()
            return

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
            if k < self.maps_beaten:
                arcade.draw_text(
                    text = 'FREEPLAY', 
                    start_x = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k,
                    start_y = 245,
                    color = arcade.color.BLACK,
                    font_size = 17,
                    width = LEVEL_WIDTH,
                    align = "center", 
                    bold = True
                )
                if ("start freeplay" in self.hover_target) and (self.hover_target[-1] == str(k+1)):
                    arcade.draw_lrtb_rectangle_outline(
                        left = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k,
                        right= LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH,
                        top=272,
                        bottom= 235,
                        color=arcade.color.BLACK,
                        border_width=3
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
                
    def on_update(self, delta_time: float = 1/30):
        if is_debug:
            self.perf_graph.update_graph(delta_time=delta_time)
        if self.paused or self.game_state == 'won' or self.game_state == 'lost' or self.game_state == 'exit confirmation':
            self.paused = True
            return
        ret = super().on_update(delta_time)

        # update some animations
        self.water_shimmer_timer -= delta_time
        if self.water_shimmer_timer <= 0:
            self.water_shimmer_ind = (self.water_shimmer_ind + 1) % 24
            self.map_water_animation.set_texture(self.water_shimmer_ind)
            while self.water_shimmer_timer <= 0:
                self.water_shimmer_timer += 0.04

        # check if any shop item is selected
        self.shop_item_selected = 0
        for n, item in enumerate(self.shop_listlist[self.current_shop_tab]):
            if item.actively_selected:
                self.shop_item_selected = n+1

        # check for projectile impacts
        for proj in self.projectiles_list.sprite_list:
            if proj.name != 'falcon':
                # see if we are on the target
                dx = proj.target_x - proj.center_x
                dy = proj.target_y - proj.center_y
                dist2_from_target = dx*dx + dy*dy
                if dist2_from_target <= (proj.speed/2)**2:
                    self.perform_impact(proj)
                    continue
                # see if we already passed the target and are now headed away
                vx = proj.velocity[0]
                vy = proj.velocity[1]
                vel_angle = atan2(vy, vx)
                tgt_angle = atan2(-dy, -dx)
                angle_diff = abs(vel_angle-tgt_angle) # this should be in [0, 2*pi]
                if angle_diff < 0.2 or angle_diff > 2*pi - 0.2: 
                    # we are headed directly away from target (+/- 0.2rad)
                    # detonate self before we get too embarrasingly far
                    self.perform_impact(proj)

        self.perform_enemy_actions(delta_time=delta_time)
        self.perform_tower_attacks(delta_time=delta_time)
        self.update_wave_progress(delta_time=delta_time)
        self.update_quests()
        self.update_abilities_and_runes(delta_time=delta_time)
        
        # move and delete sprites if needed
        self.enemies_list.update()
        self.enemies_list.on_update(delta_time) 
        self.towers_list.update()
        self.towers_list.on_update(delta_time)
        self.projectiles_list.update()
        self.projectiles_list.on_update(delta_time)
        self.effects_list.update()
        self.effects_list.on_update(delta_time)
        self.water_explosions_list.update()
        self.water_explosions_list.on_update(delta_time)

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
    
    def update_abilities_and_runes(self, delta_time: float):
        # update cooldowns
        for ability in self.abilities_list:
            if not (ability is None):
                ability.on_update(delta_time)
        
        # update unlocks
        if is_debug:
            self.abilities_unlocked = [True]*len(self.abilities_unlocked)
            self.runes_unlocked = [True]*len(self.runes_unlocked)
            return
        self.abilities_unlocked = [True, False, False, False, False]
        self.runes_unlocked = [False]*len(self.runes_unlocked)
        for tower in self.towers_list.sprite_list:
            if not tower.is_2x2:
                continue
            if tower.name == "Temple of Thor":
                self.abilities_unlocked[1] = True
                self.runes_unlocked[0] = True
            elif tower.name == "Forge":
                 self.abilities_unlocked[2] = True
                 self.runes_unlocked[1] = True
            elif tower.name == "Temple of Odin":
                self.runes_unlocked[2] = True
                self.runes_unlocked[3] = True
                self.runes_unlocked[4] = True
            elif tower.name == "Chamber of the Chief":
                self.abilities_unlocked[3] = True
                self.runes_unlocked[5] = True
            elif tower.name == "Temple of Freyr":
                self.abilities_unlocked[4] = True
                self.runes_unlocked[6] = True

    def perform_enemy_actions(self, delta_time: float):
        # take damage from dps effects:
        for enemy in self.enemies_list.sprite_list:
            for eff in enemy.temporary_effects:
                if eff.damage_per_second > 0:
                    dmg = eff.damage_per_second*delta_time
                    self.process_enemy_damage(enemy, dmg)

        # check if any enemies get kills
        for enemy in self.enemies_list.sprite_list:
            if enemy.center_y <= CHIN_HEIGHT - 0.4*CELL_SIZE:
                self.population -= 1
                enemy.remove_from_sprite_lists()

        # underwater enemy hiding
        for enemy in self.swimmers_list: 
            if enemy.can_hide:
                i, j = nearest_cell_ij(enemy.center_x, enemy.center_y)
                if self.map_cells[i][j].terrain_type == "deep":
                    enemy.is_hidden = True
                else:
                    enemy.is_hidden = False
    
    def update_wave_progress(self, delta_time: float):
        if self.wave_is_happening:
            # spawn next enemy, if needed, and decrement enemies_left_to_spawn
            if self.enemies_left_to_spawn > 0:
                if self.time_to_next_spawn <= 0.0: # time to spawn new enemy
                    new_enemy = self.wave_list[self.wave_number-1].spawn(self.next_enemy_index)
                    new_enemy.bottom = SCREEN_HEIGHT
                    if new_enemy.is_flying:
                        new_enemy.left = randint(0, floor(MAP_WIDTH-new_enemy.width))
                        if (new_enemy.left < 2*CELL_SIZE) or (new_enemy.right > MAP_WIDTH-2*CELL_SIZE):
                            new_enemy.left = randint(0, floor(MAP_WIDTH-new_enemy.width)) # re-roll the dice
                    else:
                        test_j = 99
                        while not (test_j in self.spawnable_cell_js):
                            test_j = randint(0, len(self.map_cells[0]))
                        new_enemy.center_x, _ = cell_centerxy(i=0, j=test_j)
                        new_enemy.calc_path(map=self.map_cells)
                    self.enemies_list.append(new_enemy)
                    if new_enemy.is_flying:
                        self.flyers_list.append(new_enemy)
                    else:
                        self.swimmers_list.append(new_enemy)
                    self.all_sprites.append(new_enemy)
                    self.all_health_bars.append(new_enemy.greenbar)
                    self.all_health_bars.append(new_enemy.redbar)
                    self.all_sprites.append(new_enemy.greenbar)
                    self.all_sprites.append(new_enemy.redbar)
                    if new_enemy.buff_sprite:
                        self.enemy_effects.append(new_enemy.buff_sprite)
                        self.all_sprites.append(new_enemy.buff_sprite)
                    self.enemies_left_to_spawn -= 1
                    self.next_enemy_index += 1
                    self.time_to_next_spawn = 0.25 + random()*1.5 # seconds
                else:
                    self.time_to_next_spawn -= delta_time
            # check if wave is over 
            elif self.enemies_left_to_spawn == 0 and len(self.enemies_list.sprite_list) == 0:
                self.wave_is_happening = False
                self.time_to_next_wave = 75 if self.map_number < 5 else 60
                if self.is_freeplay:
                    self.wave_list.append(self.wave_maker.make_wave())
                for tower in self.towers_list.sprite_list:
                    if tower.name == 'Sanctum of Tempest':
                        tower.hit_counter = 0
                        tower.set_texture(0)
        else: # wave is not happening
            self.time_to_next_wave -= delta_time
            if self.time_to_next_wave <= 0:
                self.start_wave()

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
                        if dmg > 0 and (tower.has_rune('kenaz') or tower.has_rune('isa')):
                            effect = deepcopy(tower.rune.effect)
                            thresh = 0.05
                            if tower.name == "Falcon Cliff":
                                if dmg == 0:
                                    thresh = 0 # zero probability of setting effect
                                else:
                                    thresh *= delta_time # probability per second is 1-(1-0.05*dt)^(1/dt) = ~0.049
                            if random() < thresh:
                                effect_added = enemy.set_effect(effect)
                                if effect_added:
                                    self.enemy_effects.append(effect)
                                    self.all_sprites.append(effect)
                                if effect.name == 'freeze':
                                    self.quest_tracker['enemies frozen'] += 1
                                elif effect.name == 'inflame':
                                    self.quest_tracker['enemies inflamed'] += 1
                        
                        self.process_enemy_damage(enemy, dmg)
                        # deal with projectiles created by tower.attack()
                        for proj in projlist: 
                            self.projectiles_list.append(proj)
                            self.all_sprites.append(proj)
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

            # fancy loop through enemies, to cope with removal(s) during the loop
            current_enemies = len(self.enemies_list.sprite_list)
            for k in range(current_enemies):
                enemy = self.enemies_list.sprite_list[current_enemies-1-k]
                dx = (enemy.center_x-projectile.target_x)
                dy = (enemy.center_y-projectile.target_y)
                dist2 = dx**2 + dy**2
                if dist2 <= projectile.splash_radius**2:
                    # Found an enemy that will take some damage and/or effects
                    for eff in projectile.effects:
                        effect = deepcopy(eff)
                        effect_added = enemy.set_effect(effect)
                        if effect_added:
                            self.enemy_effects.append(effect)
                            self.all_sprites.append(effect)
                        if effect.name == 'freeze':
                            self.quest_tracker['enemies frozen'] += 1
                        elif effect.name == 'inflame':
                            self.quest_tracker['enemies inflamed'] += 1
                    got_kill = self.process_enemy_damage(enemy, damage=projectile.damage)
                    if got_kill:
                        projectile_kills += 1
            if projectile.damage == 100: # this is a mjolnir
                if projectile_kills > self.quest_tracker["max mjolnir kills"]:
                    self.quest_tracker["max mjolnir kills"] = projectile_kills
        else: # projectiles that do not have AoE damage
            if projectile.target is None: # sad, useless projectile
                # create secondary projectiles if needed
                sub_projectiles = projectile.make_secondaries(
                    all_enemies=self.enemies_list.sprite_list, 
                    not_allowed_targets=[]
                )
                for sub in sub_projectiles:
                    self.projectiles_list.append(sub)
                    self.all_sprites.append(sub)
                projectile.remove_from_sprite_lists()
                return
            # if we reach this point, the projectile is not useless and will effect its target
            for eff in projectile.effects:
                effect = deepcopy(eff)
                effect_added = projectile.target.set_effect(effect)
                if effect_added:
                    self.enemy_effects.append(effect)
                    self.all_sprites.append(effect)
                if effect.name == 'freeze':
                    self.quest_tracker['enemies frozen'] += 1
                elif effect.name == 'inflame':
                    self.quest_tracker['enemies inflamed'] += 1
            self.process_enemy_damage(enemy=projectile.target, damage=projectile.damage)
        # ""pretty"" explosions
        if projectile.impact_effect:
            explosion = deepcopy(projectile.impact_effect)
            explosion.center_x = projectile.target_x
            explosion.center_y = projectile.target_y
            self.effects_list.append(explosion)
            self.all_sprites.append(explosion)
        # create secondary projectiles if needed
        sub_projectiles = projectile.make_secondaries(
            all_enemies = self.enemies_list.sprite_list, 
            not_allowed_targets = [projectile.target] if projectile.target else []
            )
        for sub in sub_projectiles:
            self.projectiles_list.append(sub)
            self.all_sprites.append(sub)
        projectile.remove_from_sprite_lists()

    def process_enemy_damage(self, enemy: Enemy, damage: float) -> bool:
        """Inflicts damage, updates money and quests, initializes death animations. Returns True if the enemy died"""
        earnings = enemy.take_damage_give_money(damage=damage)
        self.money += earnings
        # did the enemy die ?
        if earnings > 0:
            self.quest_tracker["enemies killed"] += 1
            if enemy.is_flying:
                self.quest_tracker["flying enemies killed"] += 1
                explosion = AirExplosion(center_x=enemy.center_x, center_y=enemy.center_y)
                self.effects_list.append(explosion)
            else:
                explosion = WaterExplosion(center_x=enemy.center_x, center_y=enemy.center_y)
                self.water_explosions_list.append(explosion)
                if enemy.is_hidden:
                    self.quest_tracker["submerged enemies killed"] += 1
            self.all_sprites.append(explosion)
            return True
        return False

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
            elif self.paused and self.game_state == 'exit confirmation':
                self.paused = False
                self.game_state = 'playing'
            else:
                self.paused = True

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
            # check if we pressed a "freeplay" button for any map
            if 238 <= y <= 273:
                for k in range(5):
                    left  = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k
                    right = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH
                    if left <= x <= right: 
                        if k < self.maps_beaten:
                            self.setup(map_number=k+1, is_freeplay=True) 
                            return super().on_mouse_press(x, y, button, modifiers)
            return 
        if self.paused and self.game_state == 'exit confirmation':
            if (SCREEN_WIDTH/2-203 <= x <= SCREEN_WIDTH/2) and (SCREEN_HEIGHT/2-105 <= y <= SCREEN_HEIGHT/2): # No exit
                self.paused = False
                self.game_state = 'playing'
            elif (SCREEN_WIDTH/2 <= x <= SCREEN_WIDTH/2+203) and (SCREEN_HEIGHT/2-105 <= y <= SCREEN_HEIGHT/2): # Yes exit
                # return to level select
                self.setup(map_number=0)
            return
        elif self.paused and (self.game_state == 'won' or self.game_state == 'lost'):
            self.setup(map_number=0)
            return
        elif self.paused:
            self.paused = False
            self.game_state = 'playing'
            return
        
        # 1. Deal with tower placement, runes, and abilities
        if (x > MAP_WIDTH) or (y < CHIN_HEIGHT): # we did not just place a tower
            self.unselect_all_items()
        else: # we clicked inside the map
            # were we trying to place / sell a tower ?
            if self.shop_item_selected > 0:
                self.attempt_tower_place(x, y)  
            elif self.rune_selected > 0:
                self.attempt_tower_enchant(x, y)
            elif self.ability_selected > 0:
                if self.ability_selected == 1:
                    self.attempt_tower_sell(x, y)
                elif self.ability_selected == 2: # Mjolnir projectile
                    if self.abilities_list[1].cooldown_remaining <= 0.01:
                        mjolnir = self.abilities_list[1].trigger(x, y)
                        self.projectiles_list.append(mjolnir)
                        self.all_sprites.append(mjolnir)
                        self.ability_selected = 0
                elif self.ability_selected == 3: # Platform placement
                    if self.abilities_list[2].cooldown_remaining <= 0.01:
                        new_platform = self.abilities_list[2].trigger(x, y)
                        if new_platform:
                            self.platforms.append(new_platform)
                            self.all_sprites.append(new_platform)
                            self.ability_selected = 0
                            self.quest_tracker['platforms placed'] += 1
                            for enemy in self.swimmers_list:
                                enemy.calc_path(map=self.map_cells)
                elif self.ability_selected == 4: # Command
                    if self.abilities_list[3].cooldown_remaining <= 0.01:
                        priority_delta, effect_radius2 = self.abilities_list[3].trigger(x, y)
                        for enemy in self.enemies_list.sprite_list:
                            dx = x - enemy.center_x
                            dy = y - enemy.center_y
                            dist2 = dx**2 + dy**2
                            if dist2 < effect_radius2:
                                enemy.priority += priority_delta
                        self.ability_selected = 0
                elif self.ability_selected == 5: # Harvest
                    if self.abilities_list[4].cooldown_remaining <= 0.01:
                        reward_fraction, effect_radius2 = self.abilities_list[4].trigger(x, y)
                        for enemy in self.enemies_list.sprite_list:
                            dx = x - enemy.center_x
                            dy = y - enemy.center_y
                            dist2 = dx**2 + dy**2
                            if dist2 < effect_radius2:
                                enemy.set_modifier('') # Remove any buff
                                self.money += reward_fraction*enemy.reward
            
        # 2. Deal with button clicks 
        # 2.1 Next Wave Start Button
        if (MAP_WIDTH-ATK_BUTT_HEIGHT-5 < x < MAP_WIDTH-5) and (INFO_BAR_HEIGHT+2 < y < CHIN_HEIGHT-10):
            if not self.wave_is_happening:
                self.start_wave()
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
        # 2.4 Rune selection 
        elif (MAP_WIDTH < x) and (186 <= y <= 215):
            for k in range(7):
                left = MAP_WIDTH + 5 + k*30
                right = MAP_WIDTH + 5 + k*30 + 29
                if left <= x <= right:
                    if self.runes_unlocked[k]:
                        self.rune_selected = k+1
        # 2.5 Ability selection 
        elif (MAP_WIDTH < x) and (4 <= y <= 44): 
            for k in range(0, 5):
                left = MAP_WIDTH + 7 + k*42
                right = MAP_WIDTH + 7 + k*42 + 40
                if left <= x <= right:
                    if self.abilities_unlocked[k] and self.abilities_list[k].cooldown_remaining < 0.01:
                        self.ability_selected = k+1
        # 2.6 Pause button
        elif (73 <= x <= 93) and (2 <= y <= 22):
            self.paused = True
        # 2.7 Exit button
        elif (3 <= x <= 48) and (2 <= y <= 22):
            self.paused = True
            self.game_state = 'exit confirmation'

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
        if new_tower.does_rotate:
            self.towers_list.append(new_tower.make_base_tower())
        self.towers_list.append(new_tower)
        self.all_sprites.append(new_tower)
        self.map_cells[i][j].is_occupied = True
        if new_tower.is_2x2:
            self.map_cells[i+1][j].is_occupied = True
            self.map_cells[i][j+1].is_occupied = True
            self.map_cells[i+1][j+1].is_occupied = True
            self.update_ability_cooldowns()
        elif new_tower.name == "Falcon Cliff":
            self.projectiles_list.append(new_tower.falcon)
            self.all_sprites.append(new_tower.falcon)
            new_tower.falcon.center_x = new_tower.center_x
            new_tower.falcon.center_y = new_tower.center_y

    def attempt_tower_sell(self, x: float, y: float):
        i, j = nearest_cell_ij(x, y)
        if not self.map_cells[i][j].is_occupied:
            return
        
        # if we reach this line, then the cell is occupied by a 1x1 or 2x2 tower
        for tower in self.towers_list.sprite_list:
            if tower.is_2x2: # we'll deal with 2x2 towers later
                continue
            ti, tj = nearest_cell_ij(tower.center_x, tower.center_y)
            if (i == ti) and (j == tj) and not('base' in tower.name.lower()):
                # found the tower
                price = self.find_tower_price(tower.name)
                self.money += int(floor(price/2))
                self.map_cells[i][j].is_occupied = False
                tower.remove_from_sprite_lists()
                if tower.name == "Falcon Cliff":
                    tower.falcon.remove_from_sprite_lists()
                elif tower.does_rotate:
                    tower.base_sprite.remove_from_sprite_lists()
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
                self.update_ability_cooldowns()
                return

    def attempt_tower_enchant(self, x: float, y: float):
        if not self.rune_selected:
            return
        if self.money < self.runes_list[self.rune_selected-1].cost:
            return
        rune = self.runes_list[self.rune_selected-1].make_another()
        i, j = nearest_cell_ij(x, y)
        if not self.map_cells[i][j].is_occupied:
            return
        
        # if we reach this line, then the cell is occupied by a 1x1 or 2x2 tower
        for tower in self.towers_list.sprite_list:
            if tower.is_2x2: # 2x2 towers are un-enchantable so skip this
                continue
            if 'base' in tower.name.lower():
                continue # tower bases don't get runes, tower tops do
            ti, tj = nearest_cell_ij(tower.center_x, tower.center_y)
            if (i == ti) and (j == tj):
                # found the tower
                if not tower.has_rune(rune.name):
                    self.money -= rune.cost
                    tower.set_rune(rune)
            
    def find_tower_price(self, tower_name):
        for shop_list in self.shop_listlist:
            for shop_item in shop_list:
                if shop_item.tower.name == tower_name:
                    return shop_item.cost
        return 0

    def update_quests(self):
        # 1. update the state-based quests in the self.quest_tracker
        # (event-based quests are updated wherever the relevant events happen)
        temples = 0
        oaks = 0
        runed_towers = 0
        for tower in self.towers_list.sprite_list:
            if "temple" in tower.name.lower():
                temples += 1
            elif tower.name == "Sacred Oak":
                oaks += 1
            if tower.has_rune('any'):
                runed_towers += 1
        self.quest_tracker["current oaks"] = oaks
        self.quest_tracker["current_temples"] = temples
        self.quest_tracker["current structures"] = len([tower for tower in self.towers_list.sprite_list if not('base' in tower.name.lower())])
        self.quest_tracker["current gold"] = self.money
        self.quest_tracker["current enchanted towers"] = runed_towers

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
            elif 238 <= y <= 273:
                for k in range(5):
                    left  = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k
                    right = LEVEL_SPACING + (LEVEL_WIDTH+LEVEL_SPACING)*k + LEVEL_WIDTH
                    if left <= x <= right: 
                        if k <= self.maps_beaten:
                            self.hover_target = "start freeplay " + str(k+1)
            return ret

        # 1. Are we hovering over a shop item ?
        if (x > MAP_WIDTH) and (y >= SHOP_BOTTOMS[-1]): 
            for k in range(0, 5):
                shop_item = self.shop_listlist[self.current_shop_tab][k]
                if SHOP_BOTTOMS[k] <= y <= SHOP_TOPS[k]:
                    if shop_item.is_unlockable or shop_item.is_unlocked:
                        self.hover_target = 'shop:' + str(self.current_shop_tab) + ':' + str(k)
                        return ret
        
        # 2. Are we hovering over a rune ?
        if (MAP_WIDTH < x) and (186 <= y <= 215):
            for k in range(7):
                left = MAP_WIDTH + 5 + k*30
                right = MAP_WIDTH + 5 + k*30 + 29
                if left <= x <= right:
                    if self.runes_unlocked[k]:
                        self.hover_target = 'rune:' + str(k)
                        return ret
                    
        # 3. Are we hovering over an ability ?
        if (MAP_WIDTH < x) and (4 <= y <= 44):
            for k in range(5):
                left = MAP_WIDTH + 7 + k*42
                right = MAP_WIDTH + 7 + k*42 + 40
                if left <= x <= right:
                    if self.abilities_unlocked[k]:
                        self.hover_target = 'ability:' + str(k)
                        return ret
                
        # 4. Are we hovering over the attack button ?
        if (MAP_WIDTH-ATK_BUTT_HEIGHT-5 < x < MAP_WIDTH-5) and (INFO_BAR_HEIGHT+2 < y < CHIN_HEIGHT-10):
            self.hover_target = 'attack_button'
            return ret

        # 5. Is there a shopitem or rune or ability previously selected ?
        if 0 < self.shop_item_selected < 9:
            self.hover_target = 'shop:' + str(self.current_shop_tab) + ':' + str(self.shop_item_selected-1)
            return ret
        if 0 < self.rune_selected < 9:
            self.hover_target = 'rune:' + str(self.rune_selected-1)
            return ret
        if 0 < self.ability_selected < 9:
            self.hover_target = 'ability:' + str(self.ability_selected-1)
            return ret
        
        # 6. Are we mousing over a tower sprite on the map ?
        if (x < MAP_WIDTH) and (CHIN_HEIGHT < y):
            for k, tower in enumerate(self.towers_list.sprite_list):
                if ((tower.left < x < tower.right) and (tower.bottom < y < tower.top)):
                    if not('base' in tower.name.lower()):
                        self.hover_target = 'tower:'+str(k)
                        return ret
                
        return ret

    def unselect_all_items(self):
        for m in range(0, 3):
            for shop_item in self.shop_listlist[m]:
                shop_item.actively_selected = False
        self.rune_selected = 0
        self.ability_selected = 0
        self.shop_item_selected = 0

    def update_ability_cooldowns(self):
        """Adjusts the cooldown duration (in s) of each ability using the base 
        cooldown and the number of corresponding buildings."""
        for k in range(1, 5): # k is the ability index
            building_name = ''
            for building in self.shop_listlist[2]:
                if k in building.tower.unlocked_power_indxs:
                    building_name = building.tower.name
                    base_cooldown = building.tower.cooldown

            n_buildings = 0
            for tower in self.towers_list:
                if tower.name == building_name:
                    n_buildings += 1

            self.abilities_list[k].cooldown = base_cooldown * 0.8**(n_buildings-1)
            self.abilities_list[k].cooldown_remaining = min(self.abilities_list[k].cooldown, 
                                                            self.abilities_list[k].cooldown_remaining)

    def start_wave(self):
        self.wave_is_happening = True
        self.wave_number += 1
        self.enemies_left_to_spawn = len(self.wave_list[self.wave_number-1].enemies_list)
        self.next_enemy_index = 0
        for ability in self.abilities_list:
            if not (ability is None):
                ability.cooldown_remaining -= max(self.time_to_next_wave, 0)


if __name__ == "__main__":
    app = GameWindow()
    app.setup(map_number=0)
    arcade.enable_timings(max_history=10000)
    arcade.run()
    arcade.print_timings()

# TODO next step : 

# Roadmap items : 
# runes on towers are drawn as part of a big spriteList
# further perfomance improvements (never below 60fps => on_draw+on_update combined must be <= 16ms)
# cut down on the use of global variables (maybe bring ability and rune name+description into those classes, add textures to GameWindow.assets, etc)
# organize the zones way better instead of having tons of hard-coded variables
# towers, projectiles, effects should use pre-loaded textures when initialized
# nicer level select
# abilities and shop items get highlighted on mouse-over
# score calculation
# warning messages when trying illegal actions
# tower unlock messages
# mac and linux compatibility
# textures / animations overhaul (attacks, effects, backgrounds)
