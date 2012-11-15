import constants
import myutils
import re
import sqlite3

def getLabelCounts(info):
  """Gets the W, Wx, w, and w' values from the info string.

  Args:
    info: The info string.

  Returns:
    A dict mapping the label name (W, Wx, w, or w') to a (numerator,
    denominator) tuple.
  """
  labels = ['W:', 'Wx:', 'w:', 'w\':']
  labelCounts = {}
  
  for label in labels:
    match = re.search('{label}(\d+)/(\d+)'.format(label=label), info)
    if match is not None:
      numerator = int(match.group(1))
      denominator = int(match.group(2))
      labelCounts[label] = (numerator, denominator)
  return labelCounts 

def parseRawCrosswikisRow(row):
  """Parses the fields from a row in dictionary.
  
  Args:
    row: A row from dictionary as a string.
    
  Returns: A tuple of the form (anchor, cprob, entity, info).
  """
  tabParts = row.split('\t')
  anchor=tabParts[0]
  remainder = tabParts[1].split(' ')
  cprob = middleParts[0]
  entity = middleParts[1]
  info = ' '.join(middleParts[2:])
  return (anchor, cprob, entity, info)


def parseRawInvCrosswikisRow(row):
  """Parses the fields from a row in inv.dict.
  
  Args:
    row: A row from inv.dict as a string.
    
  Returns: A tuple of the form (entity, cprob, anchor, info).
  """
  tabParts = row.split('\t')
  entity=tabParts[0]
  middleParts = tabParts[1].split(' ')
  cprob = middleParts[0]
  anchor = ' '.join(middleParts[1:])
  info=tabParts[2]
  return (entity, cprob, anchor, info)

def query(queryString, args):
  """Executes the given query and yields the results.

  Args:
    queryString: The SQLite query string.
    args: A tuple with all the args to pass to the query string.

  Yields: The rows returned from the query.
  """
  connection = sqlite3.connect(constants.CROSSWIKIS_DB_PATH)
  cursor = connection.cursor()
  for row in cursor.execute(queryString, args):
    yield row
  connection.commit()
  connection.close()

def aggregateResults(results):
  """Aggregates results from crosswikis by ignoring case on the anchor.

  Numerators are added up, and probabilities are averaged, weighted by their
  numerators.

  Args:
    results: a results set of the form [(anchor, entity, cprob, num, denom)]

  Returns: a new results set of the form [(anchor, entity, cprob, num, denom)]
  """
  linkCounts = {}
  linkCprobs = {}
  for anchor, entity, info, cprob in results:
    anchor=anchor.lower()
    labelCounts = getLabelCounts(info)
    num = sum([num for (num, denom) in labelCounts.values()])
    myutils.addToDict(linkCounts, (anchor, entity), num)
    myutils.addToDict(linkCprobs, (anchor, entity), num*cprob)
  denom = sum(linkCounts.values())
  results = []
  for ((anchor, entity), num) in linkCounts.items():
    cprob = linkCprobs[(anchor, entity)] / denom
    results.append((anchor, entity, cprob, num, denom))
  return results

def getEntityDistribution(string, table='crosswikis'):
  """Gets the distribution of entities linked to the synonym in Crosswikis.

  Queries the Crosswikis data for the string we're interested in, and gets a
  list of entities associated with it and their counts.

  Args:
    string: The string to search for.
    table: The table to look for the string in.

  Returns: A list of (entity, cprob, num, denom) tuples, sorted in descending
    order of conditional probability.
  """
  queryString = (
    'SELECT anchor, entity, info, cprob '
    'FROM {table} '
    'WHERE anchor=? COLLATE NOCASE'
  ).format(table=table)
  results = [row for row in query(queryString, (string,))]

  results = [(e, c, n, d) for (a, e, c, n, d) in aggregateResults(results)]
  sortedResults = sorted(results, key=(lambda item: item[1]), reverse=True)
  return sortedResults

def getStringDistribution(entity, table='crosswikis_inv'):
  """Gets the distribution of strings linked to the entity in Crosswikis.

  Queries the Crosswikis data for the entity we're interested in, and gets a
  list of strings associated with it and their counts.

  Args:
    entity: The entity to search for.
    table: The table to look for the string in.

  Returns: A list of (anchor, cprob, num, denom) tuples, sorted in descending
    order of conditional probability.
  """
  queryString = (
    'SELECT anchor, entity, info, cprob '
    'FROM {table} '
    'WHERE entity=?'
  ).format(table=table)
  results = [row for row in query(queryString, (string,))]

  results = [(e, c, n, d) for (a, e, c, n, d) in aggregateResults(results)]
  sortedResults = sorted(results, key=(lambda item: item[1]), reverse=True)
  return sortedResults
