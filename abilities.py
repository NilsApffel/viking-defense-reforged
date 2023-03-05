from arcade import (draw_arc_filled, draw_circle_filled, draw_circle_outline, 
draw_scaled_texture_rectangle, load_texture, make_transparent_color)
from arcade.color import YELLOW, RED
from constants import CELL_SIZE, CHIN_HEIGHT, MAP_WIDTH, TRANSPARENT_BLACK
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
