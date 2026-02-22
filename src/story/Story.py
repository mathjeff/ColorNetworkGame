#!python

from competition.Competition import *
from items.Items import *

import random, sys, textwrap

class StoryNode(object):
  def __init__(self):
    return

  def getNext(self):
    return None

class Menu(object):
  def __init__(self):
    self.choices = []

  def addChoice(self, text, result):
    self.choices.append((text, result))

  def chooseValue(self):
    index = self.chooseIndex()
    return self.choices[index][1]

  def chooseIndex(self):
    for i in range(len(self.choices)):
      option = self.choices[i][0]
      print(str(i + 1) + ": " + option) # first display index is 1
    choiceText = ""
    while True:
      choiceText = input("")
      number = 0
      if len(self.choices) <= 1:
        return 0 # there's only one choice so we return it
      try:
        number = int(choiceText) - 1 # first display index is 1
      except Exception as e:
        print("Choose a number!")
        continue
      if number < 0:
        print("Choose a number >= 1")
        continue
      if number >= len(self.choices):
        print("Choose a number <= " + str(len(self.choices)))
        continue
      return number

class MenuStoryNode(StoryNode):
  def __init__(self, text):
    super().__init__()
    self.text = text
    self.menu = Menu()

  def getNext(self):
    print(self.text)
    result = self.menu.chooseValue()
    self.onGoTo(result)
    return result

  def onGoTo(self, choice):
    return

  def addChoice(self, text, result):
    self.menu.addChoice(text, result)

# a SimpleStoryNode just is an abstract class that just goes to the next node
class SimpleStoryNode(StoryNode):
  def __init__(self):
    self.nextNode = None

  def setNext(self, nextNode):
    self.nextNode = nextNode

  def getNext(self):
    self.process()
    return self.nextNode

  def process(self):
    return

# a MessageStoryNode shows a message and goes to the next node
class MessageStoryNode(SimpleStoryNode):
  def __init__(self, text):
    super().__init__()
    self.text = text
    self.nextNode = None

  def process(self):
    print(self.text)
    input("(press Enter)")

# a SageStoryNode gives the user information
class SageStoryNode(SimpleStoryNode):
  def __init__(self, welcomeText, treeText):
    super().__init__()
    treeText = textwrap.dedent(treeText)
    self.tree = self.parseTree(welcomeText, treeText)
    if len(self.tree.children) < 1:
      raise Exception("Conversation is empty!")

  def process(self):
    # start at the beginning of the conversation
    currentNode = self.tree
    while currentNode is not None:
      # output next response
      print(currentNode.text)
      # wait for player
      menu = Menu()
      menu.addChoice("Back", currentNode.parent)
      for query, response in currentNode.children.items():
        menu.addChoice(query, response)
      currentNode = menu.chooseValue()

  def parseTree(self, welcomeText, text):
    stack = [SageNode(welcomeText)]
    previousIndent = -1
    lines = text.split("\n")
    for lineIndex in range(len(lines)):
      line = lines[lineIndex]
      indent = self.getIndent(line)
      content = line[indent:]
      if len(content) == 0:
        continue
      separator = ":"
      separatorIndex = content.find(separator)
      if separatorIndex < 0:
        raise Exception("Separator '" + separator + "' not found in line '" + line + "'")
      query = content[:separatorIndex]
      response = content[separatorIndex+1:]
      if indent <= previousIndent:
        stack = stack[:indent+1]
      if indent > previousIndent + 1:
        raise Exception("Error parsing line " + str(lineIndex) + ": '" + str(line) + "': indent " + str(indent) + " too much more than previous " + str(previousIndent))
      newNode = SageNode(response)
      stack[indent].addChild(query, newNode)
      stack.append(newNode)
      previousIndent = indent
    return stack[0]

  def getIndent(self, line):
    for i in range(len(line)):
      if line[i] != " ":
        return i
    return len(line)

# a node in the SageStoryNode's conversation
class SageNode(object):
  def __init__(self, text):
    self.text = text
    self.children = {}
    self.parent = None

  def addChild(self, query, child):
    self.children[query] = child
    child.parent = self

