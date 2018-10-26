import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
from math import sqrt, ceil
from collections import namedtuple

import logging, traceback, os, inspect

import time

logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)

current_time = lambda: int(round(time.time() * 1000))
start_time = 0

#################################################################################################################
def start_execution(state):
    global start_time
    start_time = current_time()
    return False

#################################################################################################################
def stop_execution():
    out_of_time = bool((current_time() - start_time) > 950)
    if out_of_time:
        logging.debug('\nRan out of time')
    return out_of_time

#################################################################################################################
def min_fleet_size(state, my_planet, target_planet):
    return target_planet.num_ships + (target_planet.growth_rate * state.distance(my_planet.ID, target_planet.ID)) + 1

#################################################################################################################
#returns a list ordered by priority comparing distance vs. strength FAVORING DISTANCE
def closest_sorted(state, from_planet, planets):
    return list(sorted(planets, key=lambda i: state.distance(from_planet.ID, i.ID)))

#################################################################################################################
def get_first_beatable(state, from_planet, planets):
    if stop_execution(): return None
    by_closest = closest_sorted(state, from_planet, planets)
    targets = [f.destination_planet for f in state.my_fleets()]
    by_closest = list(filter(lambda i: i.ID not in targets, by_closest))
    for p in by_closest:
        if p.num_ships + (state.distance(from_planet.ID, p.ID) * p.growth_rate) + 1 < from_planet.num_ships:
            return p
    return None

#################################################################################################################
def get_closest_ally(state, from_planet):
    if stop_execution(): return None
    return min(list(filter(lambda i: i.ID != from_planet.ID, state.my_planets())), key=lambda x: state.distance(from_planet.ID, x.ID), default=None)

#################################################################################################################
def is_being_targetted(state, my_planet):
    if stop_execution(): return None
    enemy_targets = [f.destination_planet for f in state.enemy_fleets()]
    return my_planet.ID in enemy_targets

#################################################################################################################
def desperado_attack(state):
    if stop_execution(): return True
    # p.num_ships + (fleet.turns_remaining * 5) + 1 - fleet.num_ships = how many ships I need to survive an attack
    for f in state.enemy_fleets():
        p = state.planets[f.destination_planet]
        #fleets are moved before planet ships are incremented!
        if f.turns_remaining == 1 and p.num_ships - f.num_ships < 1:
            weakest_neutral = get_first_beatable(state, p, state.neutral_planets())
            weakest_enemy = get_first_beatable(state, p, state.enemy_planets())
            closest_ally = get_closest_ally(state, p)
            
            try:
                if weakest_enemy:
                    issue_order(state, p.ID, weakest_enemy.ID, p.num_ships - 1)
                elif weakest_neutral:
                    issue_order(state, p.ID, weakest_neutral.ID, p.num_ships - 1)
                elif closest_ally:
                    issue_order(state, p.ID, closest_ally.ID, p.num_ships - 1)
                return False
            except Exception:
                return False
    return False

#################################################################################################################
def spread_to_closest_neutral_planet(state):
    return spread_to_planet(state, state.neutral_planets())

#################################################################################################################
def spread_to_closest_enemy_planet(state):
    return spread_to_planet(state, state.enemy_planets())

#################################################################################################################
def spread_to_planet(state, planets):
    if stop_execution(): return True

    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    if not strongest_planet: return False

    closest_target = get_first_beatable(state, strongest_planet, planets)
    if not closest_target: return False

    #enemies = list(sorted(state.enemy_planets(), key=lambda i: state.distance(i.ID, strongest_planet.ID)))

    #for enemy in enemies:

    return issue_order(state, strongest_planet.ID, closest_target.ID, min_fleet_size(state, strongest_planet, closest_target))

