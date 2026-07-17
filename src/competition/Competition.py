#!python

from items.Items import *
from persistence.Persistence import *
from interface.Interface import *

import json, os, shutil, textwrap

# represents an attack
class Attack(object):
  def __init__(self):
    return

  def act(self, target):
    return

  def afterAttacks(self, target):
    return

  def __str__(self):
    return type(self).__name__

class DamageAttack(Attack):
  def __init__(self, index, amount):
    super().__init__()
    self.index = index
    self.amount = amount

  def process(self, target):
    target.receiveDamage(self.index, self.amount)

class CutAttack(Attack):
  def __init__(self, index, numConnectionsToRemove):
    super().__init__()
    self.index = index
    self.numConnectionsToRemove = numConnectionsToRemove

  def process(self, target):
    target.disconnectCrossing(self.index, self.numConnectionsToRemove)

class PowerDrainAttack(Attack):
  def __init__(self, index, amount):
    super().__init__()
    self.index = index
    self.remaining = amount
    self.totalDrained = Energy()

  def process(self, target):
    target.drainPower(self.index, self)

  def getRemaining(self):
    return self.remaining

  def done(self):
    return self.totalDrained.getTotal() >= self.remaining

  def drained(self, energy):
    self.totalDrained = self.totalDrained.plus(energy)

class RamAttack(Attack):
  def __init__(self, damage):
    super().__init__()
    self.damage = damage

  def process(self, target):
    target.receiveRamAttack(self.damage)

class FlipAttack(Attack):
  def __init__(self, strength):
    super().__init__()
    self.strength = strength

  def process(self, target):
    target.receiveFlipAttack(self.strength)

class InfectAttack(Attack):
  def __init__(self, index, amount):
    super().__init__()
    self.index = index
    self.amount = amount
    self.spreadToNode = None

  def process(self, target):
    itemIndex = self.index
    if itemIndex < 0:
      return # miss
    network = target.network
    if itemIndex >= network.size():
      return # miss
    targetItem = network.nodes[itemIndex]
    hadHitpoints = targetItem.hitPoints > 0
    target.receiveDamage(itemIndex, self.amount)
    stillHasHitpoints = targetItem.hitPoints > 0
    self.spreadToNode = None
    if hadHitpoints:
      if stillHasHitpoints:
        print(str(self) + " not spreading because the target is still alive")
      else:
        print(str(self) + " destroyed its target")
        spreadToIndex = itemIndex + 1
        if spreadToIndex >= len(network.nodes):
          print(str(self) + " not spreading because of reaching the end of the network")
        else:
          self.spreadToNode = network.nodes[spreadToIndex]
    else:
      print(str(self) + " not spreading because target was already destroyed")

  def afterAttacks(self, target):
    if self.spreadToNode is None:
      return # previously computed unable to spread
    index = target.network.tryGetPosition(self.spreadToNode)
    if index is None:
      print(str(self) + " not spreading because " + self.spreadToNode.summarize() + " no longer in network")
      return
    print(str(self) + " spreading to " + self.spreadToNode.summarize())
    target.addIncomingAttack(InfectAttack(index, self.amount))

class AcidAttack(Attack):
  def __init__(self, index, amount):
    super().__init__()
    self.index = index
    self.amount = amount
    self.spreadToNode = None

  def process(self, target):
    itemIndex = self.index
    if itemIndex < 0:
      return # miss
    network = target.network
    if itemIndex >= network.size():
      return # miss
    targetItem = network.nodes[itemIndex]
    target.receiveDamage(itemIndex, self.amount)
    print(str(self) + " dealing " + str(self.amount) + " damage to " + targetItem.summarize())
    stillHasHitpoints = targetItem.hitPoints > 0
    self.spreadToNode = None
    if stillHasHitpoints:
      self.spreadToNode = network.nodes[itemIndex]

  def afterAttacks(self, target):
    if self.spreadToNode is None:
      return # previously computed unable to spread
    index = target.network.tryGetPosition(self.spreadToNode)
    if index is None:
      return # item no longer present
    print(str(self) + " remaining on " + self.spreadToNode.summarize() + "(" + str(self.spreadToNode.hitPoints) + " hitpoints)")
    target.addIncomingAttack(AcidAttack(index, self.amount))