# a CompetitionStoryNode runs a competition
class CompetitionStoryNode(SimpleStoryNode):
  def __init__(self, index, player, opponent, rewardMoney, runLog):
    super().__init__()
    self.index = index
    self.player = player
    self.opponent = opponent
    self.runLog = runLog
    self.rewardMoney = rewardMoney

  def process(self):
    print("Room " + str(self.index) + ": you enter a competition with " + str(self.opponent.name))
    competition = Competition([self.player, self.opponent])
    result = competition.run()
    print("")
    self.updateRunLog(result)
    if result is None:
      print("Tie!\n")
    else:
      if result:
        print("Success! You defeated " + str(self.opponent.name) + "\n")
        self.player.money += self.rewardMoney
        print("You gain "  + str(self.rewardMoney) + " money and have " + str(self.player.money) + " money")
      else:
        print("Failure\n")
        self.player.numLosses += 1
        hitpoints = self.player.getHitpoints()
        if hitpoints > 0:
          print("You may continue until " + str(hitpoints) + " more losses")
        else:
          print("Loss limit (" + str(self.player.numLosses) + ") reached. Bye!")
          sys.exit(0)

  def updateRunLog(self, successful):
    entry = RunLogCompetitionEntry(str(self.index), successful)
    self.runLog.addEntry(entry)

class ShopStoryNode(SimpleStoryNode):
  def __init__(self, player, complexity, itemDataFactory):
    super().__init__()
    self.player = player
    self.contents = self.chooseContents(complexity, itemDataFactory)
    self.purchasedItems = []
    self.itemDataFactory = itemDataFactory

  def getTotalCost(self):
    total = 0
    for content in self.contents:
      total += content.cost
    return total

  def chooseContents(self, complexity, itemDataFactory):
    simpleItems = []
    complexItems = []
    for itemData in itemDataFactory.getAll():
      if itemData.complexity <= complexity:
        simpleItems.append(itemData)
      else:
        if itemData.complexity <= complexity + 1:
          complexItems.append(itemData)
    # include all simple items if there is space
    results = []
    targetNumItems = 10
    if len(simpleItems) < targetNumItems:
      results = simpleItems[:]
    candidates = simpleItems + complexItems
    # compute some item weights based on their popularity
    weightedCandidates = []
    for candidate in candidates:
      count = candidate.popularity
      while count > 0:
        weightedCandidates.append(candidate)
        count -= 1
      if count > 0:
        if random.uniform(1) < count:
          weightedCandidates.append(candidate)
    # complete the store with random simple or complicated items
    while len(results) < targetNumItems:
      results.append(random.choice(weightedCandidates))
    # randomize the costs somewhat, and round them
    for i in range(len(results)):
      itemData = results[i].clone()
      itemData.cost = self.round(itemData.cost * random.uniform(2.0/3.0, 4.0/3.0))
      results[i] = itemData
    # sort items by description
    return self.sortItemsByDescription(results)

  def sortItemsByDescription(self, itemDataList):
    descriptions = [self.describe(itemData) for itemData in itemDataList]
    itemDataByDescription = {}
    for itemData in itemDataList:
      description = self.describe(itemData)
      itemDataHere = itemDataByDescription.get(description)
      if itemDataHere is None:
        itemDataHere = []
        itemDataByDescription[description] = itemDataHere
      itemDataHere.append(itemData)
    results = []
    for description in sorted(itemDataByDescription.keys()):
      results = results + itemDataByDescription[description]
    return results

  # rounds to the first two decimal places
  def round(self, value):
    radix = 10
    if value > 100:
      # for large values we have to shrink the number before rounding helps
      multiplier = 1
      while value > 100:
        value /= radix
        multiplier *= radix
      return round(value) * multiplier
    if value < 10:
      # for small values we have to round the number directly, otherwise we might still get rounding error
      multiplied = value
      numShifts = 0
      while multiplied < 10:
        multiplied *= 10
        numShifts += 1
      return round(value, numShifts)
    # for medium values we can simply round the number
    return round(value)

  def describe(self, itemData):
    return itemData.item.summarize() + ": cost = " + str(itemData.cost)

  def process(self):
    while True:
      print("")
      print("Welcome to the shop! You have " + str(self.player.money) + " money")
      menu = Menu()
      menu.addChoice("Bye!", -1)
      if len(self.contents) > 0:
        menu.addChoice("What are these things?", -2)
      for i in range(len(self.contents)):
        menu.addChoice(self.describe(self.contents[i]), i)
      choice = menu.chooseValue()
      if choice == -1:
        print("Bye!")
        return # done
      if choice == -2:
        self.explainItem()
        continue
      itemIndex = choice
      cost = self.contents[itemIndex].cost
      if cost > self.player.money:
        print("Not enough money: " + str(self.player.money) + " < " + str(cost))
        continue
      itemData = self.contents[itemIndex]
      item = itemData.item.clone()
      print("Enjoy your " + item.summarize() + "!")
      self.player.addItem(item)
      self.purchasedItems.append(itemData)
      self.player.money -= cost
      del self.contents[itemIndex]

  def explainItem(self):
    print("What is what?")
    menu = Menu()
    menu.addChoice("Explain all of them!", -1)
    for i in range(len(self.contents)):
      item = self.contents[i].item
      menu.addChoice(item.summarize(), i)
    choice = menu.chooseValue()
    if choice < 0:
      for content in self.contents:
        print(content.item.formatHelp())
        print("")
    else:
      item = self.contents[choice].item
      print(item.formatHelp())

  def updateRunLog(self, nodeName, runLog):
    entry = RunLogShopEntry(nodeName, self.purchasedItems, self.contents)
    runLog.addEntry(entry)

  def serializeItemData(self, itemData):
    return [self.itemDataFactory.itemDataToDict(d) for d in itemData]

