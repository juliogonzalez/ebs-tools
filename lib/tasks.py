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


from exceptions import ErrorAllVolumesSameType, ErrorAllVolumesSamePIOPS
from exceptions import InvalidVolumeType
from instances import get_instance_by_id, get_instance_by_name
from instances import start_instance_and_wait, stop_instance_and_wait
from messages import print_error, print_info, print_ok, print_special
from messages import print_warning
from snapshots import clean_snapshots_by_volume_id
from snapshots import create_snapshot_by_volume_id, snapshot_wait_creation
from threading import currentThread, enumerate, Thread
from volumes import attach_volume, check_iops_ratio, create_volume
from volumes import delete_volume, detach_volume
from volumes import get_volumes_from_instance_by_device
from volumes import get_volumes_from_instance_by_name


def task_clean_snapshots_ec2(region, instance_id=None, instance_name=None,
                             devices=None, volume_name=None,
                             hourly_backups=0, daily_backups=7,
                             weekly_backups=0, monthly_backups=4, dry=True,
                             test=False, test_number=100):
    """ Clean snapshots for volumes attached to an EC2 instance, by device or
        by tag name

        Args:
            instance_id: A string with the EC2 instance-id
            instance_name: A string with the EC2 instance name
            devices: A string with a regex to look for volumes by device
            volumename: A string with a regex to look for volumes by name
            region: A string with the AWS region where the instance is
            hourly_backups: An integer with the number of hourly backups to
                            save
            daily_backups: An integer with the number of daily backups to save
            weekly_backups: An integer with the number of weekly backups to
                            save
            monthly_backups: An integer with the number of monthly backups to
                             save, or True to save all monthly backups, or
                             False to delete all monthly backups.
            dry: A boolean stating if the action is simulated or not
            test: run the function with testing snapshots (not real)
            test_number: the number of testing snapshots
    """
    volumes = []
    if instance_name is not None:
        instance = get_instance_by_name(instance_name, region)
    if instance_id is not None:
        instance = get_instance_by_id(instance_id, region)
    if devices is not None:
        volumes = get_volumes_from_instance_by_device(instance.id, devices,
                                                      region)
    if volume_name is not None:
        volumes = get_volumes_from_instance_by_name(instance.id, volume_name,
                                                    region)
    for volume in volumes:
        task_clean_snapshots_ebs_id(volume.id, region, hourly_backups,
                                    daily_backups, weekly_backups,
                                    monthly_backups, dry, test,
                                    test_number)


def task_clean_snapshots_ebs_id(volume_id, region, hourly_backups=0,
                                daily_backups=7, weekly_backups=0,
                                monthly_backups=4, dry=True, test=False,
                                test_number=100):
    """ Clean EBS Snapshots for a given EBS ID

        Args:
            volume_id: A string with the EBS volume-id to create the snapshot
            region: A string with the AWS region where the instance is
            hourly_backups: An integer with the number of hourly backups to
                            save
            daily_backups: An integer with the number of daily backups to save
            weekly_backups: An integer with the number of weekly backups to
                            save
            monthly_backups: An integer with the number of monthly backups to
                             save, or True to save all monthly backups, or
                             False to delete all monthly backups.
            dry: A boolean stating if the action is simulated or not
            test: run the function with testing snapshots (not real)
            test_number: the number of testing snapshots
    """
    if dry is True or test is True:
        drytext = "[DRY] "
    else:
        drytext = ""
    if test is True:
        print_info("Running in test mode (no real snapshots)")
    else:
        print_info("Cleaning snapshots for volume-id %s" % (volume_id))
    snapshots = clean_snapshots_by_volume_id(volume_id, region, hourly_backups,
                                             daily_backups, weekly_backups,
                                             monthly_backups, dry, test,
                                             test_number)
    for snapshot in snapshots:
        if snapshot['type'] is not None:
            print_info("Saved snapshot %s, date %s, type %s"
                       % (snapshot['snapshot_id'],
                          snapshot['start_time'], snapshot['type']))
    for snapshot in snapshots:
        if snapshot['type'] is None:
            if snapshot['error'] is None:
                print_info("%sDeleted snapshot %s, date %s"
                           % (drytext, snapshot['snapshot_id'],
                              snapshot['start_time']))
            else:
                print_error("It was not possible to delete snapshot %s, "
                            "error: %s" % (snapshot['snapshot_id'],
                                           snapshot['error']))
    print_ok("Unneeded snapshots for %s deleted" % volume_id)


