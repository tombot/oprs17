import sqlite3
import math
from collections import OrderedDict
from collections import defaultdict

conn = sqlite3.connect('oprs2017.db')

CHANCE_2_ROTORS_FOR_3_GEAR_OPRS = .3
NUM_SIMS = 100

flatten = lambda l: [item for sublist in l for item in sublist]

def getBestEventForTeam(team):
  c = conn.execute('select auto_gear_count_opr, auto_fuel_low_count_opr, auto_fuel_high_count_opr, teleop_gear_count_opr, teleop_fuel_low_count_opr, teleop_fuel_high_count_opr, teleop_takeoff_points_opr from oprs where team_number = ? order by total_points_opr DESC limit 1;', (team,))
  res = c.fetchone()
  return res


def getTeams():
  c = conn.execute('select distinct team_number from oprs;')
  return flatten(c.fetchall())

def getBestEvents():
  if getBestEvents.s_best_events != None:
    return getBestEvents.s_best_events
  teams = getTeams()
  best_events = {}
  for team in teams:
      best_events[team] = getBestEventForTeam(team)
  getBestEvents.s_best_events = best_events
  return best_events
getBestEvents.s_best_events = None

def getContributions(team):
  e = getBestEvents()[team]
  #return (auto_gear_count_opr, auto_fuel_low_count_opr, auto_fuel_high_count_opr, teleop_gear_count_opr, teleop_fuel_low_count_opr, teleop_fuel_high_count_opr, teleop_takeoff_points_opr, )
  return e

def mutateContributions(c):
  # TODO: Figure out how to mutate scores, probably just some random walking of values
  # Maybe add/subtract half a gear
  # and 20% of fuel (dont give people who don't shoot free fuel)
  # Apply monte carlo model here. For now, leave alone.
  return c

def addStats(stats, key):
  return reduce((lambda i, j: i+j), list(map(lambda x: x[key], stats)))

def runSimMatch(red1, red2, red3, blue1, blue2, blue3):
  r1 = mutateContributions(getContributions(red1))
  r2 = mutateContributions(getContributions(red2))
  r3 = mutateContributions(getContributions(red3))
  b1 = mutateContributions(getContributions(blue1))
  b2 = mutateContributions(getContributions(blue2))
  b3 = mutateContributions(getContributions(blue3))
  red = [r1, r2, r3]
  blue = [b1, b2, b3]
  scores = {}
  for a in [("red", red), ("blue", blue)]:
    s = a[1]
    auto_gears = addStats(s, 0)
    auto_low = addStats(s, 1)
    auto_high = addStats(s, 2)
    tele_gears = addStats(s, 3)
    tele_low = addStats(s, 4)
    tele_high = addStats(s, 5)
    takeoff = addStats(s, 6)
    # auto gears
    corrected_auto_gears = 3 if auto_gears >= 3 and random.random() < CHANCE_2_ROTORS_FOR_3_GEAR_OPRS else math.floor(auto_gears)
    num_auto_rotors = 2 if corrected_auto_gears >= 3 else 1 if corrected_auto_gears >= 1 else 0
    # auto fuel
    auto_fuel = (auto_low / 3.0) + auto_high
    # auto score
    auto_score = (num_auto_rotors * 60.0) + auto_fuel

    # take off
    takeoff_percentage = takeoff / 150.0
    takeoffs = 0 if takeoff_percentage < .1 else 1 if takeoff_percentage < .4 else 2 if takeoff_percentage < .7 else 3
    takeoff_score = takeoffs * 50.0

    # total gears
    total_gears = corrected_auto_gears + tele_gears + 1 # add prepop

    # Tele rotors
    num_rotors = 0 if total_gears < 1 else 1 if total_gears < 2 else 2 if total_gears < 4 else 3 if total_gears < 8 else 4
    tele_rotors = num_rotors - num_auto_rotors
    tele_rotor_score = tele_rotors * 40.
    # Tele fuel
    tele_fuel = (tele_low / 9.0) + (tele_high / 3.0)

    tele_score = tele_fuel + tele_rotor_score
    fuel_score = tele_fuel + auto_fuel

    total_score = takeoff_score + tele_score + auto_score

    extra_fuel_rp = fuel_score > 40.0
    extra_4_rotors_rp = num_rotors >= 4

    score = (total_score, auto_score, tele_score, fuel_score, num_rotors, takeoffs, extra_fuel_rp, extra_4_rotors_rp)
    scores[a[0]] = score
  return scores

def runSimMatchWrapper(m):
  return runSimMatch(m[0], m[1], m[2], m[3], m[4], m[5])