class TestingStoryNode(CompetitionStoryNode):
  def __init__(self, player, itemDataFactory):
    super().__init__(-1, player, makeOpponent(1, itemDataFactory), 0, None)
    self.nextNode = None

  def updateRunLog(self, successful):
    return # don't save test results

class CustomizationStoryNode(SimpleStoryNode):
  def __init__(self, player):
    super().__init__()
    self.player = player

  def showStatus(self):
    print(str(len(self.player.items)) + " unused items")
    for item in self.player.items:
      print("  " + item.summarize())
    print(str(self.player.network.size()) + " items in network")
    for item in self.player.network.nodes:
      print("  " + item.describeLinks())
    print("")

  def process(self):
    print("")
    print("Customizing")
    while True:
      self.showStatus()
      menu = Menu()
      network = self.player.network
      for i in range(network.size()):
        item = network.nodes[i]
        displayIndex = i + 1
        menu.addChoice("Edit #" + str(displayIndex) + " " + item.describeLinks(), i)
      if len(self.player.items) > 0:
        menu.addChoice("Add all items to network", -1)
      menu.addChoice("Done", -2)
      choice = menu.chooseValue()
      print("")
      if choice == -1:
        self.player.network.addAll(self.player.items)
        self.player.items = []
        continue
      if choice == -2:
        return
      self.editItem(self.player.network.nodes[choice])

  def chooseNetworkItem(self, description):
    print(description)
    menu = Menu()
    for item in self.player.network.nodes:
      menu.addChoice(item.describeLinks(), item)
    return menu.chooseValue()

  def chooseNetworkItemOutput(self, description):
    print(description)
    menu = Menu()
    menu.addChoice("None", None)
    for item in self.player.network.nodes:
      for outputName in item.outputNames:
        index = self.player.network.getPosition(item)
        displayIndex = index + 1
        output = Output(item, outputName)
        menu.addChoice("#" + str(displayIndex) + " " + output.summarize(), output)
    return menu.chooseValue()

  def editItem(self, item):
    while True:
      index = self.player.network.getPosition(item)
      displayIndex = index + 1
      print("Editing #" + str(displayIndex) + " " + item.describeLinks())
      menu = Menu()
      menu.addChoice("Move", "Move")
      for linkName in item.inputsByName.keys():
        menu.addChoice("Set input " + linkName, linkName)
      menu.addChoice("Help", "Help")
      menu.addChoice("Done", "Done")
      choice = menu.chooseValue()
      if choice == "Move":
        self.moveItem(item)
        # if the item is still in the network, keep editing it
        if item in self.player.network.nodes:
          continue
        # if the item is no longer in the network, stop editing it
        return
      if choice == "Done":
        return
      if choice == "Help":
        print(item.formatHelp())
        input("(press Enter)")
        return
      linkName = choice
      dependency = self.chooseNetworkItemOutput("Choose " + linkName + " for " + item.summarize())
      item.inputsByName[linkName] = dependency

  def moveItem(self, item):
    print("Move " + item.describeLinks() + " where?")
    menu = Menu()
    for i in range(self.player.network.size()):
      displayIndex = i + 1
      menu.addChoice("Position " + str(displayIndex), i)
    menu.addChoice("Remove", -1)
    menu.addChoice("Cancel", -2)
    choice = menu.chooseValue()
    if choice == -2:
      return
    self.player.network.nodes.remove(item)
    if choice == -1:
      self.player.items.append(item)
      return
    self.player.network.insert(item, choice)

