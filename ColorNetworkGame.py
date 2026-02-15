#!python

import textwrap

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
      print(str(i) + ": " + option)
    choiceText = ""
    while True:
      choiceText = input("")
      number = 0
      if len(self.choices) <= 1:
        return 0 # there's only one choice so we return it
      try:
        number = int(choiceText)
      except Exception as e:
        print("Choose a number!")
        continue
      if number < 0:
        print("Choose a number >= 0")
        continue
      if number >= len(self.choices):
        print("Choose a number <= " + str(len(self.choices) - 1))
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
      for query, response in currentNode.children.items():
        menu.addChoice(query, response)
      menu.addChoice("Back", currentNode.parent)
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
class CompetitionStoryNode(StoryNode):
  def __init__(self, player, opponent):
    super().__init__()
    self.player = player
    self.opponent = opponent
    self.successNode = None
    self.failureNode = None

  def setSuccessNode(self, successNode):
    self.successNode = successNode

  def setFailureNode(self, failureNode):
    self.failureNode = failureNode

  def getNext(self):
    print("You enter a competition with " + str(self.opponent.name))
    competition = Competition([self.player, self.opponent])
    result = competition.run()
    print("")
    if result is None:
      print("Tie!\n")
      return self.successNode # count ties as successes for now
    if result:
      print("Success! You defeated " + str(self.opponent.name) + "\n")
      return self.successNode
    print("Failure\n")
    return self.failureNode

class ShopStoryNode(SimpleStoryNode):
  def __init__(self, player):
    super().__init__()
    self.player = player
    self.items = []
    self.items.append([Wall(), 1])
    self.items.append([Battery(), 1])
    self.items.append([Battery(), 1])
    self.items.append([Laser(), 1])
    self.items.append([Cutter(), 1])
    self.items.append([Resistor(), 1])
    self.items.append([Adder(), 1])
    self.items.append([Splitter(), 1])
    self.items.append([Joiner(), 1])
    self.items.append([If(), 1])
    self.items.append([Capacitor(), 1])
    self.items.append([Shield(), 1])

  def process(self):
    while True:
      print("")
      print("Welcome to the shop! You have " + str(self.player.money) + " money")
      menu = Menu()
      menu.addChoice("Bye!", -1)
      for i in range(len(self.items)):
        item = self.items[i][0]
        cost = self.items[i][1]
        menu.addChoice(item.summarize() + ": cost = " + str(cost), i)
      choice = menu.chooseValue()
      if choice == -1:
        print("Bye!")
        return # done
      itemIndex = choice
      cost = self.items[itemIndex][1]
      if cost > self.player.money:
        print("Not enough money: " + str(player.money) + " < " + str(cost))
        continue
      item = self.items[itemIndex][0]
      print("Enjoy your " + item.summarize() + "!")
      self.player.addItem(item)
      self.player.money -= cost
      del self.items[itemIndex]

class TestingStoryNode(CompetitionStoryNode):
  def __init__(self, player):
    super().__init__(player, makeEasyOpponent())
    self.nextNode = None

  def setNext(self, nextNode):
    self.nextNode = nextNode

  def getNext(self):
    super().getNext()
    return self.nextNode

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
      if len(self.player.items) > 0:
        menu.addChoice("Add all items to network", -1)
      menu.addChoice("Done", -2)
      network = self.player.network
      for i in range(network.size()):
        item = network.nodes[i]
        index = network.getPosition(item)
        menu.addChoice("Edit #" + str(index) + " " + item.describeLinks(), i)
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
    self.addChoice("test", tester)
    self.addChoice("customize", customizer)
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

# represents an object that a Competitor can use
class Item(object):
  def __init__(self):
    self.hitPoints = 1
    self.inputsByName = {}
    self.outputNames = []
    self.acquiringPower = False

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
    return result

  # tries to get power from the current node
  def tryGetPower(self, amount, outputName):
    return 0

  def act(self, player):
    return

  def clone(self):
    raise Exception("clone is not implemented in " + str(self))

  def summarize(self):
    return type(self).__name__

  def formatHelp(self):
    messages = [self.summarize() + ":\n"]
    messages.append(" has " + str(self.hitPoints) + " hit points\n")
    if len(self.inputsByName) > 0:
      messages.append(" has " + str(len(self.inputsByName)) + " ports for receiving power:\n")
      for key, value in self.inputsByName.items():
        messages.append("  " + str(key) + " (connected to " + str(value) + ")\n")
    if len(self.outputNames) > 0:
      messages.append(" has " + str(len(self.outputNames)) + " outputs")
      if len(self.outputNames) > 1:
        messages.append(": ")
        messages.append(str(self.outputNames))
      messages.append("\n")
    return "".join(messages)

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

# attacks based on power and signal
class Laser(Item):
  def __init__(self):
    super().__init__()
    self.requiredPower = 1
    self.damage = 1
    self.maxSignalPower = 1
    self.numPossibleTargets = 100
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    power = self.tryAcquirePower("power", self.requiredPower)
    if power >= self.requiredPower:
      damage = self.damage
    else:
      damage = 0
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.numPossibleTargets * signal / self.maxSignalPower)
    print("laser applying damage " + str(damage) + " at position " + str(targetIndex))
    competitor.applyEnemyDamage(targetIndex, damage)

  def clone(self):
    return Laser()

