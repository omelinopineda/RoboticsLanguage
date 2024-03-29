#
#   This is the Robotics Language compiler
#
#   Transformations.py: Applies tranformations to the XML structure
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

atoms = {
  'string':'Strings',
  'boolean':'Booleans',
  'real':'Reals',
  'integer':'Integers'
  }

def manySameNumbersOrStrings(x):
  '''number or string'''
  return all(map(lambda y: y in ['Reals', 'Integers'], x)) or all(map(lambda y: y == 'Strings', x))


def singleString(x):
  '''string'''
  return len(x) == 1 and x[0] == 'Strings'

def singleReal(x):
  '''real'''
  return len(x) == 1 and (x[0] == 'Reals' or x[0] == 'Integers')

def singleBoolean(x):
  '''boolean'''
  return len(x) == 1 and x[0] == 'Booleans'

def manyStrings(x):
  '''string , ... , string'''
  return [ xi == 'Strings' for xi in x ]

def manyExpressions(x):
  '''expression , ... , expression'''
  return [True]

def manyCodeBlocks(x):
  '''code block , ... , code block'''
  return [ xi == 'CodeBlock' for xi in x ]

def returnNothing(x):
  '''nothing'''
  return 'Nothing'

def returnCodeBlock(x):
  '''code block'''
  return 'CodeBlock'

def returnSameArgumentType(x):
  return x[0]
