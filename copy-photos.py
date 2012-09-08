#!/usr/bin/env python

import sys
import traceback
import os
import os.path
import string
import time
import shutil
import subprocess
from optparse import OptionParser

from progressbar import *

FILE_TYPES = [
    "crw",
    "cr2",
    "jpg",
    "avi",
    "mov",
    "mp4",
    "mts",
]

# THM files are copied when we look at the original buddy file.  We
# don't want to list them as skipped so we *really* skip them and
# don't say anything.
SPECIAL_FILE_TYPES = [
    "thm",
    "xmp"
]

parser = OptionParser()
parser.add_option("-s", "--source",
                  help="The SOURCE tree to copy from",
                  metavar="SOURCE")
parser.add_option("-d", "--dest",
                  help="The DEST tree to copy to",
                  metavar="DEST")
parser.add_option("-v", "--verbose",
                  action="store_true", default=False,
                  help="More output")
parser.add_option("-n", "--dry_run",
                  action="store_true",
                  default=False,
                  help="Do everything but the actual copy")

(options, args) = parser.parse_args()

if not (options.source and options.dest):
    parser.print_help()
    sys.exit(1)

print "Copying photos from '%s' to '%s'" % (options.source,
                                            options.dest)

copy = []
skip = []
exists = []

copy_size = 0
start_time = time.time()

def my_copy(src, dst):
  """Implement a faithful copy.

  On the mac, shell out to "cp -p" to handle wacky chattr issues with SMB
  shares.
  """
  if sys.platform == "darwin":
    subprocess.check_call(["gcp", "-p", "-f", src, dst])
  else:
    shutil.copy2(src, dst)

def queue_file(source_file, dest_file):
    """Add a file to our copy queue.

    Also check to make sure that the file doesn't exists at the
    destionation.  If it does, do some sanity checks to make sure that
    it is the same file at the dest.
    """
    if os.path.exists(dest_file):
        extra_info = ""
        source_stat = os.stat(source_file)
        dest_stat = os.stat(dest_file)
        if source_stat.st_size != dest_stat.st_size:
            extra_info += "\n    !!! sizes differ !!!"
        if abs(source_stat.st_mtime - dest_stat.st_mtime) > 5:
            extra_info += "\n    !!! times differ !!! %d" % (source_stat.st_mtime - dest_stat.st_mtime)
        if options.verbose or extra_info:
            print "Already exists:"
            print "    %s" % source_file
            print "    %s%s" % (dest_file, extra_info)
            
        exists.append(source_file)
    else:
        if options.verbose:
            print "Queuing copy:"
            print "    %s" % source_file
            print "    %s" % dest_file
        copy.append((source_file, dest_file))
    

print "Scanning directories"
for root, dirs, files in os.walk(options.source):
    files_lc = dict([(string.lower(f), i) for (i, f) in enumerate(files)])
    for (i, file) in enumerate(files):
        (base, ext) = os.path.splitext(file)
        source_ext = string.lower(ext[1:])
        source_file = os.path.join(root, file)
        
        if source_ext in FILE_TYPES:
            dest_subpath = time.strftime("%Y/%m/%Y-%m-%d",
                                         time.localtime(os.path.getmtime(source_file)))
            dest_dir = os.path.join(options.dest, dest_subpath)
            dest_file = os.path.join(dest_dir, file)

            queue_file(source_file, dest_file)

            # we have to look for certain sidecar types, such as THM
            # files and XMP files.  We have to treat these differently
            # here as they may have a different date than their buddy
            # file.
            for sidecar_ext in SPECIAL_FILE_TYPES:
                sidecar_lc = string.lower("%s.%s" % (base, sidecar_ext))
                if sidecar_lc in files_lc:
                    base_sidecar = files[files_lc[sidecar_lc]]
                    source_sidecar = os.path.join(root, base_sidecar)
                    dest_sidecar = os.path.join(dest_dir, base_sidecar)
                    queue_file(source_sidecar, dest_sidecar)

        else:
            if source_ext not in SPECIAL_FILE_TYPES:
                if options.verbose:
                    print "Skipping %s" % source_file
                skip.append(source_file)


print "Copy:    %4d" % len(copy)
print "Existed: %4d" % len(exists)
print "Skipped: %4d" % len(skip)


if not options.dry_run and len(copy):
    print
    print "Starting copy now"
    
    pb = ProgressBar(0, len(copy))
    if not options.verbose:
        pb(0)

    for (source_file, dest_file) in copy:
        try:
            if options.verbose:
                print "Copying file:"
                print "    %s" % source_file
                print "    %s" % dest_file
            else:
                pb(pb.amount + 1)
                    
            copy_size += os.path.getsize(source_file)
            dest_dir = os.path.dirname(dest_file)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            my_copy(source_file, dest_file)
        except:
            traceback.print_exc()
            os.remove(dest_file)
            sys.exit(2)



total_time = time.time() - start_time

print
print "Copied:  %4d" % len(copy)
print "Existed: %4d" % len(exists)
print "Skipped: %4d" % len(skip)

print "Time:    %4d s" % total_time
print "Data: %7d MB" % (copy_size / 1024 / 1024)
print "Perf: %.2f MB/s" % (copy_size / (1024*1024) / total_time)
