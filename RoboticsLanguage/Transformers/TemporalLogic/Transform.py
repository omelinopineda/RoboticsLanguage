#
#   This is the Robotics Language compiler
#
#   Language.py: Parses the Robotics Language
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

import copy
from lxml import etree
from RoboticsLanguage.Base import Utilities


def processTemporalOperators(code, parameters, list_of_logic, logic_id_counter):
  # find all the relevant tags
  logics = code.xpath('.//always|.//eventually')

  # reverse the list. This ensures all the dependencies of cascated
  # operators are correct
  logics.reverse()

  for logic in logics:

    # find all the signals inside the temporal logic operator that affect
    # its behaviour
    all_variables = map(lambda x: x.attrib['name'], logic.findall('.//variable'))

    # also find all signal dependencies of cascated temporal logic
    # operators
    all_previous_variables = map(
        lambda x: x.attrib['variables'], logic.findall('.//null'))

    # add all variables
    all_variables = sum([all_variables, sum(map(eval, all_previous_variables), [])], [])

    # remove duplicates and preserve order (just in case)
    unique = []
    [unique.append(item) for item in all_variables if item not in unique]
    all_variables = unique

    # extract information about logic operator
    logic_id_counter += 1
    logic_type = logic.tag
    logic_name = logic_type + '_' + str(logic_id_counter) + '_'

    definition = {'type': logic_type,
                  'name': logic_name,
                  'variables': all_variables}

    # replace the xml by serialised code
    if definition['type'] == 'alwaysInterval' or definition['type'] == 'eventuallyInterval':
      definition['max'] = Utilities.serialise(logic.getchildren()[0], parameters, parameters['language'], 'RosCpp')
      definition['min'] = Utilities.serialise(logic.getchildren()[1], parameters, parameters['language'], 'RosCpp')
      definition['logiccode'] = Utilities.serialise(logic.getchildren()[2], parameters, parameters['language'], 'RosCpp')
    else:
      definition['logiccode'] = Utilities.serialise(logic.getchildren()[0], parameters, parameters['language'], 'RosCpp')

    list_of_logic.append(definition)

    # remove cascated logic from element
    logic.remove(logic.getchildren()[0])
    logic.text = logic_name
    # rename the temporal logic tag to be 'logiccode'. Inside all replacememts of operators by
    # local variables are complete
    logic.tag = 'logiccode'

    # add a 'hidden' tag to pass the dependent signals to the parent tags
    logic.append(etree.Element("null", variables=str(all_variables)))

  return logic_id_counter


def transform(code, parameters):

  logic_properties = []
  counter = 0

  logics = code.xpath('//always|//eventually')

  if len(logics) > 0:

    # add id's to logic elements
    for logic_code in logics:
      properties = {}

      # create a unique id
      counter = counter + 1
      properties['id'] = counter
      logic_code.attrib['TemporalLogicId'] = str(counter)

      # create text element for the GUI
      if 'HTMLGUI' in parameters['globals']['output']:

        # make a copy of the code to not polute it with extra attributes
        xml_copy = copy.deepcopy(logic_code)
        root = etree.Element("root")
        root.append(xml_copy)

        # use the RoL serialiser to create the text tag
        Utilities.serialise(root.getchildren()[0], parameters, parameters['language'], 'RoL')
        properties['text'] = root.getchildren()[0].attrib['RoL']

      logic_properties.append(properties)



  parameters['Transformers']['TemporalLogic']['properties'] = logic_properties

  list_of_logic = []
  print processTemporalOperators(code,parameters, list_of_logic, 1)
  Utilities.printParameters(list_of_logic)


  return code, parameters
