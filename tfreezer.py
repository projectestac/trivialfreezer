#!/usr/bin/env python
#-*- coding: utf-8 -*-
#@authors: Pau Ferrer Ocaña

#This file is part of Trivial Freezer.

#Trivial Freezer is an easy freezer for user profiles and desktop in linux.
#Copyright (C) 2009  Pau Ferrer Ocaña

#Trivial Freezer free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#Image Haunter is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Trivial Freezer.  If not, see <http://www.gnu.org/licenses/>.


#LOCAL IMPORTS    
import sys
sys.path.insert(0, './')
from TFglobals import *
from TFmainWindow import *
from TFconfig import *

import tarfile
import re
import shutil


def move(src,dst):
    
    auxPath = 0 
        
    dstComplete = dst
    
    while os.path.exists(dst):
        dstComplete = dst + "_" + str(auxPath)
        auxPath = auxPath + 1

    shutil.move(src, dstComplete)
    return dst

#COPY A FILE TO A DIRECTORY WITHOUT OVERWRITTING THEM
def copy(src,dst):
    
    auxPath = 0
    fileName = os.path.basename(src)
    (file,extension) = fileName.split(".",1)
                 
    dstComplete = os.path.join (dst, fileName)     
    while os.path.exists(dstComplete):
        fileName = file + "_" + str(auxPath) + "." + extension
        dstComplete = os.path.join (dst, fileName)
        auxPath = auxPath + 1     
        
    shutil.copy(src, dstComplete)
    return fileName

    
##############
        
def check_root():
    if os.geteuid() != 0:
        print_error("You don't have enough privileges to run this program.")
        sys.exit()


def do_restore(time = TIME_INDEFFERENT, username = ""):
    check_root()
    print "Trivial Freezer "+VERSION
    print "===================="
    
    cfg = config()
    tars = cfg.get_frozen_users()
    
    if len(tars) > 0:
        debug(" RESTORE",DEBUG_LOW)
        if len(username) == 0:
            debug("  SYSTEM or MANUAL",DEBUG_LOW)
            for froze in tars:
                froze.restore_tar()
        elif time == TIME_SESSION:
            debug("  SESSION",DEBUG_LOW)
            for froze in tars:
                if username == froze.username:
                    froze.restore_tar()
                    break
        else: debug("  ERROR",DEBUG_LOW)
            
    debug("DONE",DEBUG_LOW)
        
def print_help():
    print "Trivial Freezer "+VERSION+" HELP"
    print "========================="
    print "Usage: "+sys.argv[0]+"  [OPTION]\n"
    print " Options:"
    print "  -x,-c       Open the configuration window (DEFAULT OPTION)"
    print "  -m          Runs manual restoration profiles"
    print "  -S          Runs starting system restoration profiles"
    print "  -s username Runs starting session restoration profiles for the specified uid"
    print "  -p          Print the XML configuration file"
    print "  -h          Show this help"
    return

def print_config():
    from xml.dom import minidom
    try:
        xdoc = minidom.parse(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE))
    except: 
        print_error("Corrupted configuration file")
        return
    
    print xdoc.toprettyxml(indent="  ")

def show_window():
    check_root()
    mainWindow().main()

def main(argv, args):
    action_ok = False
    show_help = False
    show_config = False
    configure = False
    restore = False
    user = ""
    time = TIME_INDEFFERENT
    
    for i, arg in enumerate(argv):
        if arg.startswith("-"):
            if arg == "-x" or arg == "-c":
               if action_ok:
                   show_help = True
                   configure = False
                   restore = False
               else:
                   #CONFIGURATION
                   configure = True
                   action_ok = True
            elif arg == "-m":
                if action_ok:
                   show_help = True
                   configure = False
                   restore = False
                else:
                   #MANUAL RESTORATION
                   restore = True
                   time = TIME_MANUAL
                   action_ok = True
            elif arg == "-s":
                if action_ok or args <= i + 1:
                    show_help = True
                    configure = False
                    restore = False
                else:
                    #SESSION RESTORATION
                    user = argv[i]
                    restore = True
                    time = TIME_SESSION
                    action_ok = True
            elif arg == "-S":
                if action_ok:
                    show_help = True
                    configure = False
                    restore = False
                else:
                    #SYSTEM RESTORATION
                    restore = True
                    time = TIME_SYSTEM
                    action_ok = True
            elif arg == "-d":
                if args > i + 1:
                    #DEBUG LEVEL
                    debug_level = str2int(sys.argv[i+1])
                else:
                    show_help = True
            elif arg == "-p":
                #PRINT CONFIG
                show_config = True
            else:
                #PRINT HELP
                show_help = True

    if not action_ok and not show_help and not show_config:
        configure = True
        action_ok = True
        
    if action_ok:
        if restore:
            do_restore(time,user)
        elif configure:
            show_window()
        else:
            show_help = True
    else:
        show_help = True
        
    if show_help:
        print_help()
    
    if show_config:
        print_config()

if __name__ == "__main__":
    main(sys.argv, len(sys.argv))
    