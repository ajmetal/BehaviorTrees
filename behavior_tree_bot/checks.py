
def if_enemy_has_more_fleets(state):
  return len(state.enemy_fleets()) > len(state.my_fleets())

def if_neutral_planet_available(state):
  return any(state.neutral_planets())

def have_largest_production(state):
  return sum(planet.growth_rate for planet in state.my_planets()) \
          > sum(planet.growth_rate for planet in state.enemy_planets()) \

def have_largest_fleet(state):
  return sum(planet.num_ships for planet in state.my_planets()) \
            + sum(fleet.num_ships for fleet in state.my_fleets()) \
          > sum(planet.num_ships for planet in state.enemy_planets()) \
            + sum(fleet.num_ships for fleet in state.enemy_fleets())

def no_fleets(state):
  return len(state.my_fleets()) == 0