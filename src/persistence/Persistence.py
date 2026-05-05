#!python

import json, os, random, shutil, textwrap

# a set of items that can be bought together
class Offering(object):
  def __init__(self, items, name, popularity, complexity, cost):
    self.items = [item.clone() for item in items]
    self.name = name
    self.popularity = popularity
    self.complexity = complexity
    self.cost = cost

  def clone(self):
    return Offering(self.items, self.name, self.popularity, self.complexity, self.cost)

# a collection of Offering
class OfferingFactory(object):
  def __init__(self):
    self.contents = []
    self.contentsByName = {}
    self.itemsByType = {}

  def add(self, item, popularity, complexity, baseCost):
    self.addBundle([item], popularity, complexity, baseCost)

  def addBundle(self, items, popularity, complexity, baseCost):
    baseName = "-".join([type(item).__name__ for item in items])
    self.addOffering(Offering(items, baseName, popularity, complexity, baseCost))

  def addOffering(self, offering):
    name = offering.name
    if name in self.contentsByName:
      index = 2
      while (name + str(index)) in self.contentsByName:
        index += 1
      name = name + str(index)
    offering.name = name
    self.contents.append(offering)
    self.contentsByName[offering.name] = offering
    for item in offering.items:
      self.itemsByType[type(item).__name__] = item

  def hasTemplateNamed(self, name):
    return name in self.contentsByName

  def getTemplateNamed(self, name):
    result = self.contentsByName.get(name)
    if result is None:
      raise Exception("'" + str(name) + "' not found in " + str(list(self.contentsByName.keys())))
    return result

  def cloneItemNamed(self, name):
    template = self.getTemplateNamed(name)
    items = template.items
    if len(items) != 1:
      raise Exception("Offer '" + name + "' has " + str(len(items)) + ", expected 1")
    return items[0].clone()

  def cloneItemWithType(self, itemType):
    result = self.itemsByType.get(itemType)
    if result is None:
      raise Exception("'" + str(itemType) + "' not found in " + str(list(self.itemsByType.keys())))
    return result.clone()

  def getAll(self):
    return self.contents

  def cloneAndMutateRandomItem(self):
    index = random.randint(0, len(self.contents) - 1)
    mutated = self.mutateRandomly(self.contents[index], 0.1)
    self.addOffering(mutated)

  def mutateRandomly(self, offering, maxFractionChange):
    result = offering.clone()
    for item in result.items:
      oldProperties = item.properties
      newProperties = {}
      for key in oldProperties.keys():
        value = oldProperties.get(key)
        fractionChange = random.uniform(-maxFractionChange, maxFractionChange)
        newProperties[key] = value * (1 + fractionChange)
      item.setProperties(newProperties)
    return result

  def parseOfferings(self, jsonObjects):
    result = []
    for o in jsonObjects:
      result.append(self.parseOffering(o))
    return result

  def parseOffering(self, jsonObject):
    name = jsonObject["name"]
    popularity = jsonObject["popularity"]
    complexity = jsonObject["complexity"]
    cost = jsonObject["cost"]
    items = []
    for subObject in jsonObject["items"]:
      itemType = subObject["type"]
      item = self.cloneItemWithType(itemType)
      item.setProperties(subObject["properties"])
      items.append(item)
    offering = Offering(items, name, popularity, complexity, cost)
    return offering

  def offeringsToDict(self, offeringList):
    result = []
    for offering in offeringList:
      result.append(self.offeringToDict(offering))
    return result

  def offeringToDict(self, offering):
    result = {}
    result["name"] = offering.name
    result["popularity"] = offering.popularity
    result["complexity"] = offering.complexity
    result["cost"] = offering.cost
    items = []
    for item in offering.items:
      subObject = {}
      subObject["properties"] = item.properties
      subObject["type"] = type(item).__name__
      items.append(subObject)
    result["items"] = items
    return result

