ebs-tools
=========

[![Build Status](https://jenkins-juliogonzalez.rhcloud.com/job/ebs-tools-build/badge/icon)](https://jenkins-juliogonzalez.rhcloud.com/job/ebs-tools-build/)

Tools to manage EBS volumes and snapshots

Tools
-----

### change_type

To change types of EBS volumes attached to an instance, in parallel.

Allows to select which volumes are to be migrated, and will save encryption or tags (optionally) if present.

### clean_snapshots

To clean old EBS snapshots for a volume.

Allows to save hourly, daily, weekly or monthly snapshots

### clean_ec2_snapshots

To clean old EBS snapshots for volumes attached to an instance.

Allows to save hourly, daily, weekly or monthly snapshots

### make_snapshot

To make an EBS snapshot for a volume, optionally saving tags.

### make_ec2_snapshots

To make an EBS snapshot for a volume attached to an instance, optionally saving tags.

Allows to perform snapshots in parallel.

Usage
-----

Call each script with *-h* or *--help* options to get the syntax.
