#!python

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
    self.items.append([Laser(), 1])
    self.items.append([Resistor(), 1])

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
    print(str(len(self.player.network.itemTemplates)) + " items in network")
    for item in self.player.network.itemTemplates:
      print("  " + item.describeLinks())
    print("")

  def process(self):
    print("")
    print("Customizing")
    while True:
      self.showStatus()
      menu = Menu()
      if len(self.player.items) > 0:
        menu.addChoice("Add all items to network", 0)
      if len(self.player.network.itemTemplates) > 0:
        menu.addChoice("Edit item", 1)
      menu.addChoice("Done", 2)
      choice = menu.chooseValue()
      print("")
      if choice == 0:
        self.player.network.itemTemplates += self.player.items
        self.player.items = []
        continue
      if choice == 1:
        self.chooseAndEditItem()
        continue
      return

  def chooseAndEditItem(self):
    self.editItem(self.chooseNetworkItem("Edit which item?"))

  def chooseNetworkItem(self, description):
    print(description)
    menu = Menu()
    for item in self.player.network.itemTemplates:
      menu.addChoice(item.describeLinks(), item)
    return menu.chooseValue()

  def editItem(self, item):
    menu = Menu()
    menu.addChoice("Remove", "Remove")
    for linkName in item.inputsByName.keys():
      menu.addChoice("Set input " + linkName, linkName)
    choice = menu.chooseValue()
    if choice == "Remove":
      self.player.network.itemTemplates.remove(item)
      self.player.items.append(item)
      return
    linkName = choice
    dependency = self.chooseNetworkItem("Choose " + linkName + " for " + item.summarize())
    item.inputsByName[linkName] = dependency

class MarketStoryNode(MenuStoryNode):
  def __init__(self, player):
    super().__init__("Welcome to the market")
    shop = ShopStoryNode(player)
    shop.setNext(self)
    tester = TestingStoryNode(player)
    tester.setNext(self)
    customizer = CustomizationStoryNode(player)
    customizer.setNext(self)
    self.addChoice("shop", shop)
    self.addChoice("test", tester)
    self.addChoice("customize", customizer)

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
class CompetitorItem(object):
  def __init__(self):
    self.hitPoints = 1
    self.inputsByName = {}

  def addInput(self, linkType, otherItem):
    self.inputsByName[linkType] = otherItem

  def receiveDamage(self, amount):
    self.hitPoints -= amount

  def declareInputs(self, linkTypes):
    for linkType in linkTypes:
      self.inputsByName[linkType] = None

  # tries to get power from the given link
  def tryAcquirePower(self, linkType, amount):
    if linkType not in self.inputsByName.keys():
      raise Exception("link type " + str(linkType) + " not declared in " + str(self) + ". All declared links: " + str(self.inputsByName))
    link = self.inputsByName.get(linkType)
    if link == None:
      return 0
    return link.tryGetPower(amount)

  # tries to get power from the current node
  def tryGetPower(self, amount):
    return 0

  def act(self, player):
    return

  def clone(self):
    raise Exception("clone is not implemented in " + str(self))

  def summarize(self):
    return type(self).__name__

  def describeLinks(self):
    messages = [self.summarize()]
    for name, value in self.inputsByName.items():
      if value is not None:
        messages.append(name + ": " + value.summarize())
      else:
        messages.append(name + ": None")
    return ", ".join(messages)

# attacks based on power and signal
class Laser(CompetitorItem):
  def __init__(self):
    super().__init__()
    self.maxAttackPower = 1
    self.damagePerPower = 1
    self.maxSignalPower = 1
    self.numPossibleTargets = 100
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    power = self.tryAcquirePower("power", self.maxAttackPower)
    damage = power * self.damagePerPower
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.numPossibleTargets * signal / self.maxSignalPower)
    print("laser applying damage " + str(damage) + " at position " + str(targetIndex))
    competitor.applyEnemyDamage(damage, targetIndex)

  def clone(self):
    return Laser()

