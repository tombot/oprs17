from sys import argv
import sqlite3
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import urllib2
import time

hou_urls = [
  "https://my.firstinspires.org/myarea/index.lasso?page=teamlist&event_type=FRC&sort_teams=number&year=2017&event=cmptx&skip_teams=0",
  "https://my.firstinspires.org/myarea/index.lasso?page=teamlist&event_type=FRC&sort_teams=number&year=2017&event=cmptx&skip_teams=250"
]
stl_urls = [
  "https://my.firstinspires.org/myarea/index.lasso?page=teamlist&event_type=FRC&sort_teams=number&year=2017&event=cmpmo&skip_teams=0",
  "https://my.firstinspires.org/myarea/index.lasso?page=teamlist&event_type=FRC&sort_teams=number&year=2017&event=cmpmo&skip_teams=250"
]

flatten = lambda l: [item for sublist in l for item in sublist]

def get_teams_from_urls(urls):
  teams = []
  for url in urls:
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    tables = soup.findAll("table")
    table = tables[2]
    for row in tables[2].findAll("tr"):
      if len(row.findAll("th")) < 1:
        teams.append(int(row.find("a").string))
  return teams

# with open(fname) as f:
#     content = f.readlines()

conn = sqlite3.connect('oprs2017.db')

# you may also want to remove whitespace characters like `\n` at the end of each line
# teams = filter(None, [x.strip() for x in content])

def getBest(team, stat):
  c = conn.execute('Select %s from oprs where team_number = ?;' % (stat), (team,))
  res = c.fetchall()
  nums = flatten(res)
  nums_sorted = sorted(nums, reverse=True)
  if len(nums_sorted) > 0:
    return nums_sorted[0]
  else:
    return 0

def make_title(title, teams):
  return title + " - " + time.strftime("%x") + " - " + str(len(teams)) + " teams"

def make_plots(title, teams):
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
  fig.suptitle(make_title(title, teams))
  plt.show()



make_plots("HOU CMP", get_teams_from_urls(hou_urls))
make_plots("STL CMP", get_teams_from_urls(stl_urls))
