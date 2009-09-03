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

## i18n
import gettext, sys, os
path = os.path.split(os.path.realpath(sys.argv[0]))[0]+"/"

gettext.bindtextdomain('tfreezer', path+'/locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext


################## CONSTANTS ##################

VERSION = "v0.5"

EXEC_DIRECTORY = path
CONFIG_DIRECTORY = "/etc/tfreezer/"
CONFIG_FILE = "config.xtf"
TAR_DIRECTORY = "/var/backups/tfreezer/"
TAR_HOMES = "homes"
TAR_REPOSITORY = "repository"
TAR_EXTENSION = ".tar.gz"
DEFAULT_DEPOSIT = "/lost+found"

minUID = 1001
maxUID = 65534

SMALL_ICONS = [path+"pixmaps/drop-16.png", path+"pixmaps/ice-16.png", path+"pixmaps/drops-16.png"]
NORMAL_ICONS = [path+"pixmaps/drop-32.png", path+"pixmaps/ice-32.png", path+"pixmaps/drops-32.png"]
BIG_ICONS = [path+"pixmaps/drop-64.png", path+"pixmaps/ice-64.png", path+"pixmaps/drops-64.png"]
HUGE_ICONS = [path+"pixmaps/drop-128.png", path+"pixmaps/ice-128.png", path+"pixmaps/drops-128.png"]

FREEZE_LDAP = -1
FREEZE_NONE = 0
FREEZE_ALL = 1
FREEZE_ADV = 2

OPTION_ALL = 0
OPTION_USERS = 1
OPTION_GROUPS = 2

TIME_INDEFFERENT = -1
TIME_MANUAL = 0
TIME_SESSION = 1
TIME_SYSTEM = 2

ACTION_RESTORE = 0
ACTION_KEEP = 1
ACTION_ERASE = 2
ACTION_LOST = 3

BLOCKED_PROFILES = 3

TAR_CREATE = 0
TAR_RESTORE = 1

DEBUG_DISABLED = 0
DEBUG_LOW = 1
DEBUG_MEDIUM = 2
DEBUG_HIGH = 3

WARNING = 0
ERROR = 1

debug_level = DEBUG_DISABLED

###############################################

def set_debug_level(level):
    "Sets the debug level to be output in the terminal"
    global debug_level
    debug_level = str2int(level)

def debug(text, level=DEBUG_LOW):
    "Prints a text in the terminal if the debug level is higher than the requested"
    #if debug_level == DEBUG_DISABLED:
    #    return
    
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
    