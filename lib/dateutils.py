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


from datetime import datetime, timedelta


def timedelta_months(date, nmonths):
    """ Substract a number of days from a given date and then get then
        first day of that month

        Needed as timedelta function from standard python doesn't support
        months and we don't want to rely on more third party modules

        Args:
           date: A datetime.date object with the initial date
           nmonths: The number of months to substract
        Returns:
           A datetime.date object with the first day of the month for then
           substraction
    """
    first_day = datetime(date.year, date.month, 1)
    for i in range(0, nmonths):
        first_day = datetime(first_day.year, first_day.month, 1)
        first_day = first_day - timedelta(days=1)
        first_day = datetime(first_day.year, first_day.month, 1)
    return(first_day)


def timedelta_to_strf(date, days=0, seconds=0, microseconds=0,
                      milliseconds=0, minutes=0, hours=0, weeks=0):
    """ Perform a timedelta and return result as string (UTC)

        Args:
           date: A datetime.date object with the initial date
           days: An integer with the number of days to substract
           seconds: An integer with the number of seconds to substract
           microseconds: An integer with the number of microseconds
                         to substract
           milliseconds: An integer with the number of milliseconds
                         to substract
           minutes: An integer with the number of minutes to substract
           hours: An integer with the number of hours to substract
           weeks: An integer with the number of weeks to substract
        Returns:
           A string with the result, as UTC
    """
    diff = date - timedelta(days, seconds, microseconds,
                            milliseconds, minutes, hours, weeks)
    if diff.utcoffset() is None:
        return diff.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    else:
        return diff.strftime('%Y-%m-%dT%H:%M:%S.%z')
