#!python

from competition.Competition import *
from items.Items import *

import random, sys, textwrap

class StoryNode(object):
  def __init__(self):
    return

  def getNext(self):
    return None

  def summarize(self):
    return type(self).__name__

class Menu(object):
  def __init__(self):
    self.choicesByIndex = {}
    self.previousIndex = 0 # first index is 1 by default

  def addChoice(self, text, result, index=None):
    if index is None:
      index = self.previousIndex + 1
    while index in self.choicesByIndex:
      index += 0.1
    self.previousIndex = index
    self.choicesByIndex[index] = (text, result)

  def chooseValue(self):
    index = self.chooseIndex()
    return self.choicesByIndex[index][1]

  def chooseIndex(self):
    for index in sorted(self.choicesByIndex.keys()):
      optionText = self.choicesByIndex[index][0]
      print(str(index) + ": " + str(optionText))
    choiceText = ""
    while True:
      choiceText = input("")
      number = 0
      if len(self.choicesByIndex) <= 1:
        # there's only one choice so we return it
        for index in self.choicesByIndex:
          return index
      try:
        number = float(choiceText)
      except Exception as e:
        print("Choose a number!")
        continue
      if number not in self.choicesByIndex:
        print("Choose an option!")
        continue
      return number

  def choices(self):
    result = set()
    for entry in self.choicesByIndex.values():
      result.add(entry[1])
    return result

class MenuStoryNode(StoryNode):
  def __init__(self, text):
    super().__init__()
    self.text = text
    self.menu = Menu()
    self.nextNode = None

  # gets the next node to go to after this one (which is node that the user chooses)
  def getNext(self):
    print(self.text)
    result = self.menu.chooseValue()
    self.onGoTo(result)
    return result

  # sets the next node to go to after this node and its selected choice are completed
  def setNext(self, nextNode):
    for child in self.menu.choices():
      child.setNext(nextNode)

  def onGoTo(self, choice):
    return

  def addChoice(self, text, result):
    self.menu.addChoice(text, result)
    if self.nextNode is not None:
      result.setNext(self.nextNode)

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
      menu.addChoice("Back", currentNode.parent, 0)
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
    # run competition
    print("Room " + str(self.index) + ": you enter a competition with " + str(self.opponent.name))
    competition = Competition([self.player, self.opponent])
    result = competition.run()
    # output status
    print("")
    if result is None:
      print("Tie!\n")
    else:
      if result:
        print("Success! You defeated " + str(self.opponent.name) + "\n")
      else:
        print("Failure\n")
    # process results
    self.onResult(result)

  def onResult(self, successful):
    # save the successful
    entry = RunLogCompetitionEntry(str(self.index), successful)
    self.runLog.addEntry(entry)
    # do any updates
    if successful is not None:
      if successful:
        if self.rewardMoney != 0:
          self.player.money += self.rewardMoney
          print("You gain "  + str(self.rewardMoney) + " money and have " + str(self.player.money) + " money")
      else:
        self.player.hitpoints -= 1
        hitpoints = self.player.getHitpoints()
        if hitpoints > 0:
          print("You may continue until " + str(hitpoints) + " more losses")
        else:
          print("Loss limit reached. Bye!")
          sys.exit(0)

class FinalsStoryNode(SimpleStoryNode):
  def __init__(self, player, numRemainingNodes):
    self.player = player
    self.numRemainingNodes = numRemainingNodes

  def process(self):
    print(str(self.numRemainingNodes) + " events remaining: tournament mode switches to single elimination!")
    print("Any losses after this point will result in ejection from the tournament. Good luck!")
    self.player.hitpoints = 1
    input("")

