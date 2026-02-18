#!python

import json, os, random, textwrap

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

# An ItemProperties describes the properties that are used by an Item
# It doesn't describe other things like its cost or complexity
class ItemProperties(object):
  def __init__(self, properties):
    self.properties = properties

  def get(self, name):
    result = self.properties.get(name)
    if result is None:
      raise Exception("property '" + name + "' not in " + str(list(self.properties.keys())))
    return result

# represents an object that a Competitor can use
class Item(object):
  def __init__(self, properties):
    self.hitPoints = 1
    self.inputsByName = {}
    self.outputNames = []
    self.powerAcquiredLastTurn = 0
    self.acquiringPower = False
    self.putProperties(ItemProperties(properties))
    self.properties = properties

  def putProperties(self, properties):
    raise Exception("putProperties not implemented in " + str(self))

  def addInput(self, linkType, otherItem, outputName = None):
    if outputName not in otherItem.outputNames:
      raise Exception("output '" + outputName + "' not declared in " + str(otherItem))
    self.inputsByName[linkType] = Output(otherItem, outputName)

  def receiveDamage(self, amount):
    self.hitPoints -= amount

  def declareInputs(self, linkTypes):
    for linkType in linkTypes:
      self.inputsByName[linkType] = None

  def declareOutputs(self, linkTypes):
    self.outputNames = linkTypes

  def declareOutput(self):
    self.declareOutputs([None])

  # tries to get power from the given link
  def tryAcquirePower(self, linkType, amount):
    if amount < 0:
      return 0 # no power requested
    if self.acquiringPower:
      return 0 # we don't have any power for recursive calls
    if linkType not in self.inputsByName.keys():
      raise Exception("link type " + str(linkType) + " not declared in " + str(self) + ". All declared links: " + str(self.inputsByName))
    link = self.inputsByName.get(linkType)
    result = 0
    self.acquiringPower = True
    if link is not None:
      result = link.item.tryGetPower(amount, link.outputName)
    if result > 0:
      print(str(self.summarize()) + " got " + str(result) + " power from " + link.item.summarize())
    self.acquiringPower = False
    self.powerAcquiredLastTurn += result
    return result

  # tries to get power from the current node
  def tryGetPower(self, amount, outputName):
    return 0

  def getPowerAcquiredLastTurn(self):
    return self.powerAcquiredLastTurn

  def act(self, player):
    self.powerAcquiredLastTurn = 0

  def clone(self):
    raise Exception("clone is not implemented in " + str(self))

  def summarize(self):
    return type(self).__name__

  def getHelpMessages(self):
    messages = [self.summarize() + ":"]
    messages.append("has " + str(self.hitPoints) + " hit points")
    if len(self.inputsByName) > 0:
      messages.append("has " + str(len(self.inputsByName)) + " ports for receiving power:")
      for key, value in self.inputsByName.items():
        messages.append("  " + str(key) + " (connected to " + str(value) + ")")
    if len(self.outputNames) > 0:
      outputMessage = "has " + str(len(self.outputNames)) + " outputs"
      if len(self.outputNames) > 1:
        outputMessage += ": " + str(self.outputNames)
      messages.append(outputMessage)
    return messages

  def formatHelp(self):
    messages = self.getHelpMessages()
    return "\n ".join(messages)

  def describeLinks(self):
    messages = [self.summarize()]
    for name, value in self.inputsByName.items():
      if value is not None:
        messages.append(name + ": " + value.summarize())
      else:
        messages.append(name + ": None")
    return ", ".join(messages)

# represents an output of an item
class Output(object):
  def __init__(self, item, outputName):
    self.item = item
    self.outputName = outputName

  def summarize(self):
    result = self.item.summarize()
    if self.outputName is not None:
      result = result + " " + self.outputName
    return result

  def __str__(self):
    return self.summarize()

