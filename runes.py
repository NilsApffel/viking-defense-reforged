from arcade import load_texture, draw_scaled_texture_rectangle

class Rune():
    def __init__(self, name: str, icon_file: str, preview_image_file: str, 
                 cost: float) -> None:
        self.name = name
        self.icon = load_texture(icon_file)
        self.preview_image = load_texture(preview_image_file)
        self.cost = cost

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
                            preview_image_file='./images/raidho-preview.png', cost=30)
    
    def make_another(self):
        return Raidho()
