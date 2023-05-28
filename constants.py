from arcade import load_texture, make_transparent_color
from arcade.color import BLACK
from pathlib import Path
from platform import system

# there's probably a better way than gloabl variables to handle all this sizing...
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 590
CELL_SIZE = 32
MAP_WIDTH = 480
MAP_HEIGHT = 480
CHIN_HEIGHT = SCREEN_HEIGHT-MAP_HEIGHT
INFO_BAR_HEIGHT = 23
ATK_BUTT_HEIGHT = 76
WAVE_VIEWER_WIDTH = 178
SHOP_ITEM_HEIGHT = 62
SHOP_ITEM_THUMB_SIZE = 40
SHOP_WIDTH = SCREEN_WIDTH-MAP_WIDTH
SHOP_HEIGHT = 353
SCALING = 1.0 # this does nothing as far as I can tell
SHOP_TOPS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k for k in range(0, 5)]
SHOP_BOTTOMS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k - SHOP_ITEM_HEIGHT for k in range(0, 5)]
LEVEL_SPACING = 15
LEVEL_WIDTH = (SCREEN_WIDTH - 6*LEVEL_SPACING)/5
MAP_TARGET_J = 7
HBAR_HEIGHT = 4
HBAR_WIDTH_FACTOR = 1.0

TRANSPARENT_BLACK = make_transparent_color(BLACK, transparency=180)

ICE_SHIELD_TEXTURE = load_texture('./images/iceshield.png')
FIRE_SHIELD_TEXTURE = load_texture('./images/fireshield.png')
REGEN_TEXTURE = load_texture('./images/regen.png')

home_folder = Path.home()
if system() == "Windows":
    SCORE_FOLDER = home_folder.joinpath('AppData/Local/viking-defense-refoged/')
elif system() == "Darwin":
    SCORE_FOLDER = home_folder.joinpath('Library/Application Support/viking-defense-refoged/')
else: # assuming this is Linux
    SCORE_FOLDER = home_folder.joinpath('.local/share/viking-defense-refoged/')
SCORE_FILE = SCORE_FOLDER.joinpath('./scores.csv')

ABILITY_NAMES = ["Dismantle", "Mjolnir", "Platform", "Command", "Harvest"]
ABILITY_DESCRIPTIONS = ["Dismantles tower or building. You get a refund.\n\nRefund : 50%", 
                        "Thor's legendary hammer. Damages all enemies in range.\nDamage: 100\nCooldown: ", 
                        "Sets up a barrier platform in a shallow water cell. You may build on the platforms.\nCooldown: ", 
                        "All enemies in range become priority targets.\n\nCooldown: ", 
                        "Enemies in range lose their buffs. You get part of their reward.\nProfit: 25%\nCooldown: "]

RUNE_NAMES = ["Raidho", "Hagalaz", "Tiwaz", "Kenaz", "Isa", "Sowil", "Laguz"]
RUNE_DESCRIPTIONS = ["Tower projectiles become homing and gain re-targeting ability."+
                     "\n\nInsert to a tower",
                     "Increases tower damage\n\nDamage: +25%\nInsert to a tower", 
                     "Extends tower shooting range\n\nRange: +50%\nInsert to a tower", 
                     "Grants a tower fire damage, +5% inflame chance\nDamage: +20%\nInsert to a tower", 
                     "Grants a tower ice damage, +5% freeze chance\nFreeze time : 3s\nInsert to a tower",
                     "Decreases a tower's shooting and loading time\nSpeed: 2.00x\nInsert to a tower", 
                     "Tower missiles spring to another enemy after hitting a target.\nSpring damage: 50%\nInsert to a tower"]
RUNE_ICONS = {name.lower() : load_texture('./images/'+name.lower()+'-icon.png') for name in RUNE_NAMES}
RUNE_ICONS_EXTENDED = {name.lower() : load_texture('./images/'+name.lower()+'-extended.png') for name in RUNE_NAMES}
MINI_RUNES = {name.lower() : [load_texture('./images/runes/'+name+'/'+str(k+1)+'.png') for k in range(24)] for name in RUNE_NAMES}
RUNE_PREVIEW = load_texture('./images/rune-preview.png')

