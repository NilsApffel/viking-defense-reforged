from arcade import load_texture, make_transparent_color
from arcade.color import BLACK
from pathlib import Path

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
SCORE_FOLDER = home_folder.joinpath('./AppData/Local/viking-defense-refoged/')
SCORE_FILE = SCORE_FOLDER.joinpath('./scores.csv')

ABILITY_NAMES = ["Dismantle", "Mjolnir", "Platform", "Command", "Harvest"]
ABILITY_DESCRIPTIONS = ["Dismantles tower or building. You get a refund.\n\nRefund : 50%", 
                        "Thor's legendary hammer. Damages all enemies in range.\nDamage: 100\nCooldown: 2min", 
                        "Sets up a barrier platform in a shallow water cell. You may build on the platforms.\nCooldown: 1min30sec", 
                        "All enemies in range become priority targets.\n\nCooldown: 1min", 
                        "Enemies in range lose their buffs. You get part of their reward.\nProfit: 25%\nCooldown: 2min"]

RUNE_NAMES = ["Raidho", "Hagalaz", "Tiwaz", "Kenaz", "Isa", "Sowil", "Laguz"]
RUNE_DESCRIPTIONS = ["Tower projectiles become homing and gain re-targeting ability."+
                     "\n\nInsert to a tower",
                     "Increases tower damage\n\nDamage: +25%\nInsert to a tower", 
                     "Extends tower shooting range\n\nRange: +50%\nInsert to a tower", 
                     "Grants a tower fire damage, +5% inflame chance\nDamage: +20%\nInsert to a tower", 
                     "Grants a tower ice damage, +5% freeze chance\nFreeze time : 3s\nInsert to a tower",
                     "Decreases a tower's shooting and loading time\nSpeed: 2.00x\nInsert to a tower", 
                     "Tower missiles spring to another enemy after hitting a target.\nSpring damage: 50%\nInsert to a tower"]

ASSETS = {'platform': load_texture('./images/platform.png'),
          'raidho-r': load_texture('./images/raidho-r.png'), 
          'hagalaz-h': load_texture('./images/hagalaz-h.png'),
          'tiwaz-t': load_texture('./images/tiwaz-t.png'),
          'kenaz-c': load_texture('./images/kenaz-c.png'),
          'isa-i': load_texture('./images/isa-i.png'),
          'sowil-s': load_texture('./images/sowil-s.png'),
          'laguz-l': load_texture('./images/laguz-l.png'),
          'sanctum0': load_texture('./images/SanctumOfTempest0.png'),
          'sanctum1': load_texture('./images/SanctumOfTempest1.png'),
          'sanctum2': load_texture('./images/SanctumOfTempest2.png'),
          'sanctum3': load_texture('./images/SanctumOfTempest3.png'),
          'sanctum4': load_texture('./images/SanctumOfTempest4.png'),
}
zaps_names = ['zap-'+str(10*k+10) for k in range(15)]
zaps_list = [load_texture('./images/zaps/'+s+'.png') for s in zaps_names]
ZAPS = dict(zip(zaps_names, zaps_list))

is_debug = False
