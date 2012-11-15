import constants
import myutils
import os

def writeNumInstances(string, outputPath, arg1=True, arg2=True):
  command = (
    'java -jar {jarFile} --arg{argn} "{string}" --noInst --countsOnly '
    '| grep ".*	.*" '
    '>> {outputPath}'
  )
  if arg1:
    arg1Command = command.format(
      jarFile=constants.OPENIE_BACKEND_JAR_PATH,
      argn=1,
      string=string,
      outputPath=outputPath
    )
    os.system(arg1Command)
  if arg2:
    arg2Command = command.format(
      jarFile=constants.OPENIE_BACKEND_JAR_PATH,
      argn=2,
      string=string,
      outputPath=outputPath
    )
    os.system(arg2Command)
  
def getNumInstances(instancesFile):
  instanceCounts = {}
  for line in instancesFile:
    lineParts = line.strip().split('\t')
    string = lineParts[0]
    count = int(lineParts[1])
    myutils.addToDict(instanceCounts, string, count)
  return instanceCounts
