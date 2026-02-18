#!python

import json, os, random, shutil, textwrap

# information about an item
class ItemData(object):
  def __init__(self, item, name, popularity, complexity, cost):
    self.item = item.clone()
    self.name = name
    self.popularity = popularity
    self.complexity = complexity
    self.cost = cost

  def clone(self):
    return ItemData(self.item, self.name, self.popularity, self.complexity, self.cost)

# a collection of ItemData
class ItemDataFactory(object):
  def __init__(self):
    self.contents = []
    self.contentsByName = {}

  def add(self, item, popularity, complexity, baseCost):
    name = type(item).__name__
    self.addItemData(ItemData(item, name, popularity, complexity, baseCost))

  def addItemData(self, itemData):
    name = itemData.name
    if name in self.contentsByName:
      index = 2
      while (name + str(index)) in self.contentsByName:
        index += 1
      name = name + str(index)
    itemData.name = name
    self.contents.append(itemData)
    self.contentsByName[itemData.name] = itemData

  def cloneItemNamed(self, name):
    result = self.contentsByName.get(name)
    if result is None:
      raise Exception("'" + str(name) + "' not found in " + str(list(self.contentsByName.keys())))
    return result.item.clone()

  def getAll(self):
    return self.contents[:]

  def cloneAndMutateRandomItem(self):
    index = random.randint(0, len(self.contents) - 1)
    mutated = self.mutateRandomly(self.contents[index], 0.1)
    self.addItemData(mutated)

  def mutateRandomly(self, itemData, maxFractionChange):
    result = itemData.clone()
    oldProperties = itemData.item.properties
    newProperties = {}
    for key in oldProperties.keys():
      value = oldProperties.get(key)
      fractionChange = random.uniform(-maxFractionChange, maxFractionChange)
      newProperties[key] = value * (1 + fractionChange)
    result.item.setProperties(newProperties)
    return result

  def parseItemDataList(self, jsonObjects):
    result = []
    for o in jsonObjects:
      result.append(self.parseItemData(o))
    return result

  def parseItemData(self, jsonObject):
    name = jsonObject["name"]
    item = self.cloneItemNamed(name)
    item.setProperties(jsonObject["properties"])
    popularity = jsonObject["popularity"]
    complexity = jsonObject["complexity"]
    cost = jsonObject["cost"]
    itemData = ItemData(item, name, popularity, complexity, cost)
    return itemData

  def itemDataToDict(self, itemData):
    result = {}
    result["type"] = type(itemData.item).__name__
    result["name"] = itemData.name
    result["popularity"] = itemData.popularity
    result["complexity"] = itemData.complexity
    result["cost"] = itemData.cost
    result["properties"] = itemData.item.properties
    return result

# a collection of ItemData saved to a file
class FileItemDataFactory(ItemDataFactory):
  def __init__(self, defaultFactory, filepath):
    super().__init__()
    self.defaultFactory = defaultFactory
    self.filepath = filepath
    if os.path.isfile(filepath):
      self.loadFile()
    else:
      self.loadDefaults()
      self.saveFile()

  def loadFile(self):
    json = self.readFile()
    items = self.defaultFactory.parseItemDataList(json)
    for item in items:
      self.addItemData(item)

  def readFile(self):
    with open(self.filepath) as f:
      return json.load(f)

    return # not implemented yet

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
      components.append(self.itemDataToDict(component))
    return json.dumps(components, indent = 2)

  def loadDefaults(self):
    for itemData in self.defaultFactory.getAll():
      self.addItemData(itemData)

# stores information about something from the player's run
class RunLogEntry(object):
  def __init__(self, name, content):
    self.name = name
    self.content = content

# saves information about the player's current run
class RunLog(object):
  def __init__(self, filepath):
    self.filepath = filepath
    self.entries = {}
    os.makedirs(self.filepath, exist_ok = True)

  def clear(self):
    self.entries = []
    for file in self.getFiles():
      os.remove(file)

  def addEntry(self, entry):
    self.putEntryInMemory(entry)
    entryPath = os.path.join(self.filepath, name)
    self.writeEntry(entryPath, entry)

  def putEntryInMemory(self, entry):
    name = entry.name
    self.entries[name] = entry

  def load(self):
    for file in self.getFiles():
      self.loadFile(file)

  def getFiles(self):
    filenames = os.path.listdir(self.filepath)
    results = [os.path.join(self.filepath, filename) for filename in filenames]
    return results

  def loadFile(self, file):
    entry = self.readFile(file)
    self.addEntry(entry)

  def readFile(self, file):
    with open(self.filepath) as f:
      return json.load(f)

  def writeEntry(self, path, entry):
    if os.path.exists(path):
      raise Exception("File exists: " + str(self.path))
    text = json.dumps(entry, indent = 2)
    with open(path, 'w') as f:
      f.write(text)

# Keeps track of the versions of player data across games
# Doesn't actually save the player data: that still has to be done by other classes
class Profile(object):
  def __init__(self, filepath):
    self.dataDir = filepath
    self.metadataPath = os.path.join(self.dataDir, "metadata")
    self.versions = {}
    self.targetNumBackups = 1
    if os.path.isfile(self.metadataPath):
      self.load()

  # gets the filepath to use for the next version of the given service
  def getNextFilepath(self, name):
    return self.getServiceVersionPath(name, self.getNextVersion(name))

  # Increments the stored version to use for the given service
  # Should only be called after data has already been saved for that service
  def incrementVersion(self, name):
    self.versions[name] = self.getNextVersion(name)
    self.save()

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
    self.validate()

  # verifies that we have data for each service
  def validate(self):
    for key in self.versions.keys():
      path = self.getLatestPath(key)
      if not os.path.exists(path):
        raise Exception("Path does not exist: " + path + "! Try inspecting " + str(self.dataDir) + " to see if the data can be recovered")

  def readFile(self):
    print("Loading profile data from " + str(self.metadataPath))
    with open(self.metadataPath) as f:
      return json.load(f)

  def write(self):
    text = json.dumps(self.versions, indent = 2)
    with open(self.metadataPath, 'w') as f:
      f.write(text)

  def save(self):
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
      print("shutil.rmtree " + str(path))
      #shutil.rmtree(path)

  def getServicePath(self, serviceName):
    return os.path.join(self.dataDir, serviceName)

  def listSavedVersions(self, serviceName):
    files = os.listdir(self.getServicePath(serviceName))
    return [int(file) for file in files]
