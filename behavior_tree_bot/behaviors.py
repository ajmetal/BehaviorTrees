import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
from math import sqrt

import logging, traceback, os, inspect

logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)

def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, (strongest_planet.num_ships / 2) - 1)

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

def desperado_attack(state):
    # p.num_ships + (fleet.turns_remaining * 5) + 1 - fleet.num_ships = how many ships I need to survive an attack
    for f in state.enemy_fleets():
        p = state.planets[f.destination_planet]
        #fleets are moved before planet ships are incremented!
        if f.turns_remaining == 1 and p.num_ships - f.num_ships < 1:
            weakest_planet = min(state.neutral_planets(), key=lambda x: x.num_ships, default=None)
            #if weakest_planet.num_ships > p.num_ships - 1:
            #    closest_ally = min(state.my_planets, key=lambda x: state.distance(p.ID, x.ID), default=None)
            #    return issue_order(state, p.ID, closest_ally.ID, p.num_ships - 1)
            #else:
            if weakest_planet:
                return issue_order(state, p.ID, weakest_planet.ID, p.num_ships - 1)
            return False

#This is mostly for practice.
def spread_to_closest_neutral_planet(state):

    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    if not strongest_planet: return False
    # (3) find the closest neutral planet to my strongest
    closest_planet = min(state.neutral_planets(), key=lambda p: state.distance(p.ID, strongest_planet.ID), default=None)

    if not strongest_planet or not closest_planet:
        # No legal source or destination
        return False

    if strongest_planet.num_ships * 0.75 < closest_planet.num_ships:
        return False

    return issue_order(state, strongest_planet.ID, closest_planet.ID, strongest_planet.num_ships * 0.75)

def interrupt_enemy_spread(state):
    for f in state.enemy_fleets():
        if f.destination_planet in state.neurtral_planets():
           attack_from = list(filter(lambda p: p.num_ships > f.num_ships + 2, state.my_planets()))
           if len(attack_from != 0):
              return issue_order(state, attack_from[0].ID, f.destination_planet, attack_from[0].num_ships - 1)


#This is mostly for practice.
def spread_to_closest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    #if len(state.my_fleets()) >= 3:
    #    return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)
    if strongest_planet is None: return False
    # (3) find the closest neutral planet to my strongest
    closest_enemies = sorted(state.enemy_planets(), key=lambda p: state.distance(p.ID, strongest_planet.ID))
    target = None
    for enemy in closest_enemies:
        if strongest_planet.num_ships > enemy.num_ships + (state.distance(strongest_planet.ID, enemy.ID) * enemy.growth_rate) + 2:
            target = enemy
            break
    if target:
        return issue_order(state, strongest_planet.ID, target.ID, strongest_planet.num_ships)
    return False


