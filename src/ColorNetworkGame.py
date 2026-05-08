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
    yellow = Energies.register(EnergyColor("Y", "yellow", "\033[1;33;40m", "yellow energy represents electricity"))
    black = Energies.register(EnergyColor("B", "black", "\033[1;30;40m", "black energy represents coal"))
    green = Energies.register(EnergyColor("G", "green", "\033[1;32;40m", "green energy represents energy in living cells"))
    y = SingleColorBuilder(yellow)
    b = SingleColorBuilder(black)
    g = SingleColorBuilder(green)
    m = MultiColorBuilder([yellow, black, green])
    # self.add(type(properties), popularity, complexity=1, cost)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 11, 1, 20)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 3}), 30, 1, 12)
    self.add(Wall({"hitPoints": 4}), 33, 1, 16)
    # self.add(type(properties), popularity, complexity=2, cost)
    self.add(Laser({"requiredPower": y.d(4), "damage": 4, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 21, 2, 29)
    self.add(Laser({"requiredPower": y.d(2), "damage": 2, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 16, 2, 49)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(3), "maxPossibleTarget": 3}), 26, 2, 38)
    self.add(Laser({"requiredPower": y.d(1), "damage": 0.5, "maxSignalPower": y.d(10), "maxPossibleTarget": 3}), 13, 2, 9)
    self.add(Laser({"requiredPower": b.d(1), "damage": 8, "maxSignalPower": b.d(1), "maxPossibleTarget": 0}), 20, 2, 25)
    self.add(Flipper({"maxPower": y.d(15), "strengthPerPower":3, "hitpoints":4}), 4, 2, 17)
    self.add(Infector({"requiredPower": g.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 30, 2, 16)
    self.addBundle([Battery({"maxCharge": b.d(3), "dischargeRate": 3}), Ram({"maxPower": b.d(10), "damagePerPower":4})], 20, 2, 11)
    self.add(Battery({"maxCharge": y.d(10), "dischargeRate": 4}), 22, 2, 12)
    self.add(Battery({"maxCharge": y.d(20), "dischargeRate": 2}), 15, 2, 6)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 1}), 8, 2, 9)
    self.add(Battery({"maxCharge": m.d({yellow:100, black:100, green:100}), "dischargeRate": 1}), 32, 2, 54)
    self.addBundle([Battery({"maxCharge": b.d(1), "dischargeRate": 1}), Converter({"requiredPower": b.d(1), "outputPower": y.d(10)})], 3, 2, 17)
    self.addBundle([Battery({"maxCharge": b.d(5), "dischargeRate": 5}), Converter({"requiredPower": b.d(1), "outputPower": y.d(5)})], 31, 2, 29)
    self.add(Battery({"maxCharge": g.d(1000), "dischargeRate": 1}), 28, 2, 20)
    self.addBundle([Converter({"requiredPower": b.d(0.3), "outputPower": g.d(1)}), Converter({"requiredPower": y.d(2), "outputPower": g.d(1)})], 15, 2, 16)
    self.add(Converter({"requiredPower": b.d(0.2), "outputPower": g.d(1)}), 15, 2, 10)
    self.add(Converter({"requiredPower": y.d(1), "outputPower": g.d(1)}), 20, 2, 6)
    self.addBundle([Converter({"requiredPower": g.d(1), "outputPower": y.d(2)}), Converter({"requiredPower": g.d(2), "outputPower": b.d(1)})], 10, 2, 12)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": y.d(4)}), 5, 2, 7)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": b.d(1)}), 5, 2, 11)
    self.add(Wall({"hitPoints": 8}), 19, 2, 28)
    self.add(CellWall({"hitPoints": 8, "requiredPower": g.d(1), "hitpointGainPerTurn": 1}), 19, 2, 55)
    self.add(Adder({"addition": 0.1, "maxInput": 10}), 8, 2, 10)
    self.add(Adder({"addition": 0.2, "maxInput": 10}), 22, 2, 16)
    self.add(Adder({"addition": 0.3, "maxInput": 10}), 8, 2, 12)
    self.add(Adder({"addition": 0.4, "maxInput": 10}), 16, 2, 11)
    self.add(Divider({"divisors": [2, 5]}), 9, 2, 5)
    self.add(Capacitor({"maxEnergy": y.d(10), "signalOutputFraction": 0.1}), 15, 2, 17)
    self.add(Capacitor({"maxEnergy": y.d(100), "signalOutputFraction": 0.1}), 11, 2, 15)
    self.add(Capacitor({"maxEnergy": m.d({yellow:10, black:10, green:10}), "signalOutputFraction": 0.1}), 13, 2, 17)
    self.add(Capacitor({"maxEnergy": g.d(20), "startingEnergy": g.d(10), "signalOutputFraction": 0.1}), 10, 2, 13)
    # self.add(type(properties), popularity, complexity=3, cost)
    self.add(HealthSensor({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 2, "outputRatio": 0.1}), 9, 4, 7)
    self.add(InputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 12, 3, 12)
    self.add(OutputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 8, 3, 8)
    self.add(Comparer({"threshold": 0.2}), 5, 3, 13)
    self.add(Comparer({"threshold": 0.3}), 5, 3, 17)
    self.add(Comparer({"threshold": 0.5}), 5, 3, 10)
    self.add(Comparer({"threshold": 0.7}), 5, 3, 13)
    self.add(Joiner({"numInputs": 2}), 7, 3, 7)
    self.add(Joiner({"numInputs": 3}), 10, 3, 10)
    self.add(PowerInputDrainer({"powerPerDrain": y.d(1), "maxPower": y.d(15), "maxPositionPower": y.d(10), "maxPossibleTarget": 100, "maxRadiusPower": y.d(1), "maxRadius": 5}), 10, 3, 13)
    self.add(PowerOutputDrainer({"powerPerDrain": y.d(1), "maxPower": y.d(15), "maxPositionPower": y.d(10), "maxPossibleTarget": 100, "maxRadiusPower": y.d(1), "maxRadius": 5}), 10, 3, 11)
    self.add(Shield({"defenseFraction": 1.0, "radius": 0, "requiredPower": y.d(6), "maxSignalPower": y.d(1), "maxPossibleDistance": 1}), 10, 3, 30)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": y.d(4), "maxSignalPower": y.d(10), "maxPossibleDistance": 100}), 10, 3, 11)
    # self.add(type(properties), popularity, complexity=4, cost)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 9, 4, 9)

