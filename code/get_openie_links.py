# Evaluates the synonyms from the current Open IE entity linker.
import os
import re

SYNONYM_DEV_SET_PATH = ('/home/jstn/research/knowitall/synonym-data-eval/data/'
  'odd-synonym-dev-set')
OPENIE_BACKEND_JAR_PATH = ('/home/jstn/research/knowitall/openie-backend/'
  'target/openiedemo-backend-1.0.2-SNAPSHOT-jar-with-dependencies.jar')
OPENIE_ENTITYLINKS_PATH = ('/home/jstn/research/knowitall/synonym-data-eval/'
  'results/openie-odd-entitylinks')

def getTestSynonyms(testSetFile):
  """Gets dicts for fbids, entities and synonyms from the test set file.

  Args:
    testSetFile: A tab-separated file with the first column being the Freebase
      ID of the entity, first column being the canonical Wikipedia article name,
      and all subsequent columns being possible synonyms for that entity.

  Returns: A dict mapping fbids to entity names, and a dict mapping the entity's
    Wikipedia article name and the set of synonyms for that entity.
  """
  testSet = {}
  fbidToEntityMap = {}
  for line in testSetFile:
    lineParts = [part.strip() for part in line.split('\t')]
    lineParts = [part for part in lineParts if part != '']
    fbid = lineParts[0]
    entity = lineParts[1]
    synonyms = lineParts[2:]
    testSet[entity] = set(synonyms)
    if fbid not in fbidToEntityMap:
      fbidToEntityMap[fbid] = entity
  return fbidToEntityMap, testSet

def getEntityLinks(testSet):
  """Queries the Open IE backend for synonyms and saves the output to a file.

  Args:
    testSet: A dict mapping the entity's Wikipedia article name to the set of
      synonyms for that entity.
    entityLinksFile: The file the results should be written to.
  """
  testSetSize = len(testSet)
  for index, (entity, synonyms) in enumerate(testSet.items(), start=1):
    print ("Querying synonyms for {entity} ({index} of {size})".format(
      entity=entity, index=index, size=testSetSize))
    for synonym in synonyms:
      command = ('java -jar {jarFile} --arg{argn} "{string}" --noInst '
        '--tabOutput '
        '| cut -d"	" -f{fields} '
        '| grep -v ".*ExtractionGroupFetcher.*"'
        '>> {outputPath}')
      arg1Command = command.format(
        jarFile=OPENIE_BACKEND_JAR_PATH,
        argn=1,
        string=synonym,
        fields='1,4',
        outputPath=OPENIE_ENTITYLINKS_PATH)
      arg2Command = command.format(
        jarFile=OPENIE_BACKEND_JAR_PATH,
        argn=2,
        string=synonym,
        fields='3,5',
        outputPath=OPENIE_ENTITYLINKS_PATH)
      os.system(arg1Command)
      os.system(arg2Command)

def addToDistribution(distribution, key, distKey):
  """Adds distKey to the distribution map with some key.

  Here, we have a dictionary that maps a string (the synonym) with another
  dictionary. In that dictionary, it maps the Wikipedia entity the synonym
  linked to with the number of times we've seen that entity. Hence, this adds
  one to the count of entities (distKey) we've seen linked to some synonym
  (key).

  Args:
    distribution: A dictionary that maps synonyms to dictionaries, where the
      inner dictionary maps entities to the count of how many times we've seen
      that entity linked to that synonym.
    key: The synonym.
    distKey: The entity.
  """
  if key not in distribution:
    distribution[key] = {distKey: 1}
  else:
    if distKey not in distribution[key]:
      distribution[key][distKey] = 1
    else:
      distKeyCount = distribution[key][distKey]
      distribution[key][distKey] = distKeyCount + 1

def getFbidDistribution(testSet):
  """Computes the distribution of entities linked to for each synonym.

  Args:
    testSet: The set of entities/synonyms to examine.

  Returns: A dictionary that maps synonyms to dictionaries, where the inner
    dictionary maps entities to the count of how many times we've seen that
    entity linked to that synonym.
  """
  entityLinksFile = open(OPENIE_ENTITYLINKS_PATH)
  fbidDistribution = {}
  for line in entityLinksFile:
    lineParts = line.split('\t')
    synonym = lineParts[0]
    entityInfoString = lineParts[1].strip()
    if entityInfoString != 'X':
      entityInfo = entityInfoString.split(',')
      entity = entityInfo[0]
      fbid = entityInfo[1]
      addToDistribution(fbidDistribution, synonym, entity)
  return fbidDistribution

def main():
  """Run this program twice. First, uncomment getEntityLinks, and comment
  everything below it out. This will generate a file with all the entity links
  in it. Then, comment out getEntityLinks and uncomment everything else. This
  will print out the results. It's probably better to output this to a file as
  well, but you can just use > outputFile yourself.
  """
  testSetFile = open(SYNONYM_DEV_SET_PATH, 'r')
  fbidToEntityMap, testSet = getTestSynonyms(testSetFile)

  # Only run this as needed! Takes a while.
  getEntityLinks(testSet)

#  fbidDistribution = getFbidDistribution(testSet)
#  for synonym, dist in fbidDistribution.items():
#    print(synonym)
#    for fbid, count in dist.items():
#      entity = fbidToEntityMap[fbid] if fbid in fbidToEntityMap else fbid
#      print('  {entity}: {count}'.format(entity=entity, count=count))

if __name__ == '__main__':
  main()
