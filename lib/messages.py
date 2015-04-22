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


class bcolors:
    BOLDRED = '\033[1;31m'
    BOLDGREEN = '\033[1;32m'
    BOLDYELLOW = '\033[1;33m'
    BOLDCYAN = '\033[1;36m'
    BOLDPURPLE = '\033[1;35m'
    RESET = '\033[0m'


def print_error(msg):
    """ Print an error message in red """
    print bcolors.BOLDRED + "[ERROR] %s" % msg + bcolors.RESET


def print_warning(msg):
    """ Print a warning message in yellow """
    print bcolors.BOLDYELLOW + "[WARNING] %s" % msg + bcolors.RESET


def print_ok(msg):
    """ Print an ok message in green """
    print bcolors.BOLDGREEN + "[OK] %s" % msg + bcolors.RESET


def print_info(msg):
    """ Print an info message in cyan """
    print bcolors.BOLDCYAN + "[INFO] %s" % msg + bcolors.RESET


def print_special(msg):
    """ Print an info message in cyan """
    print bcolors.BOLDPURPLE + "%s" % msg + bcolors.RESET