ASSETS = {'platform': load_texture('./images/platform.png'),
          'sanctum0': load_texture('./images/SanctumOfTempest0.png'),
          'sanctum1': load_texture('./images/SanctumOfTempest1.png'),
          'sanctum2': load_texture('./images/SanctumOfTempest2.png'),
          'sanctum3': load_texture('./images/SanctumOfTempest3.png'),
          'sanctum4': load_texture('./images/SanctumOfTempest4.png'),
          'tinybird0': load_texture('./images/TinyBird0.png'),
          'tinybird1': load_texture('./images/TinyBird1.png'),
          'tinybird2': load_texture('./images/TinyBird2.png'),
          'smallship0': load_texture('./images/SmallShip0.png'),
          'smallship1': load_texture('./images/SmallShip1.png'),
          'smallship2': load_texture('./images/SmallShip2.png'),
          'mediumdragon0': load_texture('./images/MediumDragon0.png'),
          'mediumdragon1': load_texture('./images/MediumDragon1.png'),
          'mediumdragon2': load_texture('./images/MediumDragon2.png'),
          'bigdragon0': load_texture('./images/BigDragon0.png'),
          'bigdragon1': load_texture('./images/BigDragon1.png'),
          'bigdragon2': load_texture('./images/BigDragon2.png'),
          'bigdragon3': load_texture('./images/BigDragon3.png'),
          'tinyboat0': load_texture('./images/TinyBoat0.png'),
          'tinyboat1': load_texture('./images/TinyBoat1.png'),
          'tinyboat2': load_texture('./images/TinyBoat2.png'),
          'tinyboat3': load_texture('./images/TinyBoat3.png'),
          'tinyboat4': load_texture('./images/TinyBoat4.png'),
          'smallsnake0': load_texture('./images/SmallSnake0.png'),
          'smallsnake1': load_texture('./images/SmallSnake1.png'),
          'smallsnake2': load_texture('./images/SmallSnake2.png'),
          'smallsnake3': load_texture('./images/SmallSnake3.png'),
          'smallsnake4': load_texture('./images/SmallSnake4.png'),
          'smallsnake5': load_texture('./images/SmallSnake5.png'),
          'smallsnakeUW0': load_texture('./images/SmallSnakeUnderwater0.png'),
          'smallsnakeUW1': load_texture('./images/SmallSnakeUnderwater1.png'),
          'smallsnakeUW2': load_texture('./images/SmallSnakeUnderwater2.png'),
          'smallsnakeUW3': load_texture('./images/SmallSnakeUnderwater3.png'),
          'smallsnakeUW4': load_texture('./images/SmallSnakeUnderwater4.png'),
          'smallsnakeUW5': load_texture('./images/SmallSnakeUnderwater5.png'),
          'mediumboat0': load_texture('./images/MediumBoat0.png'),
          'mediumboat1': load_texture('./images/MediumBoat1.png'),
          'mediumboat2': load_texture('./images/MediumBoat2.png'),
          'bigwhale0': load_texture('./images/BigWhale0.png'),
          'bigwhale1': load_texture('./images/BigWhale1.png'),
          'bigwhale2': load_texture('./images/BigWhale2.png'),
          'bigwhale3': load_texture('./images/BigWhale3.png'),
          'bigwhale4': load_texture('./images/BigWhale4.png'),
          'bigwhaleUW0': load_texture('./images/BigWhaleUnderwater0.png'),
          'watchtower0' : load_texture('./images/Watchtower0.png'),
          'watchtower1' : load_texture('./images/Watchtower1.png'),
          'watchtower2' : load_texture('./images/Watchtower2.png'),
          'catapult_base' : load_texture('./images/catapult_base.png'),
          'catapult_top' : load_texture('./images/catapult_top_large.png'),
          'falcon_cliff' : load_texture('./images/falcon_cliff.png'),
          'bastion' : load_texture('./images/Bastion.png'),
          'greek_fire_base' : load_texture('./images/greek_fire_base.png'),
          'greek_fire_top' : load_texture('./images/greek_fire_top.png'),
          'sacred_oak' : load_texture('./images/Oak_32x32_transparent.png'),
          'stone_head_base' : load_texture('./images/stone_head_base.png'),
          'stone_head_top' : load_texture('./images/stone_head_top.png'),
          'sparkling_pillar' : load_texture('./images/sparkling_pillar.png'),
          'quarry_of_rage' : load_texture('./images/QuarryOfRage.png'),
          'temple_of_thor' : load_texture('./images/TempleOfThor.png'),
          'forge0' : load_texture('./images/Forge0.png'),
          'forge1' : load_texture('./images/Forge1.png'),
          'forge2' : load_texture('./images/Forge2.png'),
          'temple_of_odin' : load_texture('./images/TempleOfOdin.png'),
          'chamber_of_the_chief' : load_texture('./images/ChamberChief.png'),
          'temple_of_freyr' : load_texture('./images/TempleOfFreyr.png'),
          'zap_blast' : load_texture('./images/zap_blast.png'),      
}

EFFECTS = {'slowdown' : load_texture('./images/slowdown.png'),
           'inflame' : load_texture('./images/inflame-2.png'),
           'freeze' : load_texture('./images/freeze.png'),
}

PROJECTILES = {'cannonball' : load_texture('./images/cannonball.png'),
               'falcon' : load_texture('./images/falcon.png'),
               'leaf' : load_texture('./images/leaf.png'),
               'wind_gust' : load_texture('./images/wind-gust.png'),
               'bomb' : load_texture('./images/bomb.png'),
               'mjolnir' : load_texture('./images/mjolnir-full-1.png')
}

zaps_names = ['zap-'+str(10*k+10) for k in range(15)]
zaps_list = [load_texture('./images/zaps/'+s+'.png') for s in zaps_names]
ZAPS = dict(zip(zaps_names, zaps_list))
flames_names = ['flame_particle_'+str(k) for k in range(8)]
FLAMES = [load_texture('./images/flames/'+s+'.png') for s in flames_names]

is_debug = False