class Snapshot(Thread):
    """ Object to Perform parallel snapshots

    Properties:
        volume_id: A string with the EBS volume-id to create the snapshot
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
        name: A string with the name for the new snapshot (optional)
        description: A string with the value for the description
    """

    def __init__(self, volume_id, region, dry, volume_name, description):
        Thread.__init__(self)
        self.volume_id = volume_id
        self.region = region
        self.dry = dry
        self.volume_name = volume_name
        self.description = description

    def run(self):
        task_create_snapshot_ebs_id(self.volume_id, self.region, self.dry,
                                    self.volume_name, self.description)


def task_create_snapshot_ebs_id(volume_id, region, dry, name=None,
                                description=None):
    """ Make a snapshot from a given volume-id

    Args:
        volume_id: A string with the EBS volume-id to create the snapshot
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
        name: A string with the name for the new snapshot (optional)
        description: A string with the value for the new tag
    Returns:
        A string with the snapshots' ID or None for a dry run
    """
    if dry is True:
        drytext = "[DRY] "
    else:
        drytext = ""
    print_info("%sCreating snapshot for volume-id %s, description: %s..."
               % (drytext, volume_id, description))
    snapshot = create_snapshot_by_volume_id(volume_id, region, dry, name,
                                            description)
    if dry is True:
        snapshot_id = None
        print_ok("%sSnapshot was not created because dry flag is "
                 "enabled" % drytext)
    else:
        snapshot_id = snapshot.id
        print_ok("Snapshot %s was created" % snapshot_id)
    return(snapshot_id)


def task_create_snapshots_ec2(region, instance_id=None, instance_name=None,
                              parallel=False, dry=True, devices=None,
                              volume_name=None, name=None, description=None):
    """ Make a snapshots for volumes attached to an EC2 instance, by device or
        by tag name

    Args:
        instance_id: A string with the EC2 instance-id
        instance_name: A string with the EC2 instance name
        parallel: A boolean (True to create snapshots in parallel)
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
        devices: A string with a regex to look for volumes by device
        volumename: A string with a regex to look for volumes by name
        name: A string with the name for the new snapshot (optional)
        description: A string with the value for the new tag
    Returns:
        A string with the snapshots' ID or None for a dry run
    """
    volumes = []
    if instance_name is not None:
        instance = get_instance_by_name(instance_name, region)
    if instance_id is not None:
        instance = get_instance_by_id(instance_id, region)
    if devices is not None:
        volumes = get_volumes_from_instance_by_device(instance.id, devices,
                                                      region)
    if volume_name is not None:
        volumes = get_volumes_from_instance_by_name(instance.id, volume_name,
                                                    region)
    if parallel:
        print_special("===================================")
        print_special("     STARTING PARALLEL TASKS       ")
        print_special("===================================")
    for volume in volumes:
        if parallel:
            task = Snapshot(volume.id, region, dry, name, description)
            task.start()
        else:
            task_create_snapshot_ebs_id(volume.id, region, dry, name,
                                        description)
    # Main thread
    if parallel:
        main_thread = currentThread()
        for thread in enumerate():
            # Prevent deadlock
            if thread is main_thread:
                continue
            thread.join()
        print_special("===================================")
        print_special("     FINISHED PARALLEL TASKS       ")
        print_special("===================================")


