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
def get_closest_ally(state, from_planet):
    if stop_execution(): return None
    return min(list(filter(lambda i: i.ID != from_planet.ID, state.my_planets())), key=lambda x: state.distance(from_planet.ID, x.ID), default=None)

#################################################################################################################
def is_being_targetted(state, my_planet):
    if stop_execution(): return None
    #enemy_targets = [f.destination_planet for f in state.enemy_fleets()]
    for f in state.enemy_fleets():
        if f.destination_planet == my_planet.ID:
            return f
    return None
    
#################################################################################################################
def defend(state):
    my_IDs = [p.ID for p in state.my_planets()]
    for f in state.enemy_fleets():
        if f.destination_planet in my_IDs:
            my_planet = state.planets[f.destination_planet]
            min_size = f.num_ships + (my_planet.growth_rate * f.turns_remaining) + 1
            defending_fleets = list(filter(lambda i: i.destination_planet == my_planet.ID, state.my_fleets()))
            if min_size > f.num_ships > sum([f.num_ships for f in defending_fleets]):
                return my_planet
    return None

#################################################################################################################
def clamp(n, smallest, largest): return max(smallest, min(n, largest))

#################################################################################################################
def desperado_attack(state):
    if stop_execution(): return True
    # p.num_ships + (fleet.turns_remaining * 5) + 1 - fleet.num_ships = how many ships I need to survive an attack
    for f in state.enemy_fleets():
        p = state.planets[f.destination_planet]

        #fleets are moved before planet ships are incremented!
        if f.turns_remaining == 1 and p.num_ships - f.num_ships < 1:
            weakest_enemy = get_first_beatable(state, p, state.enemy_planets())
            weakest_neutral = get_first_beatable(state, p, state.neutral_planets())
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
def get_most_threatening(state, from_planet):
    if stop_execution(): return None
    avg_ally = {"x":0, "y":0}
    allies = state.my_planets()
    if not allies or len(allies) == 0:
        return True
    avg_ally["x"] = sum(i.x for i in allies) / len(allies)
    avg_ally["y"] = sum(i.y for i in allies) / len(allies)
    enemies = list(sorted(state.enemy_planets(), key=lambda i: sqrt((avg_ally['x'] - i.x) ** 2 + (avg_ally['y'] - i.y) ** 2)))
    for p in enemies:
        if p in [f.destination_planet for f in state.my_fleets()]:
            continue
        if p.num_ships + (state.distance(from_planet.ID, p.ID) * p.growth_rate) + 1 < from_planet.num_ships:
            return p
    return None

#################################################################################################################
def spread_to_closest_neutral_planet(state):
    return spread_to_planet(state, state.neutral_planets())

#################################################################################################################
def spread_to_closest_enemy_planet(state):
    return spread_to_planet(state, state.enemy_planets(), target_enemy=True)

#################################################################################################################
def spread_to_planet(state, planets, target_enemy=False):
    while True:
        if stop_execution(): return True
        strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
        if not strongest_planet: return True
        closest_target = None
        fleet_size = 0
        planets = list(filter(lambda i: i.ID not in [f.destination_planet for f in state.my_fleets()], planets))
        if target_enemy:
            closest_target = get_first_beatable(state, strongest_planet, planets)
            #closest_target = get_most_threatening(state, strongest_planet)
            if not closest_target: return False
            fleet_size = min_fleet_size(state, strongest_planet, closest_target)
        else:
            #closest_target = get_first_beatable(state, strongest_planet, planets)
            current_targets = [f.destination_planet for f in state.my_fleets()]
            neutral = list(sorted(filter(lambda i: i.ID not in current_targets, planets), key=lambda i : i.num_ships))
            logging.debug('\nneutral planets: ' + str(neutral))
            if neutral:
                closest_target = neutral[0]
                fleet_size = closest_target.num_ships + 1
                logging.debug('\nclosest nuetral: ' + str(closest_target))
        if not closest_target: return False
        
        enemy_fleets = list(filter(lambda i: i.destination_planet == closest_target.ID, state.enemy_fleets()))
        in_transit_enemies = sum([f.num_ships for f in enemy_fleets])

        fleet_size += in_transit_enemies

        if fleet_size > strongest_planet.num_ships:
            return False
        issue_order(state, strongest_planet.ID, closest_target.ID, fleet_size)

