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

_ = load_locale()

def __check_root():
    "Checks if it's running with root privileges"
    if os.geteuid() != 0:
        print_error(_("You don't have enough privileges to run this program."))
        sys.exit()


def __do_restore(username = "", auto=True):
    "Runs a restoration for the specified username or, if not specified, the whole system"
    
    from TFconfig import config
        
    __check_root()
    
    #TOERASE 2
    import time
    start = time.time()
    
    title = "Trivial Freezer " + VERSION
    print title
    print "=" * len(title)
    
    #Load saved configuration
    cfg = config()
    cfg.load()
    
    #If the username is empty,the whole system has to be restored
    if len(username) == 0:
        time_req = TIME_SYSTEM
    else:
        time_req = TIME_SESSION
    
    #Do nothing if time requested and configured time differs and it's an automatic running
    if cfg.time != time_req and auto:
        return
    
    #Get the list of users to restore
    fu = cfg.get_frozen_users(TAR_RESTORE)
    
    if len(fu) > 0:
        #TIME TO RESTORE!
        if time_req == TIME_SYSTEM:
            debug("RESTORE SYSTEM",DEBUG_LOW)
            #Restore every user in the list
            for froze in fu:
                froze.restore_tar()
        else: #time == TIME_SESSION
            #Restore only the specified user from the list
            for froze in fu:
                if username == froze.username:
                    debug("RESTORE SESSION",DEBUG_LOW)
                    froze.restore_tar()
                    break
    else:
        debug("NOTHING TO RESTORE",DEBUG_LOW)
    
    #TOERASE 2
    end = time.time()
    print "Time elapsed = ", end - start, "seconds"
        
def __print_help():
    "Prints usage help in the command line"
    
    title = "Trivial Freezer " + VERSION
    print title
    print "=" * len(title)
    print _("Usage: "+sys.argv[0]+"  [OPTION]\n")
    print " " + _("Options:")
    print "  -a\t\t"+_("With -r indicates that it's being executed automatically")
    print "  -d "+_("level")+"\t"+_("Specify the debug level")
    print "  -h\t\t"+_("Show this help")
    print "  -p\t\t"+_("Show the XML configuration file")
    print "  -r\t\t"+_("Restore the whole system if configured")
    print "  -r "+_("username")+"\t"+_("Restore the specified user home directory if configured")
    return

def __print_config():
    "Prints XML formated configuration file in the command line"
    
    from xml.dom import minidom
    
    title = "Trivial Freezer "+VERSION
    print title
    print "=" * len(title)
    
    try:
        xdoc = minidom.parse(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE))
    except: 
        print_error(_("Corrupted configuration file"))
    else:
        print xdoc.toprettyxml(indent="  ")

def __show_window():
    "Shows the configuration window"
    
    from TFmainWindow import mainWindow
    
    __check_root()
    
    mainWindow().main()

if __name__ == "__main__":
    "Main function"
    
    argv = sys.argv
    args = len(argv)

    restore = False
    auto = False
    user = ""
    
    #Read all the command line parameters
    for i, arg in enumerate(argv):
        if arg.startswith("-"):
            #Restore
            if arg == "-r":
                #User
                if args > i and not argv[i + 1].startswith("-"):
                    user = argv[i + 1]
                
                if restore: #Already read
                    __print_help()
                    sys.exit(1)
                
                restore = True
                    
            #Automatic execution through gdm or init.d?
            elif arg == "-a":
                auto = True
                
            #Debug level
            elif arg == "-d":
                if args > i + 1:
                    set_debug_level(sys.argv[i+1])
                else: #Level not specified
                    __print_help()
                    sys.exit(1)
            
            #Show config 
            elif arg == "-p":
                __print_config()
                sys.exit()
            
            #Show help
            elif arg == "-h":
                __print_help()
                sys.exit()
                
            #Others
            else:
                __print_help()
                sys.exit(1)

    #If restoring
    if restore:
        __do_restore(user,auto)
    #else, configure
    else:
        __show_window()
  