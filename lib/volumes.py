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
from exceptions import ErrorAttachingVolume, ErrorCreatingVolume
from exceptions import ErrorDeletingVolume, ErrorDetachingVolume
from exceptions import InvalidPIOPSRatio, InvalidPIOPSValue
from exceptions import InvalidVolume, InvalidVolumeID, InvalidVolumeType
from exceptions import NoMatchingVolumesByDevice, NoMatchingVolumesByName
from exceptions import NoVolumes, VolumeCreateTagError
from exceptions import VolumeFetchError, VolumeNotAttached
from re import compile
from snapshots import get_snapshot_by_id
from time import sleep


def get_volume_by_id(volume_id, region):
    """ Get an EBS volume for a given volume id

    Args:
        volume_id: A string with the volume id to fetch
        region: A string with the AWS region where the volume is
    Returns:
        A boto.ec2.volume.Volume object
    Raises:
        InvalidVolume: If the volume id was not found
    """
    conn = ec2conn(region)
    try:
        volume = conn.get_all_volumes(volume_ids=volume_id)[0]
    except EC2ResponseError as e:
        if 'InvalidVolume.NotFound' in e.body:
            raise InvalidVolume(volume_id)
        elif 'InvalidParameterValue' in e.body:
            raise InvalidVolumeID(volume_id)
        else:
            raise VolumeFetchError(e)
    except:
        raise VolumeFetchError(e)
    return(volume)


def get_volumes_from_instance_by_device(instance_id, devices, region):
    """ Return all EBS volumes attached to an EC2 instance by device

    Args:
        instance_id: A string with the instance id to fetch
        devices: A string with a regex to look for volumes by device name
        region: A string with the AWS region where the instance and volumes are
    Returns:
        A list of boto.ec2.volume.Volume objects
    Raises:
        NoMatchingVolumes: If the regex doesn't match any volume
    """
    matched_volumes = []
    expression = compile(devices)
    volumes = get_volumes_from_instance(instance_id, region)
    for volume in volumes:
        try:
            if expression.match(volume.attach_data.device):
                matched_volumes.append(volume)
        except TypeError:
            pass
    if len(matched_volumes) > 0:
        return(matched_volumes)
    raise NoMatchingVolumesByDevice(instance_id, devices)


def get_volumes_from_instance_by_name(instance_id, name, region):
    """ Return all EBS volumes attached to an EC2 instance by name (tag)

    Args:
        instance_id: A string with the instance id to fetch
        name: A string with a regex to look for volumes by name
        region: A string with the AWS region where the instance and volumes are
        name: A string with a regex to look for volumes by name
    Returns:
        A list of boto.ec2.volume.Volume objects
    Raises:
        NoMatchingVolumes: If the regex doesn't match any volume
    """
    matched_volumes = []
    expression = compile(name)
    volumes = get_volumes_from_instance(instance_id, region)
    for volume in volumes:
        try:
            if expression.match(volume.tags.get("Name")):
                matched_volumes.append(volume)
        except TypeError:
            pass
    if len(matched_volumes) > 0:
        return(matched_volumes)
    raise NoMatchingVolumesByName(instance_id, devices)


def get_volumes_from_instance(instance_id, region):
    """ Return all EBS volumes attached to an EC2 instance

    Args:
        instance_id: A string with the instance id to fetch volumes
        region: A string with the AWS region where the instance and volumes are
    Returns:
        A list of boto.ec2.volume.Volume objects
    Raises:
        VolumeFetchError: If there is an error fetching the volume list
        NoVolumes: If there are no volumes
    """
    conn = ec2conn(region)
    try:
        volumes = conn.get_all_volumes(
            filters={'attachment.instance-id': '%s' % instance_id})
    except Exception as e:
        raise VolumeFetchError(e)
    if len(volumes) > 0:
        return(volumes)
    else:
        raise NoVolumes(instance_id)


def check_iops_ratio(volume_id, piops, region):
    """ Check if ratio iops/size for an EBS volume is valid

    Args:
        volume_id: A string with the volume id to check
        piops: Integer with the number of PIOPs for the volume
        region: A string with the AWS region where the volume is
    Returns:
        True if the ratio was valid.
    Raises:
        InvalidPIOPSValue: If the number of PIOPs is invalid
        InvalidPIOPSRatio: If the ratio is invalid.
    """
    MIN_IOPS = 100
    MAX_IOPS = 4000
    MAX_RATIO = 30
    if int(piops) < MIN_IOPS or int(piops) > MAX_IOPS:
        raise InvalidPIOPSValue(piops)
    conn = ec2conn(region)
    volume = get_volume_by_id(volume_id, region)
    ratio = int(piops) / volume.size
    if ratio <= 30:
        return(True)
    else:
        raise InvalidPIOPSRatio(volume, ratio, MAX_RATIO)


def delete_volume(volume_id, region, dry):
    """ Delete an EBS volume

    Args:
        volume_id: A string with the volume id to delete
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
    Returns:
        True if the volume was deleted
    Raises:
        ErrorDeletingVolume: If there was an error deleting the volume
    """
    conn = ec2conn(region)
    volume = get_volume_by_id(volume_id, region)
    try:
        volume.delete(dry)
    except Exception as e:
        try:
            if 'DryRun flag is set' in e.body:
                return(True)
        except:
            ErrorDeletingVolume(volume_id, e)
    while volume.status == "deleting":
        sleep(10)
        volume.update(validate=True)
    return(True)