class ShopStoryNode(SimpleStoryNode):
  def __init__(self, player, offerings, offeringFactory):
    super().__init__()
    self.player = player
    self.contents = self.chooseContents(offerings)
    self.purchasedItems = []
    self.offeringFactory = offeringFactory

  def getTotalCost(self):
    total = 0
    for content in self.contents:
      if content is not None:
        total += content.cost
    return total

  def chooseContents(self, offerings):
    return self.sortItemsByDescription(offerings)

  def sortItemsByDescription(self, offerings):
    descriptions = [self.describe(offering) for offering in offerings]
    offeringsByDescription = {}
    for offering in offerings:
      description = self.describe(offering)
      offeringsHere = offeringsByDescription.get(description)
      if offeringsHere is None:
        offeringsHere = []
        offeringsByDescription[description] = offeringsHere
      offeringsHere.append(offering)
    results = []
    for description in sorted(offeringsByDescription.keys()):
      results = results + offeringsByDescription[description]
    return results

  def describe(self, offering):
    if offering is None:
      return "Nothing"
    components = [item.summarize() for item in offering.items]
    return ", ".join(components) + ": cost = " + str(offering.cost)

  def hasOffering(self):
    for offering in self.contents:
      if offering is not None:
        return True
    return False

  def process(self):
    while True:
      print("")
      print("Welcome to the shop! You have " + str(self.player.money) + " money")
      menu = Menu()
      menu.addChoice("Done (buying items)", 0, 0)
      if self.hasOffering():
        menu.addChoice("What are these things?", 1)
      for i in range(len(self.contents)):
        menu.addChoice(self.describe(self.contents[i]), i + 2)
      choice = menu.chooseValue()
      if choice == 0:
        print("Bye!")
        return # done
      if choice == 1:
        self.explainItems()
        continue
      itemIndex = choice - 2
      offering = self.contents[itemIndex]
      if offering is None:
        print("Nothing is there!")
      else:
        cost = offering.cost
        if cost > self.player.money:
          print("Not enough money: " + str(self.player.money) + " < " + str(cost))
          continue
        # give all items to the player
        for item in offering.items:
          item = item.clone()
          print("Enjoy your " + item.summarize() + "!")
          self.player.addItem(item)
        # record what was purchased
        self.purchasedItems.append(offering)
        self.player.money -= cost
        self.contents[itemIndex] = None

  def explainItems(self):
    for offering in self.contents:
      if offering is not None:
        for item in offering.items:
          print(item.formatHelp())
          print("")

  def updateRunLog(self, nodeName, runLog):
    unpurchased = [offering for offering in self.contents if offering is not None]
    entry = RunLogShopEntry(nodeName, self.purchasedItems, unpurchased)
    runLog.addEntry(entry)

  def serializeOffering(self, offerings):
    return [self.offeringFactory.offeringToDict(o) for o in offerings]

  def summarize(self):
    nonemptyOfferings = [offering for offering in self.contents if offering is not None]
    if len(nonemptyOfferings) == 1:
      return "shop (" + self.describe(nonemptyOfferings[0]) + ")"
    return "shop (" + str(len(nonemptyOfferings)) + " items)"

  def __str__(self):
    return self.summarize()

class TestingStoryNode(CompetitionStoryNode):
  def __init__(self, player, offeringFactory):
    super().__init__(-1, player, makeOpponent(3, offeringFactory), 0, None)
    self.nextNode = None

  def onResult(self, successful):
    return # don't save test results