# represents an entity that competes with other entities
class Competitor(object):
  def __init__(self, name, network):
    self.name = name
    self.network = network
    self.enemy = None
    self.incomingAttacks = []
    self.processedAttacks = []
    self.clearShields()
    self.active = True

  def resetForNewTurn(self):
    self.clearShields()
    self.resetPowerMeters()

  def nodesAct(self):
    print(str(self.name) + "'s turn:")
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
      nodeText = node.summarize()
      if node.hitPoints <= 0: # display an empty space for destroyed items
        nodeText = "X" * inputUtils.getLength(nodeText)
      messages.append(nodeText)
    return "".join(messages)

  def clearShields(self):
    self.incomingDamageMultipliers = [1] * self.network.size()

  def resetPowerMeters(self):
    for item in self.network.nodes:
      item.powerConsumedLastTurn = item.powerConsumedThisTurn
      item.powerConsumedThisTurn = 0
      item.powerGivenLastTurn = item.powerGivenThisTurn
      item.powerGivenThisTurn = 0

  def addIncomingAttack(self, attack):
    self.incomingAttacks.append(attack)

  def addOutgoingAttack(self, attack):
    if self.active:
      self.enemy.addIncomingAttack(attack)
    else:
      print(str(self) + " unable to attack")

  def processIncomingAttacks(self):
    print("Processing " + str(len(self.incomingAttacks)) + " attacks incoming to " + str(self))
    attacksToProcess = self.incomingAttacks
    self.incomingAttacks = []
    for attack in attacksToProcess:
      attack.process(self)
    self.processedAttacks = attacksToProcess

  def afterAttacks(self):
    print("Cleaning up " + str(self) + " after attacks")
    self.removeBrokenNodes()
    for attack in self.processedAttacks:
      attack.afterAttacks(self)

  def removeBrokenNodes(self):
    remainingNodeList = []
    for node in self.network.nodes:
      if node.hitPoints > 0:
        remainingNodeList.append(node)
      else:
        print(str(self) + "'s " + node.describeLinks(self.network) + " is destroyed")
    remainingNodeSet = set(remainingNodeList)
    for node in remainingNodeList:
      for linkType, link in node.inputsByName.copy().items():
        if link is not None:
          if link.item not in remainingNodeSet:
            node.inputsByName[linkType] = None
    self.network.setItems(remainingNodeList)

  def applyEnemyDamage(self, nodeIndex, amount):
    self.addOutgoingAttack(DamageAttack(nodeIndex, amount))

  def addRamAttack(self, amount):
    self.addOutgoingAttack(RamAttack(amount))
    if self.active:
      self.addIncomingAttack(RamAttack(amount))

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

  def receiveRamAttack(self, amount):
    index = 0
    network = self.network
    nodes = network.nodes
    while index < len(nodes) and amount > 0:
      node = nodes[index]
      if node.hitPoints > 0:
        amountHere = min(node.hitPoints, amount)
        print("Ram attack dealing " + str(amountHere) + " damage at position " + str(index) + " to node " + node.describeLinks(network))
        self.receiveDamage(index, amountHere)
        amount -= amountHere
      else:
        index += 1

  def launchFlipAttack(self, strength):
    self.addOutgoingAttack(FlipAttack(strength))

  def receiveFlipAttack(self, strength):
    totalHitpoints = 0
    for node in self.network.nodes:
      if node.hitPoints > 0:
        totalHitpoints += node.hitPoints
    if totalHitpoints <= strength:
      print(str(self) + " flipped: total hitpoints " + str(totalHitpoints) + " <= strength " + str(strength))
      self.active = False
    else:
      print(str(self) + " not flipped: total hitpoints " + str(totalHitpoints) + " > strength " + str(strength))

  def launchInfectAttack(self, nodeIndex, amount):
    self.addOutgoingAttack(InfectAttack(nodeIndex, amount))

  def launchAcidAttack(self, nodeIndex, amount):
    self.addOutgoingAttack(AcidAttack(nodeIndex, amount))

  def createShield(self, position, radius, defenseFraction):
    damageMultiplier = 1 - defenseFraction
    startIndex = max(0, position - radius)
    endIndex = min(len(self.incomingDamageMultipliers), position + radius + 1)
    for i in range(startIndex, endIndex):
      self.incomingDamageMultipliers[i] *= damageMultiplier

  def disconnectEnemyConnections(self, nodeIndex, maxNumCuts):
    self.addOutgoingAttack(CutAttack(nodeIndex, maxNumCuts))

  def disconnectCrossing(self, nodeIndex, disconnectCount):
    if nodeIndex < 0:
      print("No node at position " + str(nodeIndex))
      return # miss
    if nodeIndex >= self.network.size():
      print("No node at position " + str(nodeIndex))
      return # miss
    if disconnectCount < 1:
      return # nothing to do
    print("Disconnecting up to " + str(disconnectCount) + " connections crossing position " + str(nodeIndex))
    network = self.network
    nodes = network.nodes
    numDisconnected = 0
    for i in range(len(nodes)):
      node = nodes[i]
      for linkType in node.inputsByName.keys():
        connectedOutput = node.inputsByName[linkType]
        if connectedOutput is not None:
          linkedNode = connectedOutput.item
          linkedPosition = network.tryGetPosition(linkedNode)
          if (i < nodeIndex) != (linkedPosition < nodeIndex):
            print("Disconnecting input " + linkType + " from " + node.summarize() + " pos " + str(i) + " (source pos " + str(linkedPosition) + ")")
            node.inputsByName[linkType] = None
            numDisconnected += 1
            if numDisconnected >= disconnectCount:
              print("Disconnected " + str(numDisconnected) + "/" + str(disconnectCount) + " connections")
              return

  def disconnectOutputs(self, nodeIndex):
    if nodeIndex < 0:
      print("No node at position " + str(nodeIndex))
      return # miss
    network = self.network
    if nodeIndex >= network.size():
      print("No node at position " + str(nodeIndex))
      return # miss
    sourceNode = network.nodes[nodeIndex]
    if not sourceNode.declaresOutputs():
      print("Node at position " + str(nodeIndex) + " is " + sourceNode.summarize() + " which has no outputs")
      return
    print("Disconnecting outputs at position " + str(nodeIndex) + ": node " + sourceNode.summarize())
    numDisconnected = 0
    for i in range(network.size()):
      destNode = network.nodes[i] # TODO: make this more efficient
      for linkType, link in destNode.inputsByName.items():
        if link is not None and link.item == sourceNode:
          print("Disconnecting input " + linkType + " for " + destNode.summarize())
          destNode.inputsByName[linkType] = None
          numDisconnected += 1
    if numDisconnected < 1:
      print("No outputs disconnected for " + sourceNode.summarize())

  def getEnemyPowerConsumed(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].getPowerConsumedLastTurn()

  def getEnemyPowerGiven(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].getPowerGivenLastTurn()

  def getEnemyHitpoints(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].hitPoints

  def drainEnemyPower(self, nodeIndex, amount):
    if nodeIndex < 0:
      return
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    self.addOutgoingAttack(PowerDrainAttack(nodeIndex, inputAmount, outputAmount))

  def drainPower(self, nodeIndex, effect):
    self.network.nodes[nodeIndex].drainPower(effect)

  def __str__(self):
    return self.name

