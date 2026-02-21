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

profile = Profile("data/profile/")
itemDataFactory = FileItemDataFactory(DefaultItemDataFactory(), profile.getLatestPath("items"))
itemDataFactory.ensureSaved()
runLog = RunLog(profile.getLatestPath("runlog"), itemDataFactory)

def getItemPurchaseCounts(runLog, itemDataFactory):
  counts = {}
  for itemData in itemDataFactory.getAll():
    counts[itemData.name] = 0
  shopEntries = runLog.getShopEntries()
  for entry in shopEntries:
    for itemData in entry.purchased:
      name = itemData.name
      count = counts.get(name, 0)
      counts[name] = count + 1
  return counts

print("Welcome to ColorNetwork!")
def raiseDifficulty(multiplier, purchaseCounts):
  global itemDataFactory
  # raise prices of items that were purchased the most
  averageCostMultiplier = multiplier
  totalNumPurchases = sum(purchaseCounts.values())
  numPossibleItems = len(itemDataFactory.getAll())
  increasePerPurchase = (averageCostMultiplier - 1) * numPossibleItems / totalNumPurchases
  for itemName, purchaseCount in purchaseCounts.items():
    if purchaseCount > 0:
      itemData = itemDataFactory.getTemplateNamed(itemName)
      oldCost = itemData.cost
      newCost = oldCost * (1 + purchaseCount * increasePerPurchase)
      print("increasing cost of " + itemName + " from " + str(oldCost) + " to " + str(newCost) + " due to being bought " + str(purchaseCount) + "/" + str(totalNumPurchases) + " times")
      itemData.cost = newCost

def lowerDifficulty(multiplier):
  global itemDataFactory
  # lower all prices equally
  for itemData in itemDataFactory.getAll():
    itemData.cost /= multiplier

def adjustShopFrequencies(multiplier, purchaseCounts):
  # raise the popularity of items that were purchased more
  oldWeight = 1 / multiplier
  newWeight = 1 - oldWeight
  totalNumPurchases = sum(purchaseCounts.values())
  totalPopularity = sum([itemData.popularity for itemData in itemDataFactory.getAll()])
  popularityPerPurchase = totalPopularity / totalNumPurchases
  for itemName in purchaseCounts:
    itemTemplate = itemDataFactory.getTemplateNamed(itemName)
    oldPopularity = itemTemplate.popularity
    newPopularity = oldPopularity * oldWeight + purchaseCounts[itemName] * popularityPerPurchase * newWeight
    print("changing popularity of " + itemName + " from " + str(oldPopularity) + " to " + str(newPopularity))
    itemTemplate.popularity = newPopularity

def offerChangeSettings():
  global itemDataFactory
  purchaseCounts = getItemPurchaseCounts(runLog, itemDataFactory)
  numPurchases = sum(purchaseCounts.values())
  if numPurchases < 1:
    return # didn't buy anything
  print("Choose settings for this game")
  menu = Menu()
  menu.addChoice("Same as last run", "Same")
  menu.addChoice("Easier than last run", "Easier")
  menu.addChoice("Harder than last run", "Harder")
  menu.addChoice("Different than last run", "Different")
  choice = menu.chooseValue()
  if choice == "Same":
    print("Keeping settings the same as previous game")
    return
  # make a new item factory based on the previous one
  profile.incrementVersion("items")
  itemDataFactory = FileItemDataFactory(itemDataFactory, profile.getLatestPath("items"))
  changeMultiplier = 1.1
  if choice == "Harder" or choice == "Different":
    raiseDifficulty(changeMultiplier, purchaseCounts)
  if choice == "Easier" or choice == "Different":
    lowerDifficulty(changeMultiplier)
  adjustShopFrequencies(changeMultiplier, purchaseCounts)
  itemDataFactory.ensureSaved()
  print("Ok!")

if runLog.nonEmpty():
  offerChangeSettings()
  profile.incrementVersion("runlog")

runLog = RunLog(profile.getLatestPath("runlog"), itemDataFactory)
profile.save()

def makePlayer():
  player = GamePlayer("Player")
  return player

def makeStory():
  gamePlayer = makePlayer()
  length = 10
  difficulty = 1
  complexity = 3
  welcome = StoryGenerator(gamePlayer, length, difficulty, complexity, itemDataFactory, runLog).create()

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
