from arcade import Sprite, Sound
from math import floor, sqrt
from pyglet.media import Player
import glb

def timestr(seconds: float):
    s = ''
    if seconds >= 60:
        mins = floor(seconds / 60)
        s += str(mins) + 'min'
        seconds = seconds - mins*60
    if seconds >= 1:
        s += str(floor(seconds)) + 'sec'
    return s

def normalize_tuple(xytup: tuple, new_length: float = 1.0):
    x0, y0 = xytup
    norm0 = sqrt(x0*x0 + y0*y0)
    if norm0 < 0.001:
        norm0 = 0.001
    newtup = (new_length*x0/norm0, new_length*y0/norm0)
    return newtup


class AnimatedSprite(Sprite):
    def __init__(self, texture_list: list, transition_times: list, transition_indxs: list, 
                 scale: float = 1, center_x: float = 0, center_y: float = 0, angle: float = 0):
        """Adds easier/cleaner animations to a Sprite. 
        New args : 
        - texture_list : list of arcade.Texture objects corresponding to the different textures 
                         the sprite can take
        - transition_times : list of floats, times of each transition between textures, in seconds.
                             First element must be 0, last element must be time of return-to-zero.
        - transition_indxs : list of ints, represents the number of the texture that should be 
                             used after the corresponding transition time.
        """

        if len(transition_times) != len(transition_indxs):
            raise ValueError('Transition times and indices lists must have same length')
        if (len(texture_list) < 2) or (len(transition_times) < 3):
            raise ValueError('Must provide at least 2 textures and 3 transition times (including 0 and the return-to-zero time)')
        if transition_times[0] != 0.0:
            raise ValueError('First transition time must be at 0 seconds')
        if transition_times != sorted(transition_times):
            raise ValueError('transition times must be in ascending order')
        
        super().__init__(scale=scale, center_x=center_x, center_y=center_y, angle=angle)
        for tx in texture_list:
            self.append_texture(tx)
        self.set_texture(0)
        self.frame_indx = 0

        self.transition_times = transition_times
        self.transition_indxs = transition_indxs
        self.animation_time = 0

    def on_update(self, delta_time: float = 1 / 60):
        self.animation_time += delta_time
        # animation time cannot exceed return-to-zero time
        while self.animation_time  >= self.transition_times[-1]: 
            self.animation_time  -= self.transition_times[-1]
        # find the index of the texture we should be using from now on : 
        for (k, transition_k_time) in enumerate(self.transition_times):
            if self.animation_time < transition_k_time:
                # we haven't passed transition k yet, but it's the next one 
                new_frame_indx = self.transition_indxs[k-1]
                break
        # update the texture if needed
        if new_frame_indx != self.frame_indx:
            self.set_texture(new_frame_indx)
            self.frame_indx = new_frame_indx
        return super().on_update(delta_time)

class MutableSound(Sound):
    def __init__(self, file_name: str, streaming: bool = False):
        super().__init__(file_name, streaming)

    def play(self, volume: float = 1, pan: float = 0, loop: bool = False, speed: float = 1) -> Player:
        if glb.MUTED: 
            return Player()
        return super().play(volume, pan, loop, speed)
