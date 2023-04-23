from enemies import *
from math import ceil, floor
from random import random, randint

class Wave():
    def __init__(self, number: int, modifier: str, rank: int, type1: str, quant1: int, 
                 type2: str, quant2: int, type3: str, quant3: int) -> None:
        self.number = int(number)
        rnk = int(rank)
        try:
            q1 = int(quant1)
        except:
            q1 = 0
        try:
            q2 = int(quant2)
        except:
            q2 = 0
        try:
            q3 = int(quant3)
        except:
            q3 = 0
        
        self.enemies_list = []
        for k in range(q1):
            self.enemies_list.append((modifier, rnk, type1))
        for k in range(q2):
            self.enemies_list.append((modifier, rnk, type2))
        for k in range(q3):
            self.enemies_list.append((modifier, rnk, type3))

        self.quantities = [q1]
        if q2 > 0:
            self.quantities += [q2]
            if q3 > 0:
                self.quantities += [q3]
        
    def spawn(self, enemy_index: int) -> Enemy:
        enemy_type_name = self.enemies_list[enemy_index][2]
        if 'flying' in enemy_type_name:
            if 'tiny' in enemy_type_name:
                enemy = TinyBird()
            elif 'small' in enemy_type_name:
                enemy = SmallShip()
            elif 'medium' in enemy_type_name:
                enemy = MediumDragon()
            elif 'big' in enemy_type_name:
                enemy = BigDragon()
        else:
            if 'tiny' in enemy_type_name:
                enemy = TinyBoat()
            elif 'small' in enemy_type_name:
                enemy = SmallSnake()
            elif 'medium' in enemy_type_name:
                enemy = MediumBoat()
            elif 'big' in enemy_type_name:
                enemy = BigWhale()
        enemy.set_rank(self.enemies_list[enemy_index][1])
        enemy.set_modifier(self.enemies_list[enemy_index][0])
        return enemy

    def describe(self) -> str:
        sizes_str = ''
        types_str = ''
        modifiers_str = ''

        # how many of what is in sub-wave 1 ?
        sizes_str += str(self.quantities[0]) + ' '
        name1 = self.enemies_list[0][2]
        sizes_str += name1.split(' ')[0].upper()
        if 'flying' in name1:
            types_str += 'Flying'
        elif ('BIG' in sizes_str) or ('SMALL' in sizes_str):
            types_str += 'Underwater'
        else:
            types_str += 'Floating'

        rank = self.enemies_list[0][1]
        modifier = self.enemies_list[0][0]
        if  rank > 1:
            modifiers_str += 'Rank ' + str(rank)
            if modifier:
                modifiers_str += ', '
        modifiers_str += modifier
        
        # how is sub-wave 2 different ?
        if len(self.quantities) > 1:
            sizes_str += ' & ' + str(self.quantities[1]) + ' '
            name2 = self.enemies_list[self.quantities[0]][2] # first enemy of the second sub-wave
            sizes_str += name2.split(' ')[0].upper()

            if ('flying' in name2):
                if (not ('Flying' in types_str)):
                    types_str += ' & Flying'
            else:
                if (not ('Underwater' in types_str)) and (('big' in name2) or ('small' in name2)):
                    types_str += ' & Underwater'
                if (not ('Floating' in types_str)) and (('tiny' in name2) or ('medium' in name2)):
                    types_str += ' & Floating'

        # how is sub-wave 3 different ?
        if len(self.quantities) > 2:
            sizes_str += ' & ' + str(self.quantities[2]) + ' '
            name3 = self.enemies_list[-1][2] # last enemy of the last sub-wave
            sizes_str += name3.split(' ')[0].upper()
            if ('flying' in name3):
                if (not ('Flying' in types_str)):
                    types_str += ' & Flying'
            else:
                if (not ('Underwater' in types_str)) and (('big' in name3) or ('small' in name3)):
                    types_str += ' & Underwater'
                if (not ('Floating' in types_str)) and (('tiny' in name3) or ('medium' in name3)):
                    types_str += ' & Floating'

        total = sizes_str + '\n' + types_str + '\n' + modifiers_str
        return total

# we're gonna need a GameWindow.Wave_Generator() whose make_wave() we call everytime
# maybe this is the right time to learn buffers, also ??