# a collection of Offering saved to a file
class FileOfferingFactory(OfferingFactory):
  def __init__(self, defaultFactory, filepath):
    super().__init__()
    self.defaultFactory = defaultFactory
    self.filepath = filepath
    if os.path.isfile(filepath):
      self.loadFile()
    self.loadDefaults()

  def loadFile(self):
    json = self.readFile()
    items = self.defaultFactory.parseOfferings(json)
    for item in items:
      self.addOffering(item)

  def readFile(self):
    with open(self.filepath) as f:
      return json.load(f)

    return # not implemented yet

  def ensureSaved(self):
    if not os.path.exists(self.filepath):
      self.saveFile()

  def saveFile(self):
    if os.path.exists(self.filepath):
      raise Exception("File exists: " + str(self.filepath))
    parentPath = os.path.dirname(self.filepath)
    os.makedirs(parentPath, exist_ok = True)
    text = self.serialize()
    with open(self.filepath, 'w') as f:
      f.write(text)

  def serialize(self):
    components = []
    for component in self.getAll():
      components.append(self.offeringToDict(component))
    return json.dumps(components, indent = 2)

  # add the default items to this factory, without overwriting existing items
  def loadDefaults(self):
    for offering in self.defaultFactory.getAll():
      name = offering.name
      if not self.hasTemplateNamed(name):
        self.addOffering(offering)

# information stored in the RunLog
class RunLogEntry(object):
  def __init__(self, name):
    self.name = name

  def getType():
    raise Exception("getType() not defined in " + str(self))

# stores information about vising a shop into the RunLog
class RunLogShopEntry(RunLogEntry):
  def __init__(self, name, purchased, remaining):
    super().__init__(name)
    self.purchased = purchased
    self.remaining = remaining

  def getType(self):
    return "market"

class RunLogCompetitionEntry(RunLogEntry):
  def __init__(self, name, successful):
    super().__init__(name)
    self.successful = successful

  def getType(self):
    return "competition"

class RunLogConclusionEntry(RunLogEntry):
  def __init__(self, name, successful):
    super().__init__(name)
    self.successful = successful

  def getType(self):
    return "conclusion"

# saves information about the player's current run
class RunLog(object):
  def __init__(self, filepath, offeringFactory): # needs an item factory to validate and parse the log
    self.filepath = filepath
    self.entries = {}
    os.makedirs(self.filepath, exist_ok = True)
    self.offeringFactory = offeringFactory
    self.load()

  def nonEmpty(self):
    return len(self.entries) > 0

  def addEntry(self, entry):
    self.putEntryInMemory(entry)
    self.writeEntry(entry)

  def getShopEntries(self):
    return self.getEntriesWithType("market")

  def getCompetitionEntries(self):
    return self.getEntriesWithType("competition")

  def getConclusionEntry(self):
    conclusionEntries = self.getEntriesWithType("conclusion")
    if len(conclusionEntries) == 1:
      return conclusionEntries[0]
    return None

  def getLastEntry(self):
    lastEntry = None
    for entry in self.entries.values():
      if lastEntry is None or entry.name > lastEntry.name:
        lastEntry = entry
    return lastEntry

  def getEntriesWithType(self, entryType):
    results = [entry for entry in self.entries.values() if entry.getType() == entryType]
    return results

  def putEntryInMemory(self, entry):
    name = entry.name
    if name in self.entries:
      raise Exception("Duplicate RunLog entries with name " + str(name) + "!")
    self.entries[name] = entry

  def entryToDict(self, entry):
    contents = {}
    entryType = entry.getType()
    contents["type"] = entryType
    contents["name"] = entry.name
    if entryType == "market":
      contents["purchased"] = self.offeringFactory.offeringsToDict(entry.purchased)
      contents["remaining"] = self.offeringFactory.offeringsToDict(entry.remaining)
      return contents
    if entryType == "competition":
      contents["successful"] = entry.successful
      return contents
    if entryType == "conclusion":
      contents["successful"] = entry.successful
      return contents
    raise Exception("Unrecognized entry type '" + entryType + "'")

  def dictToEntry(self, contents):
    entryType = contents["type"]
    name = contents["name"]
    if entryType == "market":
      purchased = self.offeringFactory.parseOfferings(contents["purchased"])
      remaining = self.offeringFactory.parseOfferings(contents["remaining"])
      return RunLogShopEntry(name, purchased, remaining)
    if entryType == "competition":
      return RunLogCompetitionEntry(name, contents["successful"])
    if entryType == "conclusion":
      return RunLogConclusionEntry(name, contents["successful"])
    raise Exception("Unrecognized entry type '" + entryType + "'")

  def load(self):
    for file in self.getFiles():
      self.loadFile(file)

  def getFiles(self):
    filenames = os.listdir(self.filepath)
    results = [os.path.join(self.filepath, filename) for filename in filenames]
    return results

  def loadFile(self, file):
    contents = self.readFile(file)
    entry = self.dictToEntry(contents)
    self.putEntryInMemory(entry)

  def readFile(self, file):
    with open(file) as f:
      return json.load(f)

  def writeEntry(self, entry):
    path = os.path.join(self.filepath, entry.getType() + "-" + entry.name)

    if os.path.exists(path):
      raise Exception("File exists: " + str(path))
    content = self.entryToDict(entry)
    text = json.dumps(content, indent = 2)
    with open(path, 'w') as f:
      f.write(text)

  def getEntries(self):
    return self.entries.values()

