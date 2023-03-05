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
SCALING = 1.0 # this does nothing as far as I can tell
SHOP_TOPS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k for k in range(0, 5)]
SHOP_BOTTOMS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k - SHOP_ITEM_HEIGHT for k in range(0, 5)]
LEVEL_SPACING = 15
LEVEL_WIDTH = (SCREEN_WIDTH - 6*LEVEL_SPACING)/5
MAP_TARGET_J = 7

TRANSPARENT_BLACK = make_transparent_color(BLACK, transparency=180)

ICE_SHIELD_TEXTURE = load_texture('./images/iceshield.png')
FIRE_SHIELD_TEXTURE = load_texture('./images/fireshield.png')
REGEN_TEXTURE = load_texture('./images/regen.png')

home_folder = Path.home()
SCORE_FOLDER = home_folder.joinpath('./AppData/Local/viking-defense-refoged/')
SCORE_FILE = SCORE_FOLDER.joinpath('./scores.csv')

ABILITY_NAMES = ["Dismantle", "Mjolnir"] + ["Not implemented"]*3
ABILITY_DESCRIPTIONS = ["Dismantles tower or building. You get a refund.\n\nRefund : 50%", 
                        "Thor's legendary hammer. Damages all enemies in range.\nDamage: 100\nCooldown: 2 min", 
                        "Not implemented", 
                        "Not implemented", 
                        "Not implemented"]

RUNE_NAMES = ["Raidho"]  + ["Not implemented"]*6
RUNE_DESCRIPTIONS = ["Tower projectiles become homing and gain re-targeting ability."+
                     "\n\nInsert to a tower",
                     "Not implemented", 
                     "Not implemented", 
                     "Not implemented", 
                     "Not implemented", 
                     "Not implemented", 
                     "Not implemented"]

ASSETS = {'raidho-r': load_texture('./images/raidho-r.png')}

is_debug = False
