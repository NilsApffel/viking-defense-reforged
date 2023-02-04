import arcade
from constants import *

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
