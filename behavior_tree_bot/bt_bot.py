#!/usr/bin/env python
#

"""
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own.
"""
import logging, traceback, sys, os, inspect, time
from math import inf

logging.basicConfig(filename=__file__[:-3] +'.log', filemode='w', level=logging.DEBUG)
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from behavior_tree_bot.behaviors import *
from behavior_tree_bot.checks import *
from behavior_tree_bot.bt_nodes import *

from planet_wars import PlanetWars, finish_turn

# You have to improve this tree or create an entire new one that is capable
# of winning against all the 5 opponent bots
def setup_behavior_tree():

    # Top-down construction of behavior tree
    root = Selector(name='Root')

    largest_fleet_check = Check(have_largest_fleet)
    check_production = Check(have_largest_production)
    check_neutral_planet = Check(more_neutral_than_owned)
    check_has_biggest_plnaet = Check(dont_have_biggest_planet)

    #attack > spread strategy

    selector_attack = Selector(name="attack > spread")

    action_desperado = Action(desperado_attack)
    action_attack_enemy = Action(spread_to_closest_enemy_planet)
    action_attack_neutral = Action(spread_to_closest_neutral_planet)
    action_defend = Action(defend_my_planets)
    action_reinforce = Action(reinforce_strongest)
    action_interrupt = Action(interrupt_enemy_spread)

    #repeater_attack = Repeater(child_nodes=[action_attack_enemy_from_any], name="Attack multiple times", count=3)
    """
    selector_attack.child_nodes = [action_desperado, action_attack_enemy_solo, action_attack_neutral_solo]

    sequence_offense.child_nodes = [check_production, selector_attack]

    #total offensive strat
    sequence_full_attack = Sequence(name="all out attack")

    selector_full_attack = Selector(name="full attack")
    #selector_full_attack.child_nodes = [Repeater(child_nodes=[action_attack_enemy_from_any], name="Attack multiple times", count=20)]

    sequence_full_attack.child_nodes = [check_fleet, selector_full_attack]

    repeat_spread = Repeater(name="spread multiple", count=20)
    repeat_spread.child_nodes = [check_neutral_planet, action_attack_neutral_solo]

    """

    sequence_offense = Sequence(name="take offensive stance")
    sequence_offense.child_nodes = [largest_fleet_check, action_attack_enemy]

    #sequence_greed = Sequence(name="Try to take neutral planets")
    #sequence_greed.child_nodes = [largest_fleet_check, action_attack_neutral]
    
    #repeater_spread = Repeater(child_nodes=[action_attack_neutral], name="spread multiple times", count=3)

    #sequence_defense
    #full tree
    root.child_nodes = [Action(start_execution), action_reinforce, action_interrupt, action_attack_enemy, action_attack_neutral,]

    logging.info('\n' + root.tree_to_string())
    return root

# You don't need to change this function
def do_turn(state):
    behavior_tree.execute(planet_wars)

if __name__ == '__main__':
    logging.basicConfig(filename=__file__[:-3] + '.log', filemode='w', level=logging.DEBUG)

    behavior_tree = setup_behavior_tree()
    try:
        map_data = ''
        while True:
            current_line = input()
            if len(current_line) >= 2 and current_line.startswith("go"):
                planet_wars = PlanetWars(map_data)
                do_turn(planet_wars)
                finish_turn()
                map_data = ''
            else:
                map_data += current_line + '\n'

    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
    except Exception:
        traceback.print_exc(file=sys.stdout)
        logging.exception("Error in bot.")
