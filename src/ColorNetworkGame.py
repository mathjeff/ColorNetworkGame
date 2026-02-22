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
    # self.add(type(properties), popularity, complexity=1, cost)
    self.add(Laser({"requiredPower": 1, "damage": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 20)
    self.add(Cutter({"requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 2, 1, 20)
    self.add(Battery({"maxCharge": 100, "dischargeRate": 3}), 2, 1, 20)
    self.add(Wall({"hitPoints": 4}), 2, 1, 10)
    # self.add(type(properties), popularity, complexity=2, cost)
    self.add(Laser({"requiredPower": 4, "damage": 4, "maxSignalPower": 2, "maxPossibleTarget": 100}), 2, 2, 20)
    self.add(Battery({"maxCharge": 10, "dischargeRate": 3}), 2, 2, 10)
    self.add(Battery({"maxCharge": 100, "dischargeRate": 1}), 2, 2, 10)
    self.add(Resistor({"dischargeRate": 0.01}), 1, 2, 10)
    self.add(Resistor({"dischargeRate": 0.05}), 1, 2, 10)
    self.add(Adder({"addition": 0.01, "maxInput": 10}), 1, 2, 10)
    self.add(Splitter({"maxInput": 1}), 1, 2, 10)
    self.add(Joiner({}), 1, 2, 10)
    self.add(If({"threshold": 0.01}), 1, 2, 10)
    self.add(If({"threshold": 0.05}), 1, 2, 10)
    self.add(Capacitor({"maxEnergy": 10, "signalOutputFraction": 0.01}), 1, 2, 10)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": 4, "maxSignalPower": 1, "maxPossibleDistance": 100}), 2, 2, 20)
    # self.add(type(properties), popularity, complexity=2, cost)
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

def getItemSkipCounts(runLog, itemDataFactory):
  counts = {}
  for itemData in itemDataFactory.getAll():
    counts[itemData.name] = 0
  shopEntries = runLog.getShopEntries()
  for entry in shopEntries:
    for itemData in entry.remaining:
      name = itemData.name
      count = counts.get(name, 0)
      counts[name] = count + 1
  return counts

print("Welcome to ColorNetwork!")

def raiseCosts(averageCostMultiplier, purchaseCounts, skipCounts):
  # if an item was more likely to be purchased when it was offered, then raise its price
  global itemDataFactory
  # compute how likely an item was to be purchased if it was offered
  purchaseFractions = {}
  for itemName, numPurchases in purchaseCounts.items():
    numSkips = skipCounts[itemName]
    numOffers = numPurchases + numSkips
    if numPurchases > 0:
      purchaseFraction = numPurchases / numOffers
      purchaseFractions[itemName] = purchaseFraction
  sumPurchaseFractions = sum(purchaseFractions.values())
  numPossibleItems = len(itemDataFactory.getAll())
  increasePerPurchaseFraction = (averageCostMultiplier - 1) * numPossibleItems / sumPurchaseFractions

  for itemName, purchaseFraction in purchaseFractions.items():
    itemData = itemDataFactory.getTemplateNamed(itemName)
    oldCost = itemData.cost
    newCost = oldCost * (1 + purchaseFraction * increasePerPurchaseFraction)
    print("increasing cost of " + itemName + " from " + str(oldCost) + " to " + str(newCost) + " due to being bought " + str(purchaseCounts[itemName]) + " times and skipped " + str(skipCounts[itemName]) + " times")
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
  skipCounts = getItemSkipCounts(runLog, itemDataFactory)
  competitionResults = runLog.getCompetitionEntries()
  conclusionEntry = runLog.getConclusionEntry()
  if conclusionEntry is not None and conclusionEntry.successful:
    print("Your previous game was a victory!")
  else:
    print("Your previous game was a loss")
  print("")
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

  # parameters for changing prices
  costIncrease = 1.01 # how quickly average costs increase when raising difficulty
  costShift = 1.1 # how quickly individual costs change

  # how quickly item popularity changes (for shops)
  popularityShift = 1.1

  # how quickly room difficulty changes
  roomDifficultyIncrease = 1.1 # how quickly difficulty changes in rooms

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
      raiseCosts(costIncrease * costShift, purchaseCounts, skipCounts)
      lowerCosts(costShift)
      rescaleRoomDifficulties(roomDifficultyIncrease, competitionResults)
      profile.incrementVersion("rooms")
      competitionBuilder.incrementLength()
    if choice == "Easier":
      raiseCosts(costIncrease, purchaseCounts, skipCounts)
      lowerCosts(costIncrease * costShift)
      lowerRoomDifficulties(roomDifficultyIncrease, competitionResults)
    adjustShopFrequencies(popularityShift, purchaseCounts)
  if choice == "Different":
    profile.incrementVersion("items")
    profile.incrementVersion("rooms")
    itemDataFactory = FileItemDataFactory(itemDataFactory, profile.getLatestPath("items"))
    # adjust costs
    raiseCosts(costShift, purchaseCounts, skipCounts)
    lowerCosts(costShift)
    # adjust item frequencies
    adjustShopFrequencies(popularityShift, purchaseCounts)
    # adjust room difficulties
    rescaleRoomDifficulties(roomDifficultyIncrease, competitionResults)
    lowerRoomDifficulties(roomDifficultyIncrease, competitionResults)
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
