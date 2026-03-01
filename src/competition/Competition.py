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
  def __init__(self, index):
    super().__init__()
    self.index = index

  def process(self, target):
    target.disconnect(self.index)

class PowerDrainAttack(Attack):
  def __init__(self, index, inputAmount, outputAmount):
    super().__init__()
    self.index = index
    self.inputAmount = inputAmount
    self.outputAmount = outputAmount

  def process(self, target):
    target.drainInputPower(self.index, self.inputAmount)
    target.drainOutputPower(self.index, self.outputAmount)

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

  def drainEnemyPower(self, nodeIndex, inputAmount, outputAmount):
    if nodeIndex < 0:
      return
    network = self.enemy.network
    if nodeIndex >= network.size():
      return 0
    self.enemy.addIncomingAttack(PowerDrainAttack(nodeIndex, inputAmount, outputAmount))

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
