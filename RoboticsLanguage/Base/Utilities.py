#
#   This is the Robotics Language compiler
#
#   Utilities.py: Utility functions
#
#   Created on: June 22, 2017
#       Author: Gabriel A. D. Lopes
#      Licence: Apache 2.0
#    Copyright: 2014-2017 Robot Care Systems BV, The Hague, The Netherlands. All rights reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import sys
import errno
import time
import datetime
import dill
import pprint
import logging
import coloredlogs
import dpath.util
from lxml import etree
from funcy import decorator
from shutil import copy, rmtree
from jinja2 import Environment, FileSystemLoader, Template, TemplateSyntaxError, TemplateAssertionError, TemplateError
from RoboticsLanguage.Base import Types

# -------------------------------------------------------------------------------------------------
#  Default encoding is Unicode
# -------------------------------------------------------------------------------------------------

reload(sys)
sys.setdefaultencoding('utf-8')

# -------------------------------------------------------------------------------------------------
#  Error handling
# -------------------------------------------------------------------------------------------------


def logErrors(errors, parameters):
  if isinstance(errors, list):
    for error in errors:
      logging.error(error)
      parameters['errors'].append(error)
  else:
    logging.error(errors)
    parameters['errors'].append(errors)

# given a file name and a line number, returns the text line
def fileLineNumberToLine(filename, line_number):
  with open(filename) as file:
    line = [next(file) for x in xrange(line_number)][-1]
  return line

# given a text string and a line number, returns the text line
def textLineNumberToLine(text, line_number):
  return text.split('\n')[line_number - 1]


# given a position (byte counter) and text, returns the line, line number and column number
def positionToLineColumn(position, text):
  lines = str(text).split('\n')
  counter = 0
  line_number = 1
  column_number = 0
  for line in lines:
    new_counter = counter + len(line)
    if new_counter > position:
      column_number = position - counter
      break
    else:
      counter += len(line) + 1
      line_number += 1
  return line_number, column_number, line

# generic error message


def errorMessage(error_type, reason, line='', filename='', line_number=0, column_number=0):

  line_text = '\n' + line.strip('\n') + '\n' + (' ' * column_number + '^') + '\n' if line is not '' else ''

  file_text = ' in file:\n"' + filename + '"\n' if filename is not '' else ''

  line_number_text = ' at line ' + str(line_number) if line_number > 0 else ''

  column_number_text = ' column ' + str(column_number) if column_number > 0 else ''

  return (line_text + error_type + ' error' + file_text + line_number_text + column_number_text + ': ' +
          color.BOLD + reason + color.END)

# creates error message from jinja exception


def formatJinjaErrorMessage(exception, filename=''):
  if isinstance(exception, TemplateSyntaxError):
    line = fileLineNumberToLine(exception.filename, exception.lineno)
    return errorMessage('Output template syntax', exception.message, line=line,
                        line_number=exception.lineno, filename=exception.filename)
  elif isinstance(exception, TemplateAssertionError):
    line = fileLineNumberToLine(exception.filename, exception.lineno)
    return errorMessage('Output template assertion', exception.message, line=line,
                        line_number=exception.lineno, filename=exception.filename)
  else:
    return errorMessage('Unexpected output template', exception.message, filename=filename)

# creates error message from parsley exception


def formatParsleyErrorMessage(exception):
  # get the line and column numbers
  line_number, column_number, line = positionToLineColumn(exception.position, exception.input)

  return errorMessage('Input syntax parsing', exception.formatReason(),
                      line_number=line_number, column_number=column_number, line=line)

# creates error message for file related issues


def formatOSErrorMessage(exception):
  return errorMessage('File system', exception.strerror)


def formatLxmlErrorMessage(exception, text=''):
  errors = []
  for error in exception.error_log:
    if text is not '':
      line = textLineNumberToLine(text, error.line)
    else:
      line = ''
    errors.append('\n' + errorMessage('XML parsing', error.message,
                                      line=line, line_number=error.line, column_number=error.column))
  return errors


def formatSemanticTypeErrorMessage(code_text, parameters, position, error, reason):
  # get the line and column numbers
  line_number, column_number, line = positionToLineColumn(int(position), code_text)

  parameters['errors'].append(error+reason)

  return errorMessage(error, reason,
                      line_number=line_number, column_number=column_number, line=line)



