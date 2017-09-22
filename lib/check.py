# Just a test
# ebs-tools, a set of tools to manage EBS volumes and snapshots
#
# Copyright (C) 2014 Julio Gonzalez Gil <julio@juliogonzalez.es>
#
# This file is part of ebs-tools (http://github.com/juliogonzalez/ebs-tools)
#
# ebs-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ebs-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ebs-tools.  If not, see <http://www.gnu.org/licenses/>.


from exceptions import OptInvalidBoolean, OptInvalidPosInteger
from exceptions import OptInvalidPosIntegerBoolean


def posint_or_default(option, value, default=None):
    """ Check if the value of an option is a positive integer or none,
        and return the integer or the default value, if it exists

        Args:
           option: A string with the option name
           value: A string with the value
           default: A positive integer with the default value
        Returns:
           An integer, either the value argument casted to nteger, or the
           default value, if it exists
        Raises:
           OptInvalidPosInteger: If the value was not None or a positive
                                 integer.
    """
    if value is None:
        if default is not None:
            return(default)
        else:
            OptInvalidPosInteger(option)
    try:
        if int(value) >= 0:
            return(int(value))
        else:
            raise OptInvalidPosInteger(option)
    except:
        raise OptInvalidPosInteger(option)


def boolean_posint_or_default(nparam, value, default=None):
    """ Check if the value of an option is a positive integer, a boolean,
        or none, and return the integer or the default value, if it exists

        Args:
           option: A string with the option name
           value: A string with the value
           default: A positive integer or boolean with the default value
        Returns:
           An integer or boolean, depending on the input value,
           or the default value (integer or boolean), if it exists
        Raises:
           OptInvalidPosIntegerBoolean: If the value was not None or a positive
                                 integer.
    """
    if value is None:
        if default is not None:
            return(default)
        else:
            OptInvalidPosIntegerBoolean(option)
    try:
        return(int(value))
    except:
        if value.lower() == 'true':
            return(True)
        elif value.lower() == 'false':
            return(False)
        else:
            raise OptInvalidPosIntegerBoolean(option)


def boolean_or_default(nparam, value, default=None):
    """ Check if the value of an option is a boolean or none, and return the
        integer or the default value, if it exists

        Args:
           option: A string with the option name
           value: A string with the value
           default: A boolean with the default value
        Returns:
           A boolean, or the default value (boolean), if it exists
        Raises:
           OptInvalidBoolean: If the value was not None or a positive
                                 integer.
    """
    if value is None:
        if default is not None:
            return(default)
        else:
            OptInvalidPosIntegerBoolean(option)
    if value.lower() == 'true':
        return(True)
    elif value.lower() == 'false':
        return(False)
    else:
        raise OptInvalidPosIntegerBoolean(option)


def print_usage_error(script, error):
    """ Print script's usage and an error

        Args:
           script: A string with the script filename (without path)
           error: A string with an error
        Returns:
           Nothing
    """
    print 'Usage: %s <arguments>' % script
    print ''
    print '%s: error: %s' % (script, error)
