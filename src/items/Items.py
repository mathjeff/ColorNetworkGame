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

  def __str__(self):
    return str(self.properties)

# represents an object that a Competitor can use
class Item(object):
  def __init__(self, properties):
    self.hitPoints = 1
    self.inputsByName = {}
    self.outputNames = []
    self.powerAcquiredLastTurn = 0
    self.acquiringPower = False
    self.setProperties(properties)

  def setProperties(self, properties):
    self.loadProperties(ItemProperties(properties))
    self.properties = properties

  def loadProperties(self, properties):
    raise Exception("loadProperties not implemented in " + str(self))

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

  def describeLinks(self, network):
    messages = [self.summarize()]
    for name, value in self.inputsByName.items():
      if value is not None:
        index = network.getPosition(value.item)
        displayIndex = index + 1
        messages.append(name + ": #" + str(displayIndex) + " " + value.summarize())
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

  def loadProperties(self, properties):
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
    return super().summarize() + " " + str(self.requiredPower) + "->" + str(self.damage) + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

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

  def loadProperties(self, properties):
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

  def summarize(self):
    return super().summarize() + " " + str(self.requiredPower) + "->" + "(" + str(self.maxSignalPower) + ":" + str(self.maxPossibleTarget) + ")"

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

  def loadProperties(self, properties):
    self.charge = properties.get("maxCharge")
    self.dischargeRate = properties.get("dischargeRate")
    self.readyToDischarge = 0

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
    return "Battery " + str(self.charge) + "/" + str(self.dischargeRate)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append(" holds " + str(self.charge) + " charge and can give " + str(self.dischargeRate) + " per turn to other items")
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

# limits power flow
class Resistor(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.readyToDischarge = 0
    self.declareOutput()
    self.declareInputs(["power"])

  def loadProperties(self, properties):
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

  def loadProperties(self, properties):
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
    self.signal = self.tryAcquirePower("signal", self.maxInput)

  def tryGetPower(self, requested, outputName):
    if requested <= 0:
      return 0
    power = self.tryAcquirePower("power", min(self.signal, requested))
    return power

  def clone(self):
    return Fork(self.properties)

  def getHelpMessages(self):
    messages = super().getHelpMessages()
    messages.append("tries to get up to " + str(maxInput) + " power from an input, and then tries to give up to that much power each time any item requests it")
    messages.append("This is different from other items that are willing to give all of their power to the first requester and have none left for the next")
    return messages

# a joiner takes power from two inputs
class Joiner(Item):
  def __init__(self, properties):
    super().__init__(properties)
    self.declareOutput()
    self.declareInputs(["input1", "input2"])

  def loadProperties(self, properties):
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

  def loadProperties(self, properties):
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

  def summarize(self):
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

  def loadProperties(self, properties):
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
    self.reading = 0
    self.declareInputs(["power", "positionSignal"])
    self.declareOutput()

  def loadProperties(self, properties):
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
    messages.append("The output will be set to " + str(self.outputRatio) + " times the total power read from the opponent")
    return messages
