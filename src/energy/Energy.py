# represents an amount of energy
class Energy(object):
  def __init__(self, amounts = {}):
    self.amounts = self.withoutZeros(amounts)

  def get(self, color):
    return self.amounts.get(color, 0)

  def getTypes(self):
    return self.amounts.keys()

  def getTotal(self):
    total = 0
    for value in self.amounts.values():
      total += value
    return total

  def getNumTypes(self):
    return len(self.amounts)

  def plus(self, other):
    totals = {}
    for key in self.amounts.keys():
      totals[key] = self.get(key) + other.get(key)
    for key in other.amounts.keys():
      totals[key] = self.get(key) + other.get(key)
    return Energy(totals)

  def minus(self, other):
    return self.plus(other.times(-1))

  def times(self, multiplier):
    totals = {}
    for key, value in self.amounts.items():
      totals[key] = value * multiplier
    return Energy(totals)

  def dividedBy(self, divisor):
    return self.times(1 / divisor)

  # whether all components >= 0
  def nonNegative(self):
    for value in self.amounts.values():
      if value < 0:
        return False
    return True

  # helper function
  def withoutZeros(self, amounts):
    result = {}
    for key, value in amounts.items():
      if value != 0:
        result[key] = value
    return result

  # for each component, computes the minimum in that component
  def min(self, other):
    results = {}
    for key in self.amounts.keys():
      results[key] = min(self.get(key), other.get(key))
    return Energy(results)

  # for each component, computes the maximum in that component
  def max(self, other):
    results = {}
    for key in self.amounts.keys():
      results[key] = max(self.get(key), other.get(key))
    for key in other.amounts.keys():
      results[key] = max(self.get(key), other.get(key))
    return Energy(results)

  # returns a new energy where every value in self is set to <constant>
  def withConstant(self, constant):
    results = {}
    for key in self.amounts.keys():
      results[key] = constant
    return Energy(results)

  def limitToConstant(self, constant):
    return self.min(self.withConstant(constant))

  def raiseToConstant(self, constant):
    return self.max(self.withConstant(constant))

  def nonempty(self):
    return len(self.amounts) > 0

  def __str__(self):
    if len(self.amounts) < 1:
      return "0"
    components = [str(value) + key for key, value in self.amounts.items()]
    return "".join(components)

# represents a type of energy
class EnergyColor(object):
  def __init__(self, shortName, longName, description):
    self.shortName = shortName
    self.longName = longName
    self.description = description

  def matchesName(self, name):
    if name == self.shortName:
      return True
    if name == self.longName:
      return True
    return False

  def __hash__(self):
    return self.longName.__hash__()

  def __eq__(self, other):
    return self.longName == other.longName

# represents a request for energy
class EnergyRequest(object):
  def __init__(self, energy, other = 0):
    self.amounts = energy
    self.other = other

  # tells whether this request is satisfied by this energy
  def satisfiedBy(self, energy):
    if not energy.minus(self.amounts).nonNegative():
      return False
    if energy.getTotal() < self.getTotal():
      return False
    return True

  def nonempty(self):
    return self.amounts.nonempty() or self.other > 0

  # reduces this request by the given energy amount
  def minus(self, energy):
    amounts = self.amounts.minus(energy).raiseToConstant(0)
    other = self.other - energy.getTotal()
    return EnergyRequest(amounts, other)

  # multiplies this request by the given amount
  def times(self, multiplier):
    amounts = self.amounts.times(multiplier)
    other = self.other * multiplier
    return EnergyRequest(amounts, other)

  # chooses how much energy this request wants to take from the given amount of energy
  def chooseFrom(self, energy):
    # select as much as possible in each color
    colorResult = energy.min(self.amounts)
    otherResult = Energy()
    # try to satisfy the generic requirements
    candidateTypes = list(energy.getTypes())
    while len(candidateTypes) > 0:
      remainingTarget = self.other - otherResult.getTotal()
      if remainingTarget <= 0:
        # request is satisfied so we're done
        break
      # split request into components per color
      targetPerColor = remainingTarget / len(candidateTypes)
      for i in range(len(candidateTypes) - 1, -1, -1):
        color = candidateTypes[i]
        availableInThisColor = energy.get(color) - colorResult.get(color)
        addInThisColor = min(availableInThisColor, targetPerColor)
        # count the amount acquired
        otherResult = otherResult.plus(Energy({color:addInThisColor}))
        if addInThisColor < targetPerColor:
          candidateTypes.pop(i)
    return colorResult.plus(otherResult)

  def min(self, other):
    amounts = self.amounts.min(other.amounts)
    other = min(self.other, other.other)
    return EnergyRequest(amounts, other)

  def limitToConstant(self, constant):
    amounts = self.amounts.limitToConstant(constant)
    other = min(self.other, constant)
    return EnergyRequest(amounts, other)

  def getTotal(self):
    return self.amounts.getTotal() + self.other

  def __str__(self):
    if self.other > 0:
      if self.amounts.nonempty():
        return str(self.amounts) + str(self.other)
      return str(self.other)
    return str(self.amounts)

# builds an Energy (or a structure representing an energy) with a single color
class SingleColorBuilder(object):
  def __init__(self, color):
    self.color = color

  # returns a data structure representing energy with the preconfigured color and the given value
  def d(self, amount):
    values = {}
    values[self.color] = amount
    return values

# build a structure representing an energy with a list of colors
class MultiColorBuilder(object):
  def __init__(self, colors):
    self.colors = set(colors)

  # returns a data structure representing energy with the preconfigured colors and the given values
  def d(self, amounts):
    for key in amounts.keys():
      if key not in self.colors:
        raise Exception("Invalid color '" + str(key) + "' not in " + str(self.colors))
    values = dict(amounts)
    return values