"""
#################################################################################################################
def attack_enemy_from_any(state):
    enemy_planet = min(list(sorted(state.enemy_planets(), key=lambda p: p.num_ships)))
    my_planets = iter(sorted(state.my_planets(), key=lambda p: state.distance(enemy_planet.ID, p.ID), reverse=True))
    p = next(my_planets)
    for mp in my_planets:
        if stop_execution(): return True
        target = get_first_beatable(state, mp, state.enemy_planets())
        if not target: continue
        return issue_order(state, mp.ID, target.ID, min_fleet_size(state, mp, target))
    return False
    """

#################################################################################################################
def team_attack(state, planets):
     #Planet = namedtuple('Planet', ['ID', 'x', 'y', 'owner', 'num_ships', 'growth_rate'])
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships, reverse=True))
    my_targets = [f.destination_planet for f in state.my_fleets()]
    try:
        p = next(my_planets)
        logging.debug('\n' + str(p))
        while p:
            if stop_execution(): return True
            ally = get_closest_ally(state, p)
            if not ally: return False
            team = {'ID':-1, 'x':(p.x + ally.x) / 2, 'y':(p.y + ally.y) / 2, 'owner':1, 'num_ships':p.num_ships + ally.num_ships, 'growth_rate':0 }
            enemy_planets = list(sorted(planets, key=lambda i: int(ceil(sqrt((team['x'] - i.x) ** 2 + (team['y'] - i.y) ** 2)))))
            for enemy in enemy_planets:
                if enemy.ID in my_targets: continue
                distance = int(ceil(sqrt((team['x'] - enemy.x) ** 2 + (team['y'] - enemy.y) ** 2)))
                min_ships = enemy.num_ships + (enemy.growth_rate * distance) + 1
                if min_ships < team["num_ships"] - 2:
                    issue_order(state, p.ID, enemy.ID, ((p.num_ships * (min_ships / p.num_ships)) / 2) - 1)
                    issue_order(state, ally.ID, enemy.ID, ((ally.num_ships * (min_ships / ally.num_ships)) / 2) - 1)
                    return True
            
        p = next(my_planets)
        p = next(my_planets)
    except StopIteration:
        return True    
    return True

#################################################################################################################
def team_attack_neutral(state):
   return team_attack(state, state.neutral_planets())

#################################################################################################################
def team_attack_enemy(state):
    return team_attack(state, state.enemy_planets())

#################################################################################################################
def defend_my_planets(state):
    if stop_execution(): return True
    my_IDs = [p.ID for p in state.my_planets()]
    my_planets = state.my_planets()
    for f in state.enemy_fleets():
        if f.destination_planet in my_IDs:
            targetted_planet = state.planets[f.destination_planet]
            difference = f.num_ships - (targetted_planet.num_ships + f.turns_remaining * targetted_planet.growth_rate) + 1
            closest_allies = closest_sorted(state, targetted_planet, my_planets)
            for ally in closest_allies:
                if difference > 0 and ally.num_ships > (difference + 1):
                    return issue_order(state, ally.ID, targetted_planet.ID, difference + 1)
    return False


"""
#################################################################################################################
def interrupt_enemy_spread(state):
    for f in state.enemy_fleets():
        if f.destination_planet in state.neutral_planets():
           attack_from = list(filter(lambda p: p.num_ships > f.num_ships + 2, state.my_planets()))
           if len(attack_from != 0):
              return issue_order(state, attack_from[0].ID, f.destination_planet, attack_from[0].num_ships - 1)


              
#################################################################################################################
def reinforce_my_planets(state):
    for p in state.my_planets():
        for f in state.enemy_fleets():
            if f.destination_planet == p.ID:
                break
        for ep in state.enemy_planets():
            if state.distance(p.ID, ep.ID) < 5:
                break
        nearest_enemy = min(state.enemy_planets(), key=lambda t: state.distance(t.ID, p.ID), default=None)
        if state.distance(nearest_enemy.ID, p.ID) < 3:
            return False
        other_planets = state.my_planets()
        other_planets.remove(p)
        closest_planet = min(other_planets, key=lambda mp: state.distance(p.ID, mp.ID), default=None)
        if closest_planet:
            return issue_order(state, p.ID, closest_planet.ID, p.num_ships * 0.9)
        return False
"""



