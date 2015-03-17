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


from connection import ec2conn
from datetime import datetime, timedelta
from dateutils import timedelta_months, timedelta_to_strf
from exceptions import InstanceFetchError, InvalidVolume, InvalidSnapshot
from exceptions import NoSnapshotsForVolume, SnapshotCreateError
from exceptions import SnapshotCreateTagError, SnapshotsFetchError
from exceptions import VolumeFetchError
from instances import get_instance_by_id
from time import sleep


def get_snapshot_by_id(snapshot_id, region):
    """ Get a snapshot for a given snapshot id

    Args:
        snapshot_id: A string with the snapshot id to fetch
        region: A string with the AWS region where the snapshot is
    Returns:
        A boto.ec2.snapshot.Snapshot object
    Raises:
        InvalidSnapshot: If the snapshot id was not found
    """
    conn = ec2conn(region)
    snapshot = conn.get_all_snapshots(snapshot_ids=snapshot_id)[0]
    if snapshot is None:
        raise InvalidSnapshot(snapshot_id)
    return(snapshot)


def get_snapshots_by_volume_id(volume_id, region):
    """ Get a list of snapshots for a given volume-id

    Args:
        volume_id: A string with the volume-id for the snapshot
        region: A string with the AWS region where the snapshot is
    Returns:
        A list of boto.ec2.snapshot.Snapshot objects belonging to the volume
    Raises:
        SnapshotsFetchError: If there was a problem fetching the snapshots
        NoSnapshotsForVolume: If the volume has not any snapshot
    """
    snapshots = []
    conn = ec2conn(region)
    # Test if the volume exist
    from volumes import get_volume_by_id
    get_volume_by_id(volume_id, region)
    # Get all the snapshots for the given volume
    snapshots = []
    try:
        all_snapshots = conn.get_all_snapshots(owner='self')
    except Exception as e:
        raise SnapshotsFetchError(e)
    for snapshot in all_snapshots:
        if snapshot.volume_id == volume_id:
            snapshots.append(snapshot)
    if len(snapshots) == 0:
        raise NoSnapshotsForVolume(volume_id)
    return(snapshots)


def create_snapshot_tag(snapshot, region, tagname, value):
    """ Create a new tag for the given snapshot

    Args:
        volume_id: A string with the snapshot-id for the snapshot
        region: A string with the AWS region where the snapshot is
        tagname: A string with the name for the new tag
        value: A string with the value for the new tag
    Returns:
        True if the operation succeeded
    Raises:
        SnapshotCreateTagError: If it was not possible to create the tag
    """
    try:
        conn = ec2conn(region)
        conn.create_tags(snapshot.id, {"%s" % tagname: "%s" % value})
    except Exception as e:
        raise SnapshotCreateTagError(e)
    return(True)


def create_snapshot_by_volume_id(volume_id, region, dry, name=None,
                                 description=None):
    """ Make a snapshot from a given volume-id

    Args:
        volume_id: A string with the EBS volume-id to create the snapshot
        region: A string with the AWS region where the volume is
        dry: A boolean stating if the action is simulated or not
        name: A string with the name for the new snapshot (optional)
        description: A string with the value for the description
    Returns:
        A boto.ec2.snapshot.Snapshot object with the created snapshot or
        None if this was a dry run
    Raises:
        SnapshotCreateError: If there was an error creating the snapshot
    """
    device = None
    instance = None
    conn = ec2conn(region)
    # Fetch volume object
    from volumes import get_volume_by_id
    volume = get_volume_by_id(volume_id, region)
    # Fill Name
    if name is None:
        try:
            name = volume.tags['Name']
        except:
            name = volume.id
    # Fill description
    if description is None:
        device = volume.attach_data.device
        if device:
            instance = get_instance_by_id(
                volume.attach_data.instance_id, region)
            instance_name = instance.tags['Name']
            if instance_name is None:
                instance_name = instance.id
            description = "%s %s" % (instance_name, device)
        else:
            description = 'Volume was not attached'
    # Perform the snapshot
    try:
        snapshot = conn.create_snapshot(volume_id, description, dry_run=dry)
    except Exception as e:
        try:
            if 'DryRun flag is set' in e.body:
                pass
        except:
            raise SnapshotCreateError(e)
    if dry is False:
        create_snapshot_tag(snapshot, region, "Name", name)
        return(snapshot)
    else:
        return(None)