def errorOptionalArgumentTypes(code, parameters, parameter_names, parameter_types):
  message = 'Incorrect types for optional parameters. '

  for name, types in zip(parameter_names, parameter_types):
    if not parameters['language'][code.tag]['definition']['optionalArguments'][name](types):
      message += 'The type of the optional parameter "' + name + '" should be "' + parameters['language'][code.tag]['definition']['optionalArguments'][name].__doc__ +'" instead of "' + types +'"\n'
  # show error
  logger.error(formatSemanticTypeErrorMessage(parameters['text'], parameters, getTextMinimumPositionXML(code), 'Type', message))

def errorOptionalArgumentNotDefined(code, parameters, parameter_names):
  # Error! figure out which parameter is not defined
  message = ''
  keys = parameters['language'][code.tag]['definition']['optionalArguments'].keys()

  for x in set(parameter_names) - set(keys):
    message += 'The optional parameter "' + x + '" is not defined.\n'

  message += 'The list of defined optional parameters is: '+ str(keys)

  logger.error(formatSemanticTypeErrorMessage(parameters['text'], parameters, getTextMinimumPositionXML(code), 'Type', message))

def errorArgumentTypes(code, parameters, argument_types):
  message  = 'Incorrect argument types for function "' + code.tag +'". The expected argument types are:\n   '
  message += code.tag + '( '+ parameters['language'][code.tag]['definition']['argumentTypes'].__doc__ + ' )\n'
  message += '\nInstead received:\n   ' + code.tag + '( '+ ','.join(argument_types) + ' )\n'

  logger.error(formatSemanticTypeErrorMessage(parameters['text'], parameters, getTextMinimumPositionXML(code), 'Type', message))


# -------------------------------------------------------------------------------------------------
#  Decorators for performance and debug
# -------------------------------------------------------------------------------------------------

@decorator
def log_all_calls(function):
  print 'function name:', function._func.__name__, ' arguments:', function._args
  return function()

@decorator
def name_all_calls(function):
  print 'function name:', function._func.__name__
  return function()


@decorator
def time_all_calls(function):
  start = time.time()
  result = function()
  print 'function name:', function._func.__name__, 'execution time: ', time.time() - start, 'seconds'
  return result


# -------------------------------------------------------------------------------------------------
#  logging utilities
# -------------------------------------------------------------------------------------------------

# Create a logger object.
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(levelname)s: %(message)s')
coloredlogs.install(level='WARN')

# install colours in the logger


def setLoggerLevel(level):
  coloredlogs.install(level=level.upper())

# command line codes for colors


