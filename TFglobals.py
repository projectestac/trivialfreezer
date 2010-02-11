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


import gettext, sys, os
#Path Working directory
path = os.path.split(os.path.realpath(sys.argv[0]))[0]+"/"


################## CONSTANTS ##################
#Version of the Freezer
VERSION = "v0.9.2 beta"

#Exec directory
EXEC_DIRECTORY = path
#Path of the configuration
CONFIG_DIRECTORY = "/etc/tfreezer/"
#Filename of the configuration
CONFIG_FILE = "config.xtf"

#Where to store the tar files
TAR_DIRECTORY = "/var/backups/tfreezer/"
#Subdirectory of TAR_DIRECTORY to store the home directories
TAR_HOMES = "homes"
#Subdirectory of TAR_DIRECTORY to store tars from the repository
TAR_REPOSITORY = "repository"
#Tar extension
TAR_EXTENSION = ".tar.gz"
#Default lost+found deposit
DEFAULT_DEPOSIT = "~/lost+found"
#Where in the root directory to find the id_dsa key
ID_DSA_PATH = ".ssh/id_dsa"
#Where in the root home to find the known_hosts file
KNOWN_HOSTS_PATH = ".ssh/known_hosts"

#Locale translation domain and path of the translations
LOCALE_DOMAIN = "tfreezer"
LOCALE_PATH = path + "/locale"

#Minimum uid to freeze
minUID = 1000
#Maximum uid to freeze
maxUID = 65534

#Where to find the pixmaps
PIXMAPS_PATH = path+"pixmaps"
SMALL_ICONS = [PIXMAPS_PATH+"/drop-16.png", PIXMAPS_PATH+"/ice-16.png", PIXMAPS_PATH+"/drops-16.png"]
NORMAL_ICONS = [PIXMAPS_PATH+"/drop-32.png", PIXMAPS_PATH+"/ice-32.png", PIXMAPS_PATH+"/drops-32.png"]
BIG_ICONS = [PIXMAPS_PATH+"/drop-64.png", PIXMAPS_PATH+"/ice-64.png", PIXMAPS_PATH+"/drops-64.png"]
HUGE_ICONS = [PIXMAPS_PATH+"/drop-128.png", PIXMAPS_PATH+"/ice-128.png", PIXMAPS_PATH+"/drops-128.png"]

#Frozen states
FREEZE_LDAP = -1 #LDAP ENABLED AND CLIENT FREEZER
FREEZE_NONE = 0 #UNFROZEN
FREEZE_ALL = 1 #COMPLETELLY FROZEN
FREEZE_ADV = 2 #ADVANCED FROZEN

#Selected option, all, by users or by groups
OPTION_ALL = 0
OPTION_USERS = 1
OPTION_GROUPS = 2

#Frozen Time
TIME_INDEFFERENT = -1 #Unused
TIME_SESSION = 0 #Frozen by session enabled
TIME_SYSTEM = 1 #Frozen by system enabled

#Action of the rules
ACTION_RESTORE = 0
ACTION_KEEP = 1
ACTION_ERASE = 2
ACTION_LOST = 3

#Number of blocked of editing frozen profiles
BLOCKED_PROFILES = 3

#Action to tdo with the tars
TAR_CREATE = 0
TAR_RESTORE = 1

#Debug level
DEBUG_DISABLED = 0
DEBUG_LOW = 1
DEBUG_MEDIUM = 2
DEBUG_HIGH = 3

#Error level
WARNING = 0
ERROR = 1

###############################################

debug_level = DEBUG_DISABLED

#To know if we want to kill the thread
thread_killed = False

## i18n
def load_locale():
    "Loads the locale"
    gettext.bindtextdomain(LOCALE_DOMAIN,LOCALE_PATH)
    gettext.textdomain(LOCALE_DOMAIN)
    return gettext.gettext

def get_thread_killed():
    global thread_killed
    return thread_killed

def set_thread_killed(killed):
    global thread_killed
    thread_killed = killed
    
def set_debug_level(level):
    "Sets the debug level to be output in the terminal"
    global debug_level
    debug_level = str2int(level)

def get_debug_level():
    "Gets the debug level used"
    global debug_level
    return debug_level

def debug(text, level=DEBUG_LOW):
    "Prints a text in the terminal if the debug level is higher than the requested"
    
    if level <= debug_level:
        if level == DEBUG_LOW:
            print "Debug L: "+ str(text)
        if level == DEBUG_MEDIUM:
            print "Debug M: "+ str(text)
        if level == DEBUG_HIGH:
            print "Debug H: "+ str(text)

def print_error(text,level=ERROR):
    "Prints a error or warning message in the terminal"
    if level == WARNING:
        print "Warning: "+ str(text)
        return
    
    print "Error  : "+ str(text)
    
def str2bool(v):
    "Converts an string to boolean"    
    return v.lower() in ["yes", "true", "t", "1"]

def str2int(v):
    "Converts an string to integer"
    if v != None:
        return int(v)
    else:
        return 0
    
