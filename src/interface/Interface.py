#!python

import os

class InputUtils(object):
  def __init__(self):
    self.pendingSelections = []
    self.saveToPath = None
    self.wasLastDecisionReplayed = True

  def getWasLastDecisionReplayed(self):
    return self.wasLastDecisionReplayed

  def setPath(self, path):
    if os.path.exists(path):
      self.loadPath(path)
    else:
      os.makedirs(os.path.dirname(path), exist_ok = True)
      with open(path, 'w') as file:
        file.write("")
    self.saveToPath = path

  def loadPath(self, path):
    with open(path) as file:
      for line in file:
        self.pendingSelections.append(line.rstrip())

  def addPendingSelections(self, pendingSelections):
    self.pendingSelections += pendingSelections

  # choices is a Map<Float, String> and this returns the Float key
  def getInput(self, choices):
    if len(self.pendingSelections) > 0:
      self.wasLastDecisionReplayed = True
      preselection = self.pendingSelections[0]
      del self.pendingSelections[0]
      for key, value in choices.items():
        if preselection == str(value):
          return key
      raise Exception("Cannot find '" + str(preselection) + "' in " + str(choices))
    self.wasLastDecisionReplayed = False
    while True:
      if len(choices) == 1:
        # there's only one choice so we return it
        for key, value in choices.items():
          return key
      choiceText = input("")
      try:
        number = float(choiceText)
      except Exception as e:
        print("Choose a number!")
        continue
      if number not in choices:
        print("Choose an option!")
        continue
      self.recordInput(choices[number])
      return number

  def pause(self, messageText):
    if len(self.pendingSelections) > 0:
      print(messageText)
      del self.pendingSelections[0]
    else:
      input(messageText)
      self.recordInput("")

  def recordInput(self, selection):
    if self.saveToPath is not None:
      with open(self.saveToPath, 'a') as file:
        file.write(str(selection) + "\n")

inputUtils = InputUtils()
