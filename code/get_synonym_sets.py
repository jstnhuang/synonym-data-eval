import constants
import crosswikis as cw
import myutils

TEST_SET_PATH = constants.DATA_PATH + 'cwel-test-set'
STRING_COUNTS_PATH = constants.RESULTS_PATH + 'openie-counts'

MY_RESULTS_PATH = constants.RESULTS_PATH + 'cwel/'
LINK_STATS_PATH= MY_RESULTS_PATH + '1-link-stats.tsv'
PR_OUTPUT_PATH = MY_RESULTS_PATH + '2-cwel-entity-sets-pr.tsv'
SYNSETS_OUTPUT_PATH = constants.RESULTS_PATH + '2-cwel-entity-sets.tsv'
PR_DEDUPED_PATH = MY_RESULTS_PATH + '3-cwel-pr-deduped.tsv'

def readStringCountsFile(stringCountsFile):
  """Reads the Open IE string counts file and returns its contents.

  Args:
    stringCountsFile: A file with links of the form
      {string}{TAB}{Open IE tuple count}.

  Returns: a dict mapping strings to their Open IE tuple counts.
  """
  stringCounts = {}
  for line in stringCountsFile:
    tabParts = [part.strip() for part in line.split('\t')]
    string = tabParts[0]
    count = int(tabParts[1])
    stringCounts[string] = count
  return stringCounts

def getLinkRow(table, entity, string):
  """Queries the given crosswikis table for an entity and a string.
  
  Assumes the string is case-insensitive.

  Returns: a tuple with the cprob, numerator, and denominator of that link.
  """
  queryString = (
    'SELECT anchor, entity, info, cprob '
    'FROM {table} '
    'WHERE entity=? AND anchor=? COLLATE NOCASE'
  ).format(table=table)
  results = [
    row for row in
    cw.query(queryString, (entity, string))
  ]
  results = cw.aggregateResults(results)
  if len(results) == 0:
    print('No results when querying entity/string pair.')
    return 0, 0, None
  string, entity, cprob, num, denom = results[0]
  return cprob, num, denom

def getLinkStats():
  """Retrieves stats for each (entity, string) pair in the test set.

  For each (entity, string) pair, return:
    p(entity|string),
    p(string|entity),
    the count of the pair in Crosswikis,
    the number of Open IE tuples the string appears in, and

  Save the results to disk and return the data as a list of tuples (in the above
  order).

  Returns: a list of tuples of the form (entityCprob, stringCprob, cwCount,
    tupleCount, tupleCountNorm)
  """
  testSetFile = open(TEST_SET_PATH)
  stringCountsFile = open(STRING_COUNTS_PATH)
  stringCounts = readStringCountsFile(stringCountsFile)
  linkStatsFile = open(LINK_STATS_PATH, 'w')
    
  print('Entity\tString\tP(Entity|String)\tP(String|Entity)\tCrosswikis count'
    '\tTuple count', file=linkStatsFile, flush=True)
  for line in testSetFile:
    lineParts = [part.strip() for part in line.split('\t')]
    entity = lineParts[0]
    string = lineParts[1]
    correct = True if lineParts[2] == '1' else False
    
    print('Getting data on ({}, {})'.format(entity, string))
    
    tupleCount = stringCounts[string]
    if tupleCount < 10:
      continue

    cprob, cwCount, cwDenom = getLinkRow('crosswikis_subset', entity, string)
    invCprob, invCwCount, invCwDenom = getLinkRow(
      'crosswikis_inv_subset',
      entity,
      string
    )

    print('{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(
        entity,
        string,
        1 if correct else 0,
        cprob,
        invCprob,
        cwCount,
        tupleCount,
      ),
      file=linkStatsFile,
      flush=True
    )

def linkStringToEntity(string, cprobThreshold=0.9, countThreshold=1000,
    tupleThreshold=500):
  """Gets the entity most likely to be referred to by the given string.

  Args: string: The string to get the entity link for.
    cprobThreshold: The minimum probability of the entity given the string we
      want.
    countThreshold: The minimum count of the entity we want.

  Returns: The most likely entity given the string, or None if no entity was
    found with high enough threshold.
  """
  entityDistribution = cw.getEntityDistribution(
    string,
    table='crosswikis_subset'
  )
  entityDistribution = [
    (ent, num, denom, cprob) for (ent, num, denom, cprob) in entityDistribution
    if cprob > cprobThreshold and num > countThreshold
  ]

  return entityDistribution[0] if len(entityDistribution) > 0 else None

