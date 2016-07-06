# coding: utf-8

"""
    Process Registry API

    Register processes with the Process Registry API.

    OpenAPI spec version: 0.1.5
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from pprint import pformat
from six import iteritems
import re


class ProcessDef(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """
    def __init__(self):
        """
        ProcessDef - a model defined in Swagger

        :param dict swaggerTypes: The key is attribute name
                                  and the value is attribute type.
        :param dict attributeMap: The key is attribute name
                                  and the value is json key in definition.
        """
        self.swagger_types = {
            'id': 'int',
            'name': 'str',
            'author': 'int',
            'appliance': 'str',
            'archive_url': 'str',
            'creation_date': 'datetime',
            'executable': 'str',
            'cwd': 'str',
            'environment': 'str',
            'argv': 'str',
            'output_type': 'str',
            'output_parameters': 'str'
        }

        self.attribute_map = {
            'id': 'id',
            'name': 'name',
            'author': 'author',
            'appliance': 'appliance',
            'archive_url': 'archive_url',
            'creation_date': 'creation_date',
            'executable': 'executable',
            'cwd': 'cwd',
            'environment': 'environment',
            'argv': 'argv',
            'output_type': 'output_type',
            'output_parameters': 'output_parameters'
        }

        self._id = None
        self._name = None
        self._author = None
        self._appliance = None
        self._archive_url = None
        self._creation_date = None
        self._executable = None
        self._cwd = None
        self._environment = None
        self._argv = None
        self._output_type = None
        self._output_parameters = None

    @property
    def id(self):
        """
        Gets the id of this ProcessDef.
        Unique ID of the process

        :return: The id of this ProcessDef.
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id):
        """
        Sets the id of this ProcessDef.
        Unique ID of the process

        :param id: The id of this ProcessDef.
        :type: int
        """
        
        self._id = id

    @property
    def name(self):
        """
        Gets the name of this ProcessDef.
        Name given to the process

        :return: The name of this ProcessDef.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """
        Sets the name of this ProcessDef.
        Name given to the process

        :param name: The name of this ProcessDef.
        :type: str
        """
        
        self._name = name

    @property
    def author(self):
        """
        Gets the author of this ProcessDef.
        Unique ID of the user who created the process

        :return: The author of this ProcessDef.
        :rtype: int
        """
        return self._author

    @author.setter
    def author(self, author):
        """
        Sets the author of this ProcessDef.
        Unique ID of the user who created the process

        :param author: The author of this ProcessDef.
        :type: int
        """
        
        self._author = author

    @property
    def appliance(self):
        """
        Gets the appliance of this ProcessDef.
        Name of the appliance on which the process must be run

        :return: The appliance of this ProcessDef.
        :rtype: str
        """
        return self._appliance

    @appliance.setter
    def appliance(self, appliance):
        """
        Sets the appliance of this ProcessDef.
        Name of the appliance on which the process must be run

        :param appliance: The appliance of this ProcessDef.
        :type: str
        """
        
        self._appliance = appliance

    @property
    def archive_url(self):
        """
        Gets the archive_url of this ProcessDef.
        URL of the archive to be downloaded and extracted on the worker of the cluster before starting the job

        :return: The archive_url of this ProcessDef.
        :rtype: str
        """
        return self._archive_url

    @archive_url.setter
    def archive_url(self, archive_url):
        """
        Sets the archive_url of this ProcessDef.
        URL of the archive to be downloaded and extracted on the worker of the cluster before starting the job

        :param archive_url: The archive_url of this ProcessDef.
        :type: str
        """
        
        self._archive_url = archive_url

    @property
    def creation_date(self):
        """
        Gets the creation_date of this ProcessDef.
        Date and time of creation of the process

        :return: The creation_date of this ProcessDef.
        :rtype: datetime
        """
        return self._creation_date

    @creation_date.setter
    def creation_date(self, creation_date):
        """
        Sets the creation_date of this ProcessDef.
        Date and time of creation of the process

        :param creation_date: The creation_date of this ProcessDef.
        :type: datetime
        """
        
        self._creation_date = creation_date

    @property
    def executable(self):
        """
        Gets the executable of this ProcessDef.
        Path to the executable

        :return: The executable of this ProcessDef.
        :rtype: str
        """
        return self._executable

    @executable.setter
    def executable(self, executable):
        """
        Sets the executable of this ProcessDef.
        Path to the executable

        :param executable: The executable of this ProcessDef.
        :type: str
        """
        
        self._executable = executable

    @property
    def cwd(self):
        """
        Gets the cwd of this ProcessDef.
        Working directory to be in when ruing the process

        :return: The cwd of this ProcessDef.
        :rtype: str
        """
        return self._cwd

    @cwd.setter
    def cwd(self, cwd):
        """
        Sets the cwd of this ProcessDef.
        Working directory to be in when ruing the process

        :param cwd: The cwd of this ProcessDef.
        :type: str
        """
        
        self._cwd = cwd

    @property
    def environment(self):
        """
        Gets the environment of this ProcessDef.
        JSON-formatted dictonary to give values to environment variables (can contain parameters)

        :return: The environment of this ProcessDef.
        :rtype: str
        """
        return self._environment

    @environment.setter
    def environment(self, environment):
        """
        Sets the environment of this ProcessDef.
        JSON-formatted dictonary to give values to environment variables (can contain parameters)

        :param environment: The environment of this ProcessDef.
        :type: str
        """
        
        self._environment = environment

    @property
    def argv(self):
        """
        Gets the argv of this ProcessDef.
        JSON-formatted array being a list of arguments to give to the executable (can contain parameters)

        :return: The argv of this ProcessDef.
        :rtype: str
        """
        return self._argv

    @argv.setter
    def argv(self, argv):
        """
        Sets the argv of this ProcessDef.
        JSON-formatted array being a list of arguments to give to the executable (can contain parameters)

        :param argv: The argv of this ProcessDef.
        :type: str
        """
        
        self._argv = argv

    @property
    def output_type(self):
        """
        Gets the output_type of this ProcessDef.
        type of output (e.g. file, stream)

        :return: The output_type of this ProcessDef.
        :rtype: str
        """
        return self._output_type

    @output_type.setter
    def output_type(self, output_type):
        """
        Sets the output_type of this ProcessDef.
        type of output (e.g. file, stream)

        :param output_type: The output_type of this ProcessDef.
        :type: str
        """
        
        self._output_type = output_type

    @property
    def output_parameters(self):
        """
        Gets the output_parameters of this ProcessDef.
        JSON-formatted dictionary containing parameters regarding the output (depending on the output type)

        :return: The output_parameters of this ProcessDef.
        :rtype: str
        """
        return self._output_parameters

    @output_parameters.setter
    def output_parameters(self, output_parameters):
        """
        Sets the output_parameters of this ProcessDef.
        JSON-formatted dictionary containing parameters regarding the output (depending on the output type)

        :param output_parameters: The output_parameters of this ProcessDef.
        :type: str
        """
        
        self._output_parameters = output_parameters

    def to_dict(self):
        """
        Returns the model properties as a dict
        """
        result = {}

        for attr, _ in iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self.to_dict())

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()

    def __eq__(self, other):
        """
        Returns true if both objects are equal
        """
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """
        Returns true if both objects are not equal
        """
        return not self == other