# attacks based on power and signal
class Laser(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "control"])

  def putProperties(self, properties):
    self.requiredPower = properties.get("requiredPower")
    self.damage = properties.get("damage")
    self.maxSignalPower = properties.get("maxSignalPower")
    self.maxPossibleTarget = properties.get("maxPossibleTarget")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    if power >= self.requiredPower:
      damage = self.damage
    else:
      damage = 0
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal / self.maxSignalPower)
    print("laser applying damage " + str(damage) + " at position " + str(targetIndex))
    competitor.applyEnemyDamage(targetIndex, damage)

  def clone(self):
    return Laser(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + str(self.damage)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("attacks items in the opposing robot")
    messages.append("requires at least " + str(self.requiredPower) + " energy in one turn and then deals " + str(self.damage) + " damage")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# disconnects nodes
class Cutter(Item):
  def __init__(self, properties):
    super().__init__(properties)

  def putProperties(self, properties):
    self.requiredPower = properties.get("requiredPower")
    self.maxSignalPower = properties.get("maxSignalPower")
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal / self.maxSignalPower)
    if power >= self.requiredPower:
      print("cutter cutting at position " + str(targetIndex))
      competitor.disconnectEnemy(targetIndex)
    else:
      if power > 0:
        print("cutter insufficient power: " + str(power) + " < " + str(self.requiredPower))

  def clone(self):
    return Cutter(self.properties)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("disconnects items in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# holds power and can provide it over time
class Battery(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()

  def putProperties(self, properties):
    self.charge = properties.get("maxCharge")
    self.dischargeRate = properties.get("dischargeRate")
    self.readyToDischarge = self.dischargeRate

  def act(self, competitor):
    super().act(competitor)
    self.readyToDischarge = min(self.charge, self.dischargeRate)

  def tryGetPower(self, requested, outputName):
    if requested < 0:
      return
    amount = min(requested, self.readyToDischarge)
    self.readyToDischarge -= amount
    self.charge -= amount
    return amount

  def clone(self):
    return Battery(self.properties)

  def summarize(self):
    return "Battery:" + str(self.charge)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append(" holds " + str(self.charge) + " charge and can give " + str(self.dischargeRate) + " per turn to other items")
    return messages

# just has lots of hitpoints
class Wall(Item):
  def __init__(self, properties):
    super().__init__(properties)

  def putProperties(self, properties):
    self.hitPoints = properties.get("hitPoints")

  def summarize(self):
    return "Wall:" + str(self.hitPoints)

  def clone(self):
    return Wall(self.properties)

# limits power flow
class Resistor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power"])

  def putProperties(self, properties):
    self.dischargeRate = properties.get("dischargeRate")

  def act(self, competitor):
    super().act(competitor)
    requestedAmount = self.dischargeRate - self.readyToDischarge
    receivedAmount = self.tryAcquirePower("power", requestedAmount)
    self.readyToDischarge += receivedAmount

  def tryGetPower(self, requested, outputName):
    if requested < 0:
      return 0
    amount = min(requested, self.readyToDischarge)
    self.readyToDischarge -= amount
    return amount

  def clone(self):
    return Resistor(self.properties)

  def summarize(self):
    return super().summarize() + "<" + str(self.dischargeRate)
  
  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("allows " + str(self.dischargeRate) + " power to pass through it per turn")
    return messages

# adds a constant to power flow
class Adder(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])

  def putProperties(self, properties):
    self.addition = properties.get("addition")
    self.maxInput = properties.get("maxInput")

  def act(self, competitor):
    super().act(competitor)
    signal = self.tryAcquirePower("signal", self.maxInput)
    power = self.tryAcquirePower("power", self.addition)
    self.readyToDischarge = power + signal
    print(self.summarize() + " signal " + str(signal) + " power " + str(power) + " output " + str(self.readyToDischarge))

  def tryGetPower(self, requested, outputName):
    if requested < 0:
      return 0
    amount = min(requested, self.readyToDischarge)
    self.readyToDischarge -= amount
    return amount

  def clone(self):
    return Adder(self.properties)

  def summarize(self):
    return super().summarize() + "+" + str(self.addition)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("consumes up to " + str(self.addition) + " input power plus up to " + str(self.maxInput) + " input signal and outputs the sum")
    return messages

# reads an input and gives up to that much power each time it is requested
class Splitter(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.signal = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])

  def putProperties(self, properties):
    self.maxInput = properties.get("maxInput")

  def act(self, competitor):
    super().act(competitor)
    self.signal = self.tryAcquirePower("signal", self.maxInput)

  def tryGetPower(self, requested, outputName):
    if requested <= 0:
      return 0
    power = self.tryAcquirePower("power", min(self.signal, requested))
    return power

  def clone(self):
    return Splitter(self.properties)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("reads an input and gives up to that much power each time any item requests it")
    return messages

