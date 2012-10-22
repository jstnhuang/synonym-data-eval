# Evaluates the entity links found using get_crosswikis_links.py. Each line in
# the data it generated is of the form:
# {Correct link}\t{Synonym}\t{Entity linked to by synonym}\t{Probability}
# \t{Count for entity}\t{Count for synonym}
#
# The conditional probability is just the 2nd to last column divided by the last
# column. We want to see how many of these entities were correctly linked, and
# with what probability.

SYNONYM_DEV_SET = (
  '/home/jstn/research/knowitall/synonym-data-eval/data/str-to-ents-dev-set'
)
SYNONYM_ENTITY_DIST_PATH = (
  '/home/jstn/research/knowitall/synonym-data-eval/results/cw-entity-dist.tsv'
)

def makeLinkData(cwLinkFile):
  """Turns a flat list of rows into a data structure of two nested dicts.

  Args:
    cwLinkFile: A file with columns correctEntity, synonym, entity, cprob, num,
      denom.

  Returns: A dict with correctEntity as the key, that maps to nested dicts with
    synonym as the key, which maps to a list of (entity, cprob, num, denom)
    tuples.
  """
  cwLinkData = {}
  for line in cwLinkFile:
    correctEntity, synonym, entity, cprob, num, denom = line.split('\t')
    cprob = float(cprob)
    num = int(num)
    denom = int(denom)
    entityTuple = (entity, cprob, num, denom)
    if correctEntity in cwLinkData:
      if synonym in cwLinkData[correctEntity]:
        cwLinkData[correctEntity][synonym].append(entityTuple)
      else:
        cwLinkData[correctEntity][synonym] = [entityTuple]
    else:
      cwLinkData[correctEntity] = {synonym: [entityTuple]}
  return cwLinkData

def getSynonymSet(synonymSetFile):
  """Reads a set of synonyms in a file where each line is of the form:
    {fbid}\t{entityName}\t{synonym1}\t{synonym2}\t...

    Args:
      synonymSetFile: The synonym set file.

    Returns:
      A dict mapping the entity name to its list of synonyms.
  """
  synonymSet = {}
  for line in synonymSetFile:
    lineParts = line.split('\t')
    lineParts = [part for part in lineParts if part != '' and part != '\n']
    lineParts = [part.strip() for part in lineParts]
    entityName = lineParts[1]
    synonyms = lineParts[2:]
    synonymSet[entityName] = synonyms
  return synonymSet

def printLink(entity, synonym, cprob, rank):
  """Prints an entity link from the Crosswikis data.

  Args:
    entity: The entity that was linked to.
    synonym: The string that linked to it.
    cprob: The probability of the entity given the string.
    rank: The rank (index+1) of the entity compared to all the other entities
      linked to the same synonym.
  """
  print('{entity}\t{synonym}\t{cprob}\t{rank}'.format(
      entity=entity,
      synonym=synonym,
      cprob=cprob,
      rank=rank
    )
  )

def printCorrectLinkData(synonymSet, cwLinkData):
  """Prints the link data for when a correct link was made.

  Args:
    cwLinkData: A dict with correctEntity as the key, that maps to nested dicts
      with the synonym as the key, which maps to a list of (entity, cprob, num,
      denom) tuples.
  """
  for correctEntity, synonymEntities in cwLinkData.items():
    for synonym, entityList in synonymEntities.items():
      if synonym in synonymSet[correctEntity]:
        for idx, (entity, cprob, num, denom) in enumerate(entityList, start=1):
          if entity == correctEntity:
            printLink(entity, synonym, cprob, idx)

def printRank1Links(synonymSet, cwLinkData):
  """Prints the most likely entity given a string, as well as its likelihood.

  Also prints out the ratio of the probability of the first entity to the
  probability of the second entity.

  Args:
    synonymSet: A dict mapping entities to its list of synonyms.
    cwLinkData: A dict with correctEntity as the key, that maps to nested dicts
      with the synonym as the key, which maps to a list of (entity, cprob, num,
      denom) tuples.
  """
  count = 0
  for correctEntity, synonyms in synonymSet.items():
    for synonym in synonyms:
      count += 1
      if synonym in cwLinkData[correctEntity]:
        entity, cprob, num, denom = cwLinkData[correctEntity][synonym][0]
        prob2Ratio = None
        if len(cwLinkData[correctEntity][synonym]) > 1:
          cprob2 = cwLinkData[correctEntity][synonym][1][1]
          prob2Ratio = cprob/cprob2 if cprob2 != 0 else 'Inf'
        print('{correct}\t{synonym}\t{entity}\t{cprob}\t{prob2Ratio}'.format(
            correct=correctEntity,
            synonym=synonym,
            entity=entity,
            cprob=cprob,
            prob2Ratio=prob2Ratio
          )
        )
      else:
        print('{correct}\t{synonym}\tNone'.format(
            correct=correctEntity,
            synonym=synonym
          )
        )

def evalRank1Test(synonymSet, cwLinkData):
  """Finds the precision and recall when we just pick the most likely entity.

  We pick the most likely entity in the distribution, but subject it to some
  cutoff c. We vary c from 0 to 0.95 in the outermost loop to see the effect of
  the cutoff on precision and recall.

  Args:
    synonymSet: A dict mapping entities to its list of synonyms.
    cwLinkData: A dict with correctEntity as the key, that maps to nested dicts
      with the synonym as the key, which maps to a list of (entity, cprob, num,
      denom) tuples.
  """
  numSynonyms = sum([len(list) for list in synonymSet.values()])
  print('CProb cutoff\tPrecision\tRecall')

  for cprobCutoff in [x/100 for x in range(0, 100, 5)]:
    numCorrect = 0
    numRetrieved = 0

    for correctEntity, synonymEntities in cwLinkData.items():
      for synonym, entityList in synonymEntities.items():
        if synonym not in synonymSet[correctEntity]:
          continue
        entity, cprob, num, denom = entityList[0]
        if cprob >= cprobCutoff:
          numRetrieved += 1
          if entity == correctEntity:
            numCorrect += 1
    precision = numCorrect / numRetrieved
    recall = numCorrect / numSynonyms
    print('{0}\t{1}\t{2}'.format(cprobCutoff, precision, recall))

def main():
  cwLinkFile = open(SYNONYM_ENTITY_DIST_PATH)
  cwLinkData = makeLinkData(cwLinkFile)
  synonymDevSetFile = open(SYNONYM_DEV_SET)
  synonymDevSet = getSynonymSet(synonymDevSetFile)

  evalRank1Test(synonymDevSet, cwLinkData)
  #printCorrectLinkData(synonymDevSet, cwLinkData)
  #print(sum([len(list) for list in synonymDevSet.values()]))
  #printRank1Links(synonymDevSet, cwLinkData)

if __name__ == '__main__':
  main()
