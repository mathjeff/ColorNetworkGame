from energy.Energy import *

# An ItemProperties describes the properties that are used by an Item
# It doesn't describe other things like its cost or complexity
class ItemProperties(object):
  def __init__(self, properties):
    self.properties = dict(properties)

  def get(self, name):
    result = self.properties.get(name)
    if result is None:
      raise Exception("property '" + name + "' not in " + str(list(self.properties.keys())))
    return result

  def keys(self):
    return self.properties.keys()

  def containsKey(self, key):
    return key in self.properties

  def __str__(self):
    return str(self.properties)

# represents an object that a Competitor can use
class Item(object):
  def __init__(self, properties):
    self.hitPoints = 1
    self.undeclareInputs() # Map<String, ItemOutput>
    self.undeclareOutputs() # Map<String, List<ItemInput>>
    self.powerConsumedLastTurn = 0
    self.powerConsumedThisTurn = 0
    self.powerGivenLastTurn = 0
    self.powerGivenThisTurn = 0
    self.acquiringPower = False
    self.inputPowerDrain = 0
    self.outputPowerDrain = 0
    self.setProperties(properties)

  def setProperties(self, properties):
    self.loadProperties(ItemProperties(properties))
    self.properties = properties

  def loadProperties(self, properties):
    raise Exception("loadProperties not implemented in " + str(self))

  # connects self.inputs[inputName] to otherItem.outputs[outputName]
  def setInput(self, inputName, otherItem, outputName = "None"):
    if inputName not in self.inputsByName.keys():
      raise Exception("input '" + inputName + "' not declared in " + str(self))
    oldInput = self.inputsByName[inputName]
    if oldInput is not None:
      oldInput.item.removeOutput(inputName, self, oldInput.outputName)
    if otherItem is not None:
      self.inputsByName[inputName] = ItemOutput(otherItem, outputName)
    else:
      self.inputsByName[inputName] = None
    if otherItem is not None:
      otherItem.addOutput(inputName, self, outputName)

  # adds (otherItem, inputName) to self.outputs[outputName]
  def addOutput(self, inputName, otherItem, outputName):
    if outputName not in self.outputsByName:
      raise Exception("output '" + outputName + "' not declared in " + str(self))
    self.outputsByName[outputName].append(ItemInput(otherItem, inputName))

  # removes (otherItem, inputName) from self.outputs[outputName]
  def removeOutput(self, inputName, otherItem, outputName):
    if outputName not in self.outputsByName:
      raise Exception("output '" + outputName + "' not declared in " + str(self))
    candidates = self.outputsByName[outputName]
    matchingIndices = [i for i in range(len(candidates)) if candidates[i].item == otherItem and candidates[i].inputName == inputName]
    if len(matchingIndices) != 1:
      raise Exception("Expected 1 output in " + str(self) + " connected to item " + str(otherItem) + " input " + str(inputName) + ", found " + str(len(matchingIndices)))
    candidates.pop(matchingIndices[0])

  def receiveDamage(self, amount):
    self.hitPoints -= amount

  def setHitpoints(self, amount):
    self.hitPoints = amount

  def declareInputs(self, linkTypes):
    for linkType in linkTypes:
      if linkType not in self.inputsByName:
        self.inputsByName[linkType] = None

  def declaresInputs(self):
    return len(self.inputsByName) > 0

  def undeclareInputs(self):
    self.inputsByName = {}

  def declareOutputs(self, linkTypes):
    for name in linkTypes:
      if name not in self.outputsByName:
        self.outputsByName[name] = []

  def declareOutput(self, name = "None"):
    self.declareOutputs([name])

  def undeclareOutputs(self):
    self.outputsByName = {}

  def declaresOutputs(self):
    return len(self.outputsByName) > 0

  def getInputNames(self):
    return self.inputsByName.keys()

  def getOutputNames(self):
    return self.outputsByName.keys()

  def hasConnectedInput(self):
    for itemInput in self.inputsByName.values():
      if itemInput is not None:
        return True
    return False

  def hasConnectedOutput(self):
    for itemOutputs in self.outputsByName.values():
      if len(itemOutputs) > 0:
        return True
    return False

  def drainInputPower(self, amount):
    self.inputPowerDrain += amount

  def drainOutputPower(self, amount):
    self.outputPowerDrain += amount

  # tries to get power from the given link
  def tryAcquirePower(self, linkType, amount):
    if not amount.nonempty():
      return Energy() # no power requested
    if self.acquiringPower:
      return Energy() # we don't have any power for recursive calls
    if linkType not in self.inputsByName.keys():
      raise Exception("link type " + str(linkType) + " not declared in " + str(self) + ". All declared links: " + str(self.inputsByName))
    link = self.inputsByName.get(linkType)
    result = Energy()
    powerConsumed = 0
    self.acquiringPower = True
    if link is not None:
      if link.item.outputPowerDrain > 0:
        drainRequest = EnergyRequest(Energy(), link.item.outputPowerDrain)
        drained = link.item.tryGetPower(drainRequest, link.outputName)
        if drained.getTotal() > 0:
          link.item.outputPowerDrain -= drained.getTotal()
          powerConsumed += drained.getTotal()
          print(link.item.summarize() + " output was drained of " + str(drained) + " power")
      if self.inputPowerDrain > 0:
        drainRequest = EnergyRequest(Energy(), self.inputPowerDrain)
        drained = link.item.tryGetPower(drainRequest, link.outputName)
        if drained.getTotal() > 0:
          powerConsumed += drained.getTotal()
          print(self.summarize() + " input was drained of " + str(drained) + " power")
        self.inputPowerDrain -= drained.getTotal()
      result = link.item.tryGetPower(amount, link.outputName)
      powerConsumed += result.getTotal()
      link.item.powerGivenThisTurn += powerConsumed
    if result.nonempty():
      print(str(self.summarize()) + " got " + str(result) + " power from " + link.item.summarize())
    self.acquiringPower = False
    self.powerConsumedThisTurn += powerConsumed
    return result

  # tries to get power from the current node
  def tryGetPower(self, amount, outputName):
    return Energy() # empty

  # how much power was received last turn (plus any power drains applied to inputs or outputs)
  def getPowerConsumedLastTurn(self):
    return self.powerConsumedLastTurn

  # how much power was output last turn (including any power drains applied to inputs or outputs)
  def getPowerGivenLastTurn(self):
    return self.powerGivenLastTurn

  def act(self, player):
    return

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
    if len(self.outputsByName) > 0:
      outputMessage = "has " + str(len(self.outputsByName)) + " outputs"
      if len(self.outputsByName) > 1:
        outputMessage += ": " + str(self.outputsByName.keys())
      messages.append(outputMessage)
    return messages

  def formatHelp(self):
    messages = self.getHelpMessages()
    return "\n ".join(messages)

  def describeLinks(self, network):
    index = network.getPosition(self)
    messages = [self.summarize()]
    for name, value in self.inputsByName.items():
      if value is not None:
        otherIndex = network.getPosition(value.item)
        displayIndex = otherIndex + 1
        messages.append(name + ": #" + str(displayIndex) + " " + value.summarize())
      else:
        messages.append(name + ": None")
    return "#" + str(index + 1) + " " + ", ".join(messages)

  # whether we should hint to the user that this item isn't configured properly
  def hintMisconfigured(self):
    if self.declaresInputs() and not self.hasConnectedInput():
      return True
    if self.declaresOutputs() and not self.hasConnectedOutput():
      return True
    return False