def runSimSchedule(matches):
  results = {}
  rp = {}
  num_matches = {}
  wins = {}
  rankings = {}
  losses = {}
  for i, match in enumerate(matches):
    match_i = i + 1
    match_results = runSimMatchWrapper(match)
    red_winner = match_results['red'][0] > match_results['blue'][0]
    blue_winner = not red_winner
    red_rp = (2 if red_winner else 0) + (1 if match_results['red'][6] else 0) +  (1 if match_results['red'][7] else 0)
    blue_rp = (2 if blue_winner else 0) + (1 if match_results['blue'][6] else 0) +  (1 if match_results['blue'][7] else 0)

    for team in match:
      if team not in num_matches:
        num_matches[team] = 0
      num_matches[team] += 1

    # Red
    for team in match[0:3]:
      if team not in rp:
        rp[team] = 0
      rp[team] += red_rp
      if team not in wins:
        wins[team] = 0
      if team not in losses:
        losses[team] = 0
      if red_winner:
        wins[team] += 1
      else:
        losses[team] += 1
    # Blue 
    for team in match[3:]:
      if team not in rp:
        rp[team] = 0
      rp[team] += blue_rp
      if team not in wins:
        wins[team] = 0
      if team not in losses:
        losses[team] = 0
      if blue_winner:
        wins[team] += 1
      else:
        losses[team] += 1

    results[match_i] = {
      "red_win": red_winner,
      "blue_win": blue_winner,
      "red_rp" : red_rp,
      "blue_rp": blue_rp,
      "info": match_results
    }

  rp_sorted_by_value = OrderedDict(sorted(rp.items(), key=lambda x: x[1], reverse=True))
  rank = 1
  for k, v in rp_sorted_by_value.items():
    rankings[k] = (rank, v)
    rank += 1

  return {
    "match_results": results,
    "rankings" : rankings,
    "wins":  wins,
    "losses": losses
  }


class Average:
  def __init__(self):
    self.num = 0
    self.total = 0
  def add(self, num):
    self.num += 1
    self.total += num
  def get(self):
    return self.total / (self.num * 1.0)


class ManyAverages:
  def __init__(self):
    self.items = {}
  def add(self, index, num):
    if index not in self.items:
      self.items[index] = Average()
    self.items[index].add(num)
  def get(self):
    ret = {}
    for i, v  in self.items.iteritems():
      ret[i] = v.get()
    return ret

def runSimScheduleIterations(matches, num_iters):
  rankings = ManyAverages()
  red_match_wins = ManyAverages()
  blue_match_wins = ManyAverages()
  red_match_kpa = ManyAverages()
  blue_match_kpa = ManyAverages()
  red_match_rotor_rp = ManyAverages()
  blue_match_rotor_rp = ManyAverages()
  red_match_score = ManyAverages()
  blue_match_score = ManyAverages()
  red_rps = ManyAverages()
  blue_rps = ManyAverages()

  num_matches = len(matches)
  for i in range(1, num_iters + 1):
    results = runSimSchedule(matches)
    for match_num, r in results["match_results"].iteritems():
      red_match_wins.add(match_num, 1 if r["red_win"] else 0)
      blue_match_wins.add(match_num, 1 if r["blue_win"] else 0)
      
      red_rps.add(match_num, r["red_rp"])
      blue_rps.add(match_num, r["blue_rp"])

      red_match_kpa.add(match_num, r["info"]["red"][6])
      blue_match_kpa.add(match_num, r["info"]["blue"][6])

      red_match_rotor_rp.add(match_num, r["info"]["red"][7])
      blue_match_rotor_rp.add(match_num, r["info"]["blue"][7])

      red_match_score.add(match_num, r["info"]["red"][0])
      blue_match_score.add(match_num, r["info"]["blue"][0])
    for team, rank_info in results["rankings"].iteritems():
      rankings.add(team, rank_info[0])

  red_wins_res = red_match_wins.get()
  blue_wins_res = blue_match_wins.get()

  red_score_res = red_match_score.get()
  blue_score_res = blue_score_res.get()

  red_rps_res = red_rps.get()
  blue_rps_res = blue_rps.get()

  red_kpa_res = red_match_kpa.get()
  blue_kpa_res = blue_match_kpa.get()

  red_rotor_res = red_match_rotor_rp.get()
  blue_rotor_res = blue_match_rotor_rp.get()

  results_csv = "match, r1, r2, r3, b1, b2, b3, redWin%, blueWin%, redScore, blueScore, redRps, blueRps, redKpaRp, blueKpaRp, redRotorRp, blueRotorRp\n"
  for i in range(1, num_matches + 1):
    m = matches[i-1]
    results_csv +=  ("%d, %d, %d, %d, %d, %d, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f\n" % (i, m[0], m[1], m[2], m[3], m[4], m[5], red_wins_res[i], blue_wins_res[i], red_score_res[i], blue_score_res[i], red_rps_res[i], blue_rps_res[i], red_kpa_res[i], blue_kpa_res[i], red_rotor_res[i], blue_rotor_res[i]))
  print "Match results (%d iterations):" % NUM_SIMS
  print
  print results_csv

  rankings_res = rankings.get()
  rankings_sorted_by_value = OrderedDict(sorted(rankings_res.items(), key=lambda x: x[1], reverse=False))
  rank = 1
  print
  print
  print "Rankings:"
  print
  for k, v in rankings_sorted_by_value.items():
    print "%d, %d, %.2f" % (rank, k, v)
    rank += 1

# TODO: Parse matches from text file or something, copied from pdf
# For now, here is a sample

matches_ = [
  [254, 604, 8, 118, 173, 71],
  [839, 4990, 16, 114, 1114, 2056],
  [254, 2056, 1538, 839, 115, 694]
]


runSimScheduleIterations(matches_, NUM_SIMS)
