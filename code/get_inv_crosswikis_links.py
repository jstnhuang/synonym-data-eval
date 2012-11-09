# Gets the distribution of entities the Crosswikis data links to. Recomputes the
# conditional probabilities of those entities after ignoring case. Gets test
# synonyms from a file.

import re
import sqlite3

ENTITY_DEV_SET_PATH =(
  '/home/jstn/research/knowitall/synonym-data-eval/data/odd-entity-dev-set'
)
CROSSWIKIS_DB_PATH = (
  '/home/jstn/research/knowitall/synonym-data-eval/data/google-crosswikis/'
  'synonyms.db'
)
ENTITY_SYNONYM_DIST_PATH = (
  '/home/jstn/research/knowitall/synonym-data-eval/results/'
  'cw-odd-inv-entity-dist.tsv'
)

def getTestEntities(testSetFile):
  """Gets a dict mapping entities to synonyms from the test set file.

  Args:
    testSetFile: A tab-separated file with the first column being the Freebase
      ID of the entity, first column being the canonical Wikipedia article name,
      and all subsequent columns being possible synonyms for that entity.

  Returns: A dict mapping the entity's Wikipedia article name and the set of
    synonyms for that entity.
  """
  testSet = {}
  for line in testSetFile:
    lineParts = [part.strip() for part in line.split('\t')]
    lineParts = [part for part in lineParts if part != '']
    entity = lineParts[0]
    synonyms = lineParts[1:]
    testSet[entity] = set(synonyms)
  return testSet

def parseRowInfo(info):
  """Gets the numerator of a link from the row's info string.

  We will combine the numerators from the W, Wx, w, and w' labels. Each label is
  of the form W:152/69814.

  Args:
    info: The info string.

  Returns: The total numerator.
  """
  numerator = 0
  labels = ['W:', 'Wx:', 'w:', 'w\':']
  for label in labels:
    match = re.search('{label}(\d+)/\d+'.format(label=label), info)
    if match is not None:
      numerator += int(match.group(1))
  return numerator

def addToDictCount(dictionary, key, num):
  """Adds or inserts a numerator to the key's count.

  Args:
    dictionary: A dict that maps keys to a count.
    key: The entity to map.
    num: The count to add.
  """
  if key in dictionary:
    count = dictionary[key]
    dictionary[key] = count + num
  else:
    dictionary[key] = num

def getAnchorDistribution(entity, cursor):
  """Gets the distribution of synonyms linked to the entities in crosswikis_inv.

  Queries the Crosswikis data for the entity we're interested in, and gets a
  list of synonyms associated with it and their counts.

  Args:
    entity: The string to search for.
    cursor: The sqlite3 database cursor.

  Returns: A list of (synonym, num, denom) tuples, sorted in descending order of
    conditional probability (num / denom).
  """
  query = (
    'SELECT anchor, entity, info '
    'FROM crosswikis_inv '
    'WHERE entity=? COLLATE NOCASE'
  )
  anchorCounts = {}

  for anchor, entity, info in cursor.execute(query, (entity,)):
    print('a={}, e={}, i={}'.format(anchor, entity, info))
    num = parseRowInfo(info)
    addToDictCount(anchorCounts, anchor.lower(), num)

  denom = sum(anchorCounts.values())
  anchorDistribution = list(anchorCounts.items())
  anchorDistribution = [
    (anchor, num, denom) for (anchor, num) in anchorDistribution
  ]
  sortedAnchorDistribution = sorted(
    anchorDistribution,
    key=(lambda item: 0 if item[2] == 0 else item[1]/item[2]),
    reverse=True
  )
  return sortedAnchorDistribution

def printAnchorDistribution(entity, anchorDistribution):
  """Print the anchor distribution to a file.

  The output is tab delimited, so you can load it into a spreadsheet as well.

  Args:
    entity: The entity we're looking up.
    anchorDistribution: A list of (anchor, num, denom) tuples. The list is
      sorted in descending order of conditional probability (num / denom).
  """
  outputFile = open(ENTITY_SYNONYM_DIST_PATH, 'a')
  for (anchor, num, denom) in anchorDistribution:
    print('{0}\t{1}\t{2}\t{3}\t{4}'.format(
        entity,
        anchor,
        (None if denom is 0 else num/denom),
        num,
        denom),
      file=outputFile,
      flush=True
    )
 
def main():
  testSetFile = open(ENTITY_DEV_SET_PATH)
  testSet = getTestEntities(testSetFile)
  connection = sqlite3.connect(CROSSWIKIS_DB_PATH)
  cursor = connection.cursor()

  for entity in testSet.keys():
    print(entity)
    anchorDistribution = getAnchorDistribution(entity, cursor)
    printAnchorDistribution(entity, anchorDistribution)

  connection.commit()
  connection.close()

if __name__ == '__main__':
  main()
