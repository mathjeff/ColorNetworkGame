#!python

class Menu(object):
  def __init__(self):
    return

  def getNext(self):
    return None

class ChoiceMenu(Menu):
  def __init__(self, text):
    super(ChoiceMenu).__init__()
    self.text = text
    self.choices = []

  def getNext(self):
    print(self.text)
    for i in range(len(self.choices)):
      option = self.choices[i][0]
      print(str(i) + ": " + option)
    choiceText = ""
    while True:
      choiceText = input("")
      number = 0
      try:
        number = int(choiceText)
      except Exception as e:
        print("Choose a number!")
        continue
      if number < 0:
        print("Choose a number >= 0")
        continue
      if number >= len(self.choices):
        print("Choose a number <= " + str(len(self.choices)))
        continue
      choice = self.choices[number]
      return choice[1]

  def addChoice(self, text, newMenu):
    self.choices.append((text, newMenu))

class MessageMenu(Menu):
  def __init__(self, text):
    super(MessageMenu).__init__()
    self.text = text
    self.nextNode = None

  def setNext(self, nextNode):
    self.next = nextNode

  def getNext(self):
    print(self.text)

  def getNext(self):
    print(self.text)
    input("")
    return self.nextNode

class MenuRunner(object):
  def __init__(self, startingMenu):
    self.currentMenu = startingMenu

  def run(self):
    while self.currentMenu is not None:
      self.currentMenu = self.currentMenu.getNext()

def makeStory():
  welcome = ChoiceMenu("Are you happy?")
  happy = MessageMenu("I'm glad that you're happy.")
  unhappy = MessageMenu("I hope you can be happy soon.")
  welcome.addChoice("yes", happy)
  welcome.addChoice("no", unhappy)
  return MenuRunner(welcome)

def main():
  runner = makeStory()
  runner.run()

if __name__ == "__main__":
  main()
