from arcade import (Sprite, draw_arc_filled, draw_circle_filled, draw_circle_outline, 
draw_scaled_texture_rectangle, load_texture, make_transparent_color, draw_rectangle_filled)
from arcade.color import YELLOW, RED, GREEN
from copy import deepcopy
from constants import ASSETS, CELL_SIZE, CHIN_HEIGHT, MAP_TARGET_J, MAP_WIDTH, TRANSPARENT_BLACK
from grid import nearest_cell_ij, cell_centerxy
from pathfind import find_path
from towers import Projectile, Explosion

class Ability():
    def __init__(self, name: str, icon_file: str, preview_image_file: str, 
                 cooldown: float, range: float) -> None:
        self.name = name
        self.icon = load_texture(icon_file)
        self.preview_image = load_texture(preview_image_file)
        self.cooldown = cooldown
        self.cooldown_remaining = 0.0
        self.range = range
        self.has_range = (abs(range) > 0.01)

    def preview(self, x, y, color): 
        if self.has_range:
            draw_circle_filled(
                center_x=x,
                center_y=y,
                radius=self.range, 
                color=make_transparent_color(color, transparency=32.0)
            )
            draw_circle_outline(
                center_x=x,
                center_y=y,
                radius=self.range, 
                color=make_transparent_color(color, transparency=128.0), 
                border_width=2
            )
            draw_circle_outline(
                center_x=x,
                center_y=y,
                radius=self.range-15, 
                color=make_transparent_color(color, transparency=128.0), 
                border_width=2
            )
        draw_scaled_texture_rectangle(
            center_x=x,
            center_y=y,
            texture=self.preview_image,
            scale=1.0
        )

    def draw_icon(self, x, y):
        draw_scaled_texture_rectangle(
            center_x=x,
            center_y=y,
            texture=self.icon,
            scale=1.0
        )
        if self.cooldown_remaining > 0.01:
            draw_arc_filled(
                center_x=x,
                center_y=y,
                width=40,
                height=40,
                color=TRANSPARENT_BLACK,
                start_angle=90,
                end_angle=90 + 360*(self.cooldown_remaining/self.cooldown)
            )

    def trigger(self, x, y):
        self.cooldown_remaining = self.cooldown

    def on_update(self, delta_time: float):
        self.cooldown_remaining -= delta_time
        if self.cooldown_remaining < 0.0:
            self.cooldown_remaining = 0.0


class SellTowerAbility(Ability):
    def __init__(self) -> None:
        super().__init__(name='sell tower', icon_file='./images/sell-tower-icon.png', 
                         preview_image_file='./images/coin.png', 
                         cooldown = 0.0, range = 0.0)
        
    def preview(self, x, y):
        return super().preview(x, y, color=YELLOW)
        
    def trigger(self, x, y):
        # sell tower ability can't actually handle its own trigger actions. 
        # GameWindow.attempt_tower_sell() needs to be called instead...
        return super().trigger(x, y)
        
class MjolnirAbility(Ability):
    def __init__(self) -> None:
        super().__init__(name='mjolnir', icon_file='./images/mjolnir-icon.png', 
                         preview_image_file='./images/mjolnir-preview.png', 
                         cooldown = 120.0, range = 3.0*CELL_SIZE)
        
    def preview(self, x, y):
        return super().preview(x, y, color=RED)

    def trigger(self, x, y):
        explosion = Explosion(
            filename='./images/cannonball-explosion.png',
            starting_scale=1.0,
            lifetime_seconds=0.75,
            scale_increase_rate=3.33,
        )
        mjolnir = Projectile(
            filename='./images/mjolnir-full-1.png', 
            scale=1.0,
            speed=6.0,
            center_x=MAP_WIDTH+10,
            center_y=CHIN_HEIGHT-10,
            angle_rate=-1.5*360,
            target_x=x,
            target_y=y,
            damage=100,
            do_splash_damage=True,
            splash_radius=self.range,
            impact_effect=explosion
        )
        super().trigger(x, y)
        return mjolnir


class PlatformAbility(Ability):
    def __init__(self, map_reference: list = None) -> None:
        super().__init__(name='platform', icon_file='./images/platform-icon.png', 
                         preview_image_file='./images/platform.png', 
                         cooldown = 90.0, range = 0.1)
        self.map = map_reference
        self.safe_cell_tuples = []
        self.unsafe_cell_tuples = []
        
    def preview(self, x, y):
        i, j = nearest_cell_ij(x, y)
        cx, cy = cell_centerxy(i, j)
        can_be_placed = (self.map[i][j].terrain_type == "shallow") and not(self.placement_would_block_path(i,j))
        color = GREEN if can_be_placed else RED
        draw_rectangle_filled(cx, cy, 36, 36, color)
        draw_scaled_texture_rectangle(cx, cy, texture=ASSETS["platform"])

    def trigger(self, x, y):
        i, j = nearest_cell_ij(x, y)
        cx, cy = cell_centerxy(i, j)
        can_be_placed = (self.map[i][j].terrain_type == "shallow") and not(self.placement_would_block_path(i,j))
        if can_be_placed:
            self.map[i][j].terrain_type = "ground"
            self.safe_cell_tuples = []
            super().trigger(x, y)
            return Sprite(center_x=cx, center_y=cy, texture=ASSETS["platform"])
        
    def placement_would_block_path(self, i, j):
        """Returns True if placing a platform at (i,j) results in a map where some enemies would have no path to the exit"""
        if j==0:
            return True
        
        # See if we've already tested this cell
        if (i,j) in self.safe_cell_tuples:
            return False
        if (i,j) in self.unsafe_cell_tuples:
            return True
        
        # form a list of test cases / test cells where enemies could spawn
        all_spawn_cells_js = []
        for test_j in range(len(self.map[0])):
            if self.map[0][test_j] == "shallow" or self.map[0][test_j] == "deep":
                all_spawn_cells_js.append(test_j)
        minimal_spawn_js = []
        for test_j in all_spawn_cells_js:
            if not (test_j+1 in all_spawn_cells_js):
                minimal_spawn_js.append(test_j)

        hypothetical_map = deepcopy(self.map)
        hypothetical_map[i][j].terrain_type = "ground"

        # test route from each individual spawn cell
        for spawn_j in minimal_spawn_js:
            try:
                find_path(
                    start_cell=(0, spawn_j), 
                    target_cell=(15, MAP_TARGET_J),
                    map=hypothetical_map
                )
            except ArithmeticError:
                self.unsafe_cell_tuples.append((i,j))
                return True
        # if we get to this point, then even with this cell added, all enemies would still have a valid path
        self.safe_cell_tuples.append((i,j))
        return False