class Competition(object):
  def __init__(self, gamePlayers):
    if len(gamePlayers) != 2:
      raise Exception("len(gamePlayers) = " + str(len(gamePlayers)) + " is not supported, must be 2")
    self.competitors = []
    for player in gamePlayers:
      self.competitors.append(player.buildCompetitor())
    self.competitors[0].enemy = self.competitors[1]
    self.competitors[1].enemy = self.competitors[0]

  def showCompetitorsStatus(self):
    for competitor in self.competitors:
      print(competitor.getStatus())
      print("")

  def run(self):
    maxNumRounds = 20
    for i in range(maxNumRounds):
      print("\nRound " + str(i) + "/" + str(maxNumRounds) + ": ////////////////////")
      self.showCompetitorsStatus()
      inputUtils.pause("(Press Enter) --------------------")
      print("")
      for competitor in self.competitors:
        competitor.resetForNewTurn()
      for competitor in self.competitors:
        competitor.nodesAct()
      for competitor in self.competitors:
        competitor.processIncomingAttacks()
      self.showCompetitorsStatus()
      for competitor in self.competitors:
        competitor.afterAttacks()
      for j in range(2):
        if self.competitors[j].getNumActiveNodes() < 1:
          if self.competitors[1 - j].getNumActiveNodes() < 1:
            print("tie!")
            return None
          print(self.competitors[1 - j].name + " wins because " + self.competitors[j].name + "'s network is empty")
          return (j > 0)
    for j in range(2):
      if self.competitors[j].getNumActiveNodes() < self.competitors[1 - j].getNumActiveNodes():
        print(self.competitors[1 - j].name + " wins because " + self.competitors[1 - j].name + "'s network is larger after " + str(maxNumRounds) + " rounds")
        return (j > 0)
    print("tie!")
    return None
