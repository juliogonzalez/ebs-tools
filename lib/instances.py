# ebs-tools, a set of tools to manage EBS volumes and snapshots
#
# Copyright (C) 2014 Julio Gonzalez Gil <julio@juliogonzalez.es>
#
# This file is part of ebs-tools.
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


from boto.exception import EC2ResponseError
from connection import ec2conn
from exceptions import ErrorStartingInstance, ErrorStoppingInstance
from exceptions import InstanceFetchError, InstanceStartImpossible
from exceptions import InstanceStopImpossible, InvalidInstance
from exceptions import InvalidInstanceID
from time import sleep


def get_instance_by_id(instance_id, region):
    """ Fetch ah instance object from its ID

    Args:
        instance_id: A string with the instance-id for the instance to fetch
        region: A string with the AWS region where the instance is
    Returns:
        A boto.ec2.instance.Instance object representing the instance
    Raises:
        InstanceFetchError: If there was an error fetching the instance
        InstanceNotExists: If the instance does not exist
    """
    conn = ec2conn(region)
    try:
        instance = conn.get_only_instances(instance_ids=instance_id)[0]
        return(conn.get_only_instances(instance_ids=instance_id)[0])
    except EC2ResponseError as e:
        if 'InvalidInstanceID.NotFound' in e.body:
            raise InvalidInstance(instance_id)
        elif 'InvalidInstanceID.Malformed' in e.body:
            raise InvalidInstanceID(instance_id)
        else:
            raise InstanceFetchError(e)
    except:
        raise InstanceFetchError(e)


def get_instance_by_name(instance_name, region):
    """ Fetch ah instance object from its ID

    Args:
        instance_id: A string with the instance name (tag) for the instance
                     to fetch
        region: A string with the AWS region where the instance is
    Returns:
        A boto.ec2.instance.Instance object representing the instance
    Raises:
        InstanceFetchError: If there was an error fetching the instance
        InstanceNotExists: If the instance does not exist
    """
    conn = ec2conn(region)
    try:
        reservations = conn.get_all_instances()
    except Exception as e:
        raise InstanceFetchError(e)
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.tags:
                if instance.tags.get("Name") == instance_name:
                    return(instance)
    raise InstanceNotExists(instance_name)


def get_instance_state(instance_id, region):
    """ Fetch ah instance state from its ID

    Args:
        instance_id: A string with the instance-id for the instance to fetch
        region: A string with the AWS region where the instance is
    Returns:
        A string with the instance's state
    """
    return(get_instance_by_id(instance_id, region).state)


def stop_instance_and_wait(instance_id, region, dry):
    """ Stop an EC2 instance (launch and waint until it's started

    Args:
        instance_id: A string with the instance name (tag) for the instance
                     to stop
        region: A string with the AWS region where the instance is
        dry: A boolean stating if the action is simulated or not
    Returns:
       True if the action was successful, False if the instance was already
       started
    Raises:
        InstanceStartImpossible: If it was not possible to stop the instance
                                because if its state
    """
    instancestate = get_instance_state(instance_id, region)
    if instancestate == "stopped":
        return(False)
    elif instancestate == "running" or instancestate == "stopping":
        conn = ec2conn(region)
        try:
            conn.stop_instances(instance_id, dry_run=dry)
            while instancestate != "stopped":
                sleep(15)
                instancestate = get_instance_state(instance_id, region)
        except Exception as e:
            try:
                if 'DryRun flag is set' in e.body:
                    pass
            except:
                ErrorStoppingInstance(instance_id, e)
    else:
        raise InstanceStopImpossible(instance.state)
    return(True)


def start_instance_and_wait(instance_id, region, dry):
    """ Start an EC2 instance (launch and waint until it's started

    Args:
        instance_id: A string with the instance name (tag) for the instance
                     to start
        region: A string with the AWS region where the instance is
        dry: A boolean stating if the action is simulated or not
    Returns:
       True if the action was successful, False if the instance was already
       started
    Raises:
        InstanceStartImpossible: If it was not possible to start the instance
                                because if its state
    """
    instancestate = get_instance_state(instance_id, region)
    if instancestate == "running":
        return(False)
    elif instancestate == "stopped":
        conn = ec2conn(region)
        try:
            conn.start_instances(instance_id, dry)
            while instancestate != "running":
                sleep(15)
                instancestate = get_instance_state(instance_id, region)
        except Exception as e:
            try:
                if 'DryRun flag is set' in e.body:
                    pass
            except:
                ErrorStartingInstance(instance_id, e)
    else:
        raise InstanceStartImpossible(instancestate)
    return(True)
