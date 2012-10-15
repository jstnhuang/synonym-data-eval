# Evaluates the entity links found using get_crosswikis_links.py. Each line in
# the data it generated is of the form:
# {Correct link}\t{Synonym}\t{Entity linked to by synonym}\t{Probability}
# \t{Count for entity}\t{Count for synonym}
#
# The conditional probability is just the 2nd to last column divided by the last
# column. We want to see how many of these entities were correctly linked, and
# with what probability.

import re
import sqlite3

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

def printCorrectLinkData(cwLinkData):
  """Prints the link data for when a correct link was made.

  Args:
    cwLinkData: A dict with correctEntity as the key, that maps to nested dicts
      with the synonym as the key, which maps to a list of (entity, cprob, num,
      denom) tuples.
  """
  for correctEntity, synonymEntities in cwLinkData.items():
    for synonym, entityList in synonymEntities.items():
      for index, (entity, cprob, num, denom) in enumerate(entityList, start=1):
        if entity == correctEntity:
          printLink(entity, synonym, cprob, index)

def main():
  cwLinkFile = open(SYNONYM_ENTITY_DIST_PATH)
  cwLinkData = makeLinkData(cwLinkFile)
  printCorrectLinkData(cwLinkData)

if __name__ == '__main__':
  main()
