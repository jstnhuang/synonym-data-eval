import sqlite3
import constants
import crosswikis as cw

TEST_SET_PATH = constants.DATA_PATH + 'cwel-test-set'
OUTPUT_PATH = constants.RESULTS_PATH + 'cwel-2entity-set'

def getTestData():
  """Gets all the strings that could link to a small number of entities.
  
  Returns:
    A dict mapping the entities to the strings that could link to it.
  """
  possibleStrings = {}
  correctMap = {}
  file = open(TEST_SET_PATH)
  for line in file:
    parts = line.split('\t')
    entity = parts[0]
    string = parts[1].strip()
    correct = True if int(parts[2]) == 1 else False
    correctMap[(entity, string)] = correct
    if entity in possibleStrings:
      possibleStrings[entity].append(string)
    else:
      possibleStrings[entity] = [string]
  return possibleStrings, correctMap

def linkStringToEntity(string, cprobThreshold=0.9, countThreshold=1000):
  """Gets the entity most likely to be referred to by the given string.

  Args:
    string: The string to get the entity link for.
    cprobThreshold: The minimum probability of the entity given the string we
      want.
    countThreshold: The minimum count of the entity we want.

  Returns: The most likely entity given the string, or None if no entity was
    found with high enough threshold.
  """
  entityDistribution = cw.getEntityDistribution(
    string,
    table='crosswikis_2ents'
  )
  entityDistribution = [
    (ent, num, denom, cprob) for (ent, num, denom, cprob) in entityDistribution
    if cprob > cprobThreshold and num > countThreshold
  ]
  if len(entityDistribution) > 0:
    print(string)

  return entityDistribution[0] if len(entityDistribution) > 0 else None

def runExperiment(possibleStrings, correctMap, cprobThreshold, countThreshold):
  numCorrect = len([x for x in correctMap.values() if x is True])
  returnedResults = 0
  correctResults = 0

  for origEntity, strings in possibleStrings.items():
    stringsLen = len(strings)
    for index, string in enumerate(strings, start=1):
      value = linkStringToEntity(
        string,
        cprobThreshold=cprobThreshold,
        countThreshold=countThreshold
      )
      if value is not None:
        entity, num, denom, cprobs = value
        returnedResults += 1
        if (entity, string) in correctMap and correctMap[(entity, string)]:
          correctResults += 1
  precision = correctResults / returnedResults if returnedResults != 0 else None
  recall = correctResults / numCorrect
  return precision, recall

def main():
  """Generates synonym sets for a small number of entities."""
  possibleStrings, correctMap = getTestData()
  outputFile = open(OUTPUT_PATH, 'w')

  for cprobThreshold in [x/100 for x in range(50, 100, 5)]:
    for countThreshold in [100*x for x in range(1, 11, 3)]:
  #for cprobThreshold in [x/100 for x in range(1)]:
  #  for countThreshold in [100*x for x in range(1)]:
      print('cprobThreshold={}, countThreshold={}'.format(
          cprobThreshold, countThreshold
        )
      )
      precision, recall = runExperiment(
        possibleStrings, correctMap, cprobThreshold, countThreshold
      )
      print('{}\t{}\t{}\t{}'.format(
          cprobThreshold, countThreshold, precision, recall),
        file=outputFile)

if __name__ == '__main__':
  main()
