#!/usr/bin/env python

import argparse
import os
from subprocess import Popen
import snap_cmnds

parser =  argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-s", "--snap", help="Create and mount a snapshot.")
group.add_argument("-u", "--unsnap", help="Unmount and remove a snapshot.")
parser.add_argument("-d", "--dest", help="Destination. Mount to destination directories.")
parser.add_argument("-m", "--mount", help="Mount filesystems for snapshot.")
parser.add_argument("-v", "--verbose", help="Print more verbose output.")
args = parser.parse_args()

snap_cmnds.array_id = '95'
snap_cmnds.sids = { 'gflwtst1': 'odbdev90',}

if os.geteuid() != 0:
  exit("This script must be run as root.")

snap_cmnds.check_emc()

if args.snap and args.dest:
  snap_cmnds.check_sid(args.snap)
  snap_cmnds.check_snap_sg(args.dest)
  snap_cmnds.check_snap_tdev(args.snap,args.dest)
  snap_cmnds.create_snap(args.snap,args.dest)
  snap_cmnds.check_snap_tdev_size(args.snap,args.dest)
  snap_cmnds.link_snap(args.snap,args.dest)
  snap_cmnds.add_sg_to_mv(args.dest)
  snap_cmnds.scan_disks()
  snap_cmnds.import_activate_vg(args.dest)
  snap_cmnds.clean_fs(args.dest)
  snap_cmnds.mount_lvols(args.dest)
elif args.unsnap and args.dest:
  snap_cmnds.check_sid(args.unsnap)
  snap_cmnds.umount_lvols(args.dest)
  snap_cmnds.deactivate_vg(args.dest)
  snap_cmnds.disk_cleanup(args.dest)
  snap_cmnds.remove_sg_from_mv(args.dest)
  snap_cmnds.unlink_and_terminate_snap(args.unsnap,args.dest)
elif args.mount:
  snap_cmnds.mount_lvols(args.mount) 
else:
  parser.print_help()
