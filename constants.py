# there's probably a better way than gloabl variables to handle all this sizing...
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 590
CELL_SIZE = 32
MAP_WIDTH = 480
MAP_HEIGHT = 480
CHIN_HEIGHT = SCREEN_HEIGHT-MAP_HEIGHT
INFO_BAR_HEIGHT = 23
ATK_BUTT_HEIGHT = 76 # TODO make this 76, then deal with the consequences
WAVE_VIEWER_WIDTH = 178
SHOP_ITEM_HEIGHT = 62
SHOP_ITEM_THUMB_SIZE = 40
SCALING = 1.0 # this does nothing as far as I can tell
SHOP_TOPS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k for k in range(0, 5)]
SHOP_BOTTOMS = [SCREEN_HEIGHT - 27 - (4+SHOP_ITEM_HEIGHT)*k - SHOP_ITEM_HEIGHT for k in range(0, 5)]
MAP_TARGET_J = 7