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

def check_root():
    if os.geteuid() != 0:
        print_error("You don't have enough privileges to run this program.")
        sys.exit()


def do_restore(time = TIME_INDEFFERENT, username = ""):
    check_root()
    title = "Trivial Freezer "+VERSION
    print title
    print "=" * len(title)
    
    cfg = config()
    cfg.load()
    
    #If time requested is different  of the configured time
    if cfg.time != time:
        return
    
    #Get users to restore
    fu = cfg.get_frozen_users(TAR_RESTORE)
    
    if len(fu) > 0:
        debug(" RESTORE",DEBUG_LOW)
        if len(username) == 0:
            debug("  SYSTEM or MANUAL",DEBUG_LOW)
            for froze in fu:
                froze.restore_tar()
        elif time == TIME_SESSION:
            debug("  SESSION",DEBUG_LOW)
            for froze in fu:
                if username == froze.username:
                    froze.restore_tar()
                    break
        else: debug("  ERROR",DEBUG_LOW)
            
    debug("DONE",DEBUG_LOW)
        
def print_help():
    title = "Trivial Freezer "+VERSION+" HELP"
    print title
    print "=" * len(title)
    print "Usage: "+sys.argv[0]+"  [OPTION]\n"
    print " Options:"
    print "  -d level    Specify the debug level"
    print "  -h          Show this help"
    print "  -m          Runs manual restoration profiles"
    print "  -p          Print the XML configuration file"
    print "  -S          Runs starting system restoration profiles"
    print "  -s username Runs starting session restoration profiles for the specified uid"
    print "  -x,-c       Open the configuration window (DEFAULT OPTION)"
    return

def print_config():
    title = "Trivial Freezer "+VERSION
    print title
    print "=" * len(title)
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
    action_error = False
    show_help = False
    show_config = False
    restore = False #False: show config, True: restore
    user = ""
    
    for i, arg in enumerate(argv):
        if arg.startswith("-"):
            if arg == "-x" or arg == "-c":
               if action_ok:
                   action_error = True
                   break
               else:
                   #CONFIGURATION
                   action_ok = True
                   restore = False
            elif arg == "-m":
                if action_ok:
                   action_error = True
                   break
                else:
                   #MANUAL RESTORATION
                   action_ok = True
                   restore = True
                   time = TIME_MANUAL
            elif arg == "-s":
                if action_ok or args <= i + 1:
                    action_error = True
                    break
                else:
                    #SESSION RESTORATION
                    action_ok = True
                    restore = True
                    time = TIME_SESSION
                    user = argv[i + 1]
            elif arg == "-S":
                if action_ok:
                    action_error = True
                    break
                else:
                    #SYSTEM RESTORATION
                    action_ok = True
                    restore = True
                    time = TIME_SYSTEM
            elif arg == "-d":
                if args > i + 1:
                    #DEBUG LEVEL
                    set_debug_level(sys.argv[i+1])
                else:
                    action_error = True
                    break
            elif arg == "-p":
                #PRINT CONFIG
                show_config = True
            else:
                #PRINT HELP
                show_help = True

    if not action_ok and not show_help and not show_config:
        #If no action: show window
        action_ok = True
        restore = False
        
    if action_ok and not action_error:
        if restore:
            do_restore(time,user)
        else:
            show_window()
    elif not show_config:
        show_help = True
        
    if show_help:
        print_help()
    
    if show_config:
        print_config()

if __name__ == "__main__":
    main(sys.argv, len(sys.argv))
    