profile = Profile("data/profile/")
defaultOfferingFactory = DefaultOfferingFactory()
offeringFactory = defaultOfferingFactory.withFileContents(profile.getLatestPath("items/current"))

# checks for any changes to the default offerings and updates the current offerings accordingly
def updateDefaultOfferings():
  global offeringFactory
  previousDefaultOfferingsPath = profile.getLatestPath("items/defaults")
  if not os.path.isfile(previousDefaultOfferingsPath):
    # save initial values
    defaultOfferingFactory.ensureSaved(profile.getLatestPath("items/defaults"))
    offeringFactory.ensureSaved(profile.getLatestPath("items/current"))
    profile.save()
  else:
    # compare to previous defaults
    previousDefaultOfferings = defaultOfferingFactory.withFileContents(previousDefaultOfferingsPath)
    delta = OfferingsDelta(previousDefaultOfferings, defaultOfferingFactory)
    if delta.nonempty():
      # save new defaults
      profile.incrementVersion("items/defaults")
      defaultOfferingFactory.ensureSaved(profile.getLatestPath("items/defaults"))
      # save new customized values too
      offeringFactory = offeringFactory.withDelta(delta)
      profile.incrementVersion("items/current")
      offeringFactory.ensureSaved(profile.getLatestPath("items/current"))
      profile.save()
updateDefaultOfferings()

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

print("Welcome to ColorNetwork! To quit, press <Ctrl-C>")

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
  # determine which rooms were successful
  statuses = []
  for i in range(competitionBuilder.getMaxLength()):
    statuses.append(True)
  for entry in competitionResults:
    if not entry.successful:
      index = int(entry.name)
      statuses[index] = False
  # for each room, determine whether it was near a failure, and if so, make it easier
  makeEasiers = []
  countToMakeEasier = 0
  for i in range(competitionBuilder.getMaxLength()):
    minNeighbor = max(0, i - 2)
    maxNeighbor = min(competitionBuilder.getMaxLength(), i + 3)
    nearbyFailure = False
    for neighbor in range(minNeighbor, maxNeighbor):
      if not statuses[neighbor]:
        nearbyFailure = True
    if nearbyFailure:
      countToMakeEasier += 1
    makeEasiers.append(nearbyFailure)
  multiplierPerFailure = pow(difficultyMultiplier, competitionBuilder.getMaxLength() / countToMakeEasier)
  # reduce difficulty of rooms near failures
  for i in range(competitionBuilder.getMaxLength()):
    if makeEasiers[i]:
      difficulty = competitionBuilder.getDifficulty(i)
      competitionBuilder.rescaleDifficulty(i, 1 / multiplierPerFailure)
      newDifficulty = competitionBuilder.getDifficulty(i)
      print("Rescaled difficulty at " + str(i) + " from " + str(difficulty) + " to " + str(newDifficulty))

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
    profile.incrementVersion("items/current")
    profile.incrementVersion("rooms")
    offeringFactory = offeringFactory.withFileContents(profile.getLatestPath("items/current"))
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
    profile.incrementVersion("items/current")
    profile.incrementVersion("rooms")
    offeringFactory = offeringFactory.withFileContents(profile.getLatestPath("items/current"))
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
  offeringFactory.ensureSaved(profile.getLatestPath("items/current"))
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