#################################################################################################################
def reinforce(state):
    average_enemy = { "x" : 0, "y" : 0 }
    enemies = state.enemy_planets()
    if not enemies or len(enemies) == 0:
        return True
    average_enemy["x"] = sum(i.x for i in enemies) / len(enemies)
    average_enemy["y"] = sum(i.y for i in enemies) / len(enemies)
    to_defend = defend(state)
    by_distance = list(sorted(state.my_planets(), key=lambda i: sqrt((average_enemy['x'] - i.x) ** 2 + (average_enemy['y'] - i.y) ** 2)))
    reinforce_target = None
    if to_defend:
        reinforce_target = to_defend
    else:
        if by_distance != []:
            reinforce_target = by_distance[0]
        else: 
            return False
    for i in by_distance:
        enemies_approaching = sum([f.num_ships for f in state.enemy_fleets() if f.destination_planet == i.ID])
        if i.num_ships + 1 < enemies_approaching:
            continue
        issue_order(state, i.ID, reinforce_target.ID, i.growth_rate)    
    return True

#################################################################################################################
def attack(state):
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships))

    enemy_planets = [planet for planet in state.enemy_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    enemy_planets.sort(key=lambda p: p.num_ships)

    target_planets = iter(enemy_planets)

    try:
        my_planet = next(my_planets)
        target_planet = next(target_planets)
        while True:
            required_ships = target_planet.num_ships + \
                                 state.distance(my_planet.ID, target_planet.ID) * target_planet.growth_rate + 1

            
            if my_planet.num_ships > required_ships:
                enemies_approaching = sum([f.num_ships for f in state.enemy_fleets() if f.destination_planet == my_planet.ID])
                if my_planet.num_ships - required_ships + 1 > enemies_approaching:
                    issue_order(state, my_planet.ID, target_planet.ID, required_ships)
                my_planet = next(my_planets)
                target_planet = next(target_planets)
            else:
                my_planet = next(my_planets)

    except StopIteration:
        return True

#################################################################################################################
def spread(state):
    my_planets = iter(sorted(state.my_planets(), key=lambda p: p.num_ships))

    neutral_planets = [planet for planet in state.neutral_planets()
                      if not any(fleet.destination_planet == planet.ID for fleet in state.my_fleets())]
    neutral_planets.sort(key=lambda p: p.num_ships)

    target_planets = iter(neutral_planets)

    try:
        my_planet = next(my_planets)
        target_planet = next(target_planets)
        while True:
            required_ships = target_planet.num_ships + 1
            if target_planet.ID in [f.destination_planet for f in state.enemy_fleets()]:
                closest_fleet = min(list(sorted(state.enemy_fleets(), key=lambda f: f.turns_remaining))) 
                distance_difference = state.distance(my_planet.ID, target_planet.ID) - closest_fleet.turns_remaining
                if distance_difference > 0:
                    required_ships += distance_difference * target_planet.growth_rate
                else:
                    required_ships += sum([f.num_ships for f in state.enemy_fleets() if f.destination_planet == target_planet.ID])
            
            enemies_approaching = sum([f.num_ships for f in state.enemy_fleets() if f.destination_planet == my_planet.ID])
            if my_planet.num_ships - required_ships + 1 > enemies_approaching:
                issue_order(state, my_planet.ID, target_planet.ID, required_ships)
                my_planet = next(my_planets)
                target_planet = next(target_planets)
            else:
                my_planet = next(my_planets)

    except StopIteration:
        return True

#################################################################################################################
def team_attack(state):
    #Planet = namedtuple('Planet', ['ID', 'x', 'y', 'owner', 'num_ships', 'growth_rate'])
    my_planets = state.my_planets()#list(iter(sorted(state.my_planets(), key=lambda p: p.num_ships, reverse=True)))
    my_targets = [f.destination_planet for f in state.my_fleets()]
    fleet_strength = sum([f.num_ships for f in state.my_fleets()])
    for enemy in state.enemy_planets():
        if enemy.ID in my_targets: break
        for ally in my_planets:
            if stop_execution(): return True
            min_ships = enemy.num_ships + (enemy.growth_rate * state.distance(ally.ID, enemy.ID)) + 1
            #issue_order(state, ally.ID, enemy.ID, ((ally.num_ships * (min_ships / ally.num_ships)) / len(my_planets)) - len(my_planets))
            issue_order(state, ally.ID, enemy.ID, clamp(fleet_strength / len(my_planets), min_ships / len(my_planets), ally.num_ships - 1))
            #return True
    return True

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



#################################################################################################################
def interrupt_enemy_spread(state):
    for f in state.enemy_fleets():
        if f.destination_planet in [i.ID for i in state.neutral_planets()] and not f.destination_planet in [fleet.destination_planet for fleet in state.my_fleets()]:
            attack_from = list(filter(lambda p: state.distance(p.ID, f.destination_planet) - 1 == f.turns_remaining, state.my_planets()))
            #logging.debug("\ninterruptable: " + str(attack_from))
            #if attack_from != []:
            for p in attack_from:
                #fleet_size = state.planets[f.destination_planet].growth_rate * state.distance(p.ID, f.destination_planet) + 2
                fleet_size = 2
                if p.num_ships > fleet_size:
                    issue_order(state, p.ID, f.destination_planet, fleet_size)
                    break
    return False