# Keeps track of the versions of player data across games
# Doesn't actually save the player data: that still has to be done by other classes
class Profile(object):
  def __init__(self, filepath):
    self.dataDir = filepath
    self.metadataPath = os.path.join(self.dataDir, "metadata")
    self.versions = {}
    self.targetNumBackups = 10
    if os.path.isfile(self.metadataPath):
      self.load()

  # gets the filepath to use for the next version of the given service
  def getNextFilepath(self, name):
    return self.getServiceVersionPath(name, self.getNextVersion(name))

  # Increments the stored version to use for the given service
  # Should only be called after data has already been saved for that service
  def incrementVersion(self, name):
    self.versions[name] = self.getNextVersion(name)

  # gets the latest filepath for a service
  def getLatestPath(self, name):
    version = self.getVersion(name)
    return self.getServiceVersionPath(name, version)

  # gets the version to use for the next version of the given service
  def getNextVersion(self, name):
    return self.getVersion(name) + 1

  # gets the latest version of a service
  def getVersion(self, name):
    if name not in self.versions:
      self.versions[name] = 1
    return self.versions[name]

  # gets the filepath for a service
  def getServiceVersionPath(self, name, version):
    return os.path.join(self.getServicePath(name), str(version))

  def load(self):
    try:
      self.versions = self.readFile()
    except Exception as e:
      raise Exception("Failed to read " + str(self.metadataPath), e)
    try:
      self.validate()
    except Exception as e:
      raise Exception("Loaded data is not valid! try inspecting " + str(self.dataDir) + " to see if the data can be recovered", e)

  # verifies that we have data for each service
  def validate(self):
    for key in self.versions.keys():
      path = self.getLatestPath(key)
      if not os.path.exists(path):
        raise Exception("Path does not exist: " + path)

  def readFile(self):
    print("Loading profile data from " + str(self.metadataPath))
    with open(self.metadataPath) as f:
      return json.load(f)

  def write(self):
    text = json.dumps(self.versions, indent = 2)
    with open(self.metadataPath, 'w') as f:
      f.write(text)

  def save(self):
    try:
      self.validate()
    except Exception as e:
      raise Exception("Internal error: must save service data before saving Profile data", e)
    self.write()
    self.garbageCollect()

  def garbageCollect(self):
    for name in self.versions.keys():
      savedVersions = self.listSavedVersions(name)
      latestVersion = self.versions[name]
      if latestVersion not in savedVersions:
        raise Exception("error in garbage collection: version '" + str(latestVersion) + "' not found in versions " + str(savedVersions) + " for service " + str(name))
      for version in savedVersions:
        if version < latestVersion - self.targetNumBackups:
          self.removeServiceVersion(name, version)

  def removeServiceVersion(self, name, version):
    path = self.getServiceVersionPath(name, version)
    if os.path.isfile(path):
      os.remove(path)
    else:
      shutil.rmtree(path)

  def getServicePath(self, serviceName):
    return os.path.join(self.dataDir, serviceName)

  def listSavedVersions(self, serviceName):
    files = os.listdir(self.getServicePath(serviceName))
    return [int(file) for file in files]
