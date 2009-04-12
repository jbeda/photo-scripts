#!/usr/bin/env python

import sys
import os
import os.path
import string
import time
import shutil
from optparse import OptionParser

FILE_TYPES = [
    "crw",
    "cr2",
    "jpg",
    "avi",
    "thm",
    "mov"
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

if not (options.source or options.dest):
    parser.print_help()
    sys.exit(1)

print "Copying photos from '%s' to '%s'" % (options.source,
                                            options.dest)

copy = []
skip = []
exists = []

copy_size = 0
start_time = time.time()

for root, dirs, files in os.walk(options.source):
    for file in files:
        source_ext = string.lower(os.path.splitext(file)[1][1:])
        source_file = os.path.join(root, file)
        if source_ext in FILE_TYPES:
            dest_subpath = time.strftime("%Y/%m/%Y-%m-%d",
                                         time.localtime(os.path.getmtime(source_file)))
            dest_dir = os.path.join(options.dest, dest_subpath)
            dest_file = os.path.join(dest_dir, file)

            if os.path.exists(dest_file):
                print "Already exists:"
                print "    %s" % source_file
                print "    %s" % dest_file
                
                source_stat = os.stat(source_file)
                dest_stat = os.stat(dest_file)
                if source_stat.st_size != dest_stat.st_size:
                    print "    !!! sizes differ !!!"
                if abs(source_stat.st_mtime - dest_stat.st_mtime) > 5:
                    print "    !!! times differ !!! %d" % (source_stat.st_mtime - dest_stat.st_mtime)
                exists.append(source_file)
            else:
                if options.verbose:
                    print "Copying file:"
                    print "    %s" % source_file
                    print "    %s" % dest_file
                else:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                if not options.dry_run:
                    try:
                        if not os.path.exists(dest_dir):
                            os.makedirs(os.path.join(options.dest, dest_subpath))
                        shutil.copy2(source_file,
                                     dest_file)
                    except:
                        os.remove(dest_file)
                        sys.exit(2)
                        
                copy.append(source_file)
                copy_size += os.path.getsize(source_file)
        else:
            print "Skipping %s" % source_file
            skip.append(source_file)

total_time = time.time() - start_time

print
print "Copied:  %4d" % len(copy)
print "Existed: %4d" % len(exists)
print "Skipped: %4d" % len(skip)

print "Time:    %4d s" % total_time
print "Data: %7d MB" % (copy_size / 1024 / 1024)
print "Perf: %.2f MB/s" % (copy_size / (1024*1024) / total_time)