class color:
  PURPLE = '\033[95m'
  CYAN = '\033[96m'
  DARKCYAN = '\033[36m'
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  YELLOW = '\033[93m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  END = '\033[0m'


def incrementCompilerStep(parameters, name):
  # update the compiler step
  parameters['debug']['stepCounter'] = parameters['debug']['stepCounter']+1

  # log the current step
  logger.info('Step ['+str(parameters['debug']['stepCounter'])+"]: " + name)

  return parameters

def showDebugInformation(code,parameters):
    if parameters['debug']['step'] == parameters['debug']['stepCounter']:

      # show debug information for xml code
      if parameters['debug']['xml']:
        print(etree.tostring(code,pretty_print=True))

      # show debug information for parameters
      if parameters['debug']['parameters']:
        pprint.pprint(parameters)

      # show debug information for specific xml code
      if parameters['debug']['xmlPath'] is not '':
        try:
          for element in code.xpath(parameters['debug']['xmlPath']):
            print(etree.tostring(element,pretty_print=True))
        except:
          logger.warning("The path'" + parameters['debug']['xmlPath'] + "' is not present in the code")

      # show debug information for specific parameters
      if parameters['debug']['parametersPath'] is not '':
        try:
          for element in paths(parameters,parameters['debug']['parametersPath']):
            pprint.pprint(element)
        except:
          logger.warning("The path'" + parameters['debug']['parametersPath'] + "' is not defined in the internal parameters.")

      if parameters['debug']['stop']:
        sys.exit(0)


# -------------------------------------------------------------------------------------------------
#  Module utilities
# -------------------------------------------------------------------------------------------------


def importModule(a, b, c):
  return __import__('RoboticsLanguage.' + a + '.' + b, globals(), locals(), ensureList(c))

# @TODO use decorators for caching


def cache(name, function, cache_path='/.rol/cache/'):
  global logger
  path = os.path.expanduser("~") + cache_path + name + '.data'
  if os.path.isfile(path):
    data = dill.load(open(path, "rb"))
    return data
  else:
    logger.debug('Computing and caching ' + name + '...')
    data = function()
    createFolder(os.path.expanduser("~") + cache_path)
    dill.dump(data, open(path, "wb")) #, protocol=dill.HIGHEST_PROTOCOL)
    return data


def removeCache(cache_path='/.rol/cache'):
  global logger
  logger.debug('Removing caching...')
  path = os.path.expanduser("~") + cache_path
  if os.path.isdir(path):
    rmtree(path)


# -------------------------------------------------------------------------------------------------
#  Dictionary utilities
# -------------------------------------------------------------------------------------------------

def isKeyDefined(key, d):
  if isinstance(d, dict):
    return key in d.keys()
  else:
    return False


def isDefined(dictionary,element):
  return len(dpath.util.values(dictionary, element)) > 0


def getDictValue(key, d):
  if isKeyDefined(key, d):
    return d[key]
  else:
    return None


# @REFACTOR remove this function later
def mergeDictionaries(a, b):
  dpath.util.merge(b, a)
  return b


def flatDictionary(d, s='-', list=None, name=''):
  if list is None:
    list = {}
  for key, value in d.iteritems():
    if isinstance(value, dict):
      list.update(flatDictionary(value, s, list, name + s + key))
    else:
      list[name + s + key] = value
  return list


def unflatDictionary(l, s='-'):
  dictionary = {}
  for key, value in l.iteritems():
    dpath.util.new(dictionary, key.replace(s, '/'), value)
  return dictionary


def path(dictionary, dictionary_path):
  return dpath.util.get(dictionary, dictionary_path)


def paths(dictionary, dictionary_path):
  return dpath.util.values(dictionary, dictionary_path)

# -------------------------------------------------------------------------------------------------
#  String utilities
# -------------------------------------------------------------------------------------------------


def lowerNoSpace(s):
  return s.replace(' ', '').lower()


def lowerSpaceToDash(s):
  return s.replace(' ', '-').lower()


def underscore(text):
  return text.replace('/', '_').replace(' ', '_').replace('.', '_').lower()


def underscoreFullCaps(text):
  return text.replace('/', '_').replace(' ', '_').replace('.', '_').upper()


def fullCaps(text):
  return text.replace('/', '').replace(' ', '').replace('.', '').replace('_', '').upper()


def smartTitle(s):
  return ' '.join(w[0].upper() + w[1:] for w in s.split())


def camelCase(text):
  return smartTitle(text.replace('/', ' ').replace('.', ' ').replace('_', ' ')).replace(' ', '')


def initials(text):
  return ''.join(c for c in smartTitle(text) if c.isupper())


# -------------------------------------------------------------------------------------------------
#  List utilities
# -------------------------------------------------------------------------------------------------

def ensureList(a):
  if isinstance(a, list):
    return a
  else:
    return [a]


# -------------------------------------------------------------------------------------------------
#  File utilities
# -------------------------------------------------------------------------------------------------


def findFileType(extension='py', path='.'):
  for root, dirs, files in os.walk(path):
    for eachfile in files:
      fileName, fileExtension = os.path.splitext(eachfile)
      if fileExtension.lower() == '.' + extension:
        yield root + '/' + eachfile


def findFileName(name, path='.'):
  for root, dirs, files in os.walk(path):
    for eachfile in files:
      if os.path.basename(eachfile) == name:
        yield root + '/' + eachfile


def createFolder(path):
  if not os.path.exists(path):
    try:
      os.makedirs(path)
    except OSError as exc:  # Guard against race condition
      if exc.errno != errno.EEXIST:
        raise


def createFolderForFile(filename):
  createFolder(os.path.dirname(filename))


# -------------------------------------------------------------------------------------------------
#  XML utilities
# -------------------------------------------------------------------------------------------------

def xpath(xml, path):
  result = xml.xpath(path)
  if isinstance(result, list):
    return result[0]
  else:
    return result


def xpaths(xml, path):
  return xml.xpath(path)


def text(xml):
  if xml.text is None:
    return ''
  else:
    return xml.text


def tag(xml):
  return xml.tag


def attributes(xml):
  return xml.attrib


def attribute(xml, name):
  if isinstance(xml, list):
    xml = xml[0]
  attributes = xml.attrib
  if name in attributes.keys():
    return attributes[name]
  else:
    return ''


def optionalArgument(xml, name):
  try:
    return optionalArguments(xml)[name]
  except:
    return None

def optionalArguments(xml):
  return {a.xpath('name/text()')[0]: a.xpath('*[not(self::name)]')[0] for a in xml.xpath('optionalArgument')}


def getTextMinimumPositionXML(xml):
  minimum = xml.attrib['p'] if 'p' in xml.attrib else sys.maxint

  childrens_minimum = [getTextMinimumPositionXML(x) for x in xml.getchildren()]

  if childrens_minimum == []:
    return minimum
  else:
    return min(min(childrens_minimum),minimum)

# -------------------------------------------------------------------------------------------------
#  Other utilities
# -------------------------------------------------------------------------------------------------

def todaysDate(format):
  today = datetime.date.today()
  return today.strftime(format)

# -------------------------------------------------------------------------------------------------
#  semantic type checker
# -------------------------------------------------------------------------------------------------
def semanticChecking(code, parameters):

  # traverse xml and set all types for all atomic tags
  [x.set('type',b) for a,b in Types.atoms.iteritems() for x in code.xpath('//'+a)]

  # check types
  code, parameters = semanticTypeChecker(code,parameters)

  return code, parameters


def semanticTypeChecker(code,parameters):

  # if element is an atom, jut return
  if code.tag in Types.atoms:
    return code, parameters

  # @TODO traverse also the optionalArguments. Maybe define it as a tag for generality
  # first recursively traverse all children elements that are not optionalArgument
  for element in code.xpath('*[not(self::optionalArgument)]'):
    element, parameters = semanticTypeChecker(element,parameters)

  # for this element find the parameters and arguments
  parameter_names = code.xpath('optionalArgument/name/text()')
  parameter_types = code.xpath('optionalArgument/*/@type')
  argument_types = code.xpath('*/@type')
  keys = parameters['language']

  # check optional arguments
  if all([x in keys[code.tag]['definition']['optionalArguments'].keys() for x in parameter_names]):

    # check types for optional arguments
    if not all(map(lambda x,y: keys[code.tag]['definition']['optionalArguments'][x]([y]) , parameter_names, parameter_types)):
      # Error: incorrect types for optional arguments!
      errorOptionalArgumentTypes(code, parameters, parameter_names, parameter_types)
  else:
    # Error: optional argument not defined
    errorOptionalArgumentNotDefined(code, parameters, parameter_names)

  # check mandatory argument types
  if all(keys[code.tag]['definition']['argumentTypes'](argument_types)):

    # compute resulting type
    code.attrib['type'] = keys[code.tag]['definition']['returnType'](argument_types)

  else:
    # Error: mandatory argument missing or incorrect
    errorArgumentTypes(code, parameters, argument_types)

  return code, parameters


def fillDefaultsInOptionalArguments(code, parameters):
  '''Fill in defaults in optional arguments in case they are not explicitely defined.'''

  for element in code.xpath('*[not(self::optionalArgument)]'):
    __, parameters = fillDefaultsInOptionalArguments(element, parameters)

  # if this tag has optional parameters defined
  if len(dpath.util.values(parameters['language'][code.tag],'definition/optionalArguments')) > 0:

    # find all optional parameters
    parameter_names = code.xpath('optionalArgument/name/text()')

    # get the list of missing parameters
    missing_parameters = list(set(parameters['language'][code.tag]['definition']['optionalArguments'].keys()) - set(parameter_names))

    for parameter in missing_parameters:

      # create XML structure
      optional_argument_tag = etree.Element('optionalArgument')
      name_tag = etree.Element('name')

      # add the name of the optinal parameter
      name_tag.text = parameter

      # @WARNING the __doc__ definition of the type functions must be correct. How to deal with non-single types?
      # get the type for the optional parameter
      value_tag = etree.Element(parameters['language'][code.tag]['definition']['optionalArguments'][parameter].__doc__)

      # set the default value
      value_tag.text = str(parameters['language'][code.tag]['definition']['optionalDefaults'][parameter])

      # append new tag to the code
      optional_argument_tag.append(name_tag)
      optional_argument_tag.append(value_tag)
      code.append(optional_argument_tag)

  return code, parameters


# -------------------------------------------------------------------------------------------------
#  template engine
# -------------------------------------------------------------------------------------------------


default_template_engine_filters = {'todaysDate': todaysDate,
                                   'dpath': path,
                                   'xpath': xpath,
                                   'dpaths': paths,
                                   'xpaths': xpaths,
                                   'isDefined': isDefined,
                                   'ensureList': ensureList,
                                   'text': text,
                                   'tag': tag,
                                   'attributes': attributes,
                                   'attribute': attribute,
                                   'optionalArgument': optionalArgument,
                                   'optionalArguments': optionalArguments,
                                   'initials': initials,
                                   'underscore': underscore,
                                   'fullCaps': fullCaps,
                                   'camelCase': camelCase,
                                   'underscoreFullCaps': underscoreFullCaps}
# @TODO add list of files to ignore


def templateEngine(code, parameters, filepatterns, templates_path, deploy_path,
                   filters=default_template_engine_filters):

  files_to_process = []
  files_to_copy = []

  try:
    # find all the template files in the template folder
    for root, dirs, files in os.walk(templates_path):
      for file in files:
        if file.endswith(".template"):
          files_to_process.append(os.path.join(root, file))
        else:
          files_to_copy.append(os.path.join(root, file))

    # rename files and directory names from template
    # @WARNING For paths that contain duplicate strings this might fail
    new_files = [x.replace(templates_path, deploy_path).replace('.template', '') for x in files_to_process]
    new_copy_files = [x.replace(templates_path, deploy_path) for x in files_to_copy]

    # rename files acording to file pattern names
    for key, value in filepatterns.iteritems():
      for i in range(len(new_files)):
        new_files[i] = new_files[i].replace('_' + key + '_', value)
      for i in range(len(new_copy_files)):
        new_copy_files[i] = new_copy_files[i].replace('_' + key + '_', value)

    # create the Jinja environment
    env = Environment(loader=FileSystemLoader('/'))

    # add filters
    for key, value in filters.iteritems():
      env.filters[key] = value

    # process all files
    for i in range(0, len(files_to_process)):
      try:
        # open templates
        template_body = env.get_template(files_to_process[i])

        # fill in the text
        text_body = template_body.render(code=code, parameters=parameters)
      except TemplateError as e:
        logErrors(formatJinjaErrorMessage(e, filename=files_to_process[i]), parameters)
        return False

      # create paths for the new files if needed
      createFolderForFile(new_files[i])

      # write files
      new_package_file = open(new_files[i], 'w')
      new_package_file.write(text_body)
      new_package_file.close()
      logging.debug('Wrote file ' + new_files[i] + '...')

    # copy support files
    for i in range(0, len(files_to_copy)):
      # create paths for the new files if needed
      createFolderForFile(new_copy_files[i])

      # copy files
      copy(files_to_copy[i], new_copy_files[i])
      logging.debug('Copied file ' + new_copy_files[i] + '...')

  except OSError as e:
    logErrors(formatOSErrorMessage(e), parameters)
    return False
  return True


# @WARNING this function does not work on the root node (since it uses the getparent function)
def serialise(code, parameters, keywords, language, filters={}):

  snippet = ''

  try:
    # load keyword template text
    keyword = keywords[code.tag]['output'][language]

    try:
      # start the template for this tag
      template = Template(keyword)

      # load the text filters
      for key, value in filters:
        template.globals[key] = value

      # render tags according to dictionary
      snippet = template.render(children=map(lambda x: serialise(x, parameters, keywords, language, filters), code.getchildren()),
                                childrenTags=map(lambda x: x.tag, code.getchildren()),
                                attributes=code.attrib,
                                parentAttributes=code.getparent().attrib,
                                parentTag=code.getparent().tag,
                                text=text(code),
                                parameters=parameters)
      # save text in attribute
      code.attrib[language] = snippet

    except TemplateError as e:
      logErrors(formatJinjaErrorMessage(e), parameters)

  except KeyError:
      # get the line and column numbers
    line_number, column_number, line = positionToLineColumn(int(code.attrib['p']), parameters['text'])

    # create error error_message
    logErrors(errorMessage('Language semantic', 'Keyword \'' + code.tag + '\' not defined',
                           line_number=line_number, column_number=column_number, line=line), parameters)

  return snippet