def readLinkStatsFile(linkStatsFile):
  """Reads the link stats file and returns a list of tuples with its contents.

  Args:
    linkStatsFile: A file with the link stats in in, generated by getLinkStats()

  Returns: a list of tuples, each of the form: (entity, string, isCorrect,
    cprob, invCprob, cwCount, tupleCount, tc)
  """
  next(linkStatsFile) # Ignore column headers.
  results = []
  for line in linkStatsFile:
    linkParts = [part.strip() for part in line.split('\t')]
    entity = linkParts[0]
    string = linkParts[1]
    isCorrect = True if linkParts[2] == '1' else False
    cprob = float(linkParts[3])
    invCprob = float(linkParts[4])
    cwCount = int(linkParts[5])
    tupleCount = int(linkParts[6])
    results.append(
      (entity, string, isCorrect, cprob, invCprob, cwCount, tupleCount)
    )
  return results

def runExperiment(linkStats, cprobThreshold, countThreshold, tupleThreshold):
  returnedCount = 0
  correctCount = 0
  totalCorrectCount = 0
  synset = []

  for line in linkStats:
    entity, string, isCorrect, cProb, invCProb, cwCount, tupleCount = line
    totalCorrectCount += isCorrect
    if (cProb > cprobThreshold
        and cwCount > countThreshold
        and tupleCount > tupleThreshold):
      returnedCount += 1
      if isCorrect:
        correctCount += 1
        synset.append((entity, string, 1 if isCorrect else 0))
  precision = correctCount / returnedCount if returnedCount != 0 else None
  recall = correctCount / totalCorrectCount
  return precision, recall, synset

def tryThresholds():
  """Sweep thresholds and compute the precision and recall.

  Outputs the synonym sets generated to a file according to runExperiment().

  Returns: a list of tuples of the form (cprobThreshold, countThreshold,
    tupleThreshold, precision, recall).
  """
  linkStatsFile = open(LINK_STATS_PATH)
  linkStats = readLinkStatsFile(linkStatsFile)
  prOutputFile = open(PR_OUTPUT_PATH, 'w')
  synsetsFile = open(SYNSETS_OUTPUT_PATH, 'w')

  cprobThresholds = [x/100 for x in range(0, 100, 5)]
  countThresholds = [10, 100, 500, 1000, 1500, 2000, 4000, 10000]
  tupleThresholds = range(10, 2000, 100)
  results = []

  for p in cprobThresholds:
    for c in countThresholds:
      for t in tupleThresholds:
        print('p={}, c={}, t={}'.format(p, c, t))
        precision, recall, synset = runExperiment(linkStats, p, c, t)

        print('{}\t{}\t{}\t{}\t{}'.format(p, c, t, precision, recall),
          file=prOutputFile,
          flush=True
        )
        results.append((p, c, t, precision, recall))

  return results

def readPrFile(prFile):
  results = []
  for line in prFile:
    lineParts = [part.strip() for part in line.split('\t')]
    p = lineParts[0]
    c = lineParts[1]
    t = lineParts[2]
    precision = lineParts[3]
    recall = lineParts[4]
    results.append((p, c, t, precision, recall))
  return results

def dedupePr():
  prFile = open(PR_OUTPUT_PATH)
  dedupedPrFile = open(PR_DEDUPED_PATH, 'w')
  prResults = readPrFile(prFile)
  prCounts = {}
  prParams = {}
  for p, c, t, precision, recall in prResults:
    myutils.addToDict(prCounts, (precision, recall), 1)
    prParams[(precision, recall)] = 'p={}, c={}, t={}'.format(p, c, t)
  for ((precision, recall), count) in prCounts.items():
    paramString = prParams[(precision, recall)]
    print('{}\t{}\t{}\t{}'.format(
        paramString,
        precision,
        recall,
        count
      ),
      file=dedupedPrFile
    )
     
def main():
  # Step 1: get (entity, anchor, correct) tuples from test set and join it with
  # stats on the (entity, anchor) link.
#  linkStats = getLinkStats()

  # Step 2: try to maximize
#  prResults = tryThresholds()

  dedupePr()

if __name__ == '__main__':
  main()
