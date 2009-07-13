## i18n

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext


ldap_host = 'ldap://localhost'
ldap_dn = 'dc=iescopernic,dc=com'


################## CONSTANTS ##################

VERSION = "v0.5"

CONFIG_DIRECTORY = "/etc/tfreezer/"
CONFIG_FILE = "config.xtf"
TAR_DIRECTORY = "/var/backups/tfreezer/"
TAR_HOMES = "homes"
TAR_REPOSITORY = "repository"
TAR_EXTENSION = ".tar.gz"
DEFAULT_DEPOSIT = "/lost+found"

minUID = 1001
maxUID = 65534

SMALL_ICONS = ["pixmaps/drop-16.png", "pixmaps/ice-16.png", "pixmaps/drops-16.png"]
NORMAL_ICONS = ["pixmaps/drop-32.png", "pixmaps/ice-32.png", "pixmaps/drops-32.png"]
BIG_ICONS = ["pixmaps/drop-64.png", "pixmaps/ice-64.png", "pixmaps/drops-64.png"]
HUGE_ICONS = ["pixmaps/drop-128.png", "pixmaps/ice-128.png", "pixmaps/drops-128.png"]

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

def debug(text, level=DEBUG_LOW):
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
    if level == WARNING:
        print "Warning: "+ str(text)
        return
    
    print "Error  : "+ str(text)
    
    
#Converts an string to boolean
def str2bool(v):
    return v.lower() in ["yes", "true", "t", "1"]

def str2int(v):
    if v != None:
        return int(v)
    else:
        return 0
    