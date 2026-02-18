#!python

from competition.Competition import *
from items.Items import *
from persistence.Persistence import *
from story.Story import *

import json, os, random, shutil, textwrap

# a collection of predefined ItemData
class DefaultItemDataFactory(ItemDataFactory):
  def __init__(self):
    super().__init__()
    self.loadDefaults()

  def loadDefaults(self):
    self.contents = []
    # self.add(type(properties), popularity, complexity, cost)
    self.add(Laser({"requiredPower": 1, "damage": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 2)
    self.add(Cutter({"requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 2)
    self.add(Battery({"maxCharge": 100, "dischargeRate": 3}), 2, 1, 2)
    self.add(Wall({"hitPoints": 4}), 2, 1, 1)
    self.add(Resistor({"dischargeRate": 0.01}), 1, 2, 1)
    self.add(Adder({"addition": 0.01, "maxInput": 10}), 1, 2, 1)
    self.add(Splitter({"maxInput": 1}), 1, 2, 1)
    self.add(Joiner({}), 1, 2, 1)
    self.add(If({"threshold": 0.05}), 1, 2, 1)
    self.add(Capacitor({"maxEnergy": 10, "signalOutputFraction": 0.01}), 1, 2, 1)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": 4, "maxSignalPower": 1, "maxPossibleDistance": 100}), 2, 2, 2)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100, "outputRatio": 0.01}), 1, 3, 1)

profile = Profile("../data/profile/")
itemDataFactory = FileItemDataFactory(DefaultItemDataFactory(), profile.getLatestPath("items"))
itemDataFactory.ensureSaved()
runLog = RunLog(profile.getLatestPath("runlog"))

print("Welcome to ColorNetwork!")
def offerChangeSettings():
  global itemDataFactory
  print("Choose settings for this game")
  menu = Menu()
  menu.addChoice("Same as last run", "Same")
  menu.addChoice("Different from last run", "Different")
  choice = menu.chooseValue()
  if choice == "Different":
    print("Creating something different")
    profile.incrementVersion("items")
    itemDataFactory = FileItemDataFactory(itemDataFactory, profile.getLatestPath("items"))
    itemDataFactory.cloneAndMutateRandomItem()
    itemDataFactory.saveFile()
    return
  print("Keeping settings the same as previous game")

if runLog.nonEmpty():
  offerChangeSettings()
  profile.incrementVersion("runlog")

runLog = RunLog(profile.getLatestPath("runlog"))
profile.save()

def makePlayer():
  player = GamePlayer("Player")
  return player

def makeStory():
  gamePlayer = makePlayer()
  length = 10
  difficulty = 1
  complexity = 1
  welcome = StoryGenerator(gamePlayer, length, difficulty, complexity, itemDataFactory, runLog).create()

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
