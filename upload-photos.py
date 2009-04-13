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
    "mov"
]

# THM files are copied when we look at the original buddy file.  We
# don't want to list them as skipped so we *really* skip them and
# don't say anything.
SPECIAL_FILE_TYPES = [
    "thm"
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

def queue_file(source_file, dest_file):
    """Add a file to our copy queue.

    Also check to make sure that the file doesn't exists at the
    destionation.  If it does, do some sanity checks to make sure that
    it is the same file at the dest.
    """
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
            print "Queuing copy:"
            print "    %s" % source_file
            print "    %s" % dest_file
        copy.append((source_file, dest_file))
    

print "Scanning directories"
for root, dirs, files in os.walk(options.source):
    for file in files:
        (base, ext) = os.path.splitext(file)
        source_ext = string.lower(ext[1:])
        source_file = os.path.join(root, file)
        
        source_thm = os.path.join(root, base + ".THM")
        
        if source_ext in FILE_TYPES:
            dest_subpath = time.strftime("%Y/%m/%Y-%m-%d",
                                         time.localtime(os.path.getmtime(source_file)))
            dest_dir = os.path.join(options.dest, dest_subpath)
            dest_file = os.path.join(dest_dir, file)

            queue_file(source_file, dest_file)

            # I've seen cases where the .THM (thumbnail buddy file for
            # movies and old CRWs) have a date different than the
            # original.  To fix this, take the date from the original
            # and copy the THM if it exists.
            if os.path.exists(source_thm):
                dest_thm = os.path.join(dest_dir, base + ".THM")
                queue_file(source_thm, dest_thm)

        else:
            if source_ext not in SPECIAL_FILE_TYPES:
                print "Skipping %s" % source_file
                skip.append(source_file)


if not options.dry_run:
    print
    print "Starting copy now"
    
    for (source_file, dest_file) in copy:
        try:
            if options.verbose:
                print "Copying file:"
                print "    %s" % source_file
                print "    %s" % dest_file
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                    
            copy_size += os.path.getsize(source_file)
            dest_dir = os.path.dirname(dest_file)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy2(source_file,
                         dest_file)
        except:
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
