#!python

from competition.Competition import *
from items.Items import *
from persistence.Persistence import *

import json, os, random, shutil, textwrap

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
    return self.menu.chooseValue()

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
  def __init__(self, player, opponent):
    super().__init__()
    self.player = player
    self.opponent = opponent

  def process(self):
    print("You enter a competition with " + str(self.opponent.name))
    competition = Competition([self.player, self.opponent])
    result = competition.run()
    print("")
    if result is None:
      print("Tie!\n")
    else:
      if result:
        print("Success! You defeated " + str(self.opponent.name) + "\n")
      else:
        print("Failure\n")

class ShopStoryNode(SimpleStoryNode):
  def __init__(self, player):
    super().__init__()
    self.player = player
    self.contents = itemDataFactory.getAll()

  def process(self):
    while True:
      print("")
      print("Welcome to the shop! You have " + str(self.player.money) + " money")
      menu = Menu()
      menu.addChoice("Bye!", -1)
      if len(self.contents) > 0:
        menu.addChoice("What are these things?", -2)
      for i in range(len(self.contents)):
        item = self.contents[i].item
        cost = self.contents[i].cost
        menu.addChoice(item.summarize() + ": cost = " + str(cost), i)
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
        print("Not enough money: " + str(player.money) + " < " + str(cost))
        continue
      item = self.contents[itemIndex].item
      print("Enjoy your " + item.summarize() + "!")
      self.player.addItem(item)
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

class TestingStoryNode(CompetitionStoryNode):
  def __init__(self, player):
    super().__init__(player, makeEasyOpponent())
    self.nextNode = None

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
        index = network.getPosition(item)
        menu.addChoice("Edit #" + str(index) + " " + item.describeLinks(), i)
      if len(self.player.items) > 0:
        menu.addChoice("Add all items to network", -1)
      menu.addChoice("Done", -2)
      choice = menu.chooseValue()
      print("")
      if choice == -1:
        self.player.network.nodes += self.player.items
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
        output = Output(item, outputName)
        menu.addChoice("#" + str(index) + " " + output.summarize(), output)
    return menu.chooseValue()

  def editItem(self, item):
    while True:
      index = self.player.network.getPosition(item)
      print("Editing #" + str(index) + " " + item.describeLinks())
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
    menu.addChoice("Remove", -1)
    for i in range(self.player.network.size()):
      menu.addChoice("Position " + str(i), i)
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
  def __init__(self, player):
    super().__init__("Welcome to the market")
    shop = ShopStoryNode(player)
    shop.setNext(self)
    tester = TestingStoryNode(player)
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
    self.addChoice("shop", shop)
    self.addChoice("customize", customizer)
    self.addChoice("test", tester)
    self.addChoice("talk to the sage", sage)

  def setNext(self, nextNode):
    self.addChoice("Bye!", nextNode)

# a StoryNodeRunner follows a path of StoryNode objects
class StoryNodeRunner(object):
  def __init__(self, startingMenu):
    self.currentMenu = startingMenu

  def run(self):
    while self.currentMenu is not None:
      self.currentMenu = self.currentMenu.getNext()

# represents a network of items
class Network(object):
  def __init__(self):
    self.nodes = []
    self.nodePositions = None

  def addItem(self, template):
    self.nodes.append(template)
    self.nodePositions = None

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

  def addItem(self, item):
    self.items.append(item)

  def buildCompetitor(self):
    return Competitor(self.name, self.network.clone())

# creates a StoryNode network
class StoryGenerator(object):
  def __init__(self, player, targetLength, difficulty, complexity):
    self.player = player
    self.targetLength = targetLength
    self.difficulty = difficulty
    self.complexity = complexity

  def create(self):
    player = self.player
    # create intro
    welcome = MessageStoryNode("Welcome to ColorNetwork!")
    firstMarket = self.makeMarket(0)
    welcome.setNext(firstMarket)
    firstOpponent = self.makeCompetition(0)
    firstMarket.setNext(firstOpponent)
    currentNode = firstOpponent

    # create main content
    numMarketsRemaining = max(1, int(self.targetLength / 20))
    index = 0
    while index < self.targetLength:
      lengthRemaining = self.targetLength - index
      rand = random.randint(0, lengthRemaining)
      index += 1
      if rand < numMarketsRemaining:
        market = self.makeMarket(index)
        currentNode.setNext(market)
        currentNode = market
        numMarketsRemaining -= 1
        continue
      competition = self.makeCompetition(index)
      currentNode.setNext(competition)
      currentNode = competition

    success = MessageStoryNode("Success!")
    currentNode.setNext(success)
    return welcome

  def makeMarket(self, index):
    return MarketStoryNode(self.player)

  def makeCompetition(self, index):
    opponent = makeEasyOpponent()
    competition = CompetitionStoryNode(self.player, opponent)
    return competition

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
runLog = RunLog(profile.getLatestPath("runlog"))
profile.save()

def makePlayer():
  player = GamePlayer("Player")
  return player

def makeEasyOpponent():
  player = GamePlayer("Test Opponent")
  battery1 = itemDataFactory.cloneItemNamed("Battery")
  laser1 = itemDataFactory.cloneItemNamed("Laser")
  laser1.addInput("power", battery1)
  player.network.addItem(itemDataFactory.cloneItemNamed("Wall"))
  player.network.addItem(laser1)
  player.network.addItem(battery1)
  return player

def makeStory():
  gamePlayer = makePlayer()
  length = 10
  difficulty = 1
  complexity = 1
  welcome = StoryGenerator(gamePlayer, length, difficulty, complexity).create()

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