class MarketStoryNode(MenuStoryNode):
  def __init__(self, nodeName, player, complexity, itemDataFactory, runLog):
    super().__init__("Welcome to the market")
    self.nodeName = nodeName
    self.runLog = runLog
    self.shop = ShopStoryNode(player, complexity, itemDataFactory)
    self.shop.setNext(self)
    tester = TestingStoryNode(player, itemDataFactory)
    tester.setNext(self)
    customizer = CustomizationStoryNode(player)
    customizer.setNext(self)
    sage = SageStoryNode("Greetings", """
    What is this place?:This is a robot competition
     Can I get a robot?:You can buy robot parts in a shop and assemble them yourself
      How do I assemble a robot?:Put the pieces in some order and then connect the ones that need power to the ones that provide power
     How do robot competitions work?:Two robots attack each other until one has no pieces left or time runs out. Then the robot with the most pieces remaining wins
      How do robots attack?:Some items will attack a piece of the other robot if you give them power
    Will I be happy here?:It depends. This place is still a work in progress, but what are you looking for?
     I'd love to participate in a robot competition:Excellent! I expect you will like it.
     I like hard math problems:This place has been designed for you, actually.
      Wow!:Yes, and if you're familiar with The Python, you may be able to change it further to your liking.
       What's The Python?:If you are worthy, you will find it yourself.
     I want easy math problems:I'm sure you will be able to enjoy some of our kiddie events.
     I'm looking for an incredible story:We don't have any plans for that right now - you might want to head somewhere else.
     I want to adventure with beautiful people:[The sage blinks twice] Well, I'm more wrinkled than I used to be but I think you'll find us to be beautiful on the inside.
    What makes you a sage?:I know many things.
     So where should I go next?:Try the shop.
     Really? What else do you know?:Are you familiar with https://github.com/mathjeff/JeffsKnowledgeGraph ?
    """)
    sage.setNext(self)
    self.addChoice("shop", self.shop)
    self.addChoice("customize", customizer)
    self.addChoice("test", tester)
    self.addChoice("talk to the sage", sage)
    self.exitNode = None

  def getTotalCost(self):
    return self.shop.getTotalCost()

  def setNext(self, nextNode):
    self.addChoice("Bye!", nextNode)
    self.exitNode = nextNode

  def onGoTo(self, nextNode):
    if nextNode == self.exitNode:
      self.shop.updateRunLog(self.nodeName, self.runLog)

# a StoryNodeRunner follows a path of StoryNode objects
class StoryNodeRunner(object):
  def __init__(self, startingMenu):
    self.currentMenu = startingMenu

  def run(self):
    while self.currentMenu is not None:
      self.currentMenu = self.currentMenu.getNext()

# creates a StoryNode network
class StoryGenerator(object):
  def __init__(self, player, competitionBuilder, itemDataFactory, runLog):
    self.player = player
    self.targetLength = competitionBuilder.getMaxLength()
    self.competitionBuilder = competitionBuilder
    self.itemDataFactory = itemDataFactory
    self.runLog = runLog

  def create(self):
    player = self.player
    estimatedPlayerMoney = player.money
    firstNode = MessageStoryNode("Let's begin")
    currentNode = firstNode
    index = -1
    previousMarketCost = 0
    previousNodeIsMarket = False
    while True:
      index += 1
      if index >= self.targetLength:
        break
      # if we think the player will have a lot of money, offer a shop
      if (not previousNodeIsMarket) and random.randint(0, estimatedPlayerMoney) >= previousMarketCost / 5:
        market = self.makeMarket(index)
        previousMarketCost = market.getTotalCost()
        currentNode.setNext(market)
        currentNode = market
        estimatedPlayerMoney = int(max(estimatedPlayerMoney - previousMarketCost, estimatedPlayerMoney / 4))
        previousNodeIsMarket = True
        continue
      previousNodeIsMarket = False
      # in most cases, send the player to a competition
      rewardMoney = 10
      estimatedPlayerMoney += rewardMoney
      competition = self.competitionBuilder.buildCompetition(player, index, self.itemDataFactory, rewardMoney, self.runLog)
      currentNode.setNext(competition)
      currentNode = competition

    success = MessageStoryNode("You win!")
    currentNode.setNext(success)
    return firstNode

  def makeMarket(self, index):
    fractionComplete = index / self.targetLength
    maxComplexity = 4
    nodeComplexity = 1 + fractionComplete * (maxComplexity - 1)
    nodeName = str(index)
    return MarketStoryNode(nodeName, self.player, nodeComplexity, self.itemDataFactory, self.runLog)

