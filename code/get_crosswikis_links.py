# Gets the distribution of entities the Crosswikis data links to. Recomputes the
# conditional probabilities of those entities after ignoring case. Gets test
# synonyms from a file.

import re
import sqlite3

SYNONYM_DEV_SET_PATH =(
  '/home/jstn/research/knowitall/synonym-data-eval/data/odd-synonym-dev-set'
)
CROSSWIKIS_DB_PATH = (
  '/home/jstn/research/knowitall/synonym-data-eval/data/google-crosswikis/'
  'synonyms.db'
)
SYNONYM_ENTITY_DIST_PATH = (
  '/home/jstn/research/knowitall/synonym-data-eval/results/'
  'cw-odd-entity-dist.tsv'
)

def getTestSynonyms(testSetFile):
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
    fbid = lineParts[0]
    entity = lineParts[1]
    synonyms = lineParts[2:]
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

def addToEntityCount(entityCounts, entity, num):
  """Adds or inserts a numerator to the entity's count.

  Args:
    entityCounts: A dict that maps entities to the numerator count.
    entity: The entity to map.
    num: The numerator of the conditional probability.
  """
  if entity in entityCounts:
    currentNum = entityCounts[entity]
    entityCounts[entity] = currentNum + num
  else:
    entityCounts[entity] = num

def getEntityDistribution(synonym, cursor):
  """Gets the distribution of entities linked to the synonym in Crosswikis.

  Queries the Crosswikis data for the synonym we're interested in, and gets a
  list of entities associated with it and their counts.

  Args:
    synonym: The string to search for.
    cursor: The sqlite3 database cursor.

  Returns: A list of (entity, num, denom) tuples, sorted in descending order of 
    conditional probability (num / denom).
  """
  query = (
    'SELECT anchor, entity, info '
    'FROM crosswikis '
    'WHERE anchor=? COLLATE NOCASE'
  )
  # Crosswikis is case sensitive. To make this case insensitive, we sum the
  # numerators for unique synonym spellings and make that the denominator for
  # them all.
  entityCounts = {}

  for anchor, entity, info in cursor.execute(query, (synonym,)):
    num = parseRowInfo(info)
    addToEntityCount(entityCounts, entity, num)

  denom = sum(entityCounts.values())
  entityDistribution = list(entityCounts.items())
  entityDistribution = [
    (entity, num, denom) for (entity, num) in entityDistribution
  ]
  sortedEntityDistribution = sorted(
    entityDistribution,
    key=(lambda item: 0 if item[2] == 0 else item[1]/item[2]),
    reverse=True
  )
  return sortedEntityDistribution

def printEntityDistribution(correctEntity, synonym, entityDistribution):
  """Print the entity distribution to standard output.

  The output is tab delimited, so you can load it into a spreadsheet as well.

  Args:
    correctEntity: The correct entity for the synonym.
    synonym: The synonym we're evaluating.
    entityDistribution: A list of (entity, num, denom) tuples. The list is
      sorted in descending order of conditional probability (num / denom).
  """
  outputFile = open(SYNONYM_ENTITY_DIST_PATH, 'a')
  for (entity, num, denom) in entityDistribution:
    print('{0}\t{1}\t{2}\t{3}\t{4}\t{5}'.format(
        correctEntity,
        synonym,
        entity,
        (None if denom is 0 else num/denom),
        num,
        denom),
      file=outputFile,
      flush=True
    )

def main():
  testSetFile = open(SYNONYM_DEV_SET_PATH)
  testSet = getTestSynonyms(testSetFile)
  connection = sqlite3.connect(CROSSWIKIS_DB_PATH)
  cursor = connection.cursor()

  for entity, synonyms in testSet.items():
    print(entity)
    for synonym in synonyms:
      entityDistribution = getEntityDistribution(synonym, cursor)
      printEntityDistribution(entity, synonym, entityDistribution)

  connection.commit()
  connection.close()

if __name__ == '__main__':
  main()
