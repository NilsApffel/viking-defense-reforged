from arcade import draw_scaled_texture_rectangle
from constants import MINI_RUNES, RUNE_ICONS, RUNE_ICONS_EXTENDED, RUNE_PREVIEW
from effects import Inflame, Freeze
from utils import AnimatedSprite


class Rune():
    def __init__(self, name: str, cost: float) -> None:
        self.name = name
        try:
            self.icon = RUNE_ICONS[name]
            self.extended_icon = RUNE_ICONS_EXTENDED[name]
        except KeyError:
            self.icon = RUNE_ICONS['laguz']
            self.extended_icon = RUNE_ICONS_EXTENDED['laguz']
        self.preview_image = RUNE_PREVIEW
        self.cost = cost
        self.effect = None

    def preview(self, x, y): 
        draw_scaled_texture_rectangle(
            center_x=x,
            center_y=y,
            texture=self.preview_image,
            scale=1.0
        )

    def draw_icon(self, x, y, large: bool = False):
        draw_scaled_texture_rectangle(
            center_x=x,
            center_y=y,
            texture=self.extended_icon if large else self.icon,
            scale=1.0
        )

    def make_another(self):
        return Rune('Example Rune', self.cost)


class Raidho(Rune):
    def __init__(self) -> None:
        super().__init__(name='raidho', cost=30)
    
    def make_another(self):
        return Raidho()


class Hagalaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='hagalaz', cost=50)
    
    def make_another(self):
        return Hagalaz()


class Tiwaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='tiwaz', cost=70)
    
    def make_another(self):
        return Tiwaz()
    

class Kenaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='kenaz', cost=100)
        self.effect = Inflame()
    
    def make_another(self):
        return Kenaz()
    

class Isa(Rune):
    def __init__(self) -> None:
        super().__init__(name='isa', cost=100)
        self.effect = Freeze()
    
    def make_another(self):
        return Isa()


class Sowil(Rune):
    def __init__(self) -> None:
        super().__init__(name='sowil', cost=120)
        
    def make_another(self):
        return Sowil()


class Laguz(Rune):
    def __init__(self) -> None:
        super().__init__(name='laguz', cost=150)
    
    def make_another(self):
        return Laguz()


class MiniRune(AnimatedSprite):
    def __init__(self, rune: Rune, center_x: float = 0, center_y: float = 0):
        super().__init__(texture_list=MINI_RUNES[rune.name] ,
                         transition_times=[0.04*k for k in range(len(MINI_RUNES[rune.name])+1)], 
                         transition_indxs=list(range(len(MINI_RUNES[rune.name])))+[0], 
                         center_x=center_x, center_y=center_y)
