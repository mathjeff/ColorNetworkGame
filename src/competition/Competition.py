#!python

from items.Items import *
from persistence.Persistence import *

import json, os, random, shutil, textwrap

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
  def __init__(self, index, disconnectInputs, disconnectOutputs):
    super().__init__()
    self.index = index
    self.disconnectInputs = disconnectInputs
    self.disconnectOutputs = disconnectOutputs

  def process(self, target):
    if self.disconnectInputs:
      target.disconnectInputs(self.index)
    if self.disconnectOutputs:
      target.disconnectOutputs(self.index)

class PowerDrainAttack(Attack):
  def __init__(self, index, inputAmount, outputAmount):
    super().__init__()
    self.index = index
    self.inputAmount = inputAmount
    self.outputAmount = outputAmount

  def process(self, target):
    target.drainInputPower(self.index, self.inputAmount)
    target.drainOutputPower(self.index, self.outputAmount)

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

# represents an entity that competes with other entities
class Competitor(object):
  def __init__(self, name, network):
    self.name = name
    self.network = network
    self.enemy = None
    self.incomingAttacks = []
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
      messages.append(node.summarize())
    return "".join(messages)

  def clearShields(self):
    self.incomingDamageMultipliers = [1] * self.network.size()

  def resetPowerMeters(self):
    for item in self.network.nodes:
      item.powerAcquiredLastTurn = item.powerAcquiredThisTurn
      item.powerAcquiredThisTurn = 0

  def addIncomingAttack(self, attack):
    self.incomingAttacks.append(attack)

  def addOutgoingAttack(self, attack):
    if self.active:
      self.enemy.addIncomingAttack(attack)
    else:
      print(str(self) + " unable to attack")

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

  def createShield(self, position, radius, defenseFraction):
    damageMultiplier = 1 - defenseFraction
    startIndex = max(0, position - radius)
    endIndex = min(len(self.incomingDamageMultipliers), position + radius + 1)
    for i in range(startIndex, endIndex):
      self.incomingDamageMultipliers[i] *= damageMultiplier

  def disconnectEnemyInputs(self, nodeIndex):
    self.addOutgoingAttack(CutAttack(nodeIndex, True, False))

  def disconnectInputs(self, nodeIndex):
    if nodeIndex < 0:
      print("No node at position " + str(nodeIndex))
      return # miss
    if nodeIndex >= self.network.size():
      print("No node at position " + str(nodeIndex))
      return # miss
    network = self.network
    node = network.nodes[nodeIndex]
    if len(node.inputsByName) < 1:
      print("No inputs to disconnect at position " + str(nodeIndex) + ": " + node.describeLinks(network))
    else:
      print("Disconnecting inputs at position " + str(nodeIndex) + ": " + node.describeLinks(network))
    for linkType in node.inputsByName.keys():
      existing = node.inputsByName[linkType]
      if existing is not None:
        print("Disconnecting input " + linkType + " for " + node.summarize())
        node.inputsByName[linkType] = None
      else:
        print("Input " + linkType + " for " + node.summarize() + " is already disconnected")

  def disconnectEnemyOutputs(self, nodeIndex):
    self.addOutgoingAttack(CutAttack(nodeIndex, False, True))

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

  def getEnemyPowerAcquired(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].getPowerAcquiredLastTurn()

  def getEnemyHitpoints(self, nodeIndex):
    if nodeIndex < 0:
      return 0
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    return network.nodes[nodeIndex].hitPoints

  def drainEnemyPower(self, nodeIndex, inputAmount, outputAmount):
    if nodeIndex < 0:
      return
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    self.addOutgoingAttack(PowerDrainAttack(nodeIndex, inputAmount, outputAmount))

  def drainInputPower(self, nodeIndex, amount):
    self.network.nodes[nodeIndex].drainInputPower(amount)

  def drainOutputPower(self, nodeIndex, amount):
    self.network.nodes[nodeIndex].drainOutputPower(amount)

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
        competitor.resetForNewTurn()
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
