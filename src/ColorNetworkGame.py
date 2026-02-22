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
    self.add(Laser({"requiredPower": 1, "damage": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 20)
    self.add(Cutter({"requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 20)
    self.add(Battery({"maxCharge": 100, "dischargeRate": 3}), 2, 1, 20)
    self.add(Wall({"hitPoints": 4}), 2, 1, 10)
    self.add(Resistor({"dischargeRate": 0.01}), 1, 2, 10)
    self.add(Adder({"addition": 0.01, "maxInput": 10}), 1, 2, 10)
    self.add(Splitter({"maxInput": 1}), 1, 2, 10)
    self.add(Joiner({}), 1, 2, 10)
    self.add(If({"threshold": 0.05}), 1, 2, 10)
    self.add(Capacitor({"maxEnergy": 10, "signalOutputFraction": 0.01}), 1, 2, 10)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": 4, "maxSignalPower": 1, "maxPossibleDistance": 100}), 2, 2, 20)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100, "outputRatio": 0.01}), 1, 3, 10)

profile = Profile("data/profile/")
itemDataFactory = FileItemDataFactory(DefaultItemDataFactory(), profile.getLatestPath("items"))
itemDataFactory.ensureSaved()
competitionBuilder = CompetitionBuilder(profile.getLatestPath("rooms"))
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

def raiseCosts(averageCostMultiplier, purchaseCounts):
  global itemDataFactory
  # raise prices of items that were purchased the most
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

def lowerCosts(multiplier):
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

def rescaleRoomDifficulties(difficultyMultiplier, competitionResults):
  for i in range(competitionBuilder.getMaxLength()):
    difficulty = competitionBuilder.getDifficulty(i)
    competitionBuilder.rescaleDifficulty(i, difficultyMultiplier)
    newDifficulty = competitionBuilder.getDifficulty(i)
    print("Rescaled difficulty at " + str(i) + " from " + str(difficulty) + " to " + str(newDifficulty))

def lowerRoomDifficulties(difficultyMultiplier, competitionResults):
  numFailures = 0
  for entry in competitionResults:
    if not entry.successful:
      numFailures += 1
  if numFailures < 1:
    # if there is no data, then rescale all difficulty settings by the same amount
    rescaleRoomDifficulties(1 / difficultyMultiplier, competitionResults)
    return
  multiplierPerFailure = pow(difficultyMultiplier, competitionBuilder.getMaxLength() / numFailures)
  for entry in competitionResults:
    if not entry.successful:
      index = int(entry.name)
      difficulty = competitionBuilder.getDifficulty(index)
      competitionBuilder.rescaleDifficulty(index, 1 / multiplierPerFailure)
      newDifficulty = competitionBuilder.getDifficulty(index)
      print("Rescaled difficulty at " + str(index) + " from " + str(difficulty) + " to " + str(newDifficulty))

def offerChangeSettings():
  global itemDataFactory
  purchaseCounts = getItemPurchaseCounts(runLog, itemDataFactory)
  numPurchases = sum(purchaseCounts.values())
  if numPurchases < 1:
    return # didn't buy anything
  competitionResults = runLog.getCompetitionEntries()
  print("Choose settings for this game")
  menu = Menu()
  menu.addChoice("Same as last run", "Same")
  menu.addChoice("Easier than last run", "Easier")
  menu.addChoice("Harder than last run", "Harder")
  menu.addChoice("Shorter than last run", "Shorter")
  menu.addChoice("Longer than last run", "Longer")
  menu.addChoice("Different than last run", "Different")
  choice = menu.chooseValue()
  if choice == "Same":
    print("Keeping settings the same as previous game")
    return
  changeMultiplier = 1.1
  # adjust length if requested
  if choice == "Shorter":
    profile.incrementVersion("rooms")
    competitionBuilder.decrementLength()
  if choice == "Longer":
    profile.incrementVersion("rooms")
    competitionBuilder.incrementLength()
  # adjust difficulty if requested
  if choice in ["Easier", "Harder"]:
    # make a new item factory based on the previous one
    profile.incrementVersion("items")
    profile.incrementVersion("rooms")
    itemDataFactory = FileItemDataFactory(itemDataFactory, profile.getLatestPath("items"))
    if choice == "Harder":
      raiseCosts(changeMultiplier, purchaseCounts)
      rescaleRoomDifficulties(changeMultiplier, competitionResults)
      profile.incrementVersion("rooms")
      competitionBuilder.incrementLength()
    if choice == "Easier":
      lowerCosts(changeMultiplier)
      lowerRoomDifficulties(changeMultiplier, competitionResults)
    adjustShopFrequencies(changeMultiplier, purchaseCounts)
  if choice == "Different":
    profile.incrementVersion("items")
    profile.incrementVersion("rooms")
    itemDataFactory = FileItemDataFactory(itemDataFactory, profile.getLatestPath("items"))
    # adjust costs
    raiseCosts(changeMultiplier, purchaseCounts)
    lowerCosts(changeMultiplier)
    # adjust item frequencies
    adjustShopFrequencies(changeMultiplier, purchaseCounts)
    # adjust room difficulties
    rescaleRoomDifficulties(changeMultiplier, competitionResults)
    lowerRoomDifficulties(changeMultiplier, competitionResults)
  itemDataFactory.ensureSaved()
  competitionBuilder.ensureSaved(profile.getLatestPath("rooms"))

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
  welcome = StoryGenerator(gamePlayer, competitionBuilder, itemDataFactory, runLog).create()

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