class VolumeMigrate(Thread):
    """ Object to Perform all needed task to change an EBS volume type

    Properties:
        region: A string with the AWS region where the volume will be
        dry: A boolean stating if the action is simulated or not
        instance_id: A string with the instance-id for the instance where there
                     volume is attached.
        volume: A boto.ec2.volume.Volume with the volume to change
        vtype: A string with the new volume type (io1|standard|gp2)
        newpiops: An integer with the new number of PIOPs (only when vtype=io1)
    """

    def __init__(self, region, dry, instance_id, volume, vtype, newpiops, tid):
        Thread.__init__(self)
        self.region = region
        self.dry = dry
        self.instance_id = instance_id
        self.volume = volume
        self.vtype = vtype
        self.newpiops = newpiops
        self.tid = tid

    def run(self):
        if self.dry is True:
            drytext = "[DRY] "
        else:
            drytext = ""
        idtext = "[%s] " % self.tid
        # Construct name
        try:
            name = self.volume.tags['Name']
        except:
            name = self.volume.id
        # Construct description
        description = "Migration from %s" % self.volume.type
        if self.volume.type == "io1":
            description = "%s (%s IOPS) " % (description, self.volume.iops)
        description = "%s to %s" % (description, self.vtype)
        if self.vtype == "io1":
            description = "%s (%s IOPS)" % (description, self.newpiops)
        description = "%s (%s %s)" % (description,
                                      self.volume.attach_data.instance_id,
                                      self.volume.attach_data.device)
        # Perform Snapshot
        snapshot_id = task_create_snapshot_ebs_id(self.volume.id, self.region,
                                                  self.dry,
                                                  description=description)
        if self.dry is False:
            print_info("%s%sWaiting for snapshot %s to be available..."
                       % (drytext, idtext, snapshot_id))
            snapshot_wait_creation(snapshot_id, self.region)
        # Detach volume
        print_info("%s%sDettaching volume %s..." % (drytext, idtext,
                                                    self.volume.id))
        detach_volume(self.volume.id, self.region, self.dry)
        if self.dry is True:
            print_ok("%s%sVolume %s was not dettached because dry flag is "
                     "enabled" % (drytext, idtext, self.volume.id))
        else:
            print_ok("%sVolume %s was dettached" % (idtext, self.volume.id))
        # Create volume
        print_info("%s%sCreate volume from snapshot %s..." % (drytext, idtext,
                                                              snapshot_id))
        if self.vtype == "io1":
            nvolume = create_volume(self.volume.region, self.dry,
                                    self.volume.zone, self.volume.size,
                                    self.vtype, self.newpiops, name,
                                    self.volume.tags, self.volume.encrypted,
                                    snapshot_id)
        if self.vtype == "standard" or self.vtype == "gp2":
            nvolume = create_volume(self.volume.region, self.dry,
                                    self.volume.zone, self.volume.size,
                                    self.vtype, None, name,
                                    self.volume.tags, self.volume.encrypted,
                                    snapshot_id)
        if self.dry is True:
            print_ok("%s%sVolume was not created because dry flag is enabled"
                     % (drytext, idtext))
            print_ok("%s%sNot attaching new volume, as this is a dry run"
                     % (drytext, idtext))
        else:
            print_ok("%sVolume %s was created from snapshot %s"
                     % (idtext, nvolume.id, snapshot_id))
            # Attach volume
            print_info("%sAttaching volume %s to %s as %s..."
                       % (idtext, nvolume.id,  self.instance_id,
                          self.volume.attach_data.device))
            attach_volume(nvolume.id, self.instance_id,
                          self.volume.attach_data.device, self.region,
                          self.dry)
        print_info("%s%sDeleting old volume %s..." % (drytext, idtext,
                                                      self.volume.id))
        delete_volume(self.volume.id, self.region, self.dry)
        if self.dry is True:
            print_ok("%s%sOld volume %s was not deleted because dry flag is "
                     "enabled" % (drytext, idtext, self.volume.id))
        else:
            print_ok("%sOld volume %s was deleted, but remember you still "
                     "have its snapshot in case there're problems!"
                     % (idtext, self.volume.id))