def detach_volume(volume_id, region, dry):
    """ Dettach an EBS volume

    Args:
        volume_id: A string with the volume id to detach
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
    Returns:
        True if the volume was detached
    Raises:
        VolumeNotAttached: If the volume was not attached
        ErrorDetachingVolume: If there was a problem detaching the volume
    """
    conn = ec2conn(region)
    volume = get_volume_by_id(volume_id, region)
    device = volume.attach_data.device
    if device is None:
        raise VolumeNotAttached(volume_id)
    try:
        volume.detach(dry_run=dry)
    except Exception as e:
        try:
            if 'DryRun flag is set' in e.body:
                return(True)
        except:
            raise ErrorDetachingVolume(volume_id, e)
    while volume.attach_data.status is not None:
        sleep(10)
        volume.update(validate=True)
    return(True)


def attach_volume(volume_id, instance_id, device, region, dry):
    """ Dettach an EBS volume

    Args:
        volume_id: A string with the volume id to attach
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
    Returns:
        True if the volume was attached
    Raises:
        ErrorAttachingVolume: If there is a problem attaching the volume
    """
    conn = ec2conn(region)
    volume = get_volume_by_id(volume_id, region)
    try:
        volume.attach(instance_id, device, dry)
    except Exception as e:
        try:
            if 'DryRun flag is set' in e.body:
                return(True)
        except:
            raise ErrorAttachingVolume(volume_id, e)
    while volume.attach_data.status != "attached":
        sleep(10)
        volume.update(validate=True)
    return(True)


def create_volume_tags(volume_id, region, tags):
    """ Create a new tags for the given volume-id
    Args:
        volume_id: A string with the volume-id for the volume
        region: A string with the AWS region where the volume is
        tags:  A python dictionary with tags for the new volume
    Returns:
        True if the operation succeeded
    """
    for key, value in tags.iteritems():
        create_volume_tag(volume_id, region, key, value)
    return(True)


def create_volume_tag(volume_id, region, tagname, value):
    """ Create a new tag for the given volume-id
    Args:
        volume_id: A string with the volume-id for the volume
        region: A string with the AWS region where the volume is
        tagname: A string with the name for the new tag
        value: A string with the value for the new tag
    Returns:
        True if the operation succeeded
    Raises:
        VolumeCreateTagError: If it was not possible to create the tag
    """
    try:
        conn = ec2conn(region)
        conn.create_tags(volume_id, {"%s" % tagname: "%s" % value})
    except Exception as e:
        raise VolumeCreateTagError(e)
    return(True)


def create_volume(region, dry, zone, size, vtype, piops=None, name=None,
                  tags=None, encrypted=False, snapshot_id=None,
                  savetags=False):
    """ Create an EBS volume (optionally from a snapshot

    Args:
        region: A string with the AWS region where the volume will be
        dry: A boolean stating if the action is simulated or not
        zone: A string withe AWS availabily zone where the volume will be
        size: An integer with the size for the new volume (GB)
        vtype: A string with the volume type (io1|standard|gp2)
        piops: An integer with the number of PIOPs (only when vtype=io1)
        name: A string with the name for the volume (optional, if a tag name
              is specified in variable tags, the function will use it)
        tags:  A python dictionary with tags for the new volume
        encrypted: A boolean stating if the new volume will be encrypted or
                   not (ignored a snapshot was specified, as will use the
                   value from the snapshot)
        snapshot_id: A string with the snapshot-id for the snapshot
    Returns:
        A boto.ec2.volume.Volume object if the operation was successful
    Raises:
        ErrorCreatingVolume: If there is a problem creating the volume
    """
    conn = ec2conn(region)
    if snapshot_id is not None:
        encrypted = get_snapshot_by_id(snapshot_id, region).encrypted
    if vtype != "io1" and vtype != "gp2" and vtype != "standard":
        raise InvalidVolumeType(vtype)
    try:
        if vtype == "io1":
            volume = conn.create_volume(size, zone, snapshot_id, "io1", piops,
                                        encrypted=encrypted, dry_run=dry)
        elif vtype == "standard" or vtype == "gp2":
            volume = conn.create_volume(size, zone, snapshot_id, vtype,
                                        encrypted=encrypted, dry_run=dry)
    except Exception as e:
        try:
            if 'DryRun flag is set' in e.body:
                return(True)
        except:
            raise ErrorCreatingVolume(e)
    if volume.status == "error":
        raise ErrorCreatingVolume("Error creating volume: volume status is "
                                  "error")
    while volume.status == "creating":
        sleep(15)
        volume.update(validate=True)
    if tags is not None:
        if savetags:
            for tagkey, tagvalue in tags.iteritems():
                if tagkey == 'Name' and name is not None:
                    create_volume_tag(volume.id, region, 'Name', name)
                else:
                    create_volume_tag(volume.id, region, tagkey, tagvalue)
        else:
            if name is not None:
                create_volume_tag(volume.id, region, 'Name', name)
    return(volume)
