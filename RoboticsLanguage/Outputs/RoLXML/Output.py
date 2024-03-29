#
#   This is the Robotics Language compiler
#
#   Output.py: Generates a XML file in the Robotics Language format
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

from lxml import etree
import copy
from RoboticsLanguage.Base import Utilities

def output(xml, parameters):

  # get node name
  node_name_underscore = Utilities.underscore(parameters['node']['name'])

  # make a copy of the xml tree
  xml_copy = copy.deepcopy(xml)

  # delete all atributes
  for element in xml_copy.iter():
    element.attrib.clear()

  # save the tree into a file
  with open(parameters['globals']['deploy'] + '/' + node_name_underscore + '.xml', 'w') as xml_file:
    xml_file.write('<?xml version="1.0"?>\n' + etree.tostring(xml_copy, pretty_print = True))

    Utilities.logging.debug('Wrote file '+parameters['globals']['deploy'] + '/' + node_name_underscore + '.xml...')

  return 0