def snapshot_wait_creation(snapshot_id, region):
    """ Wait till a snapshot is finished

    Args:
        volume_id: A string with the snapshot-id
        region: A string with the AWS region where the volume is
    Raises:
        SnapshotCreateError: If there was an error creating the snapshot
    """
    conn = ec2conn(region)
    snapshot = conn.get_all_snapshots(snapshot_id)[0]
    try:
        while snapshot.status != "completed":
            sleep(60)
            snapshot.update(validate=True)
    except Exception as e:
        raise SnapshotCreateError(e)


class SavedSnapshot(object):

    """ Class to create snapshot objects for the save list

        Args:
            start_time: A datetime object with the start time of the snapshot
            id: A string with the snapshot identifier
            type: A string with the snapshot type
    """

    def __init__(self, id, start_time, type=None):
        self.id = id
        self.type = type
        self.start_time = start_time


def create_test_snapshot_objects(total):
    """ Create an array with n*3 snapshot objects for testing

        Args:
            total: number of snapshot objects to create
        Returns:
            A list of SavedSnapshot objects
    """
    snapshots = []
    now = datetime.utcnow()
    for i in range(0, total):
        snapshots.append(SavedSnapshot("snap-%07da" % i,
                                       timedelta_to_strf(now, days=i)))
        snapshots.append(SavedSnapshot("snap-%07db" % i,
                                       timedelta_to_strf(now, days=i,
                                                         minutes=30)))
        snapshots.append(SavedSnapshot("snap-%07dc" % i,
                                       timedelta_to_strf(now, days=i,
                                                         minutes=120)))
    return(snapshots)


