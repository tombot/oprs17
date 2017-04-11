from sys import argv
import sqlite3
import matplotlib.pyplot as plt

script, fname = argv

flatten = lambda l: [item for sublist in l for item in sublist]

with open(fname) as f:
    content = f.readlines()

conn = sqlite3.connect('oprs2017.db')

# you may also want to remove whitespace characters like `\n` at the end of each line
teams = filter(None, [x.strip() for x in content])

def getBest(team, stat):
  c = conn.execute('Select %s from oprs where team_number = ?;' % (stat), (team,))
  res = c.fetchall()
  nums = flatten(res)
  nums_sorted = sorted(nums, reverse=True)
  if len(nums_sorted) > 0:
    return nums_sorted[0]
  else:
    return 0

gears = {}
fuel = {}
auto_fuel = {}
takeoff = {}

for team in teams:
  auto_fuel[team] = getBest(team, 'auto_fuel_high_count_opr')
  fuel[team] = getBest(team, 'teleop_fuel_high_count_opr')
  gears[team] = getBest(team, 'gear_count_opr') 
  takeoff[team] = getBest(team, 'teleop_takeoff_points_opr')

auto_fuel_vals = sorted(auto_fuel.values(), reverse=True)
fuel_vals = sorted(fuel.values(), reverse=True)
gears_val = sorted(gears.values(), reverse=True)
takeoff_val = sorted(takeoff.values(), reverse=True)

fig, axes = plt.subplots(2, 2)
axes[0, 0].plot(auto_fuel_vals)
axes[0, 0].set_title('Auto fuel OPR')
axes[0, 1].plot(fuel_vals)
axes[0, 1].set_title('Tele fuel OPR')
axes[1, 0].plot(gears_val)
axes[1, 0].set_title('Gear OPR')
axes[1, 1].plot(takeoff_val)
axes[1, 1].set_title('Climb OPR')
fig.suptitle("STL Champs")
plt.show()
