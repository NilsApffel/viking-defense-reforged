from arcade import load_texture, draw_scaled_texture_rectangle
from effects import Inflame, Freeze

class Rune():
    def __init__(self, name: str, icon_file: str, preview_image_file: str, 
                 cost: float) -> None:
        self.name = name
        self.icon = load_texture(icon_file)
        self.preview_image = load_texture(preview_image_file)
        self.cost = cost
        self.effect = None

    def preview(self, x, y): 
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

    def make_another(self):
        return Rune('Example Rune', self.icon_file, self.preview_image_file, self.cost)


class Raidho(Rune):
    def __init__(self) -> None:
        super().__init__(name='raidho', icon_file='./images/raidho-icon.png', 
                            preview_image_file='./images/rune-preview.png', cost=30)
    
    def make_another(self):
        return Raidho()


class Hagalaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='hagalaz', icon_file='./images/hagalaz-icon.png', 
                            preview_image_file='./images/rune-preview.png', cost=50)
    
    def make_another(self):
        return Hagalaz()


class Tiwaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='tiwaz', icon_file='./images/tiwaz-icon.png', 
                            preview_image_file='./images/rune-preview.png', cost=70)
    
    def make_another(self):
        return Tiwaz()
    

class Kenaz(Rune):
    def __init__(self) -> None:
        super().__init__(name='kenaz', icon_file='./images/kenaz-icon.png', 
                            preview_image_file='./images/rune-preview.png', cost=100)
        self.effect = Inflame()
    
    def make_another(self):
        return Kenaz()
    

class Isa(Rune):
    def __init__(self) -> None:
        super().__init__(name='isa', icon_file='./images/isa-icon.png', 
                            preview_image_file='./images/rune-preview.png', cost=100)
        self.effect = Freeze()
    
    def make_another(self):
        return Isa()


class Sowil(Rune):
    def __init__(self) -> None:
        super().__init__(name='sowil', icon_file='./images/sowil-icon.png', 
                         preview_image_file='./images/rune-preview.png', cost=120)
        
    def make_another(self):
        return Sowil()