# represents an output of an item
class ItemOutput(object):
  def __init__(self, item, outputName):
    self.item = item
    self.outputName = outputName

  def summarize(self):
    result = self.item.summarize()
    if self.outputName != "None":
      result = result + " " + self.outputName
    return result

  def __str__(self):
    return self.summarize()

# represents an input of an item
class ItemInput(object):
  def __init__(self, item, inputName):
    self.item = item
    self.inputName = inputName

  def summarize(self):
    result = self.item.summarize()
    if self.inputName != "None":
      result = result + " " + self.inputName
    return result

  def __str__(self):
    return self.summarize()

# attacks based on power and signal
class Laser(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "control"])

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.damage = properties.get("damage")
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    if self.requiredPower.satisfiedBy(power):
      damage = self.damage
    else:
      damage = 0
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal.getTotal() / self.maxSignalPower.getTotal())
    print("laser applying damage " + str(damage) + " at position " + str(targetIndex))
    competitor.applyEnemyDamage(targetIndex, damage)

  def clone(self):
    return Laser(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + str(self.damage) + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("attacks items in the opposing robot")
    messages.append("requires at least " + str(self.requiredPower) + " energy in one turn and then deals " + str(self.damage) + " damage")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# disconnects node inputs
class InputCutter(Item):
  def __init__(self, properties):
    super().__init__(properties)

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal.getTotal() / self.maxSignalPower.getTotal())
    if self.requiredPower.satisfiedBy(power):
      print(self.summarize() + " trying to cut at position " + str(targetIndex))
      competitor.disconnectEnemyInputs(targetIndex)
    else:
      if power.nonempty():
        print(self.summarize() + " insufficient power: " + str(power) + " < " + str(self.requiredPower))

  def clone(self):
    return InputCutter(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("disconnects inputs from items in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# disconnects node outputs
class OutputCutter(Item):
  def __init__(self, properties):
    super().__init__(properties)

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.declareInputs(["power", "control"])

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal.getTotal() / self.maxSignalPower.getTotal())
    if self.requiredPower.satisfiedBy(power):
      print(self.summarize() + " cutting at position " + str(targetIndex))
      competitor.disconnectEnemyOutputs(targetIndex)
    else:
      if power.nonempty():
        print(self.summarize() + " insufficient power: " + str(power) + " < " + str(self.requiredPower))

  def clone(self):
    return OutputCutter(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("disconnects outputs from items in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# holds power and can provide it over time
class Battery(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()

  def loadProperties(self, properties):
    self.charge = Energy(properties.get("maxCharge"))
    self.dischargeRate = properties.get("dischargeRate")
    self.readyToDischarge = Energy()

  def act(self, competitor):
    super().act(competitor)
    self.readyToDischarge = self.charge.min(self.charge.withConstant(self.dischargeRate))

  def tryGetPower(self, requested, outputName):
    amount = requested.chooseFrom(self.readyToDischarge)
    self.readyToDischarge = self.readyToDischarge.minus(amount)
    self.charge = self.charge.minus(amount)
    return amount

  def clone(self):
    return Battery(self.properties)

  def summarize(self):
    return "Battery " + str(self.charge) + "/" + str(self.dischargeRate)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    prefix = " holds " + str(self.charge) + " charge and can give "
    if self.charge.getNumTypes() > 1:
      amountText = str(self.dischargeRate) + " of each color per turn"
    else:
      amountText = str(self.dischargeRate) + " per turn"
    suffix = " to other items"
    messages.append(prefix + amountText + suffix)
    return messages

# just has lots of hitpoints
class Wall(Item):
  def __init__(self, properties):
    super().__init__(properties)

  def loadProperties(self, properties):
    self.hitPoints = properties.get("hitPoints")

  def summarize(self):
    return "Wall " + str(self.hitPoints)

  def clone(self):
    return Wall(self.properties)

# grows while it has energy
class CellWall(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power"])

  def loadProperties(self, properties):
    self.hitPoints = properties.get("hitPoints")
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.hitpointGainPerTurn = properties.get("hitpointGainPerTurn")

  def act(self, competitor):
    super().act(competitor)
    if self.requiredPower.satisfiedBy(self.tryAcquirePower("power", self.requiredPower)):
      newHitpoints = self.hitPoints + self.hitpointGainPerTurn
      print(self.summarize() + " hitpoints increasing by " + str(self.hitpointGainPerTurn) + " to " + str(newHitpoints))
      self.hitPoints = newHitpoints

  def summarize(self):
    return "CellWall " + str(self.hitPoints) + " " + str(self.requiredPower) + "->+" + str(self.hitpointGainPerTurn)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("each turn if powered with " + str(self.requiredPower) + ", increases hitpoints by " + str(self.hitpointGainPerTurn)) 
    return messages

  def clone(self):
    return CellWall(self.properties)

# adds a constant to each color of power
class Adder(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])
    self.signal = 0

  def loadProperties(self, properties):
    self.maxInput = EnergyRequest(Energy(), properties.get("maxInput"))
    self.addition = properties.get("addition")

  def act(self, competitor):
    super().act(competitor)
    self.signal = self.tryAcquirePower("signal", self.maxInput).getTotal()
    print(self.summarize() + " signal " + str(self.signal))

  def tryGetPower(self, requested, outputName):
    targetOutput = requested.limitToConstant(self.signal + self.addition)
    power = self.tryAcquirePower("power", targetOutput)
    return power

  def clone(self):
    return Adder(self.properties)

  def summarize(self):
    return super().summarize() + "+" + str(self.addition)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("at the start of its turn, reads input up to " + str(self.maxInput))
    messages.append("whenever an item asks it for power, it attempts to consume an amount of input power equal to the last read signal plus " + str(self.addition) + ", and outputs the result")
    return messages

# Divides power flow by a constant
class Divider(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readyToDischarge = 0
    self.declareInputs(["power"])

  def loadProperties(self, properties):
    self.divisors = properties.get("divisors")
    outputNames = [self.getOutputName(divisor) for divisor in self.divisors]
    self.undeclareOutputs()
    self.declareOutputs(outputNames)

  def getOutputName(self, divisor):
    if divisor < 1:
      raise Exception("Divisor must be >= 1, not " + str(divisor))
    return "output" + str(divisor)

  def getDivisor(self, outputName):
    prefix = "output"
    if outputName.startswith(prefix):
      divisorText = outputName[len(prefix):]
      return int(divisorText)
    return 1

  def tryGetPower(self, requested, outputName):
    divisor = self.getDivisor(outputName)
    targetInput = requested.times(divisor)
    actualInput = self.tryAcquirePower("power", targetInput)
    return actualInput.dividedBy(divisor)

  def clone(self):
    return Divider(self.properties)

  def summarize(self):
    return super().summarize() + "/" + str(self.divisors)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("outputs the input power divided by one of " + str(self.divisors))
    return messages

# reads an input and gives up to that much power each time it is requested
class Fork(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.signal = 0
    self.declareOutput()
    self.declareInputs(["power", "signal"])

  def loadProperties(self, properties):
    self.maxInput = properties.get("maxInput")

  def act(self, competitor):
    super().act(competitor)
    self.signals = {}

  def getSignal(self, color):
    result = self.signals.get(color)
    if result is None:
      result = self.tryAcquirePower("signal", EnergyRequest(Energy({color:self.maxInput}, 0)))
      self.signals[color] = result
    return result

  def tryGetPower(self, requested, outputName):
    # compute signal
    signal = Energy({})
    for key in requested.getTypes():
      signal = signal.plus(self.getSignal(key))
    # try to acquire
    result = self.tryAcquirePower("power", signal)
    return result

  def clone(self):
    return Fork(self.properties)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("tries to get up to " + str(self.maxInput) + " power from an input, and then tries to give up to that much power each time any item requests it")
    messages.append("This is different from other items that are willing to give all of their power to the first requester and have none left for the next")
    return messages

# a joiner takes power from two inputs
class Joiner(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()
    self.numInputs = 0

  def loadProperties(self, properties):
    self.undeclareInputs()
    numInputs = int(properties.get("numInputs"))
    inputNames = [self.getInputName(i) for i in range(numInputs)]
    self.declareInputs(inputNames)

  def getInputName(self, number):
    return "input" + str(number)

  def tryGetPower(self, requested, outputName):
    power = Energy({})
    for i in range(len(self.numInputs)):
      inputName = self.getInputName(i)
      power = power.plus(self.tryAcquirePower(inputName, requested.minus(power)))
    return power

  def clone(self):
    return Joiner(self.properties)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("takes power from up to three inputs and provides it as output")
    return messages

# a comparer compares a signal to a constant, and then lets power one port based on the result
class Comparer(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutputs(["low", "high"])
    self.reading = 0
    self.declareInputs(["power", "signal"])
    self.high = False

  def loadProperties(self, properties):
    threshold = properties.get("threshold")
    self.threshold = EnergyRequest(Energy(), threshold)

  def act(self, competitor):
    super().act(competitor)
    self.high = self.threshold.satisfiedBy(self.tryAcquirePower("signal", self.threshold))

  def tryGetPower(self, requested, outputName):
    if (outputName == "high") == (self.high):
      return self.tryAcquirePower("power", requested)
    return Energy({})

  def clone(self):
    return Comparer(self.properties)

  def summarize(self):
    return super().summarize() + ">=" + str(self.threshold)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("checks whether the signal is at least " + str(self.threshold) + ". If it is, then power is allowed through the output named 'high'. Otherwise power is allowed through the output named 'low'")
    return messages

# a Capacitor stores energy
class Capacitor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.energy = Energy()
    self.declareOutputs(["power", "signal"])
    self.declareInputs(["power"])

  def loadProperties(self, properties):
    self.maxEnergy = Energy(properties.get("maxEnergy"))
    if properties.containsKey("startingEnergy"):
      self.energy = Energy(properties.get("startingEnergy"))
    self.signalOutputFraction = properties.get("signalOutputFraction")

  def act(self, competitor):
    super().act(competitor)
    request = EnergyRequest(self.maxEnergy.minus(self.energy))
    self.energy = self.energy.plus(self.tryAcquirePower("power", request))

  def tryGetPower(self, requested, outputName):
    if outputName == "signal":
      available = self.energy.times(self.signalOutputFraction)
    else:
      available = self.energy
    amount = requested.chooseFrom(available)
    self.energy = self.energy.minus(amount)
    return amount

  def clone(self):
    copy = Capacitor(self.properties)
    copy.energy = self.energy
    return copy

  def summarize(self):
    return super().summarize() + " " + str(self.energy) + "/" + str(self.maxEnergy)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("can store up to " + str(self.maxEnergy) + " energy and release it at any time")
    messages.append("can output " + str(self.signalOutputFraction) + " times its stored energy as an output signal")
    return messages

# a Shield defends against damage
class Shield(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "distance", "direction"])

  def loadProperties(self, properties):
    self.defenseFraction = properties.get("defenseFraction")
    self.radius = properties.get("radius")
    self.requiredEnergy = EnergyRequest(Energy(properties.get("requiredPower")))
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleDistance = properties.get("maxPossibleDistance")

  def act(self, competitor):
    super().act(competitor)
    energy = self.tryAcquirePower("power", self.requiredEnergy)
    distanceSignal = self.tryAcquirePower("distance", self.maxSignalPower)
    directionSignal = self.tryAcquirePower("direction", self.maxSignalPower)
    if self.requiredEnergy.satisfiedBy(energy):
      ourPosition = competitor.network.getPosition(self)
      distance = int(self.maxPossibleDistance * distanceSignal.getTotal() / self.maxSignalPower.getTotal())
      if directionSignal.nonempty():
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
    return super().summarize() + " " + str(self.requiredEnergy) + "->" + self.getDefenseText() + " +/-" + str(self.radius)

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
    self.givenReading = 0
    self.consumedReading = 0
    self.declareInputs(["power", "positionSignal"])
    self.declareOutputs(["producedSignal", "consumedSignal", "totalSignal"])

  def loadProperties(self, properties):
    self.radius = properties.get("radius")
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.outputRatio = properties.get("outputRatio")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    positionSignal = self.tryAcquirePower("positionSignal", self.requiredPower)
    if self.requiredPower.satisfiedBy(power):
      index = int(self.maxPossibleTarget * positionSignal.getTotal() / self.maxSignalPower.getTotal())
      givenReading = 0
      consumedReading = 0
      lowIndex = index - self.radius
      highIndex = index + self.radius
      for i in range(lowIndex, highIndex + 1):
        consumedReading += competitor.getEnemyPowerConsumed(i)
        givenReading += competitor.getEnemyPowerGiven(i)
      print(self.summarize() + " reading opponent total power usage from " + str(lowIndex) + " to " + str(highIndex) + ", gave " + str(givenReading) + " consumed " + str(consumedReading))
      self.givenReading = min(givenReading * self.outputRatio, power.getTotal())
      self.consumedReading = min(consumedReading * self.outputRatio, power.getTotal())
    else:
      if power.nonempty():
        print("power " + str(power) + " not enough to power " + self.summarize())
      self.givenReading = 0
      self.consumedReading = 0

  def tryGetPower(self, requested, outputName):
    if outputName == "givenSignal":
      result = requested.limitToConstant(self.givenReading)
      return result
    if outputName == "consumedSignal":
      result = requested.limitToConstant(self.consumedReading)
      return result
    if outputName == "totalSignal":
      result = requested.limitToConstant(self.givenReading + self.consumedReading)
    return Energy()

  def clone(self):
    return PowerUsageSensor(self.properties)

  def summarize(self):
    return super().summarize()

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Measures power usage with radius " + str(self.radius) + " from the target position in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    messages.append("The producedSignal output will be set to " + str(self.outputRatio) + " times the total power output by the measured items")
    messages.append("The consumedSignal output will be set to " + str(self.outputRatio) + " times the total power consumed by the measured items")
    messages.append("The totalSignal output will be set to the producedSignal output plus the consumedSignal output")
    return messages

# senses the number of hitpoints in an item
class HealthSensor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readings = []
    self.declareInputs(["power", "positionSignal"])

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.outputRatio = properties.get("outputRatio")
    self.radius = int(properties.get("radius"))
    self.undeclareOutputs()
    for i in range(self.getNumOutputs()):
      self.declareOutput(self.getOutputName(i))

  def getNumOutputs(self):
    return self.radius * 2 + 1

  def getOutputName(self, index):
    return "output" + str(index)

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    positionSignal = self.tryAcquirePower("positionSignal", self.requiredPower)
    self.readings = []
    if self.requiredPower.satisfiedBy(power):
      baseIndex = int(self.maxPossibleTarget * positionSignal.getTotal() / self.maxSignalPower.getTotal())
      for index in range(baseIndex - self.radius, baseIndex + self.radius + 1):
        hitpoints = competitor.getEnemyHitpoints(index)
        reading = min(hitpoints * self.outputRatio, power.getTotal())
        self.readings.append(reading)
        print(self.summarize() + " reading opponent hitpoints at " + str(index) + " of " + str(hitpoints) + ", outputting " + str(self.reading))
    else:
      if power.nonempty():
        print("power " + str(power) + " not enough to power " + self.summarize())
      self.reading = []

  def getOutputIndex(self, outputName):
    for i in range(self.getNumOutputs()):
      if self.getOutputName(i) == outputName:
        return i
    raise Exception("Output " + outputName + " not found in " + str(self))

  def tryGetPower(self, requested, outputName):
    outputIndex = self.getOutputIndex(outputName)
    if outputIndex >= len(self.readings):
      print("Reading " + str(outputIndex) + " not available")
      return Energy()
    reading = self.readings[outputIndex]
    result = requested.limitToConstant(reading)
    return result

  def clone(self):
    return HealthSensor(self.properties)

  def summarize(self):
    return super().summarize()

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Measures hitpoints of items within radius " + str(self.radius) + " of the target position in the opposing robot")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    messages.append("Provides " + str(self.getNumOutputs()) + " output signals. Each one is set to the hitpoints of the corresponding item in the opponent's robot times " + str(self.outputRatio))
    return messages

# drains power
class PowerInputDrainer(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "positionSignal", "radiusSignal"])

  def loadProperties(self, properties):
    self.powerPerDrain = EnergyRequest(Energy(properties.get("powerPerDrain")))
    self.maxPower = EnergyRequest(Energy(properties.get("maxPower")))
    self.maxPositionPower = EnergyRequest(Energy(properties.get("maxPositionPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.maxRadiusPower = EnergyRequest(Energy(properties.get("maxRadiusPower")))
    self.maxRadius = properties.get("maxRadius")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.maxPower)
    positionSignal = self.tryAcquirePower("positionSignal", self.maxPositionPower)
    radiusSignal = self.tryAcquirePower("radiusSignal", self.maxRadiusPower)
    index = int(self.maxPossibleTarget * positionSignal.getTotal() / self.maxPositionPower.getTotal())
    radius = int(self.maxRadius * radiusSignal.getTotal() / self.maxRadiusPower.getTotal())
    lowIndex = index - radius
    highIndex = index + radius + 1
    numTargetPositions = highIndex - lowIndex
    drainPerPosition = int(power.getTotal() / numTargetPositions / self.powerPerDrain.getTotal())
    if drainPerPosition < 1:
      print("Power " + str(power) + " to " + self.summarize() + " not enough to apply a drain to " + str(numTargetPositions) + " positions")
    
    for i in range(lowIndex, highIndex):
      competitor.drainEnemyPower(i, drainPerPosition, 0)
    print(self.summarize() + " draining opponent input power of " + str(drainPerPosition) + " from each opponent item from " + str(lowIndex + 1) + " to " + str(highIndex))

  def clone(self):
    return PowerInputDrainer(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.powerPerDrain) + "/" + str(self.maxPower) + "->1" + "+/-(" + str(self.maxRadiusPower) + ":" + str(self.maxRadius) + ") (" + str(self.maxPositionPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Drains input power from items in the opposing robot")
    messages.append("You can supply power to the radius port to change how many items this targets. A radius power level of 0 will produce a radius of 0. A radius power level of " + str(self.maxRadiusPower) + " will produce a radius of " + str(self.maxRadius))
    messages.append("Max power usage is " + str(self.maxPower))
    messages.append("For every " + str(self.powerPerDrain) + " input power, drains 1 input power from target items in the opposing robot (divided evenly, rounded down)")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxPositionPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# drains power
class PowerOutputDrainer(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "positionSignal", "radiusSignal"])

  def loadProperties(self, properties):
    self.powerPerDrain = EnergyRequest(Energy(properties.get("powerPerDrain")))
    self.maxPower = EnergyRequest(Energy(properties.get("maxPower")))
    self.maxPositionPower = EnergyRequest(Energy(properties.get("maxPositionPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")
    self.maxRadiusPower = EnergyRequest(Energy(properties.get("maxRadiusPower")))
    self.maxRadius = properties.get("maxRadius")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.maxPower)
    positionSignal = self.tryAcquirePower("positionSignal", self.maxPositionPower)
    radiusSignal = self.tryAcquirePower("radiusSignal", self.maxRadiusPower)
    index = int(self.maxPossibleTarget * positionSignal.getTotal() / self.maxPositionPower.getTotal())
    radius = int(self.maxRadius * radiusSignal.getTotal() / self.maxRadiusPower.getTotal())
    lowIndex = index - radius
    highIndex = index + radius + 1
    numTargetPositions = highIndex - lowIndex
    drainPerPosition = int(power.getTotal() / numTargetPositions / self.powerPerDrain.getTotal())
    if drainPerPosition < 1:
      print("Power " + str(power) + " to " + self.summarize() + " not enough to apply a drain to " + str(numTargetPositions) + " positions")
    
    for i in range(lowIndex, highIndex):
      competitor.drainEnemyPower(i, 0, drainPerPosition)
    print(self.summarize() + " draining opponent output power of " + str(drainPerPosition) + " from each opponent item from " + str(lowIndex + 1) + " to " + str(highIndex))

  def clone(self):
    return PowerOutputDrainer(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.powerPerDrain) + "/" + str(self.maxPower) + "->1" + "+/-(" + str(self.maxRadiusPower) + ":" + str(self.maxRadius) + ") (" + str(self.maxPositionPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Drains output power from items in the opposing robot")
    messages.append("You can supply power to the radius port to change how many items this targets. A radius power level of 0 will produce a radius of 0. A radius power level of " + str(self.maxRadiusPower) + " will produce a radius of " + str(self.maxRadius))
    messages.append("Max power usage is " + str(self.maxPower))
    messages.append("For every " + str(self.powerPerDrain) + " input power, drains 1 output power from target items in the opposing robot (divided evenly, rounded down)")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxPositionPower) + " will target position " + str(self.maxPossibleTarget))
    return messages

# converts power from one type to another type
class Converter(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power"])
    self.declareOutput()

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.outputPower = Energy(properties.get("outputPower"))
    self.numUsesPerTurn = int(properties.get("numUsesPerTurn"))
    self.readyToDischarge = Energy()

  def act(self, competitor):
    super().act(competitor)
    self.readyToDischarge = Energy()
    for i in range(self.numUsesPerTurn):
      power = self.tryAcquirePower("power", self.requiredPower)
      if self.requiredPower.satisfiedBy(power):
        self.readyToDischarge = self.readyToDischarge.plus(self.outputPower)
      else:
        if power.nonempty():
          print("power " + str(power) + " not enough to power " + str(self))
        break

  def tryGetPower(self, requested, outputName):
    amount = requested.chooseFrom(self.readyToDischarge)
    self.readyToDischarge = self.readyToDischarge.minus(amount)
    return amount

  def clone(self):
    return Converter(self.properties)

  def summarize(self):
    return "Converter " + str(self.requiredPower) + "->" + str(self.outputPower) + "(" + str(self.numUsesPerTurn) + "X)"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("converts " + str(self.requiredPower) + " to " + str(self.outputPower) + " every turn, " + str(self.numUsesPerTurn) + " times per turn")
    return messages

# does equal damage to both competitors
class Ram(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power"])

  def loadProperties(self, properties):
    self.maxPower = EnergyRequest(Energy(properties.get("maxPower")))
    self.damagePerPower = properties.get("damagePerPower")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.maxPower)
    damage = power.getTotal() * self.damagePerPower
    if damage >= 1:
      competitor.addRamAttack(damage)
    else:
      if power.nonempty():
        print("power " + str(power) + " not enough for " + str(self) + " to do damage")

  def clone(self):
    return Ram(self.properties)

  def summarize(self):
    return "Ram <=" + str(self.maxPower) + "->" + str(self.damagePerPower) + "x"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Uses up to " + str(self.maxPower) + " energy to deal " + str(self.damagePerPower) + " damage per power to each competitor each turn")
    messages.append("If this damage destroys an item, it will continue on to subsequent items")
    return messages

# wins if the opponent has few enough hitpoints
class Flipper(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power"])

  def loadProperties(self, properties):
    self.maxPower = EnergyRequest(Energy(properties.get("maxPower")))
    self.strengthPerPower = properties.get("strengthPerPower")
    self.setHitpoints(float(properties.get("hitpoints")))

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.maxPower)
    strength = power.getTotal() * self.strengthPerPower
    if strength >= 1:
      position = competitor.network.getPosition(self)
      if position != 0:
        print("Cannot run " + self.summarize() + " because of being in position " + str(position) + " rather than 0")
      else:
        competitor.launchFlipAttack(strength)
    else:
      if power.nonempty():
        print("power " + str(power) + " not enough for " + str(self) + " to function")

  def clone(self):
    return Flipper(self.properties)

  def summarize(self):
    return "Flipper (" + str(self.hitPoints) + ") <=" + str(self.maxPower) + "->" + str(self.strengthPerPower) + "x"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("Uses up to " + str(self.maxPower) + " energy to attempt to flip the opponent. Flip strength equals " + str(self.strengthPerPower) + " times power used")
    messages.append("If this strength is more than the opponent's hitpoints, the opponent is flipped and cannot attack anymore")
    messages.append("If not in position 0 in the network, has no effect")
    return messages

# launches attacks that repeatedly destroy weak items
class Infector(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareInputs(["power", "control"])

  def loadProperties(self, properties):
    self.requiredPower = EnergyRequest(Energy(properties.get("requiredPower")))
    self.damage = properties.get("damage")
    self.maxSignalPower = EnergyRequest(Energy(properties.get("maxSignalPower")))
    self.maxPossibleTarget = properties.get("maxPossibleTarget")

  def act(self, competitor):
    super().act(competitor)
    power = self.tryAcquirePower("power", self.requiredPower)
    if self.requiredPower.satisfiedBy(power):
      damage = self.damage
    else:
      damage = 0
    signal = self.tryAcquirePower("control", self.maxSignalPower)
    targetIndex = int(self.maxPossibleTarget * signal.getTotal() / self.maxSignalPower.getTotal())
    print("infector launching attack of strength " + str(damage) + " at position " + str(targetIndex))
    competitor.launchInfectAttack(targetIndex, damage)

  def clone(self):
    return Infector(self.properties)

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + str(self.damage) + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("launches one pathogen per turn at the opposing robot")
    messages.append("each pathogen will do " + str(self.damage) + " damage. If that damage destroys the target item, the pathogen will proceed to the next item in the next turn")
    messages.append("requires at least " + str(self.requiredPower) + " energy in one turn and then deals " + str(self.damage) + " damage")
    messages.append("You can supply power to the control port to change where this aims. A control power level of 0 will target position 0. A control power level of " + str(self.maxSignalPower) + " will target position " + str(self.maxPossibleTarget))
    return messages
