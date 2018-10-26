import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
from math import sqrt

import logging, traceback, os, inspect

logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)

#################################################################################################################
#returns a list ordered by priority comparing distance vs. strength FAVORING DISTANCE
def closest_sorted(state, from_planet, planets):
    return sorted(planets, key=lambda i: state.distance(from_planet.ID, i.ID))

#################################################################################################################
def get_first_beatable(state, from_planet, planets):
    by_closest = closest_sorted(state, from_planet, planets)
    targets = [f.destination_planet for f in state.my_fleets()]
    by_closest = list(filter(lambda i: i.ID not in targets, by_closest))
    for p in by_closest:
        if p.num_ships + (state.distance(from_planet.ID, p.ID) * p.growth_rate) + 1 < from_planet.num_ships:
            return p
    return None

#################################################################################################################
def get_closest_ally(state, from_planet):
    return min(list(filter(lambda i: i.ID != from_planet.ID, state.my_planets())), key=lambda x: state.distance(from_planet.ID, x.ID), default=None)

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

#################################################################################################################
def desperado_attack(state):
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
                    return issue_order(state, p.ID, weakest_enemy.ID, p.num_ships - 1)
                elif weakest_neutral:
                    return issue_order(state, p.ID, weakest_neutral.ID, p.num_ships - 1)
                elif closest_ally:
                    return issue_order(state, p.ID, closest_ally.ID, p.num_ships - 1)
                return False
            except Exception:
                return False

#################################################################################################################
def spread_to_closest_neutral_planet(state):

    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    if not strongest_planet: return False

    closest_planet = get_first_beatable(state, strongest_planet, state.neutral_planets())
    if not closest_planet: return False

    if strongest_planet.num_ships * 0.75 < closest_planet.num_ships:
        return False

    return issue_order(state, strongest_planet.ID, closest_planet.ID, closest_planet.num_ships + 1)

#################################################################################################################
def interrupt_enemy_spread(state):
    for f in state.enemy_fleets():
        if f.destination_planet in state.neutral_planets():
           attack_from = list(filter(lambda p: p.num_ships > f.num_ships + 2, state.my_planets()))
           if len(attack_from != 0):
              return issue_order(state, attack_from[0].ID, f.destination_planet, attack_from[0].num_ships - 1)

#################################################################################################################
def spread_to_closest_enemy_planet(state):

    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    if strongest_planet is None: return False

    closest_enemy = get_first_beatable(state, strongest_planet, state.enemy_planets())
    if not closest_enemy: return False

    return issue_order(state, strongest_planet.ID, closest_enemy.ID, strongest_planet.num_ships)


