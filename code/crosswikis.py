import sqlite3
import re
import constants

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

def addToDictCount(dictionary, key, num):
  """Adds or inserts a number to the key's count.

  Args:
    dictionary: A dict that maps keys to a count.
    key: The entity to map.
    num: The number to add.
  """
  if key in dictionary:
    count = dictionary[key]
    dictionary[key] = count + num
  else:
    dictionary[key] = num

def queryOne(queryString, args):
  """Executes the given query and returns the first result.

  Args:
    queryString: The SQLite query string.
    args: A tuple with all the args to pass to the query string.

  Returns: The first row returned from the query.
  """
  connection = sqlite3.connect(constants.CROSSWIKIS_DB_PATH)
  cursor = connection.cursor()
  cursor.execute(queryString, args)
  row = cursor.fetchone()
  connection.commit()
  connection.close()
  return row

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

def getEntityDistribution(string, table='crosswikis'):
  """Gets the distribution of entities linked to the synonym in Crosswikis.

  Queries the Crosswikis data for the string we're interested in, and gets a
  list of entities associated with it and their counts.

  Args:
    string: The string to search for.
    cursor: The sqlite3 database cursor.

  Returns: A list of (entity, num, denom) tuples, sorted in descending order of 
    conditional probability (num / denom).
  """
  connection = sqlite3.connect(constants.CROSSWIKIS_DB_PATH)
  cursor = connection.cursor()
  query = (
    'SELECT anchor, entity, info, cprob '
    'FROM {table} '
    'WHERE anchor=? COLLATE NOCASE'
  ).format(table=table)
  entityCounts = {}
  entityCprobs = {}

  for anchor, entity, info, cprob in cursor.execute(query, (string,)):
    labelCounts = getLabelCounts(info)
    num = sum([num for (num, denom) in labelCounts.values()])
    addToDictCount(entityCounts, entity, num)
    if entity in entityCprobs:
      entityCprobs[entity].append(cprob)
    else:
      entityCprobs[entity] = [cprob]

  connection.commit()
  connection.close()

  denom = sum(entityCounts.values())
  entityDistribution = list(entityCounts.items())
  entityDistribution = [
    (entity, num, denom, sum(entityCprobs[entity])/len(entityCprobs[entity])) for (entity, num) in entityDistribution
  ]
  sortedEntityDistribution = sorted(
    entityDistribution,
    key=(lambda item: 0 if item[2] == 0 else item[1]/item[2]),
    reverse=True
  )
  return sortedEntityDistribution
