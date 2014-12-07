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


# EC2 general exceptions


class EC2ConnectError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error connecting to EC2 API: %s' % self.error)

# Instance exceptions


class ErrorStartingInstance(Exception):

    def __init__(self, instance_id, error):
        self.instance_id = instance_id
        self.error = error

    def __str__(self):
        return('Error starting instance %s: %s' % self.instance_id, self.error)


class ErrorStoppingInstance(Exception):

    def __init__(self, instance_id, error):
        self.instance_id = instance_id
        self.error = error

    def __str__(self):
        return('Error stopping instance %s: %s' % self.instance_id, self.error)


class InstanceFetchError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error fetching EC2 instance: %s' % self.error)


class InvalidInstance(Exception):

    def __init__(self, instance_id):
        self.instance_id = instance_id

    def __str__(self):
        return('Instance %s does not exist' % self.instance_id)


class InvalidInstanceID(Exception):

    def __init__(self, instance_id):
        self.instance_id = instance_id

    def __str__(self):
        return('Invalid instance-id: %s' % self.instance_id)


class InstanceStopImpossible(Exception):

    def __init__(self, instance_id, instance_state):
        self.instance_id = instance_id
        self.instance_state = instance_state

    def __str__(self):
        return('It is not possible to stop the instance %s with the state %s'
               % (self.instance_id, self.instance_state))


class InstanceStartImpossible(Exception):

    def __init__(self, instance_id, instance_state):
        self.instance_id = instance_id
        self.instance_state = instance_state

    def __str__(self):
        return('It is not possible to start the instance %s with the state %s'
               % (self.instance_id, self.instance_state))

# EBS snapshot exceptions


class SnapshotCreateTagError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error creating EBS snapshot tag: %s' % self.error)


class SnapshotCreateError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error creating EBS snapshot: %s' % self.error)


class SnapshotsFetchError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error fetching EBS snapshots: %s' % self.error)


class NoSnapshotsForVolume(Exception):

    def __init__(self, volume_id):
        self.volume_id = volume_id

    def __str__(self):
        return('Volume %s does not have snapshots' % self.volume_id)


class InvalidSnapshot(Exception):

    def __init__(self, snapshot_id):
        self.snapshot = snapshot

    def __str__(self):
        return('Snapshot %s does not exist' % self.snapshot_id)

# EBS volume exceptions


class VolumeFetchError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error fetching EBS Volume: %s' % self.error)


class InvalidVolume(Exception):

    def __init__(self, volume_id):
        self.volume_id = volume_id

    def __str__(self):
        return('Volume %s does not exist' % self.volume_id)


class InvalidVolumeID(Exception):

    def __init__(self, volume_id):
        self.volume_id = volume_id

    def __str__(self):
        return('%s is an invalid volume id' % self.volume_id)


class InvalidVolumeType(Exception):

    def __init__(self, vtype):
        self.vtype = vtype

    def __str__(self):
        return('Invalid Volume Type: %s' % self.vtype)


class NoMatchingVolumes(Exception):

    def __init__(self, instance_id, devices):
        self.instance_id = instance_id
        self.devices = devices

    def __str__(self):
        return('Regex \'%s\' does not match any volumes for instance %s'
               % (self.devices, self.instance_id))


class InvalidPIOPSValue(Exception):

    def __init__(self, piops):
        self.piops = piops

    def __str__(self):
        return('Invalid PIOPS volume: %s' % self.piops)


class InvalidPIOPSRatio(Exception):

    def __init__(self, volume_id, piops, MAX_RATIO):
        self.volume_id = volume_id
        self.piops = piops
        self.MAX_RATIO = MAX_RATIO

    def __str__(self):
        return('Size/IOPS ratio (%s) for volume %s is not valid (must be'
               ' better lower or equal than %s)' % (self.piops, self.volume_id,
                                                    self.MAX_RATIO))


class VolumeCreateTagError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return('Error creating EBS Volume tag: %s' % self.error)


class VolumeNotAttached(Exception):

    def __init__(self, volume_id):
        self.piops = volume_id

    def __str__(self):
        return('Volume %s is not attached to any instance' % self.volume_id)


class ErrorAttachingVolume(Exception):

    def __init__(self, volume_id, error):
        self.volume_id = volume_id
        self.error = error,

    def __str__(self):
        return('Error attaching volume %s: %s' % (self.volume_id, self.error))


class ErrorDeletingVolume(Exception):

    def __init__(self, volume_id, error):
        self.volume_id = volume_id
        self.error = error,

    def __str__(self):
        return('Error deleting volume %s: %s' % (self.volume_id, self.error))


class ErrorDetachingVolume(Exception):

    def __init__(self, volume_id, error):
        self.volume_id = volume_id
        self.error = error,

    def __str__(self):
        return('Error detaching volume %s: %s' % (self.volume_id, self.error))


class ErrorCreatingVolume(Exception):

    def __str__(self):
        return('Error creating volume')


class ErrorAllVolumesSameType(Exception):

    def __init__(self, vtype):
        self.vtype, = vtype,

    def __str__(self):
        return('You are trying to migrate all volumes from %s type to %s type'
               % (self.vtype, self.vtype))


class ErrorAllVolumesSamePIOPS(Exception):

    def __str__(self):
        return('You are trying to migrate all volumes to the same IOPS value'
               ' they already have')

# Program argument exceptions


class OptionNotPresent(Exception):

    def __init__(self, option):
        self.option = option

    def __str__(self):
        return('Option --%s is not present' % self.option)


class OptionsAlternativesNotPresent(Exception):

    def __init__(self, option1, option2):
        self.option1 = option1
        self.option2 = option2

    def __str__(self):
        return('You need to specify either --%s or --%s' % (self.option1,
                                                            self.option2))


class InvalidVolumeTypeio1(Exception):

    def __str__(self):
        return('Volume type is io1, specify iops (see --help)')


class OptInvalidValue(Exception):

    def __init__(self, option):
        self.option = option

    def __str__(self):
        return('Unknown value for --%s' % self.option)


class OptInvalidPosInteger(Exception):

    def __init__(self, option):
        self.option = option

    def __str__(self):
        return('--%s must have an positive integer value' % self.option)


class OptInvalidBoolean(Exception):

    def __init__(self, option):
        self.option = option

    def __str__(self):
        return('--%s must have an boolean value' % self.option)


class OptInvalidPosIntegerBoolean(Exception):

    def __init__(self, option):
        self.option = option

    def __str__(self):
        return('--%s must be have a positive integer or boolean value'
               % self.option)
