#!python

from competition.Competition import *
from energy.Energy import *
from items.Items import *
from persistence.Persistence import *
from story.Story import *

import json, os, random, shutil, textwrap

# a collection of predefined Offering
class DefaultOfferingFactory(OfferingFactory):
  def __init__(self):
    super().__init__()
    self.loadDefaults()

  def loadDefaults(self):
    self.contents = []
    yellow = "Y" # yellow energy: electricity
    black = "B" # black energy: coal
    y = SingleColorBuilder(yellow)
    b = SingleColorBuilder(black)
    m = MultiColorBuilder([yellow, black])
    # self.add(type(properties), popularity, complexity=1, cost)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 12, 1, 25)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 3}), 26, 1, 22)
    self.add(Wall({"hitPoints": 4}), 37, 1, 49)
    # self.add(type(properties), popularity, complexity=2, cost)
    self.add(Laser({"requiredPower": y.d(4), "damage": 4, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 23, 2, 28)
    self.add(Laser({"requiredPower": y.d(2), "damage": 2, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 18, 2, 37)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(3), "maxPossibleTarget": 3}), 27, 2, 28)
    self.add(Laser({"requiredPower": y.d(1), "damage": 0.5, "maxSignalPower": y.d(10), "maxPossibleTarget": 3}), 15, 2, 14)
    self.add(Laser({"requiredPower": b.d(1), "damage": 8, "maxSignalPower": y.d(1), "maxPossibleTarget": 0}), 20, 2, 45)
    self.add(Flipper({"maxPower": y.d(10), "strengthPerPower":2, "hitpoints":4}), 3, 2, 3)
    self.addBundle([Battery({"maxCharge": b.d(3), "dischargeRate": 3}), Ram({"maxPower": b.d(10), "damagePerPower":4})], 25, 2, 35)
    self.add(Battery({"maxCharge": y.d(10), "dischargeRate": 4}), 27, 2, 22)
    self.add(Battery({"maxCharge": y.d(20), "dischargeRate": 2}), 19, 2, 14)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 1}), 3, 2, 3)
    self.add(Battery({"maxCharge": m.d({yellow:100, black:100}), "dischargeRate": 1}), 29, 2, 33)
    self.addBundle([Battery({"maxCharge": b.d(1), "dischargeRate": 1}), Converter({"requiredPower": b.d(1), "outputPower": y.d(10)})], 4, 2, 6)
    self.addBundle([Battery({"maxCharge": b.d(5), "dischargeRate": 5}), Converter({"requiredPower": b.d(1), "outputPower": y.d(5)})], 30, 2, 38)
    self.add(Wall({"hitPoints": 8}), 22, 2, 63)
    self.add(Adder({"addition": 0.1, "maxInput": 10}), 7, 2, 6)
    self.add(Adder({"addition": 0.2, "maxInput": 10}), 25, 2, 18)
    self.add(Adder({"addition": 0.3, "maxInput": 10}), 7, 2, 6)
    self.add(Adder({"addition": 0.4, "maxInput": 10}), 21, 2, 21)
    self.add(Divider({"divisor": 2}), 2, 2, 3)
    self.add(Divider({"divisor": 5}), 19, 2, 9)
    self.add(Capacitor({"maxEnergy": y.d(10), "signalOutputFraction": 0.1}), 17, 2, 16)
    self.add(Capacitor({"maxEnergy": y.d(100), "signalOutputFraction": 0.1}), 6, 2, 9)
    # self.add(type(properties), popularity, complexity=3, cost)
    self.add(HealthSensor({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 2, 4, 3)
    self.add(InputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 13, 3, 12)
    self.add(OutputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 8, 3, 6)
    self.add(IfLess({"threshold": 0.2}), 1, 3, 3)
    self.add(IfMore({"threshold": 0.3}), 1, 3, 3)
    self.add(IfMore({"threshold": 0.5}), 1, 3, 3)
    self.add(IfMore({"threshold": 0.7}), 1, 3, 3)
    self.add(Joiner({}), 6, 3, 5)
    self.add(PowerInputDrainer({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 1, "drainPerItem": 1}), 3, 3, 3)
    self.add(PowerOutputDrainer({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 1, "drainPerItem": 1}), 4, 3, 3)
    self.add(Shield({"defenseFraction": 1.0, "radius": 0, "requiredPower": y.d(6), "maxSignalPower": y.d(1), "maxPossibleDistance": 1}), 8, 3, 6)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": y.d(4), "maxSignalPower": y.d(10), "maxPossibleDistance": 100}), 2, 3, 3)
    # self.add(type(properties), popularity, complexity=4, cost)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 1, 4, 3)

profile = Profile("data/profile/")
offeringFactory = FileOfferingFactory(DefaultOfferingFactory(), profile.getLatestPath("items"))
offeringFactory.ensureSaved()
competitionBuilder = CompetitionBuilder(profile.getLatestPath("rooms"))
runLog = RunLog(profile.getLatestPath("runlog"), offeringFactory)

def getItemPurchaseCounts(runLog, offeringFactory):
  counts = {}
  for offering in offeringFactory.getAll():
    counts[offering.name] = 0
  shopEntries = runLog.getShopEntries()
  for entry in shopEntries:
    for offering in entry.purchased:
      name = offering.name
      count = counts.get(name, 0)
      counts[name] = count + 1
  return counts

def getItemSkipCounts(runLog, offeringFactory):
  counts = {}
  for offering in offeringFactory.getAll():
    counts[offering.name] = 0
  shopEntries = runLog.getShopEntries()
  for entry in shopEntries:
    for offering in entry.remaining:
      name = offering.name
      count = counts.get(name, 0)
      counts[name] = count + 1
  return counts

print("Welcome to ColorNetwork!")

def raiseCosts(averageCostMultiplier, purchaseCounts, skipCounts):
  # if an item was more likely to be purchased when it was offered, then raise its price
  global offeringFactory
  # compute how likely an item was to be purchased if it was offered
  purchaseFractions = {}
  for itemName, numPurchases in purchaseCounts.items():
    numSkips = skipCounts[itemName]
    numOffers = numPurchases + numSkips
    if numPurchases > 0:
      purchaseFraction = numPurchases / numOffers
      purchaseFractions[itemName] = purchaseFraction
  sumPurchaseFractions = sum(purchaseFractions.values())
  numPossibleItems = len(offeringFactory.getAll())
  increasePerPurchaseFraction = (averageCostMultiplier - 1) * numPossibleItems / sumPurchaseFractions

  for itemName, purchaseFraction in purchaseFractions.items():
    offering = offeringFactory.getTemplateNamed(itemName)
    oldCost = offering.cost
    newCost = oldCost * (1 + purchaseFraction * increasePerPurchaseFraction)
    print("increasing cost of " + itemName + " from " + str(oldCost) + " to " + str(newCost) + " due to being bought " + str(purchaseCounts[itemName]) + " times and skipped " + str(skipCounts[itemName]) + " times")
    offering.cost = newCost

def lowerCosts(multiplier):
  global offeringFactory
  # lower all prices equally
  for offering in offeringFactory.getAll():
    offering.cost /= multiplier

def adjustShopFrequencies(multiplier, purchaseCounts):
  # raise the popularity of items that were purchased more
  oldWeight = 1 / multiplier
  newWeight = 1 - oldWeight
  totalNumPurchases = sum(purchaseCounts.values())
  totalPopularity = sum([offering.popularity for offering in offeringFactory.getAll()])
  popularityPerPurchase = totalPopularity / totalNumPurchases
  for itemName in purchaseCounts:
    itemTemplate = offeringFactory.getTemplateNamed(itemName)
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
  global offeringFactory
  purchaseCounts = getItemPurchaseCounts(runLog, offeringFactory)
  numPurchases = sum(purchaseCounts.values())
  if numPurchases < 1:
    return # didn't buy anything
  skipCounts = getItemSkipCounts(runLog, offeringFactory)
  competitionResults = runLog.getCompetitionEntries()
  conclusionEntry = runLog.getConclusionEntry()
  if conclusionEntry is not None and conclusionEntry.successful:
    print("Your previous game was a victory at round " + conclusionEntry.name + "!")
  else:
    lastEntry = runLog.getLastEntry()
    when = ""
    if lastEntry is not None:
      when = " at round " + lastEntry.name
    print("Your previous game was a loss" + when)
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
  costShift = 1.09 # how quickly individual costs change

  # how quickly item popularity changes (for shops)
  popularityShift = 1.11

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
    offeringFactory = FileOfferingFactory(offeringFactory, profile.getLatestPath("items"))
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
    offeringFactory = FileOfferingFactory(offeringFactory, profile.getLatestPath("items"))
    # adjust costs
    raiseCosts(costShift, purchaseCounts, skipCounts)
    lowerCosts(costShift)
    # adjust item frequencies
    adjustShopFrequencies(popularityShift, purchaseCounts)
    # adjust room difficulties
    rescaleRoomDifficulties(roomDifficultyIncrease, competitionResults)
    lowerRoomDifficulties(roomDifficultyIncrease, competitionResults)
  offeringFactory.ensureSaved()
  competitionBuilder.ensureSaved(profile.getLatestPath("rooms"))

  print("Ok!")

if runLog.nonEmpty():
  offerChangeSettings()
  profile.incrementVersion("runlog")

runLog = RunLog(profile.getLatestPath("runlog"), offeringFactory)
profile.save()

def makePlayer():
  player = GamePlayer("Player")
  return player

def makeStory():
  gamePlayer = makePlayer()
  welcome = StoryGenerator(gamePlayer, competitionBuilder, offeringFactory, runLog).create()

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