def clean_snapshots_by_volume_id(volume_id, region, hourly_backups,
                                 daily_backups, weekly_backups,
                                 monthly_backups, dry, test,
                                 test_number):
    """ Clean EBS Snapshots for a given EBS ID

      Args:
          volume_id: A string with the EBS volume-id to create the snapshot
          region: A string with the AWS region where the instance is
          hourly_backups: An integer with the number of hourly backups to save
          daily_backups: An integer with the number of daily backups to save
          weekly_backups: An integer with the number of weekly backups to save
          monthly_backups: An integer with the number of monthly backups to
                           salve, or True to save all monthly backups, or False
                           to delete all monthly backups.
          dry: A boolean stating if the action is simulated or not
          test: run the function with testing snapshots (not real)
          test_number: the number of testing snapshots
      Returns:
          A list with dicts in the form
          {
            'snapshot-id': '...',
            'start_time' : '...',
            'type' : '...',
            'error': '...'
          }

          If type is not None, the snapshot was saved, else was deleted
          If error is not None, the procedure tried to deleted the snapshot
          but it couldn't because of an error, and the field contains the
          error's value
    """
    now = datetime.utcnow()
    # Datetimes for most recent limits for each kind of backup
    last_hour = datetime(now.year, now.month, now.day, now.hour)
    last_midnight = datetime(now.year, now.month, now.day)
    last_sunday = (datetime(now.year, now.month, now.day) -
                   timedelta(days=(now.weekday() + 1) % 7))
    last_first = datetime(now.year, now.month, 1)

    # There are no snapshots older than 1/1/2006 (year when AWS started
    # working
    oldest_snapshot_date = datetime(2006, 1, 1)

    # Fill the list of snapshots
    if test is True:
        snapshots = create_test_snapshot_objects(test_number)
    else:
        snapshots = get_snapshots_by_volume_id(volume_id, region)

    # Sort snapshots by date and time (descending)
    snapshots.sort(cmp=lambda x,
                   y: cmp(x.start_time, y.start_time), reverse=True)

    # No days, weeks or monts founds so far
    find_hours = 0
    find_days = 0
    find_weeks = 0
    find_months = 0

    # Dictionary to save snapshots to be preserved
    processed_snapshots = []

    for snapshot in snapshots:
        processed_snapshots.append({"snapshot_id": snapshot.id,
                                    "start_time": snapshot.start_time,
                                    "type": None,
                                    "error": None})
        # Convert snapshot date (string) to date object to compare
        snapshot_date = datetime.strptime(snapshot.start_time,
                                          '%Y-%m-%dT%H:%M:%S.000Z')
        found = False

        # Test every hour till oldest_snapshot_date and save if we still
        # don't have enough hourly backups
        if find_hours < hourly_backups:
            hours = 0
            while (not found and ((last_hour - timedelta(hours=hours)) >
                                  oldest_snapshot_date)):
                if ((snapshot_date.date() == (last_hour -
                   timedelta(hours=hours)).date()) and
                    (snapshot_date.hour == (last_hour -
                                            timedelta(hours=hours)).hour)):
                    for i in range(len(processed_snapshots)):
                        if (processed_snapshots[i]['snapshot_id'] ==
                                snapshot.id):
                            processed_snapshots[i]['type'] = "hourly"
                    find_hours += 1
                    found = True
                    # To ignore more backups for the day, jump to the previous
                    # hour
                    last_hour = last_hour - timedelta(hours=hours + 1)
                hours += 1

        # Test every day till oldest_snapshot_date and save if we still
        # don't have enough daily backups
        elif find_days < daily_backups:
            days = 0
            while (not found and ((last_midnight - timedelta(days=days)) >
                                  oldest_snapshot_date)):
                if snapshot_date.date() == (last_midnight -
                                            timedelta(days=days)).date():
                    for i in range(len(processed_snapshots)):
                        if (processed_snapshots[i]['snapshot_id'] ==
                                snapshot.id):
                            processed_snapshots[i]['type'] = "daily"
                    find_days += 1
                    last_sunday = (snapshot_date -
                                   timedelta(days=(snapshot_date.weekday() + 1)
                                             % 7))
                    # If the snapshot is sunday, then the calculate previous
                    # sunday
                    if last_sunday.date() == snapshot_date.date():
                        last_sunday = (snapshot_date -
                                       timedelta(days=(snapshot_date.weekday()
                                                       + 1)
                                                 % 7 + 7))
                    found = True
                    # To ignore more backups for the day, jump to the previous
                    # midnight
                    last_midnight = last_midnight - timedelta(days=days + 1)
                days += 1

        # Test every sunday till oldest_snapshot_date and save if we still
        # don't have enough weekly backups
        elif find_weeks < weekly_backups:
            weeks = 0
            while (not found and ((last_sunday - timedelta(days=weeks * 7)) >
                                  oldest_snapshot_date)):
                # If snapshot date is equal to the tested sunday, save it
                if (snapshot_date.date() == (last_sunday -
                   timedelta(days=weeks * 7)).date()):
                    for i in range(len(processed_snapshots)):
                        if (processed_snapshots[i]['snapshot_id'] ==
                                snapshot.id):
                            processed_snapshots[i]['type'] = "weekly"
                    find_weeks += 1
                    last_first = timedelta_months(snapshot_date, 0)
                    # If the snapshot the first of the month, then the
                    # calculate previous one
                    if last_first.date() == snapshot_date.date():
                        last_first = timedelta_months(last_first, 1)
                    found = True
                    # To ignore more backups for the week, jump to the previous
                    # sunday
                    last_sunday = (
                        last_sunday - timedelta(days=(weeks + 1) * 7))
                weeks += 1

        # Test 1st day of every month till oldest_snapshot_date and save if we
        # still don't have enough hourly backups
        elif (find_months < monthly_backups) or monthly_backups is True:
            months = 0
            while (not found and
                   (timedelta_months(last_first, months) >
                    oldest_snapshot_date)):
                if (snapshot_date.date() ==
                        timedelta_months(last_first, months).date()):
                    for i in range(len(processed_snapshots)):
                        if (processed_snapshots[i]['snapshot_id'] ==
                           snapshot.id):
                            processed_snapshots[i]['type'] = "monthly"
                    find_months += 1
                    found = True
                    # To ignore more backups for the month, jump to the
                    # previous month start
                    last_first = timedelta_months(last_first, months + 1)
                months += 1
    for snapshot in snapshots:
        for i in range(len(processed_snapshots)):
            if (processed_snapshots[i]['snapshot_id'] == snapshot.id and
                    processed_snapshots[i]['type'] is None):
                if test is False:
                    try:
                        snapshot.delete(dry_run=dry)
                    except Exception as e:
                        try:
                            if 'DryRun flag is set' in e:
                                pass
                        except:
                            for i in range(len(processed_snapshots)):
                                if (processed_snapshots[i]['snapshot_id'] ==
                                        snapshot.id):
                                    processed_snapshots[i]['error'] = e
                            pass
    return(processed_snapshots)
