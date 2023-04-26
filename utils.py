from math import floor, sqrt

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