class CustomizationStoryNode(SimpleStoryNode):
  def __init__(self, player):
    super().__init__()
    self.player = player

  def showStatus(self):
    print(str(len(self.player.items)) + " unused items")
    for item in self.player.items:
      print("  " + item.summarize())
    network = self.player.network
    print(str(network.size()) + " items in network:")
    for item in network.nodes:
      print("  " + self.describeItem(item))
    print("")

  def process(self):
    print("")
    print("Customizing")
    network = self.player.network
    while True:
      self.showStatus()
      menu = Menu()
      menu.addChoice("Done (configuring network)", "Done", 0)
      if len(self.player.items) > 0:
        menu.addChoice("Add all items to network", "Add")
      if len(network.nodes) > 0:
        menu.addChoice("Move an item", "Move")
        menu.addChoice("Edit an item", "Edit")
        menu.addChoice("Remove an item", "Remove")
        menu.addChoice("Explain an item", "Help")
      choice = menu.chooseValue()
      if choice == "Add":
        self.player.network.addAll(self.player.items)
        self.player.items = []
        continue
      if choice == "Move":
        self.moveItems()
        continue
      if choice == "Edit":
        self.linkItems()
        continue
      if choice == "Remove":
        self.removeItems()
        continue
      if choice == "Help":
        self.helpItems()
        continue
      if choice == "Done":
        return

  def moveItems(self):
    network = self.player.network
    while True:
      nodes = network.nodes
      fromIndex = self.chooseNetworkPosition("Select item to move:", "Done (moving items)", "Move", nodes)
      if fromIndex < 0:
        return
      toIndex = self.chooseNetworkPosition("Select new position:", "Cancel", "Position", nodes)
      if toIndex < 0:
        continue
      item = network.removeAt(fromIndex)
      network.insert(toIndex, item)

  def linkItems(self):
    nodes = self.player.network.nodes
    while True:
      choices = [item for item in nodes if item.declaresInputs()]
      destIndex = self.chooseNetworkPosition("Select item to link:", "Done (linking items)", "Link", choices)
      if destIndex < 0:
        return
      item = nodes[destIndex]
      inputName = self.chooseNetworkItemInput(item)
      source = self.chooseNetworkItemOutput("Select source for " + item.summarize())
      if source is not None:
        item.setInput(inputName, source.item, source.outputName)
      else:
        item.setInput(inputName, None)

  def chooseNetworkPosition(self, prompt, cancelText, choicePrefix, validChoices):
    print(prompt)
    choiceSet = set(validChoices)
    menu = Menu()
    menu.addChoice(cancelText, -1, 0)
    network = self.player.network
    for i in range(len(network.nodes)):
      item = network.nodes[i]
      if item in choiceSet:
        displayIndex = i + 1
        menu.addChoice(choicePrefix + " " + self.describeItem(item), i, displayIndex)
    return menu.chooseValue()

  def chooseNetworkItemInput(self, item):
    menu = Menu()
    for linkName in item.getInputNames():
      menu.addChoice("Set input " + linkName, linkName)
      if len(item.getInputNames()) == 1:
        return linkName
    print("Select input in " + item.describeLinks(self.player.network) + ":")
    return menu.chooseValue()

  def chooseNetworkItemOutput(self, description):
    print(description)
    menu = Menu()
    menu.addChoice("None", None, index=0)
    for item in self.player.network.nodes:
      index = self.player.network.getPosition(item)
      outputIndex = 0
      for outputName in item.getOutputNames():
        outputIndex += 1
        displayIndex = index + 1
        output = ItemOutput(item, outputName)
        menu.addChoice("#" + str(displayIndex) + " " + output.summarize(), output, displayIndex)
    return menu.chooseValue()

  def describeItem(self, item):
    itemText = item.describeLinks(self.player.network)
    if item.hintMisconfigured():
      itemText = "! " + itemText
    return itemText

  def removeItems(self):
    while True:
      nodes = self.player.network.nodes
      fromIndex = self.chooseNetworkPosition("Select item to remove:", "Done (removing items)", "Remove", nodes)
      if fromIndex < 0:
        return
      item = nodes.pop(fromIndex)
      self.player.items.append(item)

  def helpItems(self):
    nodes = self.player.network.nodes
    while True:
      index = self.chooseNetworkPosition("Explain which item?", "Done (explaining items)", "Explain", nodes)
      if index < 0:
        return
      print(nodes[index].formatHelp())
      input("(press Enter)")

