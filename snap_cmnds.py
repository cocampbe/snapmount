import socket, subprocess, os

sym_dir = '/opt/emc/SYMCLI/bin'
os.environ["PATH"] += os.pathsep + sym_dir
host = socket.gethostname().split(".")[0]

def check_sid(sid):
  if sid not in sids:
    print "Invalid source sid. Valid sids are:"
    print "   " + str(sids.keys())
    exit(1)


def check_snap_sg(dest_sid):
  sg_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  print "Checking for SG", sg_name
  symsg_show = subprocess.Popen(['symsg', '-sid', array_id, 'show', sg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  symsg_show.wait()
  if symsg_show.returncode != 0:
    print " * SG does not exist. Creating SG", sg_name
    symsg_create = subprocess.Popen(['symsg', '-sid', array_id, 'create', sg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    symsg_create.wait()
    if symsg_create.returncode != 0:
      print " * Error creating SG. Exiting."
      exit(1)
  else:
    print " * SG", sg_name, "exists. Continuing..."


def check_snap_tdev(src_sid,dest_sid):
  tdev_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  sg_name = tdev_name
  print "Checking if tdev", tdev_name, "exists."
  symdev_list = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-identifier', 'device_name'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_symdev_list = subprocess.Popen(['grep', '-w', tdev_name], stdin=symdev_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_symdev_list.wait()
  if grep_symdev_list.returncode != 0:
    print " * Target device does not exist. Creating device", tdev_name, "."
    src_dev_size = get_source_disk_size(src_sid)
    symconf_status = subprocess.Popen(['symconfigure', '-sid', array_id, '-cmd', "create dev count=1,size=" + src_dev_size + "mb,config=tdev,emulation=fba,preallocate size=all,sg=" + sg_name + ",device_name=" + tdev_name, 'commit', '-nop'])
  else:
     print " * Device", tdev_name, "exists. Continuing..."
    

def check_snap_tdev_size(src_sid,dest_sid):
  tdev_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  sg_name = tdev_name
  print "Checking if source and target tdev sizes match."
  src_dev_size = get_source_disk_size(src_sid)
  dest_dev_size = get_target_disk_size(dest_sid)
  if src_dev_size > dest_dev_size: 
    print " * Source device is larger than destination device. Attempting to grow target device ", tdev_name, "."
    print " * Getting symid for ", tdev_name, "."
    symdev_list = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-identifier', 'device_name'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    grep_symdev_list = subprocess.Popen(['grep', '-w', tdev_name], stdin=symdev_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tdev_num = grep_symdev_list.communicate()[0].split()[0]
    print " * Target device number is ", tdev_num, "."
    symdev_resize = subprocess.Popen(['symdev', '-sid', array_id, 'modify', tdev_num, '-tdev', '-cap', src_dev_size, '-captype', 'MB', '-nop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    symdev_resize.wait()
    if symdev_resize.returncode != 0:
      print " * Error growing target device ", tdev_name, ". Exiting."
      exit(1)
  else: 
    print " * Target device size matches source. Continuing..."
    

def get_source_disk_size(src_sid):
  src_dev_name = ''.join(sids[src_sid] + "_" + src_sid).upper()
  print " * Getting source device size for ", src_dev_name, "."
  symdev_list = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-identifier', 'device_name'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_symdev_list = subprocess.Popen(['grep', '-w', src_dev_name], stdin=symdev_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  dev_num = grep_symdev_list.communicate()[0].split()[0].strip()
  print "   * Sym device name is ", dev_num, "."
  src_device_info = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-devs', dev_num], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_src_device_info = subprocess.Popen(['grep', '-w', dev_num], stdin=src_device_info.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  src_dev_size = grep_src_device_info.communicate()[0].split()[-1].strip()
  print "   * Sym device size is ", src_dev_size, "MB."
  return src_dev_size


def get_target_disk_size(dest_sid):
  dest_tdev_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  print " * Getting target device size for ", dest_tdev_name, "."
  symdev_list = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-identifier', 'device_name'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_symdev_list = subprocess.Popen(['grep', '-w', dest_tdev_name], stdin=symdev_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  dev_num = grep_symdev_list.communicate()[0].split()[0].strip()
  print "   * Sym device name is ", dev_num, "."
  src_device_info = subprocess.Popen(['symdev', '-sid', array_id, 'list', '-devs', dev_num], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_dest_device_info = subprocess.Popen(['grep', '-w', dev_num], stdin=src_device_info.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  dest_dev_size = grep_dest_device_info.communicate()[0].split()[-1].strip()
  print "   * Sym device size is ", dest_dev_size, "MB."
  return dest_dev_size


def create_snap(src_sid,dest_sid):
  snap_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  src_sg_name = ''.join(sids[src_sid] + "_" + src_sid).upper()
  print "Checking if snapshot ", src_sg_name, " exists."
  snapvx_status = subprocess.Popen(['symsnapvx', '-sid', array_id, 'list', '-sg', src_sg_name, '-snapshot_name', snap_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  snapvx_status.wait()
  if snapvx_status.returncode != 0: 
    print " * Snap does not exist. Creating snap."
    snapvx_establish = subprocess.Popen(['symsnapvx', '-sid', array_id, '-sg', src_sg_name, '-name', snap_name, 'establish', '-nop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    snapvx_establish.wait()
    if snapvx_establish.returncode != 0:
      print " * Error creating snap ", snap_name, " from ", src_sg_name, ". Exiting."
      exit(1)
    symsnapvx_list = subprocess.Popen(['symsnapvx', '-sid', array_id, 'list', '-sg', src_sg_name, '-snapshot_name', snap_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  else:
    print " * Snap ", snap_name, " exists. Continuing..."


def link_snap(src_sid,dest_sid):
  snap_name = ''.join(host + "_" + dest_sid + "_SNAP").upper()
  src_sg_name = ''.join(sids[src_sid] + "_" + src_sid).upper()
  dest_sg_name = ''.join(host + "_" + dest_sid + "_SNAP").upper()
  print "Checking if snapshot is already linked."
  snapvx_link_status = subprocess.Popen(['symsnapvx', '-sid', array_id, 'list', '-sg', src_sg_name, '-snapshot_name', snap_name, '-linked'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  snapvx_link_status_out, snapvx_link_status_err = snapvx_link_status.communicate() 
  if "do not have any Snapvx information" in snapvx_link_status_err:
    print " * Snap is not linked to an SG. Creating link of ", snap_name, " to ", dest_sg_name, "."
    snapvx_link = subprocess.Popen(['symsnapvx', '-sid', array_id, '-sg', src_sg_name, '-lnsg', dest_sg_name, '-snapshot_name', snap_name, 'link', '-copy', '-nop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    snapvx_link.wait() 
    if snapvx_link.returncode != 0:
      print " * Error linking snap ", snap_name, " to ", dest_sg_name, ". Exiting."
      exit(1)
  else: 
    print " * Link of ", snap_name, " to ", dest_sg_name, " already exists. Continuing..."
    

def unlink_and_terminate_snap(src_sid,dest_sid):
  snap_name = ''.join(host + "_" + dest_sid + "_snap").upper()
  src_sg_name = ''.join(sids[src_sid] + "_" + src_sid).upper()
  dest_sg_name = "{dest_host}_{dest_sid}_snap".format(dest_host=host,dest_sid=dest_sid).upper()
  print "Unlinking snap", snap_name, "from", src_sg_name, "."
  snapvx_unlink = subprocess.Popen(['symsnapvx', '-sid', array_id, '-sg', src_sg_name, '-lnsg', dest_sg_name, '-snapshot_name', snap_name, 'unlink', '-symforce', '-nop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  snapvx_unlink_out,snapvx_unlink_err =  snapvx_unlink.communicate()
  if snapvx_unlink.returncode != 0:
    if "already in the desired" in snapvx_unlink_err:
      print " * Snapshot is already unlinked. Continuing..."
    else:
      print " * Error unlinking snap. Exiting."
      exit(1)
  else:
    print " * Unlink successful!"
  print "Terminating snap", snap_name, "."
  snapvx_terminate = subprocess.Popen(['symsnapvx', '-sid', array_id, '-sg', src_sg_name, '-snapshot_name', snap_name, 'terminate', '-nop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  snapvx_terminate_out, snapvx_terminate_err = snapvx_terminate.communicate()
  if snapvx_terminate.returncode != 0:
    if "No snapshot was found" in snapvx_terminate_err:
      print " * Snapshot is already Terminated. Continuing..."
    else:
      print "Error terminating snap. Exiting."
      exit(1)
  else:
    print " * Termination successful!"
    

def add_sg_to_mv(dest_sid):
  dest_sg_name = "{dest_host}_{dest_sid}_SNAP".format(dest_host=host,dest_sid=dest_sid).upper()
  parent_sg_name = "{dest_host}_SG".format(dest_host=host).upper()
  print "Checking if", dest_sg_name, "is already a child of", parent_sg_name, "."
  symsg_parent_info = subprocess.Popen(['symsg', '-sid', array_id, 'show', parent_sg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_symsg_parent_info = subprocess.Popen(['grep', '-w', dest_sg_name], stdin=symsg_parent_info.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if "IsChild" in grep_symsg_parent_info.communicate()[0]: 
    print " *", dest_sg_name, "is already a child of SG", parent_sg_name," . Continuing..."
  else: 
    print " *", dest_sg_name, "is not a child of", parent_sg_name, ". Adding."
    symsg_add_status = subprocess.Popen(['symsg', '-sid', array_id, '-sg', parent_sg_name, 'add', 'sg', dest_sg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    symsg_add_status.wait()
    if symsg_add_status.returncode != 0: 
      print " * Error adding", dest_sg_name, "to", parent_sg_name, ". Exiting."
      exit(1)
        
    
def remove_sg_from_mv(dest_sid):
  sg_name = "{host}_{dest_sid}_SNAP".format(host=host,dest_sid=dest_sid).upper()
  parent_sg_name = "{dest_host}_SG".format(dest_host=host).upper()
  print "Removing", sg_name, "from parent", parent_sg_name, "."
  symsg_remove = subprocess.Popen(['symsg', '-sid', array_id, '-sg', parent_sg_name, 'remove', 'sg', sg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  symsg_remove_out,symsg_remove_err = symsg_remove.communicate()
  if symsg_remove.returncode != 0:
    if "No Storage groups" in symsg_remove_err.strip():
      print " * Storage group not found in parent. Continuing..."
    else:
      print " * Error removing", sg_name, "from", parent_sg_name, ". Exiting."
      exit(1)
   

def scan_disks():
  print "Scanning bus for new disks."
  scan_hba = subprocess.Popen(['/etc/opt/emcpower/emcplun_linux', 'scan', 'hba', '-noprompt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  scan_hba.wait()
  if scan_hba.returncode != 0: 
    print " * Error scanning bus for disks. Exiting."
    exit(1)
  else:
    print " * Scanning complete."
    

def disk_cleanup(dest_sid):
  disk_dev_file = get_disk_dev_file(dest_sid).strip()
  print "Attempting to remove disk."
  if "Not found" in disk_dev_file:
    print " * No disk found. Continuing..."
  else: 
    print "Removing disk", disk_dev_file, "."
    remove_disk_status = subprocess.Popen(['/etc/opt/emcpower/emcplun_linux', 'remove', disk_dev_file, '-noprompt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    remove_disk_status.wait()
    if remove_disk_status.returncode != 0: 
      print " * Error removing disk. Exiting."
      exit(1)
    

def import_activate_vg(dest_sid):
  disk_dev_file = get_disk_dev_file(dest_sid).strip()
  vg_basename = "vg" + dest_sid
  vgs_returncode = check_vgs(vg_basename)
  if vgs_returncode == 0:
    print " * Volume group", vg_basenamei, "is already imported. Continuing..."
  else:
    print "Importing and Activating volume group"
    print " * Running vgimportclone with basename vg{dest_sid}.".format(dest_sid=dest_sid)
    vgimportclone = subprocess.Popen(['/sbin/vgimportclone', '--basevgname', vg_basename, disk_dev_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vgimportclone.wait()
    if vgimportclone.returncode == 0:
      print "  * Vgimportclone successful."
    else:
      print "  * Vgimportclone error. Exiting."
      exit(1)
    print " * Activating volume group."
    vgchange = subprocess.Popen(['/sbin/vgchange', '-a', 'y', vg_basename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vgchange.wait()
    if vgchange.returncode == 0:
      print "  * Vgchange successful."
    else:
      print "  * Vgchange error. Exiting."
      exit(1)


def deactivate_vg(dest_sid):
  vg_name = "vg" + dest_sid
  vgs_returncode = check_vgs(vg_name)
  print "Deactivating VG vg{dest_sid}.".format(dest_sid=dest_sid)
  if vgs_returncode == 0:
    vgchange = subprocess.Popen(['/sbin/vgchange', '-a', 'n', "vg{dest_sid}".format(dest_sid=dest_sid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vgchange.wait()
    if vgchange.returncode != 0:
      print " * Error deactivating volume group. Exiting."
      exit(1)
    else:
      print " * Deactivation successful!"
  else:
    print " * Volume group not present. Continuing..."


def check_vgs(vg_name):
  vgs = subprocess.Popen(['/sbin/vgs', vg_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  vgs.wait()
  return vgs.returncode


def get_disk_dev_file(dest_sid):
  dest_sg_name = "{dest_host}_{dest_sid}_SNAP".format(dest_host=host,dest_sid=dest_sid).upper()
  print "Getting device file for {dest_sg_name}.".format(dest_sg_name=dest_sg_name)
  syminq_list = subprocess.Popen(['syminq', '-identifier', 'device_name'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_syminq_list = subprocess.Popen(['grep', 'emcpower'], stdin=syminq_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_grep_syminq_list = subprocess.Popen(['grep', '-w', dest_sg_name], stdin=grep_syminq_list.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  try:
    disk_dev_file = grep_grep_syminq_list.communicate()[0].split()[0].strip()
  except:
    return "Not found"
  if "emcpower" not in disk_dev_file: 
    print " * Device is null. Error getting disk device file. Exiting."
    exit(1)
  else:  
    print " * Device file is {disk_dev_file}.".format(disk_dev_file=disk_dev_file)
  return disk_dev_file


def clean_fs(dest_sid):
  if check_mounts(dest_sid) == 0:
    print " * Skipping file system check"
  else:
    lvols = ('data', 'ctl', 'arch')
    for lvol in lvols:
      print "Checking file system /dev/vg{dest_sid}/{lvol}.".format(dest_sid=dest_sid,lvol=lvol)
      fsck = subprocess.Popen(['/sbin/fsck', '-p', "/dev/vg{dest_sid}/{lvol}".format(dest_sid=dest_sid,lvol=lvol)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      fsck.wait()
      if fsck.returncode == 0:
        print " * File system is clean."
      else:
        print " * Error checking file system."
    

def mount_lvols(dest_sid):
  if check_mounts(dest_sid) == 0:
    print " * Skipping mount. File systems already mounted."
  else:
    print " * Mounting file systems."
    mounts = {'data':'oradata', 'ctl':'oractl', 'arch':'arch'}
    for lvol in mounts:
      if not os.path.isdir("/{dest_sid}/{sub_folder}".format(dest_sid=dest_sid,sub_folder=mounts[lvol])):
        mkdir_p("/{dest_sid}/{sub_folder}".format(dest_sid=dest_sid,sub_folder=mounts[lvol]))
      mount = subprocess.Popen(['/bin/mount', "/dev/vg{dest_sid}/{lvol}".format(dest_sid=dest_sid,lvol=lvol), "/{dest_sid}/{sub_folder}".format(dest_sid=dest_sid,sub_folder=mounts[lvol])], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def umount_lvols(dest_sid):
  if  check_mounts(dest_sid) == 0:
    print "Umounting file systems."
    mounts = ('arch', 'oradata', 'oractl')
    for mount in mounts: 
      unmount = subprocess.Popen(['/bin/umount', "/{dest_sid}/{mount}".format(dest_sid=dest_sid,mount=mount)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      unmount.wait()
      if unmount.returncode != 0:
        print " * Error unmounting file system /{dest_sid}/{mount}.".format(dest_sid=dest_sid,mount=mount)
        print " * Check that mount is not in use and try again." 
        exit(1)
    print " * Unmount successful!"
  else:
    print " * Continuing..."

def check_emc():
  is_powerpath_installed = subprocess.Popen(['/bin/rpm', '-q', 'EMCpower.LINUX'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  is_powerpath_installed.wait()
  if is_powerpath_installed == 0:
    print "EMC Powerpath is not installed. Exiting."
    exit(1)
  is_symcli_installed = subprocess.Popen(['/bin/rpm', '-q', 'symcli-symcli'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  is_symcli_installed.wait()
  if is_symcli_installed == 0: 
    print "EMC Solutions Enabler is not installed. Exiting."
    exit(1)
    

def check_mounts(dest_sid):
  print "Checking if file systems are mounted." 
  df = subprocess.Popen(['df', '-lPk'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  grep_df = subprocess.Popen(['grep', dest_sid], stdin=df.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  mounts = grep_df.communicate()[0].splitlines()
  if len(mounts) == 3:
    print " * File systems are mounted."
    return 0
  else :
    print " * File systems are not mounted."
    return 1
