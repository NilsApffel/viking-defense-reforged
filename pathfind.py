# here I call (i,j) tuples cells, and lists of consecutive (i,j) tuples routes

def are_adjacent(cell1: tuple, cell2: tuple):
    if cell1[0] == cell2[0] and abs(cell1[1]-cell2[1]) == 1:
        return True
    if cell1[1] == cell2[1] and abs(cell1[0]-cell2[0]) == 1:
        return True
    return False

def get_adjacent_cells(i: int, j: int):
    return [(i-1,j), (i+1,j), (i,j-1), (i,j+1)]

def new_routing_options(known_cells: list, known_routes: list, map: list):
    print("I know how to go to these:", known_cells)
    new_cells = []
    new_routes = []
    for kcell, kroute in zip(known_cells, known_routes):
        for tup in get_adjacent_cells(kcell[0], kcell[1]):
            i = tup[0]
            j = tup[1]
            if i<0 or j<0 or i>15 or j>14:
                continue # this cell is outside the map, skip it
            if (not (tup in known_cells)) and (not (tup in new_cells)):
                if (map[i][j] == "ground"):
                    continue
                # this is a new cell we can reach
                new_cells.append(tup)
                # loop on all known routes to find one with lower g-score that leads to the same place
                best_route = kroute
                best_g = gscore(kroute)
                for cell, route in zip(known_cells, known_routes):
                    if gscore(route) < best_g and are_adjacent(cell, tup):
                        best_route = route
                        best_g = gscore(route)
                new_routes.append(best_route + [tup])
                # print("found route", best_route, "to", tup)
    return new_cells, new_routes

def gscore(route: list):
    return len(route)

def hscore(cell: tuple, target: tuple):
    return abs(cell[0]-target[0]) + abs(cell[1]-target[1])

def fscore(cell: tuple, route: list, target: tuple):
    return gscore(route) + hscore(cell, target)

def find_path(start_cell: tuple, target_cell: tuple, map: list):
    known_cells = [start_cell]
    known_paths = [[start_cell]]
    known_fscores = [fscore(cell=start_cell, route=[start_cell], target=target_cell)]

    for k in range(226):
        # get all new reachable cells
        new_cells, new_routes = new_routing_options(known_cells, known_paths, map)
        if len(new_cells) == 0:
            raise ArithmeticError("No new discoverable cells, but no path found to target")
        new_fscores = []
        for nc, nr in zip(new_cells, new_routes):
            new_fscores.append(fscore(cell=nc, route=nr, target=target_cell))
        min_new_fscore = min(new_fscores)

        # keep paths to the new cells that achieve minimum f-score
        for nc, nr, nf in zip(new_cells, new_routes, new_fscores):
            if nf == min_new_fscore:
                if nc[0] == target_cell[0] and nc[1] == target_cell[1]:
                    # found the best path, exit function
                    # print("found path after", k, "iterations")
                    return nr
                known_cells.append(nc)
                known_paths.append(nr)
                known_fscores.append(nf)
    raise ArithmeticError("Could not find a path to target")