def check_migration_logic(volumes, vtype, newpiops, region):
    """ Check migration logic (if there's something to migrate, IOPs...)

    Args:
        volumes: A list of boto.ec2.volume.Volume to check
        vtype: A string with the new volume type (io1|standard|gp2)
        newpiops: An integer with the new number of PIOPs (only when vtype=io1)
        region: A string with the AWS region where the volume will be
    Returns:
        True if not problems are detected
    Raises:
        ErrorAllVolumesSameType: If all the volumes have the same original and
                                 new type.
        ErrorAllVolumesSamePIOPS: If all the volumes have the same number
                                  original and new PIOPs.
    """
    sametype = 0
    samepiops = 0
    for volume in volumes:
        if ((vtype == "standard" and volume.type == "standard") or
                (vtype == "gp2" and volume.type == "gp2")):
            print_warning("%s will migrate from %s type to %s type which "
                          "doesn't make too much sense" % (volume.id,
                                                           volume.type,
                                                           vtype))
            print_warning("Procedure will continue anyway")
            sametype += 1
        if vtype == "io1":
            if volume.iops == int(newpiops):
                print_warning("%s will migrate from %s IOPS to %s IOPS "
                              "which doesn't make too much "
                              "sense" % (volume.id, volume.iops, newpiops))
                print_warning("Procedure will continue anyway")
                samepiops += 1
            check_iops_ratio(volume.id, newpiops, region)
    if sametype == len(volumes):
        raise ErrorAllVolumesSameType(vtype)
    if samepiops == len(volumes):
        raise ErrorAllVolumesSamePIOPS()
    return(True)


def migrate_volumes(region, dry, devices, vtype, newpiops=None,
                    instance_id=None, instance_name=None):
    """ Change type for all EBS volumes attached to an EC2 instance

    Args:
        region: A string with the AWS region where the volume will be
        dry: A boolean stating if the action is simulated or not
        devices: A string with a regex to look for devices
        vtype: A string with the new volume type (io1|standard|gp2)
        newpiops: An integer with the new number of PIOPs (only when vtype=io1)
        instance_id: A string with the instance-id where the volumes are
                     attached
    Returns:
        True if all the volumes were migrated
    """
    if vtype not in ['gp2', 'io1', 'standard']:
        raise InvalidVolumeType(vtype)
    if dry is True:
        drytext = "[DRY] "
    else:
        drytext = ""
    if instance_name is not None:
        instance = get_instance_by_name(instance_name, region)
    else:
        instance = get_instance_by_id(instance_id, region)
    volumes = get_volumes_from_instance_by_device(instance.id, devices, region)
    check_migration_logic(volumes, vtype, newpiops, region)
    print_info
    print_info("%sStopping instance..." % drytext)
    was_started = stop_instance_and_wait(instance.id, region, dry)
    if was_started is True:
        print_ok("%sInstance stopped" % drytext)
    else:
        print_ok("%sNot stopping instance as it was stopped" % drytext)
    print_special("===================================")
    print_special("     STARTING PARALLEL CHANGES     ")
    print_special("===================================")
    tid = 0
    for volume in volumes:
        task = VolumeMigrate(region, dry, instance.id, volume, vtype, newpiops,
                             tid)
        task.start()
        tid += 1
    # Main thread
    main_thread = currentThread()
    for thread in enumerate():
        # Prevent deadlock
        if thread is main_thread:
            continue
        thread.join()
    print_special("===================================")
    print_special("     FINISHED PARALLEL CHANGES     ")
    print_special("===================================")
    print_ok("%sAll volumes were successfully changed" % drytext)
    if was_started is True:
        print_info("%sStarting instance..." % drytext)
        was_stopped = start_instance_and_wait(instance.id, region, dry)
        print_ok("%sInstance started" % drytext)
    else:
        print_ok("%sNot starting %s as it was stopped before the migration"
                 % (drytext, instance.id))
    print_ok("All tasks finished!")
    return(True)