class MarketStoryNode(MenuStoryNode):
  def __init__(self, nodeName, description, player, offerings, offeringFactory, runLog):
    super().__init__("Welcome to market " + str(nodeName))
    self.nodeName = nodeName
    self.description = description
    self.runLog = runLog
    self.shop = ShopStoryNode(player, offerings, offeringFactory)
    self.shop.setNext(self)
    tester = TestingStoryNode(player, offeringFactory)
    tester.setNext(self)
    customizer = CustomizationStoryNode(player)
    customizer.setNext(self)
    sage = SageStoryNode("Greetings", """
    What is this place?:This is a robot competition
     Can I get a robot?:You can buy robot parts in a shop and assemble them yourself
      How do I assemble a robot?:Put the items in some order and then connect the ones that need power to the ones that provide power
     How do robot competitions work?:Two robots attack each other until one has no items left or time runs out. Then the robot with the most items remaining wins
      How do robots attack?:Some items will attack an item in the other robot if you give them power
       How can I give power to an item?:Some items produce charge during their turn, which can be given to other items if you connect them. Pay attention to the order of your items. During your turn, items in a robot activate from left to right.
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
    self.addChoice(self.shop, self.shop)
    self.addChoice("customize", customizer)
    self.addChoice("test", tester)
    self.addChoice("talk to the sage", sage)
    self.exitNode = None

  def getTotalCost(self):
    return self.shop.getTotalCost()

  def setNext(self, nextNode):
    self.addChoice("Leave (the market)", nextNode)
    self.exitNode = nextNode

  def onGoTo(self, nextNode):
    if nextNode == self.exitNode:
      self.shop.updateRunLog(self.nodeName, self.runLog)

  def summarize(self):
    return self.description

class SuccessStoryNode(SimpleStoryNode):
  def __init__(self, name, runLog):
    super().__init__()
    self.name = name
    self.runLog = runLog

  def process(self):
    self.runLog.addEntry(RunLogConclusionEntry(self.name, True))
    print("You win!")

# a StoryNodeRunner follows a path of StoryNode objects
class StoryNodeRunner(object):
  def __init__(self, startingMenu):
    self.currentMenu = startingMenu

  def run(self):
    while self.currentMenu is not None:
      self.currentMenu = self.currentMenu.getNext()

# a LazyStoryNode asks a StoryGenerator to generate the next node when needed
class LazyStoryNode(StoryNode):
  def __init__(self, index, generator):
    self.index = index
    self.generator = generator

  def getNext(self):
    return self.generator.getRoomAfter(self.index)

class OfferingFilter(object):
  def __init__(self):
    return

  def acceptsOffering(self, offering):
    raise Exception("acceptsOffering not implemented in " + str(self))

  def summarize(self):
    return type(self).__name__

class AllOfferingsFilter(OfferingFilter):
  def __init__(self):
    return

  def acceptsOffering(self, offering):
    return True

  def summarize(self):
    return "all types of items"

class PowerSource_OfferingFilter(OfferingFilter):
  def __init__(self):
    super().__init__()

  def acceptsOffering(self, offering):
    # if any item in the offering is a power sink, then the offering isn't a power source
    for item in offering.items:
      if item.declaresInputs() and not item.declaresOutputs():
        return False
    # if at least one item is a power source, the offering is a power source
    for item in offering.items:
      if item.declaresOutputs() and not item.declaresInputs():
        return True
    return False

  def summarize(self):
    return "energy sources"

class PowerSink_OfferingFilter(OfferingFilter):
  def __init__(self):
    super().__init__()

  def acceptsOffering(self, offering):
    # if any item in the offering is a power source, then the offering isn't a power sink
    for item in offering.items:
      if item.declaresOutputs() and not item.declaresInputs():
        return False
    # if at least one item is a power sink, the offering is a power sink
    for item in offering.items:
      if item.declaresInputs() and not item.declaresOutputs():
        return True
    return False

  def summarize(self):
    return "energy sinks"

class PowerTransformer_OfferingFilter(OfferingFilter):
  def __init__(self):
    super().__init__()

  def acceptsOffering(self, offering):
    for item in offering.items:
      if item.declaresInputs() and item.declaresOutputs():
        return True
    return False

  def summarize(self):
    return "power connectors/transformers"

class Color_OfferingFilter(OfferingFilter):
  def __init__(self, color):
    super().__init__()
    self.color = color

  def acceptsOffering(self, offering):
    for item in offering.items:
      if self.acceptsItem(item):
        return True
    return False

  def acceptsItem(self, item):
    properties = item.properties
    for propertyName in properties.keys():
      propertyValue = properties.get(propertyName)
      if isinstance(propertyValue, dict):
        if self.color.shortName in propertyValue.keys():
          return True
    return False

  def summarize(self):
    return "items involving " + self.color.formatLongName() + " energy"

# creates a StoryNode network
class StoryGenerator(object):
  def __init__(self, player, competitionBuilder, offeringFactory, runLog):
    self.player = player
    self.targetLength = competitionBuilder.getMaxLength()
    self.competitionBuilder = competitionBuilder
    self.offeringFactory = offeringFactory
    self.runLog = runLog
    self.previousMarketIndex = -100
    self.finalsLength = player.hitpoints
    self.nextShopNumItems = 12
    self.makeMultipleMarkets = False

  def create(self):
    player = self.player
    firstNode = MessageStoryNode("Starting!")
    door = LazyStoryNode(-1, self)
    firstNode.setNext(door)
    return firstNode

  def makeRoom(self, index):
    # some special cases near the end of the game
    if index > self.targetLength:
      return None
    if index == self.targetLength:
      return SuccessStoryNode(str(index), self.runLog)
    if index == self.targetLength - self.finalsLength - 1:
      finalsNode = FinalsStoryNode(self.player, self.finalsLength)
      return finalsNode
    # decide whether to make a market
    makeMarket = (index >= self.previousMarketIndex + 4)
    if index == self.targetLength - 1:
      makeMarket = False
    if makeMarket:
      self.previousMarketIndex = index
      if self.makeMultipleMarkets:
        market = self.makeMarkets(index, 2, self.nextShopNumItems)
      else:
        market = self.makeMarket(index, AllOfferingsFilter(), self.nextShopNumItems)
      self.makeMultipleMarkets = True
      self.nextShopNumItems = 2
      return market
    self.previousNodeIsMarket = False
    # in most cases, send the player to a competition
    rewardMoney = 3
    competition = self.competitionBuilder.buildCompetition(self.player, index, self.offeringFactory, rewardMoney, self.runLog)
    return competition

  def makeMarkets(self, index, numMarkets, numItems):
    # candidate offering filters
    candidateFilters = [AllOfferingsFilter(), PowerSource_OfferingFilter(), PowerSink_OfferingFilter(), PowerTransformer_OfferingFilter()]
    for color in Energies.getAll():
      candidateFilters.append(Color_OfferingFilter(color))
    # choose two at random
    index1 = random.randint(0, len(candidateFilters) - 1)
    index2 = random.randint(1, len(candidateFilters) - 1)
    if index2 == index1:
      index2 = 0
    filter1 = candidateFilters[index1]
    filter2 = candidateFilters[index2]
    market1 = self.makeMarket(index, filter1, numItems)
    market2 = self.makeMarket(index, filter2, numItems)
    chooser = MenuStoryNode("Choose a market to visit!")
    chooser.addChoice(market1.description, market1)
    chooser.addChoice(market2.description, market2)
    return chooser

  def makeMarket(self, index, offeringFilter, numItems):
    fractionComplete = index / self.targetLength
    maxComplexity = 10
    nodeComplexity = 1 + fractionComplete * (maxComplexity - 1)
    nodeName = str(index)
    candidates = self.filterOfferings(self.offeringFactory.getAll(), offeringFilter)
    offerings = self.chooseMarketContents(nodeComplexity, index, numItems, candidates)
    description = "a market with " + offeringFilter.summarize()
    return MarketStoryNode(nodeName, description, self.player, offerings, self.offeringFactory, self.runLog)

  def filterOfferings(self, offerings, offeringsFilter):
    result = [offering for offering in offerings if offeringsFilter.acceptsOffering(offering)]
    return result

  def chooseMarketContents(self, complexity, index, targetNumItems, candidateOfferings):
    # find a bunch of candidates
    simpleItems = []
    complexItems = []
    for offering in candidateOfferings:
      if offering.complexity <= complexity:
        simpleItems.append(offering)
      else:
        if offering.complexity <= complexity + 1:
          complexItems.append(offering)
    results = []
    if targetNumItems >= len(simpleItems):
      # we can add all simple items, so do that first
      results += simpleItems
      # next, add some of the remaining complicated items
      results += self.chooseDistinctRandomWeightedItems(complexItems, targetNumItems - len(results))
    else:
      # we can't add all of the simple items, so just add the simple items
      results += self.chooseDistinctRandomWeightedItems(simpleItems, targetNumItems)
    # randomize the costs somewhat, and round them
    for i in range(len(results)):
      offering = results[i].clone()
      offering.cost = self.round(offering.cost * random.uniform(2.0/3.0, 4.0/3.0))
      results[i] = offering
    return results

  # choose distinct random items, weighted by popularity
  def chooseDistinctRandomWeightedItems(self, choices, count):
    if len(choices) < 1:
      raise Exception("no choices!")
    results = []
    currentChoices = []
    while len(results) < count:
      if len(currentChoices) < 1:
        currentChoices = choices[:]
      choice = self.chooseRandomWeightedItem(currentChoices)
      results.append(choice)
      currentChoices.remove(choice)
    return results

  # chooses a random item, weighted by popularity
  def chooseRandomWeightedItem(self, choices):
    if len(choices) < 1:
      raise Exception("no choices!")
    totalPopularity = 0
    for choice in choices:
      totalPopularity += choice.popularity
    number = random.uniform(0, totalPopularity)
    cumulative = 0
    for choice in choices:
      cumulative += choice.popularity
      if number <= cumulative:
        return choice
    raise Exception("random number " + str(number) + " > cumulative " + str(cumulative))

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

  def getRoomAfter(self, index):
    room = self.makeRoom(index + 1)
    if room is not None:
      door = LazyStoryNode(index + 1, self)
      room.setNext(door)
    return room

# builds competitions and keeps track of difficulty
class CompetitionBuilder(object):
  def __init__(self, filepath):
    if os.path.isfile(filepath):
      self.loadFile(filepath)
    else:
      self.setupDefaults()
      self.save(filepath)

  def buildCompetition(self, player, roomIndex, offeringFactory, rewardMoney, runLog):
    difficulty = self.getDifficulty(roomIndex)
    opponent = makeOpponent(difficulty, offeringFactory)
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
    self.difficulties = [int((i + 6) / 4) for i in range(55)]

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

  def insert(self, index, item):
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
          item.setInput(linkType, otherItem, linkInput.outputName)
    result = Network()
    result.setItems(builtNodes)
    return result

  def size(self):
    return len(self.nodes)

  def getPosition(self, node):
    result = self.tryGetPosition(node)
    if result is None:
      raise Exception("Node " + str(node) + " not in network")
    return result

  def tryGetPosition(self, node):
    if self.nodePositions is None:
      self.nodePositions = {self.nodes[i] : i for i in range(len(self.nodes))}
    return self.nodePositions.get(node)

  def removeAt(self, index):
    self.nodePositions = None
    return self.nodes.pop(index)

# represents the player
class GamePlayer(object):
  def __init__(self, name):
    self.name = name
    self.money = 100
    self.items = []
    self.network = Network()
    self.hitpoints = 3

  def addItem(self, item):
    self.items.append(item)

  def buildCompetitor(self):
    return Competitor(self.name, self.network.clone())

  def getHitpoints(self):
    return self.hitpoints

def makeOpponent(difficulty, offeringFactory):
  player = GamePlayer("Opponent")
  network = player.network
  batteries = []
  lasers = []
  for i in range(int(difficulty)):
    choice = random.randint(0, 2)
    if choice == 0:
      battery = offeringFactory.cloneItemNamed("Battery")
      network.addItem(battery)
      batteries.append(battery)
      continue
    if choice == 1:
      laser = offeringFactory.cloneItemNamed("Laser")
      network.addItem(laser)
      lasers.append(laser)
      continue
    if choice == 2:
      network.addItem(offeringFactory.cloneItemNamed("Wall"))
      continue
  if len(batteries) > 0:
    for laser in lasers:
      laser.setInput("power", random.choice(batteries))
  return player