class WaveMaker():
    def __init__(self) -> None:
        self.flying_wave_prob = 0.0
        self.modifier_prob = 0.0
        self.flying_wave_num = 0 # Careful, wave numbers can sometimes repeat and/or be skipped
        self.swimming_wave_num = 0
        self.is_flying_wave = False
        self.sizes = ['tiny', 'small', 'medium', 'big']
        self.costs_per_size = [1, 2, 4, 6]
        self.modifiers = ['fire shield', 'fast', 'ice shield', 'regeneration']
        self.modifier_cost_factor = 2.0
        self.rank_duration = 24
        self.wave_number = 0

    def make_wave(self) -> Wave:
        self.wave_number += 1

        # 1. pick flying or swimming type
        if random() < self.flying_wave_prob:
            self.is_flying_wave = True
            self.flying_wave_prob -= 0.1
        else:
            self.is_flying_wave = False
            self.flying_wave_prob += 0.1
        self.flying_wave_prob = max(0.1, self.flying_wave_prob)
        self.flying_wave_prob = min(self.flying_wave_prob, 0.9)
        
        # 2. Define the enemy budget and other params for this wave
        if self.is_flying_wave:
            overall_progress = self.flying_wave_num
        else:
            overall_progress = self.swimming_wave_num
        current_rank = overall_progress // self.rank_duration + 1
        progress_through_rank = overall_progress % self.rank_duration
        budget = ceil((progress_through_rank+1) / 4)*4 # budget is in {4, 8, 12, ... 24}

        # 3. Pick a size of enemy and calc the number of enemies
        enemy_size = progress_through_rank % 4
        if budget < self.costs_per_size[3]:
            enemy_size = min(enemy_size, 2)
        enemy_cost = self.costs_per_size[enemy_size]
        num_enemies = floor(budget/enemy_cost)

        # 4. Add modifiers if needed
        if num_enemies > 2 and random() < self.modifier_prob:
            modifier = self.modifiers[randint(0,3)]
            budget /= self.modifier_cost_factor
            num_enemies = floor(budget/enemy_cost)
            self.modifier_prob = 0.0
        else:
            modifier = ''
            self.modifier_prob += 0.05 * progress_through_rank

        # 5. Split into two groups of different-sized enemies, if needed
        if num_enemies > 5 and enemy_size > 0 and randint(0, 1): # make some smaller guys as well
            big_guys_size = enemy_size
            big_guys_cost = self.costs_per_size[big_guys_size]
            num_big_guys = floor(num_enemies / 2)
            budget_for_smalls = budget - big_guys_cost*num_big_guys*(self.modifier_cost_factor if modifier else 1.0)
            small_guys_size = big_guys_size - 1
            small_guys_cost = self.costs_per_size[small_guys_size]
            num_small_guys = floor(budget_for_smalls/small_guys_cost)

        elif num_enemies > 13 and enemy_size < 3 and randint(0, 1): # make some bigger guys as well
            small_guys_size = enemy_size
            small_guys_cost = self.costs_per_size[small_guys_size]
            num_small_guys = ceil(num_enemies / 2)
            budget_for_bigs = budget - small_guys_cost*num_small_guys*(self.modifier_cost_factor if modifier else 1.0)
            big_guys_size = small_guys_size + 1
            big_guys_cost = self.costs_per_size[big_guys_size]
            num_big_guys = floor(budget_for_bigs/big_guys_cost)
        else:
            big_guys_size = enemy_size
            num_big_guys = num_enemies
            small_guys_size = 0
            num_small_guys = 0

        # 6. Make this into a Wave
        wave = Wave(
            number=self.wave_number,
            modifier=modifier,
            rank=current_rank,
            type1=self.sizes[big_guys_size] + (' flying' if self.is_flying_wave else ''),
            type2=(self.sizes[small_guys_size] if num_small_guys > 0 else '') + (' flying' if self.is_flying_wave else ''),
            type3='',
            quant1=num_big_guys,
            quant2=num_small_guys,
            quant3=0
        )

        # 7. increment counters
        self.swimming_wave_num += randint(0, 1)
        self.flying_wave_num += randint(0, 1)
        if self.is_flying_wave:
            self.flying_wave_num += 1
        else:
            self.swimming_wave_num += 1

        return wave