# holds power and can provide it over time
class Battery(CompetitorItem):
  def __init__(self):
    super().__init__()
    self.charge = 100
    self.dischargeRate = 3
    self.readyToDischarge = self.dischargeRate

  def act(self, competitor):
    self.readyToDischarge = min(self.charge, self.dischargeRate)

  def tryGetPower(self, requested):
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
class Wall(CompetitorItem):
  def __init__(self):
    super().__init__()
    self.hitPoints = 4

  def summarize(self):
    return "Wall:" + str(self.hitPoints)

  def clone(self):
    return Wall()

# limits power flow
class Resistor(CompetitorItem):
  def __init__(self):
    super().__init__()
    self.dischargeRate = 0.01
    self.readyToDischarge = 0
    self.declareInputs(["input"])

  def act(self, competitor):
    requestedAmount = self.dischargeRate - self.readyToDischarge
    receivedAmount = self.tryAcquirePower("input", requestedAmount)
    self.readyToDischarge += receivedAmount

  def tryGetPower(self, requested):
    if requested < 0:
      return
    amount = min(requested, self.readyToDischarge)
    self.readyToDischarge -= amount
    return amount

  def clone(self):
    return Resistor()

# represents an entity that competes with other entities
class Competitor(object):
  def __init__(self, name, network):
    self.name = name
    self.network = network
    self.enemy = None

  def nodesAct(self):
    print(str(self.name) + "'s turn:")
    for node in self.network:
      node.act(self)

  def active(self):
    result = len(self.network) > 0
    return result

  def getStatus(self):
    messages = []
    messages.append(self.name + ", " + str(len(self.network)) + " nodes:\n")
    for i in range(len(self.network)):
      if i != 0:
        messages.append(", ")
      node = self.network[i]
      messages.append(node.summarize())
    return "".join(messages)

  def removeBrokenNodes(self):
    remainingNodeList = [node for node in self.network if node.hitPoints > 0]
    remainingNodeSet = set(remainingNodeList)
    for node in remainingNodeList:
      for linkType, linkNode in node.inputsByName.copy().items():
        if linkNode not in remainingNodeSet:
          node.inputsByName[linkType] = None
    self.network = remainingNodeList

  def applyEnemyDamage(self, amount, nodeIndex):
    self.enemy.receiveDamage(amount, nodeIndex)

  def receiveDamage(self, amount, nodeIndex):
    if nodeIndex < 0:
      return # miss
    if nodeIndex >= len(self.network):
      return # miss
    node = self.network[nodeIndex]
    node.receiveDamage(amount)

# represents a template for an entity that competes with other entities
class CompetitorTemplate(object):
  def __init__(self):
    self.itemTemplates = []

  def addItem(self, template):
    self.itemTemplates.append(template)

  def build(self, name):
    # create nodes and identify indices
    builtNodes = []
    templateIndices = {}
    for i in range(len(self.itemTemplates)):
      template = self.itemTemplates[i]
      builtNodes.append(template.clone())
      templateIndices[template] = i
    # add links
    for i in range(len(self.itemTemplates)):
      template = self.itemTemplates[i]
      item = builtNodes[i]
      for linkType, otherTemplate in template.inputsByName.items():
        if otherTemplate is not None:
          otherIndex = templateIndices[otherTemplate]
          otherItem = builtNodes[otherIndex]
          item.addInput(linkType, otherItem)
    return Competitor(name, builtNodes)

# represents the player
class GamePlayer(object):
  def __init__(self, name):
    self.name = name
    self.money = 100
    self.items = []
    self.network = CompetitorTemplate()

  def addItem(self, item):
    self.items.append(item)

  def buildCompetitor(self):
    return self.network.build(self.name)

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
    for i in range(20):
      print("\nRound " + str(i) + ": ////////////////////")
      for competitor in self.competitors:
        print(competitor.getStatus())
        print("")
      input("(Press Enter) --------------------")
      print("")
      for competitor in self.competitors:
        competitor.nodesAct()
      for competitor in self.competitors:
        competitor.removeBrokenNodes()
      if not self.competitors[1].active():
        return True # win
      if not self.competitors[0].active():
        return False # lose
    return None # tie

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
  player.network.addItem(battery1)
  player.network.addItem(laser1)
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
