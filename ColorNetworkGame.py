#!python

class StoryNode(object):
  def __init__(self):
    return

  def getNext(self):
    return None

class ChoiceMenu(StoryNode):
  def __init__(self, text):
    super().__init__()
    self.text = text
    self.choices = []

  def getNext(self):
    print(self.text)
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
        print("Choose a number <= " + str(len(self.choices)))
        continue
      choice = self.choices[number]
      return choice[1]

  def addChoice(self, text, newMenu):
    self.choices.append((text, newMenu))

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

# a MessageMenu shows a message and goes to the next node
class MessageMenu(SimpleStoryNode):
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
    if result is None:
      result = True # count ties as successes for now
    if result:
      return self.successNode
    return self.failureNode

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

  # tries to get power from the given link
  def tryAcquirePower(self, linkType, amount):
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
    return

  def summarize(self):
    return type(self).__name__

# attacks based on power and signal
class Laser(CompetitorItem):
  def __init__(self):
    super().__init__()
    self.maxAttackPower = 1
    self.damagePerPower = 1
    self.maxSignalPower = 1
    self.numPossibleTargets = 100

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
          del node.inputsByName[linkType]
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
        otherIndex = templateIndices[otherTemplate]
        otherItem = builtNodes[otherIndex]
        item.addInput(linkType, otherItem)
    return Competitor(name, builtNodes)

# represents the player
class GamePlayer(object):
  def __init__(self, name):
    self.name = name
    self.money = 0
    self.items = []
    self.network = CompetitorTemplate()

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
  player.network.addItem(battery1)
  player.network.addItem(laser1)
  return player

def makeOpponent():
  player = GamePlayer("Opponent")
  for i in range(4):
    player.network.addItem(Battery())
  return player

def makeStory():
  gamePlayer = makePlayer()
  welcome = MessageMenu("Welcome to ColorNetwork!")

  opponent1 = makeOpponent()
  competition1 = CompetitionStoryNode(gamePlayer, opponent1)
  welcome.setNext(competition1)
 
  successNode = MessageMenu("Success!")
  failureNode = MessageMenu("Failure")
  competition1.setSuccessNode(successNode)
  competition1.setFailureNode(failureNode)

  return StoryNodeRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
