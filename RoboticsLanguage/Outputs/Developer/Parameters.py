#
#   This is the Robotics Language compiler
#
#   Parameters.py: Defines the parameters for this package
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

manifesto = {
    'packageName': 'Developer',
    'packageShortName': 'developer',
}


parameters = {
    'create': {
        'input': '',
        'transformer': '',
        'output': '',
        'reference':False
    }
}

command_line_flags = {
    'create:input':
        {
            'longFlag': 'create-input-template',
            'description': 'Create a template for an Input module'
        },
    'create:transformer':
        {
            'longFlag': 'create-transformer-template',
            'description': 'Create a template for a Transformer module'
        },
    'create:output':
        {
            'longFlag': 'create-output-template',
            'description': 'Create a template for an Output module'
        },
    'create:reference':
        {
            'longFlag': 'create-reference-documentation',
            'noArgument': True,
            'description': 'Creates the Reference Documentation for the Robotics Language'
        }


}
