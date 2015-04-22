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


from boto import ec2
from exceptions import EC2ConnectError

_ec2_connection = None


def ec2conn(region):
    """ Connect to EC2 API

    Args:
        region: The string for the AWS region to connect
    Returns:
        A boto.ec2.connection.EC2Connection object with the connection
    Raises:
        EC2Connect: If connection was not possible
    """
    global _ec2_connection
    if _ec2_connection is None:
        try:
            _ec2_connection = ec2.connect_to_region(region)
            # As per boto documentation
            if _ec2_connection is None:
                raise Exception('Region %s is invalid' % region)
        except Exception as e:
            raise EC2ConnectError(e)
    return _ec2_connection