# disconnects nodes
class Cutter(Item):
  def __init__(self):
    super().__init__()
    self.requiredPower = 1
    self.maxSignalPower = 1
    self.numPossibleTargets = 100
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    power = self.tryAcquirePower("power", self.requiredPower)
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.numPossibleTargets * signal / self.maxSignalPower)
    if power >= self.requiredPower:
      print("cutter cutting at position " + str(targetIndex))
      competitor.disconnectEnemy(targetIndex)
    else:
      if power > 0:
        print("cutter insufficient power: " + str(power) + " < " + str(self.requiredPower))

  def clone(self):
    return Cutter()

# holds power and can provide it over time
class Battery(Item):
  def __init__(self):
    super().__init__()
    self.charge = 100
    self.dischargeRate = 3
    self.declareOutput()
    self.readyToDischarge = self.dischargeRate

  def act(self, competitor):
    self.readyToDischarge = min(self.charge, self.dischargeRate)

  def tryGetPower(self, requested, outputName):
    if requested < 0:
      return
    amount = min(requested, self.readyToDischarge)
    self.readyToDischarge -= amount
    self.charge -= amount
    return amount

  def clone(self):
    return Battery()

  def summarize(self):
    return "Battery:" + str(self.charge)

# just has lots of hitpoints
class Wall(Item):
  def __init__(self):
    super().__init__()
    self.hitPoints = 4

  def summarize(self):
    return "Wall:" + str(self.hitPoints)

  def clone(self):
    return Wall()

# limits power flow
class Resistor(Item):
  def __init__(self):
    super().__init__()
    self.dischargeRate = 1
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power"])

  def act(self, competitor):
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
    return Resistor()

  def summarize(self):
    return super().summarize() + "<" + str(self.dischargeRate)

# adds a constant to power flow
class Adder(Item):
  def __init__(self):
    super().__init__()
    self.addition = 0.01
    self.maxInput = 1
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])

  def act(self, competitor):
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
    return Adder()

  def summarize(self):
    return super().summarize() + "+" + str(self.addition)

# reads an input and gives up to that much power each time it is requested
class Splitter(Item):
  def __init__(self):
    super().__init__()
    self.maxInput = 1
    self.signal = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])

  def act(self, competitor):
    self.signal = self.tryAcquirePower("signal", self.maxInput)

  def tryGetPower(self, requested, outputName):
    if requested <= 0:
      return 0
    power = self.tryAcquirePower("power", min(self.signal, requested))
    return power

  def clone(self):
    return Splitter()

# a joiner takes power from two inputs
class Joiner(Item):
  def __init__(self):
    super().__init__()
    self.declareOutput()
    self.declareInputs(["input1", "input2"])

  def tryGetPower(self, requested, outputName):
    if requested <= 0:
      return 0
    power = 0
    power += self.tryAcquirePower("input1", requested - power)
    power += self.tryAcquirePower("input2", requested - power)
    return power

  def clone(self):
    return Joiner()

# an If allows power through if the signal is above a threshold
class If(Item):
  def __init__(self):
    super().__init__()
    self.threshold = 0.05
    self.declareOutput()
    self.on = False
    self.declareInputs(["power", "signal"])

  def act(self, competitor):
    self.on = self.tryAcquirePower("signal", self.threshold) >= self.threshold

  def tryGetPower(self, requested, outputName):
    if self.on:
      return self.tryAcquirePower("power", requested)
    return 0

  def clone(self):
    return If()

# a Capacitor stores energy
class Capacitor(Item):
  def __init__(self):
    super().__init__()
    self.energy = 0
    self.maxEnergy = 10
    self.signalOutputFraction = 0.01
    self.declareOutputs(["power", "signal"])
    self.declareInputs(["power"])

  def act(self, competitor):
    self.energy += self.tryAcquirePower("power", self.maxEnergy - self.energy)

  def tryGetPower(self, requested, outputName):
    if outputName == "signal":
      requested = self.energy * self.signalOutputFraction
    amount = min(requested, self.energy)
    self.energy -= amount
    return amount

  def clone(self):
    return Capacitor()

  def summarize(self):
    return super().summarize() + " " + str(self.energy) + "/" + str(self.maxEnergy)

# a Shield defends against damage
class Shield(Item):
  def __init__(self):
    super().__init__()
    self.defenseFraction = 0.5
    self.radius = 1
    self.requiredEnergy = 3
    self.maxSignalPower = 1
    self.maxPossibleDistance = 100
    self.declareInputs(["power", "distance", "direction"])

  def act(self, competitor):
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
    return Shield()

  def summarize(self):
    defenseText = str(int(self.defenseFraction * 100)) + "%"
    return super().summarize() + " " + defenseText + " +/-" + str(self.radius)

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

def makePlayer():
  player = GamePlayer("Player")
  battery1 = Battery()
  laser1 = Laser()
  laser1.addInput("power", battery1)
  #player.network.addItem(Wall())
  #player.network.addItem(battery1)
  #player.network.addItem(laser1)
  return player

def makeEasyOpponent():
  player = GamePlayer("Test Opponent")
  battery1 = Battery()
  laser1 = Laser()
  laser1.addInput("power", battery1)
  player.network.addItem(Wall())
  player.network.addItem(laser1)
  player.network.addItem(battery1)
  return player

def makeStory():
  gamePlayer = makePlayer()
  welcome = MessageStoryNode("Welcome to ColorNetwork!")

  shop = MarketStoryNode(gamePlayer)
  welcome.setNext(shop)

  opponent1 = makeEasyOpponent()
  competition1 = CompetitionStoryNode(gamePlayer, opponent1)
  shop.setNext(competition1)
 
  successNode = MessageStoryNode("You Win!")
  failureNode = MessageStoryNode("Game Over")
  competition1.setSuccessNode(successNode)
  competition1.setFailureNode(failureNode)

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
