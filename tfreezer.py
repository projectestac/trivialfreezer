#!/usr/bin/env python
#-*- coding: utf-8 -*-
#@authors: Pau Ferrer Ocaña

#This file is part of Trivial Freezer.

#Trivial Freezer is an easy freezer for user profiles and desktop in linux.
#Copyright (C) 2009  Pau Ferrer Ocaña

#Trivial Freezer is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#Trivial Freezer is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Trivial Freezer.  If not, see <http://www.gnu.org/licenses/>.


import sys
sys.path.insert(0, './')
from TFglobals import *
from TFmainWindow import *   
from TFconfig import *

def check_root():
    if os.geteuid() != 0:
        print_error("You don't have enough privileges to run this program.")
        sys.exit()


def do_restore(username = ""):
    check_root()
    title = "Trivial Freezer " + VERSION
    print title
    print "=" * len(title)
    
    cfg = config()
    cfg.load()
    
    if len(username) == 0:
        time = TIME_SYSTEM
    else:
        time = TIME_SESSION
    
    #If time requested is different  of the configured time
    if cfg.time != time:
        return
    
    #Get users to restore
    fu = cfg.get_frozen_users(TAR_RESTORE)
    
    if len(fu) > 0:
        debug(" RESTORE",DEBUG_LOW)
        if time == TIME_SYSTEM:
            debug("  SYSTEM",DEBUG_LOW)
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
    title = "Trivial Freezer " + VERSION + " HELP"
    print title
    print "=" * len(title)
    print "Usage: "+sys.argv[0]+"  [OPTION]\n"
    print " Options:"
    print "  -d level    Specify the debug level"
    print "  -h          Show this help"
    print "  -p          Print the XML configuration file"
    print "  -r          Restore the whole system if configured"
    print "  -r username Restore the whole system if configured for the specified username"
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
    error = False
    show_help = False
    show_config = False
    restore = False #False: show config, True: restore
    user = ""
    
    for i, arg in enumerate(argv):
        if arg.startswith("-"):
            if arg == "-r":
                if args > i and not argv[i + 1].startswith("-"):
                    user = argv[i + 1]
                    
                if restore:
                    error = True
                    break
                else:
                    #RESTORATION
                    restore = True
                    
            elif arg == "-d":
                if args > i + 1:
                    #DEBUG LEVEL
                    set_debug_level(sys.argv[i+1])
                else:
                    error = True
                    break
                
            elif arg == "-p":
                #PRINT CONFIG
                show_config = True
                
            elif arg == "-h":
                #PRINT HELP
                show_help = True
            else:
                error = True

    if show_help or error:
        print_help()
    elif restore:
        do_restore(user)
    elif show_config:
        print_config()
    else:
        show_window()

if __name__ == "__main__":
    import time
    start = time.time()
    main(sys.argv, len(sys.argv))
    end = time.time()
    print "Time elapsed = ", end - start, "seconds"
    