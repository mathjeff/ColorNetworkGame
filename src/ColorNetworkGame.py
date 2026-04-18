#!python

from competition.Competition import *
from energy.Energy import *
from items.Items import *
from persistence.Persistence import *
from story.Story import *

import json, math, os, random, shutil, textwrap

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
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 11, 1, 16)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 3}), 25, 1, 9)
    self.add(Wall({"hitPoints": 4}), 37, 1, 15)
    # self.add(type(properties), popularity, complexity=2, cost)
    self.add(Laser({"requiredPower": y.d(4), "damage": 4, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 25, 2, 42)
    self.add(Laser({"requiredPower": y.d(2), "damage": 2, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 17, 2, 35)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(3), "maxPossibleTarget": 3}), 24, 2, 17)
    self.add(Laser({"requiredPower": y.d(1), "damage": 0.5, "maxSignalPower": y.d(10), "maxPossibleTarget": 3}), 15, 2, 15)
    self.add(Laser({"requiredPower": b.d(1), "damage": 8, "maxSignalPower": y.d(1), "maxPossibleTarget": 0}), 23, 2, 65)
    self.add(Flipper({"maxPower": y.d(10), "strengthPerPower":2, "hitpoints":4}), 3, 2, 14)
    self.addBundle([Battery({"maxCharge": b.d(3), "dischargeRate": 3}), Ram({"maxPower": b.d(10), "damagePerPower":4})], 23, 2, 29)
    self.add(Battery({"maxCharge": y.d(10), "dischargeRate": 4}), 22, 2, 10)
    self.add(Battery({"maxCharge": y.d(20), "dischargeRate": 2}), 17, 2, 13)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 1}), 9, 2, 5)
    self.add(Battery({"maxCharge": m.d({yellow:100, black:100}), "dischargeRate": 1}), 28, 2, 21)
    self.addBundle([Battery({"maxCharge": b.d(1), "dischargeRate": 1}), Converter({"requiredPower": b.d(1), "outputPower": y.d(10)})], 3, 2, 12)
    self.addBundle([Battery({"maxCharge": b.d(5), "dischargeRate": 5}), Converter({"requiredPower": b.d(1), "outputPower": y.d(5)})], 32, 2, 36)
    self.add(Wall({"hitPoints": 8}), 21, 2, 40)
    self.add(Adder({"addition": 0.1, "maxInput": 10}), 10, 2, 17)
    self.add(Adder({"addition": 0.2, "maxInput": 10}), 25, 2, 24)
    self.add(Adder({"addition": 0.3, "maxInput": 10}), 11, 2, 20)
    self.add(Adder({"addition": 0.4, "maxInput": 10}), 19, 2, 14)
    self.add(Divider({"divisor": 2}), 10, 2, 5)
    self.add(Divider({"divisor": 5}), 21, 2, 5)
    self.add(Capacitor({"maxEnergy": y.d(10), "signalOutputFraction": 0.1}), 16, 2, 17)
    self.add(Capacitor({"maxEnergy": y.d(100), "signalOutputFraction": 0.1}), 10, 2, 4)
    # self.add(type(properties), popularity, complexity=3, cost)
    self.add(HealthSensor({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 9, 4, 7)
    self.add(InputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 12, 3, 8)
    self.add(OutputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 9, 3, 9)
    self.add(IfLess({"threshold": 0.2}), 5, 3, 10)
    self.add(IfMore({"threshold": 0.3}), 5, 3, 17)
    self.add(IfMore({"threshold": 0.5}), 5, 3, 10)
    self.add(IfMore({"threshold": 0.7}), 5, 3, 10)
    self.add(Joiner({}), 7, 3, 7)
    self.add(PowerInputDrainer({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 1, "drainPerItem": 1}), 5, 3, 29)
    self.add(PowerOutputDrainer({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 1, "drainPerItem": 1}), 5, 3, 10)
    self.add(Shield({"defenseFraction": 1.0, "radius": 0, "requiredPower": y.d(6), "maxSignalPower": y.d(1), "maxPossibleDistance": 1}), 11, 3, 25)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": y.d(4), "maxSignalPower": y.d(10), "maxPossibleDistance": 100}), 9, 3, 9)
    # self.add(type(properties), popularity, complexity=4, cost)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 9, 4, 9)

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

# adds two Map<Object, Integer>
def addCounts(a, b):
  result = {}
  for key in a:
    result[key] = a.get(key, 0) + b.get(key, 0)
  for key in b:
    result[key] = a.get(key, 0) + b.get(key, 0)
  return result

print("Welcome to ColorNetwork!")

def getAverageItemCost():
  items = offeringFactory.getAll()
  total = sum([item.cost for item in items])
  return total / len(items)

def raiseCosts(averageCostMultiplier, purchaseCounts, skipCounts):
  # if an item was more likely to be purchased when it was offered, then raise its price
  totalCost = sum([item.cost for item in offeringFactory.getAll()])
  totalIncrease = totalCost * (averageCostMultiplier - 1)
  # compute how likely an item was to be purchased if it was offered
  purchaseFractions = {}
  totalWeight = 0
  for itemName, numPurchases in purchaseCounts.items():
    numSkips = skipCounts[itemName]
    numOffers = numPurchases + numSkips
    if numPurchases > 0:
      purchaseFraction = numPurchases / numOffers
      purchaseFractions[itemName] = purchaseFraction
      item = offeringFactory.getTemplateNamed(itemName)
      weight = purchaseFraction * item.cost
      totalWeight += weight
  numPossibleItems = len(offeringFactory.getAll())
  increasePerFractionWeight = totalIncrease

  for itemName, purchaseFraction in purchaseFractions.items():
    offering = offeringFactory.getTemplateNamed(itemName)
    oldCost = offering.cost
    weight = oldCost * purchaseFraction
    newCost = oldCost + (increasePerFractionWeight * weight / totalWeight)
    print("increasing cost of " + itemName + " from " + str(oldCost) + " to " + str(newCost) + " due to being bought " + str(purchaseCounts[itemName]) + " times and skipped " + str(skipCounts[itemName]) + " times")
    offering.cost = newCost

def lowerCosts(multiplier, offerCounts):
  totalWeight = 0
  for itemName, offerCount in offerCounts.items():
    item = offeringFactory.getTemplateNamed(itemName)
    weight = offerCount * item.cost
    totalWeight += weight
  totalCost = sum([item.cost for item in offeringFactory.getAll()])
  totalDecrease = totalCost - totalCost / multiplier
  decreasePerWeightFraction = totalDecrease
  # if an item was offered more often, then lower its price more
  for itemName, offerCount in offerCounts.items():
    offering = offeringFactory.getTemplateNamed(itemName)
    if offerCount > 0:
      weight = offerCount * offering.cost
      weightFraction = weight / totalWeight
      oldCost = offering.cost
      newCost = max(1, oldCost - weightFraction * decreasePerWeightFraction)
      print("decreasing cost of " + itemName + " from " + str(oldCost) + " to " + str(newCost) + " due to being offered " + str(offerCount) + " times")
      offering.cost = newCost

def adjustShopFrequencies(multiplier, purchaseCounts, skipCounts):
  # raise the popularity of items that were purchased more
  totalNumPurchases = sum(purchaseCounts.values())
  totalNumSkips = sum(skipCounts.values())
  # compute the average purchase rate among purchased item types
  purchaseRates = {}
  for itemName in purchaseCounts:
    itemPurchaseCount = purchaseCounts[itemName]
    itemSkipCount = skipCounts[itemName]
    itemOfferCount = itemPurchaseCount + itemSkipCount
    if itemOfferCount > 0:
      purchaseRates[itemName] = itemPurchaseCount / itemOfferCount

  # compute total popularity
  totalPopularity = sum([offeringFactory.getTemplateNamed(name).popularity for name in purchaseRates])
  # increase popularity of items that were bought more often than normal
  newPopularities = {}
  for itemName in purchaseRates:
    item = offeringFactory.getTemplateNamed(itemName)
    newPopularities[itemName] = item.popularity * math.pow(multiplier, purchaseRates[itemName])
  # renormalize
  newTotalPopularity = sum([newPopularities[offering] for offering in newPopularities])
  for itemName in purchaseRates:
    newPopularity = newPopularities[itemName] * totalPopularity / newTotalPopularity
    item = offeringFactory.getTemplateNamed(itemName)
    print("changing popularity of " + itemName + " from " + str(item.popularity) + " to " + str(newPopularity) + " due to being bought " + str(purchaseCounts[itemName]) + " times and skipped " + str(skipCounts[itemName]) + " times")
    item.popularity = newPopularity

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
  offerCounts = addCounts(purchaseCounts, skipCounts)
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
      lowerCosts(costShift, offerCounts)
      rescaleRoomDifficulties(roomDifficultyIncrease, competitionResults)
      profile.incrementVersion("rooms")
      competitionBuilder.incrementLength()
    if choice == "Easier":
      raiseCosts(costIncrease, purchaseCounts, skipCounts)
      lowerCosts(costIncrease * costShift, offerCounts)
      lowerRoomDifficulties(roomDifficultyIncrease, competitionResults)
    adjustShopFrequencies(popularityShift, purchaseCounts, skipCounts)
  if choice == "Different":
    profile.incrementVersion("items")
    profile.incrementVersion("rooms")
    offeringFactory = FileOfferingFactory(offeringFactory, profile.getLatestPath("items"))
    # adjust costs
    print("average item cost = " + str(getAverageItemCost()))
    raiseCosts(costShift, purchaseCounts, skipCounts)
    lowerCosts(costShift, offerCounts)
    print("average item cost = " + str(getAverageItemCost()))
    # adjust item frequencies
    adjustShopFrequencies(popularityShift, purchaseCounts, skipCounts)
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
