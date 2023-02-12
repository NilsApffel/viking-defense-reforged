import arcade
from towers import Tower

class ShopItem():
    def __init__(self, is_unlocked: bool = False, is_unlockable: bool = False, thumbnail: str = None, 
                    scale: float = 1.0, cost: float = 100, tower: Tower = None, 
                    quest: str = None, quest_thresh: int = 10, quest_var_name: str = None) -> None:
        self.is_unlocked = is_unlocked
        self.is_unlockable = is_unlockable
        if thumbnail is None:
            thumbnail = "images/question.png"
        self.thumbnail = arcade.load_texture(thumbnail)
        self.scale = scale
        self.cost = cost
        self.tower = tower
        if self.tower is None:
            self.tower = Tower()
        self.actively_selected = False
        if quest is None:
            self.quest = "Not yet implemented"
        else:
            self.quest = quest
        self.quest_thresh = quest_thresh
        self.quest_progress = 0
        if quest_var_name is None:
            self.quest_var_name = "_"
        else:
            self.quest_var_name = quest_var_name
