import constants
import crosswikis
import openie

SYNONYM_PATH = constants.DATA_PATH + 'cwel-test-set-abe'
TEMP_OUTPUT_PATH = constants.RESULTS_PATH + 'openie-counts-temp'
OUTPUT_PATH = constants.RESULTS_PATH + 'openie-counts'

def getStrings(synonymsFile):
  strings = []
  for row in synonymsFile:
    entity, cprob, anchor, info = crosswikis.parseRawInvCrosswikisRow(row)
    strings.append(anchor)
  return strings

def getCounts(strings):
#  for string in strings:
#    openie.writeNumInstances(string, TEMP_OUTPUT_PATH)
  tempOutputFile = open(TEMP_OUTPUT_PATH)
  return openie.getNumInstances(tempOutputFile)

def main():
  synonymsFile = open(SYNONYM_PATH)
  strings = getStrings(synonymsFile)

  instanceCounts = getCounts(strings)
  outputFile = open(OUTPUT_PATH, 'w')
  for (string, count) in instanceCounts.items():
    print('{}\t{}'.format(string, count), file=outputFile)

if __name__ == '__main__':
  main()
