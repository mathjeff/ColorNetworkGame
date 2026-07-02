#!python

from competition.Competition import *
from energy.Energy import *
from items.Items import *
from persistence.Persistence import *
from story.Story import *

import json, math, os, shutil, textwrap

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
    grey = Energies.register(EnergyColor("E", "grey", "\033[1;37;40m", "grey energy represents solid materials like rocks"))
    y = SingleColorBuilder(yellow)
    b = SingleColorBuilder(black)
    g = SingleColorBuilder(green)
    e = SingleColorBuilder(grey)
    m = MultiColorBuilder([yellow, black, green, grey])
    # self.add(type(properties), popularity, complexity=1, cost)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 10, 1, 27)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 3}), 41, 1, 15)
    self.add(Wall({"hitPoints": 4, "outputPerDamage": e.d(1)}), 35, 1, 22)
    # self.add(type(properties), popularity, complexity=2, cost)
    self.add(Laser({"requiredPower": y.d(4), "damage": 4, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 21, 2, 27)
    self.add(Laser({"requiredPower": y.d(2), "damage": 2, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 11, 2, 38)
    self.add(Laser({"requiredPower": y.d(1), "damage": 1, "maxSignalPower": y.d(3), "maxPossibleTarget": 3}), 17, 2, 39)
    self.add(Laser({"requiredPower": y.d(1), "damage": 0.5, "maxSignalPower": y.d(6), "maxPossibleTarget": 3}), 10, 2, 8)
    self.add(Laser({"requiredPower": b.d(1), "damage": 8, "maxSignalPower": b.d(1), "maxPossibleTarget": 0}), 26, 2, 29)
    self.add(Flipper({"maxPower": y.d(20), "strengthPerPower":3, "hitpoints":4}), 5, 2, 24)
    self.add(Infector({"requiredPower": g.d(1), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 37, 2, 20)
    self.add(Catapult({"requiredPower": m.d({yellow:1, grey:1}), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 20, 2, 20)
    self.add(Gatling({"requiredEnergy": y.d(1), "requiredAmmo": e.d(0.2), "damage": 1, "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 20, 2, 20)
    self.addBundle([Battery({"maxCharge": b.d(3), "dischargeRate": 3}), Ram({"maxPower": b.d(10), "damagePerPower":4})], 24, 2, 23)
    self.add(Battery({"maxCharge": y.d(10), "dischargeRate": 4}), 20, 2, 9)
    self.add(Battery({"maxCharge": y.d(20), "dischargeRate": 2}), 17, 2, 9)
    self.add(Battery({"maxCharge": y.d(100), "dischargeRate": 1}), 7, 2, 12)
    self.add(Battery({"maxCharge": m.d({yellow:100, black:100, green:100, grey:100}), "dischargeRate": 1}), 22, 2, 29)
    self.addBundle([Battery({"maxCharge": b.d(2), "dischargeRate": 1}), Converter({"requiredPower": b.d(1), "outputPower": y.d(10), "numUsesPerTurn": 1})], 4, 2, 10)
    self.addBundle([Battery({"maxCharge": b.d(5), "dischargeRate": 5}), Converter({"requiredPower": b.d(1), "outputPower": y.d(5), "numUsesPerTurn": 1})], 29, 2, 23)
    self.add(Battery({"maxCharge": g.d(1000), "dischargeRate": 1}), 24, 2, 16)
    self.addBundle([Converter({"requiredPower": b.d(0.3), "outputPower": g.d(1), "numUsesPerTurn": 1}), Converter({"requiredPower": y.d(1.9), "outputPower": g.d(1), "numUsesPerTurn": 1}), Converter({"requiredPower": e.d(1), "outputPower": g.d(1), "numUsesPerTurn": "1"})], 7, 2, 21)
    self.add(Converter({"requiredPower": b.d(0.5), "outputPower": g.d(2), "numUsesPerTurn": 1}), 12, 2, 7)
    self.add(Converter({"requiredPower": y.d(0.4), "outputPower": g.d(0.5), "numUsesPerTurn": 2}), 25, 2, 14)
    self.add(Converter({"requiredPower": e.d(1), "outputPower": g.d(2), "numUsesPerTurn": 1}), 25, 2, 14)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": m.d({yellow:1, black:1, grey: 1}), "numUsesPerTurn": 1}), 7, 2, 18)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": y.d(4), "numUsesPerTurn": 3}), 5, 2, 12)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": b.d(2), "numUsesPerTurn": 1}), 6, 2, 11)
    self.add(Converter({"requiredPower": g.d(1), "outputPower": e.d(1), "numUsesPerTurn": 1}), 6, 2, 11)
    self.add(Wall({"hitPoints": 8, "outputPerDamage": e.d(1)}), 14, 2, 35)
    self.add(UnstableWall({"hitPoints": 12, "outputPerDamage": e.d(1), "decayPerTurn": 1}), 14, 2, 35)
    self.add(CellWall({"hitPoints": 8, "requiredPower": g.d(1), "hitpointGainPerUse": 1, "numUsesPerTurn": 2}), 12, 2, 32)
    self.add(Adder({"addition": 0.2, "maxInput": 10}), 19, 2, 12)
    self.add(Adder({"addition": 0.4, "maxInput": 10}), 15, 2, 16)
    self.add(Counter({"step": 0.1}), 20, 2, 20)
    self.add(Comparer({"threshold": 0.2}), 6, 2, 10)
    self.add(Comparer({"threshold": 0.3}), 6, 2, 10)
    self.add(Divider({"divisors": [2, 5]}), 10, 2, 8)
    self.add(Capacitor({"maxEnergy": y.d(10), "signalOutputFraction": 0.1}), 14, 2, 23)
    self.add(Capacitor({"maxEnergy": y.d(100), "signalOutputFraction": 0.1}), 9, 2, 16)
    self.add(Capacitor({"maxEnergy": m.d({yellow:10, black:10, green:10, grey:2}), "startingEnergy": m.d({yellow: 2, black:2, green:2, grey:2}), "signalOutputFraction": 0.1}), 11, 2, 14)
    self.add(Capacitor({"maxEnergy": g.d(20), "startingEnergy": g.d(10), "signalOutputFraction": 0.1}), 10, 2, 11)
    self.add(Capacitor({"maxEnergy": e.d(20), "startingEnergy": e.d(10), "signalOutputFraction": 0.1}), 10, 2, 20)
    self.add(Joiner({"numInputs": 2}), 13, 2, 21)
    # self.add(type(properties), popularity, complexity=3, cost)
    self.add(InputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 10, 3, 10)
    self.add(OutputCutter({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100}), 7, 3, 7)
    self.add(Adder({"addition": 0.1, "maxInput": 10}), 7, 3, 15)
    self.add(Adder({"addition": 0.3, "maxInput": 10}), 8, 3, 11)
    self.add(Comparer({"threshold": 0.5}), 6, 3, 10)
    self.add(Comparer({"threshold": 0.7}), 6, 3, 10)
    self.add(Joiner({"numInputs": 3}), 11, 3, 17)
    self.add(PowerInputDrainer({"powerPerDrain": y.d(1), "maxPower": y.d(15), "maxPositionPower": y.d(10), "maxPossibleTarget": 100, "maxRadiusPower": y.d(1), "maxRadius": 5}), 10, 3, 17)
    self.add(PowerOutputDrainer({"powerPerDrain": y.d(1), "maxPower": y.d(15), "maxPositionPower": y.d(10), "maxPossibleTarget": 100, "maxRadiusPower": y.d(1), "maxRadius": 5}), 8, 3, 9)
    self.add(Shield({"defenseFraction": 1.0, "radius": 0, "requiredPower": y.d(6), "maxSignalPower": y.d(1), "maxPossibleDistance": 1}), 11, 3, 44)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": y.d(4), "maxSignalPower": y.d(10), "maxPossibleDistance": 100}), 11, 3, 13)
    # self.add(type(properties), popularity, complexity=4, cost)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 9, 4, 11)
    self.add(HealthSensor({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "radius": 2, "outputRatio": 0.1}), 10, 4, 7)
    self.add(HitpointScanner({"requiredPower": y.d(1), "maxSignalPower": y.d(10), "maxPossibleTarget": 100, "outputRatio": 0.1}), 10, 4, 7)

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
  competitionBuilder.rescaleDifficulty(difficultyMultiplier)

def lowerRoomDifficulties(difficultyMultiplier, competitionResults):
  competitionBuilder.rescaleDifficulty(1 / difficultyMultiplier)

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
  menu.addChoice("Much easier than last run", "Much easier")
  menu.addChoice("Slightly easier than last run", "Easier")
  menu.addChoice("Same as last run", "Same")
  menu.addChoice("Different than last run", "Different")
  menu.addChoice("Slightly harder than last run", "Harder")
  menu.addChoice("Much harder than last run", "Much harder")
  choice = menu.chooseValue()
  if choice == "Same":
    print("Keeping settings the same as previous game")
    return

  # parameters for changing prices
  costIncrease = 1.01 # how quickly average costs increase when raising difficulty
  costShift = (numPurchases / offeringFactory.getNumOfferings() / 10) + 1 # how quickly individual costs change

  # how quickly item popularity changes (for shops)
  popularityShift = 1.15

  # how quickly room difficulty changes
  roomDifficultyIncrease = 1.1 # how quickly difficulty changes in rooms

  if choice in ["Much easier", "Much harder"]:
    power = 4
    costIncrease = pow(costIncrease, power)
    roomDifficultyIncrease = pow(roomDifficultyIncrease, power)

  # adjust difficulty if requested
  if choice in ["Much easier", "Easier", "Harder", "Much harder"]:
    # make a new item factory based on the previous one
    profile.incrementVersion("items/current")
    profile.incrementVersion("rooms")
    offeringFactory = offeringFactory.withFileContents(profile.getLatestPath("items/current"))
    if choice in ["Harder", "Much harder"]:
      raiseCosts(costIncrease * costShift, purchaseCounts, skipCounts)
      lowerCosts(costShift, offerCounts)
      rescaleRoomDifficulties(roomDifficultyIncrease, competitionResults)
      profile.incrementVersion("rooms")
      competitionBuilder.incrementLength()
    if choice in ["Easier", "Much easier"]:
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

def shouldContinuePreviousGame():
  if inputUtils.fileHasPendingDecisions(profile.getLatestPath("choices")) and runLog.getConclusionEntry() is None:
    print("Do you want to resume your previous game?")
    menu = Menu()
    menu.addChoice("Continue", "Continue")
    menu.addChoice("Abandon", "Abandon")
    choice = menu.chooseValue()
    return choice == "Continue"
  return False

if not shouldContinuePreviousGame():
  if runLog.nonEmpty():
    offerChangeSettings()
    profile.incrementVersion("runlog")
    runLog = RunLog(profile.getLatestPath("runlog"), offeringFactory)
  if inputUtils.fileHasPendingDecisions(profile.getLatestPath("choices")):
    profile.incrementVersion("choices")

inputUtils.setPath(profile.getLatestPath("choices"))
profile.save()

def makePlayer():
  player = GamePlayer("Player")
  return player

def makeStory():
  gamePlayer = makePlayer()
  welcome = StoryGenerator(gamePlayer, competitionBuilder, offeringFactory, runLog).create()

  return StoryNodeRunner(welcome)

def main():
  random.seed(profile.getVersion("runlog"))
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
