
def if_enemy_has_more_fleets(state):
    return len(state.enemy_fleets()) > len(state.my_fleets())

def if_neutral_planet_available(state):
    return any(state.neutral_planets())

def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

# Returns the ID of the closest neutral planet, or None if all planets are claimed
def closest_neutral_planet(state):
  closestDistance = 1000000
  for myPlanet in state.my_planets():
    for neutralPlanet in state.neutral_planets():
      if state.distance(myPlanet, neutralPlanet) < closestDistance:
        closestDistance = state.distance(myPlanet, neutralPlanet)
        CNP = neutralPlanet.ID()
  if CNP != None:
    return CNP
  else:
    return None