# a joiner takes power from two inputs
class Joiner(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()
    self.declareInputs(["input1", "input2"])

  def putProperties(self, properties):
    return

  def tryGetPower(self, requested, outputName):
    if requested <= 0:
      return 0
    power = 0
    power += self.tryAcquirePower("input1", requested - power)
    power += self.tryAcquirePower("input2", requested - power)
    return power

  def clone(self):
    return Joiner({})

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("takes power from two inputs")
    return messages

# an If allows power through if the signal is above a threshold
class If(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()
    self.on = False
    self.declareInputs(["power", "signal"])

  def putProperties(self, properties):
    self.threshold = properties.get("threshold")

  def act(self, competitor):
    super().act(competitor)
    self.on = self.tryAcquirePower("signal", self.threshold) >= self.threshold

  def tryGetPower(self, requested, outputName):
    if self.on:
      return self.tryAcquirePower("power", requested)
    return 0

  def clone(self):
    return If(self.properties)

  def summarise(self):
    return super().summarize() + ">" + str(self.threshold)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("allows power through if the signal is above " + str(self.threshold))
    return messages

# a Capacitor stores energy
class Capacitor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.energy = 0
    self.declareOutputs(["power", "signal"])
    self.declareInputs(["power"])

  def putProperties(self, properties):
    self.maxEnergy = properties.get("maxEnergy")
    self.signalOutputFraction = properties.get("signalOutputFraction")

  def act(self, competitor):
    super().act(competitor)
    self.energy += self.tryAcquirePower("power", self.maxEnergy - self.energy)

  def tryGetPower(self, requested, outputName):
    if outputName == "signal":
      requested = self.energy * self.signalOutputFraction
    amount = min(requested, self.energy)
    self.energy -= amount
    return amount

  def clone(self):
    return Capacitor(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.energy) + "/" + str(self.maxEnergy)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("can store up to " + str(self.maxEnergy) + " energy and release it at any time")
    messages.append("can output " + str(self.signalOutputFraction) + " of the stored energy as an output signal")
    return messages

# a Shield defends against damage
class Shield(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "distance", "direction"])

  def putProperties(self, properties):
    self.defenseFraction = properties.get("defenseFraction")
    self.radius = properties.get("radius")
    self.requiredEnergy = properties.get("requiredPower")
    self.maxSignalPower = properties.get("maxSignalPower")
    self.maxPossibleDistance = properties.get("maxPossibleDistance")

  def act(self, competitor):
    super().act(competitor)
    energy = self.tryAcquirePower("power", self.requiredEnergy)
    distanceSignal = self.tryAcquirePower("distance", self.maxSignalPower)
    directionSignal = self.tryAcquirePower("direction", self.maxSignalPower)
    if energy >= self.requiredEnergy:
      ourPosition = competitor.network.getPosition(self)
      distance = int(self.maxPossibleDistance * distanceSignal / self.maxSignalPower)
      if directionSignal > 0:
        position = ourPosition - distance
      else:
        position = ourPosition + distance
      competitor.createShield(position, self.radius, self.defenseFraction)
      print("created shield " + str(self.defenseFraction) + " from positions " + str(position - self.radius) + " to " + str(position + self.radius))
    else:
      print("power " + str(energy) + " not enough to power " + self.summarize())

  def clone(self):
    return Shield(self.properties)

  def getDefenseText(self):
    return str(int(self.defenseFraction * 100)) + "%"

  def summarize(self):
    return super().summarize() + " " + self.getDefenseText() + " +/-" + str(self.radius)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    
    messages.append("defends items up to " + str(self.radius) + " space away from the target, decreasing damage received by " + self.getDefenseText())
    messages.append("requires " + str(self.requiredEnergy) + " power per turn to function")
    messages.append("targets itself by default")
    messages.append("can be aimed up to " + str(self.maxPossibleDistance) + " spaces away from itself by setting distance input power to " + str(self.maxSignalPower))
    messages.append("will aim to the left if the direction input power is nonzero")
    return messages

# senses power usage
class PowerUsageSensor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.reading = 0
    self.declareInputs(["power", "positionSignal"])
    self.declareOutput()

  def putProperties(self, properties):
    self.radius = properties.get("radius")
    self.requiredPower = properties.get("requiredPower")
    self.maxSignalPower = properties.get("maxSignalPower")
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.outputRatio = properties.get("outputRatio")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    positionSignal = self.tryAcquirePower("positionSignal", self.requiredPower)
    if power >= self.requiredPower:
      index = int(self.maxPossibleTarget * positionSignal / self.maxSignalPower)
      reading = 0
      lowIndex = index - self.radius
      highIndex = index + self.radius
      for i in range(lowIndex, highIndex + 1):
        reading += competitor.getEnemyPowerAcquired(i)
      self.reading = min(reading * self.outputRatio, power)
      print(self.summarize() + " reading enemy total power acquired from " + str(lowIndex) + " to " + str(highIndex) + ", outputting " + str(self.reading))
    else:
      if power > 0:
        print("power " + str(energy) + " not enough to power " + self.summarize())

  def tryGetPower(self, requested, outputName):
    amount = min(requested, self.reading)
    self.reading -= amount
    return amount

  def clone(self):
    return PowerUsageSensor(self.properties)

  def summarize(self):
    return super().summarize()

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Measures power usage with radius " + str(self.radius) + " from the target position in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# represents an attack
class Attack(object):
  def __init__(self):
    return

def act(self, target):
    return

class DamageAttack(Attack):
  def __init__(self, index, amount):
    super().__init__()
    self.index = index
    self.amount = amount

  def process(self, target):
    target.receiveDamage(self.index, self.amount)

class CutAttack(Attack):
  def __init__(self, index):
    super().__init__()
    self.index = index

  def process(self, target):
    target.disconnect(self.index)

# represents an entity that competes with other entities
class Competitor(object):
  def __init__(self, name, network):
    self.name = name
    self.network = network
    self.enemy = None
    self.incomingAttacks = []
    self.clearShields()

  def nodesAct(self):
    print(str(self.name) + "'s turn:")
    self.clearShields()
    for node in self.network.nodes:
      node.act(self)

  def getNumActiveNodes(self):
    return self.network.size()

  def getStatus(self):
    messages = []
    messages.append(self.name + ", " + str(self.network.size()) + " nodes:\n")
    for i in range(self.network.size()):
      if i != 0:
        messages.append(", ")
      node = self.network.nodes[i]
      messages.append(node.summarize())
    return "".join(messages)

  def clearShields(self):
    self.incomingDamageMultipliers = [1] * self.network.size()

  def addIncomingAttack(self, attack):
    self.incomingAttacks.append(attack)

  def processIncomingAttacks(self):
    for attack in self.incomingAttacks:
      attack.process(self)
    self.incomingAttacks = []
    self.removeBrokenNodes()

  def removeBrokenNodes(self):
    remainingNodeList = [node for node in self.network.nodes if node.hitPoints > 0]
    remainingNodeSet = set(remainingNodeList)
    for node in remainingNodeList:
      for linkType, link in node.inputsByName.copy().items():
        if link is not None:
          if link.item not in remainingNodeSet:
            node.inputsByName[linkType] = None
    self.network.nodes = remainingNodeList

  def applyEnemyDamage(self, nodeIndex, amount):
    self.enemy.addIncomingAttack(DamageAttack(nodeIndex, amount))

  def receiveDamage(self, nodeIndex, amount):
    if nodeIndex < 0:
      return # miss
    if nodeIndex >= self.network.size():
      return # miss
    node = self.network.nodes[nodeIndex]
    multiplier = self.incomingDamageMultipliers[nodeIndex]
    if multiplier != 1:
      result = amount * multiplier
      print("shields changed damage at " + str(nodeIndex) + " from " + str(amount) + " to " + str(result))
      amount = result
    node.receiveDamage(amount)

  def createShield(self, position, radius, defenseFraction):
    damageMultiplier = 1 - defenseFraction
    startIndex = max(0, position - radius)
    endIndex = min(len(self.incomingDamageMultipliers), position + radius + 1)
    for i in range(startIndex, endIndex):
      self.incomingDamageMultipliers[i] *= damageMultiplier

  def disconnectEnemy(self, nodeIndex):
    self.enemy.addIncomingAttack(CutAttack(nodeIndex))

  def disconnect(self, nodeIndex):
    if nodeIndex < 0:
      return # miss
    if nodeIndex >= self.network.size():
      return # miss
    node = self.network.nodes[nodeIndex]
    for linkType in node.inputsByName.keys():
      node.inputsByName[linkType] = None

  def getEnemyPowerAcquired(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].getPowerAcquiredLastTurn()

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

class Competition(object):
  def __init__(self, gamePlayers):
    if len(gamePlayers) != 2:
      raise Exception("len(gamePlayers) = " + str(len(gamePlayers)) + " is not supported, must be 2")
    self.competitors = []
    for player in gamePlayers:
      self.competitors.append(player.buildCompetitor())
    self.competitors[0].enemy = self.competitors[1]
    self.competitors[1].enemy = self.competitors[0]

  def run(self):
    maxNumRounds = 20
    for i in range(maxNumRounds):
      print("\nRound " + str(i) + "/" + str(maxNumRounds) + ": ////////////////////")
      for competitor in self.competitors:
        print(competitor.getStatus())
        print("")
      input("(Press Enter) --------------------")
      print("")
      for competitor in self.competitors:
        competitor.nodesAct()
      for competitor in self.competitors:
        competitor.processIncomingAttacks()
      for j in range(2):
        if self.competitors[j].getNumActiveNodes() < 1:
          print(self.competitors[1 - j].name + " wins because " + self.competitors[j].name + "'s network is empty")
          return (j > 0)
    for j in range(2):
      if self.competitors[j].getNumActiveNodes() < self.competitors[1 - j].getNumActiveNodes():
        print(self.competitors[1 - j].name + " wins because " + self.competitors[1 - j].name + "'s network is larger after " + str(maxNumRounds) + " rounds")
        return (j > 0)
    print("tie!")
    return None

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

# information about an item
class ItemData(object):
  def __init__(self, item, name, complexity, cost):
    self.item = item.clone()
    self.name = name
    self.complexity = complexity
    self.cost = cost

  def clone(self):
    return ItemData(self.item, self.name, self.complexity, self.cost)

# a collection of ItemData
class ItemDataFactory(object):
  def __init__(self):
    self.contents = []
    self.contentsByName = {}

  def add(self, item, complexity, baseCost):
    name = type(item).__name__
    self.addItemData(ItemData(item, name, complexity, baseCost))

  def addItemData(self, itemData):
    name = itemData.name
    if name in self.contentsByName:
      index = 2
      while (name + str(index)) in self.contentsByName:
        index += 1
      name = name + str(index)
    itemData.name = name
    self.contents.append(itemData)
    self.contentsByName[itemData.name] = itemData

  def cloneItemNamed(self, name):
    result = self.contentsByName.get(name)
    if result is None:
      raise Exception("'" + name + "' not found in " + str(list(self.contentsByName.keys())))
    return result.item.clone()

  def getAll(self):
    return self.contents[:]

  def cloneAndMutateRandomItem(self):
    index = random.randint(0, len(self.contents) - 1)
    mutated = self.mutateRandomly(self.contents[index], 0.1)
    self.addItemData(mutated)

  def mutateRandomly(self, itemData, maxFractionChange):
    result = itemData.clone()
    properties = dict(result.item.properties)
    for key, value in properties.items():
      fractionChange = random.uniform(-maxFractionChange, maxFractionChange)
      properties[key] = value * (1 + fractionChange)
    result.item.putProperties(properties)
    return result

  def parseItemDataList(self, jsonObjects):
    result = []
    for o in jsonObjects:
      result.append(self.parseItemData(o))
    return result

  def parseItemData(self, jsonObject):
    name = jsonObject["name"]
    item = self.cloneItemNamed(name)
    item.putProperties(jsonObject["properties"])
    complexity = jsonObject["complexity"]
    cost = jsonObject["cost"]
    itemData = ItemData(item, name, complexity, cost)
    return itemData

  def itemDataToDict(self, itemData):
    result = {}
    result["type"] = type(itemData.item).__name__
    result["name"] = itemData.name
    result["complexity"] = itemData.complexity
    result["cost"] = itemData.cost
    result["properties"] = itemData.item.properties
    return result

# a collection of predefined ItemData
class DefaultItemDataFactory(ItemDataFactory):
  def __init__(self):
    super().__init__()
    self.loadDefaults()

  def loadDefaults(self):
    self.contents = []
    self.add(Laser({"requiredPower": 1, "damage": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 1, 2)
    self.add(Cutter({"requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100}), 1, 2)
    self.add(Battery({"maxCharge": 100, "dischargeRate": 3}),1, 2)
    self.add(Wall({"hitPoints": 4}), 1, 1)
    self.add(Resistor({"dischargeRate": 0.01}), 2, 1)
    self.add(Adder({"addition": 0.01, "maxInput": 10}), 2, 1)
    self.add(Splitter({"maxInput": 1}), 2, 1)
    self.add(Joiner({}), 2, 1)
    self.add(If({"threshold": 0.05}), 2, 1)
    self.add(Capacitor({"maxEnergy": 10, "signalOutputFraction": 0.01}), 2, 1)
    self.add(Shield({"defenseFraction": 0.5, "radius": 1, "requiredPower": 4, "maxSignalPower": 1, "maxPossibleDistance": 100}), 2, 2)
    self.add(PowerUsageSensor({"radius": 1, "requiredPower": 1, "maxSignalPower": 1, "maxPossibleTarget": 100, "outputRatio": 0.01}), 3, 1)


# a collection of ItemData saved to a file
class FileItemDataFactory(ItemDataFactory):
  def __init__(self, defaultFactory, filepath):
    super().__init__()
    self.defaultFactory = defaultFactory
    self.filepath = filepath
    if os.path.isfile(filepath):
      self.loadFile()
    else:
      self.loadDefaults()
      self.saveFile()

  def loadFile(self):
    json = self.readFile()
    items = self.defaultFactory.parseItemDataList(json)
    for item in items:
      self.addItemData(item)

  def readFile(self):
    print("Loading item data from " + str(self.filepath))
    with open(self.filepath) as f:
      return json.load(f)

    return # not implemented yet

  def saveFile(self):
    text = self.serialize()
    with open(self.filepath, 'w') as f:
      f.write(text)

  def serialize(self):
    components = []
    for component in self.getAll():
      components.append(self.itemDataToDict(component))
    return json.dumps(components, indent = 2)

  def loadDefaults(self):
    for itemData in self.defaultFactory.getAll():
      self.addItemData(itemData)

itemDataFactory = FileItemDataFactory(DefaultItemDataFactory(), "./data/profile")
itemDataFactory.cloneAndMutateRandomItem()

def makePlayer():
  player = GamePlayer("Player")
  #battery1 = Battery()
  #laser1 = Laser()
  #laser1.addInput("power", battery1)
  #player.network.addItem(Wall())
  #player.network.addItem(battery1)
  #player.network.addItem(laser1)
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
