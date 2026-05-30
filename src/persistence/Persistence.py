#!python

from interface.Interface import *

import json, os, shutil, textwrap

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

  def __repr__(self):
    return "Offering name:" + str(self.name) + " cost:" + str(self.cost)

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

  def getNumOfferings(self):
    return len(self.getAll())

  def tryParseOfferings(self, jsonObjects):
    result = []
    for o in jsonObjects:
      try:
        result.append(self.parseOffering(o))
      except Exception as e:
        print("Failed to parse "  + str(o) + ": " + str(e) + ", ignoring")
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
      items.append(self.itemToDict(item))
    result["items"] = items
    return result

  def itemToDict(self, item):
    result = {}
    result["properties"] = item.properties
    result["type"] = type(item).__name__
    return result

  # makes a new factory based on the contents of the given path, or self if empty
  def withFileContents(self, path):
    if not os.path.exists(path):
      return self
    result = OfferingFactory()
    json = self.readFile(path)
    items = self.tryParseOfferings(json)
    for item in items:
      result.addOffering(item)
    return result

  def readFile(self, path):
    with open(path) as f:
      return json.load(f)

  def ensureSaved(self, path):
    if not os.path.exists(path):
      self.saveToFile(path)

  def saveToFile(self, path):
    if os.path.exists(path):
      raise Exception("File exists: " + str(path))
    parentPath = os.path.dirname(path)
    os.makedirs(parentPath, exist_ok = True)
    text = self.serialize()
    with open(path, 'w') as f:
      f.write(text)

  def serialize(self):
    components = []
    for component in self.getAll():
      components.append(self.offeringToDict(component))
    return json.dumps(components, indent = 2)

  # apply an OfferingsDelta and return a new OfferingFactory
  def withDelta(self, delta):
    newOfferings = delta.applyTo(self.getAll())
    newFactory = OfferingFactory()
    for offering in newOfferings:
      newFactory.addOffering(offering)
    return newFactory

# stores the difference between two OfferingFactory
class OfferingsDelta(object):
  def __init__(self, oldFactory, newFactory):
    self.newFactory = newFactory
    self.oldOfferings = oldFactory.getAll()
    self.newOfferings = newFactory.getAll()
    self.oldKeys = self.getKeys(self.oldOfferings)
    self.newKeys = self.getKeys(self.newOfferings)
    self.removedOfferings = [offering for offering in self.oldOfferings if self.getKey(offering) not in self.newKeys]
    self.addedOfferings = [offering for offering in self.newOfferings if self.getKey(offering) not in self.oldKeys]
    if self.nonempty():
      print("OfferingsDelta removed " + str(self.removedOfferings) + " added " + str(self.addedOfferings))

  def nonempty(self):
    return len(self.removedOfferings) > 0 or len(self.addedOfferings) > 0

  def getKey(self, offering):
    contents = [self.newFactory.itemToDict(item) for item in offering.items]
    return json.dumps(contents)

  def getKeys(self, offerings):
    result = set()
    for offering in offerings:
      result.add(self.getKey(offering))
    return result

  # apply this delta to a List<Offering> and return a new list
  def applyTo(self, offerings):
    results = []
    pendingAdds = self.addedOfferings[:]
    for i in range(len(offerings)):
      offering = offerings[i]
      key = self.getKey(offering)
      if key in self.oldKeys and key not in self.newKeys:
        # item was removed from the defaults
        print("OfferingsDelta applyTo removing " + str(offering))
        if len(pendingAdds) > 0:
          print("OfferingsDelta applyTo adding " + str(pendingAdds[0]))
          results.append(pendingAdds[0])
          pendingAdds = pendingAdds[1:]
      else:
        results.append(offering)
    if len(pendingAdds) > 0:
      print("OfferingsDelta applyTo adding " + str(pendingAdds))
    results += pendingAdds
    return results

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

  def newEntry(self, entry):
    if not inputUtils.getWasLastDecisionReplayed():
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
    lastNumber = 0
    for entry in self.entries.values():
      number = int(entry.name)
      if lastEntry is None or number > lastNumber:
        lastEntry = entry
        lastNumber = number
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
      purchased = self.offeringFactory.tryParseOfferings(contents["purchased"])
      remaining = self.offeringFactory.tryParseOfferings(contents["remaining"])
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
