from enemies import *

class Wave():
    def __init__(self, number, modifier, rank, type1, quant1, type2, quant2, type3, quant3) -> None:
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
            if not ('Flying' in types_str):
                if (not ('Underwater' in types_str)) and (('big' in name2) or ('small' in name2)):
                    types_str += ' & Underwater'
                if (not ('Floating' in types_str)) and (('tiny' in name2) or ('medium' in name2)):
                    types_str += ' & Floating'

        # how is sub-wave 3 different ?
        if len(self.quantities) > 2:
            sizes_str += ' & ' + str(self.quantities[2]) + ' '
            name3 = self.enemies_list[-1][2] # last enemy of the last sub-wave
            sizes_str += name3.split(' ')[0].upper()
            if not ('Flying' in types_str):
                if (not ('Underwater' in types_str)) and (('big' in name3) or ('small' in name3)):
                    types_str += ' & Underwater'
                if (not ('Floating' in types_str)) and (('tiny' in name3) or ('medium' in name3)):
                    types_str += ' & Floating'

        total = sizes_str + '\n' + types_str + '\n' + modifiers_str
        return total
