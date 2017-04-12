from sys import argv
import sqlite3
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import urllib2
import time
import numpy as np

NUM_TOP_TEAMS = 39

def make_url_for_event_and_skip(event, skip):
  return "https://my.firstinspires.org/myarea/index.lasso?page=teamlist&event_type=FRC&sort_teams=number&year=2017&event=" + event + "&skip_teams=" + str(skip)

def make_new_url_for_event_and_skip(event, skip):
  return "https://frc-events.firstinspires.org/2017/" + event


flatten = lambda l: [item for sublist in l for item in sublist]

def get_teams_from_urls(urls, new_type = False):
  teams = []
  for url in urls:
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    tables = soup.findAll("table")
    for row in tables[1].findAll("tr"):
      if len(row.findAll("th")) < 1:
        teams.append(int(row.find("a").string))
  return teams

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
  return title + " - " + time.strftime("%x")


def make_plots(event_infos):
  global_fig, g_axes = plt.subplots(2, 3)
  g_axes[0, 0].set_title('Auto fuel OPR')
  g_axes[0, 0].set_ylabel('# Balls')
  g_axes[0, 0].set_xlabel('Percentile')
  g_axes[0, 1].set_title('Tele fuel OPR')
  g_axes[0, 1].set_ylabel('# Balls')
  g_axes[0, 1].set_xlabel('Percentile')
  g_axes[0, 2].set_title('Fuel OPR')
  g_axes[0, 2].set_ylabel('# Points')
  g_axes[0, 2].set_xlabel('Percentile')
  g_axes[1, 0].set_title('Gear OPR')
  g_axes[1, 0].set_ylabel('# Gears')
  g_axes[1, 0].set_xlabel('Percentile')
  g_axes[1, 1].set_title('Climb OPR')
  g_axes[1, 1].set_ylabel('Climb points')
  g_axes[1, 1].set_xlabel('Percentile')

  top_n_fig, top_n_axes = plt.subplots(2, 3)
  top_n_axes[0, 0].set_title('Auto fuel OPR')
  top_n_axes[0, 0].set_ylabel('# Balls')
  top_n_axes[0, 0].set_xlabel('Team index')
  top_n_axes[0, 1].set_title('Tele fuel OPR')
  top_n_axes[0, 1].set_ylabel('# Balls')
  top_n_axes[0, 1].set_xlabel('Team index')
  top_n_axes[0, 2].set_title('Fuel OPR')
  top_n_axes[0, 2].set_ylabel('# Points')
  top_n_axes[0, 2].set_xlabel('Team index')
  top_n_axes[1, 0].set_title('Gear OPR')
  top_n_axes[1, 0].set_ylabel('# Gears')
  top_n_axes[1, 0].set_xlabel('Team index')
  top_n_axes[1, 1].set_title('Climb OPR')
  top_n_axes[1, 1].set_ylabel('Climb points')
  top_n_axes[1, 1].set_xlabel('Team index')

  event_names = []
  for event_info in event_infos:
    gears = {}
    fuel = {}
    fuel_points = {}
    auto_fuel = {}
    takeoff = {}
    event_name, teams = event_info
    event_names.append(event_name)
    for team in teams:
      auto_fuel[team] = getBest(team, 'auto_fuel_high_count_opr')
      fuel[team] = getBest(team, 'teleop_fuel_high_count_opr')
      gears[team] = getBest(team, 'gear_count_opr')
      takeoff[team] = getBest(team, 'teleop_takeoff_points_opr')
      fuel_points[team] = (fuel[team] / 3.0) + auto_fuel[team]

    auto_fuel_vals = sorted(auto_fuel.values(), reverse=True)
    fuel_vals = sorted(fuel.values(), reverse=True)
    gears_val = sorted(gears.values(), reverse=True)
    takeoff_val = sorted(takeoff.values(), reverse=True)
    fuel_points_val = sorted(fuel_points.values(), reverse=True)
    percentiles = np.arange(0., 100.0, (100./float(len(teams))));

    g_axes[0, 0].plot(percentiles, auto_fuel_vals)
    g_axes[0, 1].plot(percentiles, fuel_vals)
    g_axes[0, 2].plot(percentiles, fuel_points_val)
    g_axes[1, 0].plot(percentiles, gears_val)
    g_axes[1, 1].plot(percentiles, takeoff_val)


    nums  = np.arange(0, NUM_TOP_TEAMS, 1);
    top_n_axes[0, 0].plot(nums, auto_fuel_vals[0:NUM_TOP_TEAMS])
    top_n_axes[0, 1].plot(nums, fuel_vals[0:NUM_TOP_TEAMS])
    top_n_axes[0, 2].plot(nums, fuel_points_val[0:NUM_TOP_TEAMS])
    top_n_axes[1, 0].plot(nums, gears_val[0:NUM_TOP_TEAMS])
    top_n_axes[1, 1].plot(nums, takeoff_val[0:NUM_TOP_TEAMS])

  g_axes[0, 0].legend(event_names, loc='upper right')
  top_n_axes[0, 0].legend(event_names, loc='upper right')

  global_fig.suptitle(make_title("Normalized OPR Comparison", teams))
  top_n_fig.suptitle(make_title("Top " + str(NUM_TOP_TEAMS) + " OPR Comparison", teams))
  plt.show(global_fig)
  plt.show(top_n_fig)


# main start here
conn = sqlite3.connect('oprs2017.db')
hou_urls = [
  make_url_for_event_and_skip("cmptx", 0),
  make_url_for_event_and_skip("cmptx", 250)
]
stl_urls = [
  make_url_for_event_and_skip("cmpmo", 0),
  make_url_for_event_and_skip("cmptx", 250)
]
other_events = [
  # ["SJ", "casj"],
  # ["LV", "nvlv"],
  # ["NECMP", "necmp"]
  ["Consumers", "micmp1"],
  ["Dow", "micmp2"],
  ["DTE", "micmp3"],
  ["Ford", "micmp4"]
]
# events = [
#   ["HOU CMP", get_teams_from_urls(hou_urls)],
#   ["STL CMP", get_teams_from_urls(stl_urls)],
# ]
events = []
for e in other_events:
  events.append([e[0], get_teams_from_urls([make_new_url_for_event_and_skip(e[1], 0)], True)])

make_plots(events)