# builds competitions and keeps track of difficulty
class CompetitionBuilder(object):
  def __init__(self, filepath):
    if os.path.isfile(filepath):
      self.loadFile(filepath)
    else:
      self.setupDefaults()
      self.save(filepath)

  def buildCompetition(self, player, roomIndex, itemDataFactory, rewardMoney, runLog):
    difficulty = self.getDifficulty(roomIndex)
    opponent = makeOpponent(difficulty, itemDataFactory)
    competition = CompetitionStoryNode(roomIndex, player, opponent, rewardMoney, runLog)
    return competition

  def getMaxLength(self):
    return len(self.difficulties)

  def getDifficulty(self, roomIndex):
    return self.difficulties[roomIndex]

  def rescaleDifficulty(self, roomIndex, difficulty):
    self.difficulties[roomIndex] *= difficulty

  def decrementLength(self):
    if len(self.difficulties) > 2:
      self.difficulties = self.difficulties[:-1]

  def incrementLength(self):
    lastDifficulty = self.difficulties[-1]
    nextDifficulty = lastDifficulty * (len(self.difficulties) + 1) / len(self.difficulties)
    self.difficulties.append(nextDifficulty)

  def loadFile(self, filepath):
    self.difficulties = self.readFile(filepath)

  def ensureSaved(self, filepath):
    if not os.path.isfile(filepath):
      self.save(filepath)

  def save(self, filepath):
    if os.path.exists(filepath):
      raise Exception("File exists: " + str(filepath))
    parentPath = os.path.dirname(filepath)
    os.makedirs(parentPath, exist_ok = True)
    text = self.serialize()
    with open(filepath, 'w') as f:
      f.write(text)

  def readFile(self, filepath):
    with open(filepath) as f:
      return json.load(f)

  def serialize(self):
    return str(self.difficulties)

  def setupDefaults(self):
    self.difficulties = [i for i in range(10)]

# represents a network of items
class Network(object):
  def __init__(self):
    self.nodes = []
    self.nodePositions = None

  def addItem(self, template):
    self.nodes.append(template)
    self.nodePositions = None

  def addAll(self, templates):
    self.setItems(self.nodes + templates)

  def insert(self, item, index):
    self.setItems(self.nodes[:index] + [item] + self.nodes[index:])

  def setItems(self, nodes):
    self.nodes = nodes
    self.nodePositions = None

  def clone(self):
    # create nodes and identify indices
    builtNodes = []
    nodeIndices = {}
    for i in range(len(self.nodes)):
      template = self.nodes[i]
      builtNodes.append(template.clone())
      nodeIndices[template] = i
    # add links
    for i in range(len(self.nodes)):
      template = self.nodes[i]
      item = builtNodes[i]
      for linkType, linkInput in template.inputsByName.items():
        if linkInput is not None:
          linkItem = linkInput.item
          otherIndex = nodeIndices[linkItem]
          otherItem = builtNodes[otherIndex]
          item.addInput(linkType, otherItem, linkInput.outputName)
    result = Network()
    result.setItems(builtNodes)
    return result

  def size(self):
    return len(self.nodes)

  def getPosition(self, node):
    if self.nodePositions is None:
      self.nodePositions = {self.nodes[i] : i for i in range(len(self.nodes))}
    return self.nodePositions[node]

# represents the player
class GamePlayer(object):
  def __init__(self, name):
    self.name = name
    self.money = 100
    self.items = []
    self.network = Network()
    self.numLosses = 0

  def addItem(self, item):
    self.items.append(item)

  def buildCompetitor(self):
    return Competitor(self.name, self.network.clone())

  def getHitpoints(self):
    return 3 - self.numLosses

def makeOpponent(difficulty, itemDataFactory):
  player = GamePlayer("Opponent")
  network = player.network
  batteries = []
  lasers = []
  for i in range(int(difficulty)):
    choice = random.randint(0, 2)
    if choice == 0:
      battery = itemDataFactory.cloneItemNamed("Battery")
      network.addItem(battery)
      batteries.append(battery)
      continue
    if choice == 1:
      laser = itemDataFactory.cloneItemNamed("Laser")
      network.addItem(laser)
      lasers.append(laser)
      continue
    if choice == 2:
      network.addItem(itemDataFactory.cloneItemNamed("Wall"))
      continue
  if len(batteries) > 0:
    for laser in lasers:
      laser.addInput("power", random.choice(batteries))
  return player
