from TFglobals import *
from TFprofile import *

from xml.dom import minidom

import os

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext


class source:
    def __init__(self):
        self.name = ""
        self.file = ""
    
class profile:
    def __init__(self):
        self.title = ""
        self.rules = []
        self.edited = True
        self.saved_source = False
        self.source = ""
        self.deposit = ""
        self.valid = True
    
class rule:
    name = ""
    filter = ""
    action = ACTION_KEEP
    
    def __init__(self, name, filter, action):
        self.name = name
        self.filter = filter
        self.action = action
        
class user_group:
    id = ""
    profile = FREEZE_NONE
    
    def __init__(self,id, profile):
        self.id = id
        self.profile = profile
    
class config:
    
    def __init__(self):
        self.sources = []
        self.profiles = []
        self.time = TIME_MANUAL
        self.option = OPTION_ALL
        self.all = FREEZE_NONE
        self.users = []
        self.groups = []
        self.frozen_users = []
        self.load()
        
    def load(self):
        try:  
            xdoc = minidom.parse(os.path.join(CONFIG_DIRECTORY, CONFIG_FILE))
        except:
            print_error(_("Corrupted config file, taking defaults"),WARNING)
    
        #Load the saved sources
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        try:   
            os.makedirs(dirname,0755)
        except OSError as (errno, strerror):
            print_error(dirname + " " + strerror,WARNING)
            
        del self.sources
        self.sources = []
        
        try:
            xSources = xdoc.getElementsByTagName("sources")[0].getElementsByTagName("source")
        except:
            print_error(_("Corrupted or empty sources tag, taking defaults"),WARNING)
        else:
            for xSource in xSources:
                try:
                    s = source()
                    s.name = xSource.getAttribute("title")
                    s.file = xSource.getAttribute("file")
                    filename = os.path.join (dirname, s.file)
                    tar = tarfile.open(filename,'r')
                    tar.close()
                except:
                    print_error(_("Corrupted source file tag, ignoring..."),WARNING)
                else:
                    self.sources.append(s)
        
        #NOT SAVED SOURCES FILES
        files = os.listdir(dirname)
        for file in files:
            path = os.path.join (dirname, file)
            if not os.path.isdir(path) or os.path.islink(path):
                trobat = False
                
                for src in self.sources:
                    if file == src.file:
                        trobat = True
                        break
                
                if not trobat:
                    try:
                        tar = tarfile.open(path,'r')
                        tar.close()
                    except:
                        print_error(_("Unreadable tar file, ignoring..."), WARNING)
                    else:
                        s = source()
                        s.name = file.split(".",1)[0]
                        s.file = file
                        self.sources.append(s)
            
        del self.profiles
        self.profiles = []                           
        try:
            xProfiles = xdoc.getElementsByTagName("profile")
        except:
            print_error("Corrupted profile tag, taking defaults",WARNING)
            p = profile()
            p.edited = False
            p.title = _("Total Unfrozen")
            r = rule(_("Everything"),".",ACTION_KEEP)
            p.rules.append(r)
            self.profiles.append(p)
            
            p = profile()
            p.title = _("Total Frozen")
            p.edited = False
            r = rule(_("Everything"),".",ACTION_RESTORE)
            p.rules.append(r)
            self.profiles.append(p)

            p = profile()
            p.title = _("Configuration Frozen")
            p.edited = False
            r = rule(_("Configuration"),"^\.",ACTION_RESTORE)
            p.rules.append(r)
            r = rule(_("Everything"),".",ACTION_KEEP)
            p.rules.append(r)
            self.profiles.append(p)
            
            
        else:
            for i, xProfile in enumerate(xProfiles):
                p = profile()
                try:
                    p.title = xProfile.getAttribute("name")
                except:
                    print_error("Corrupted name attribute on profile tag, taking defaults",WARNING)
                    if i == FREEZE_NONE:
                        p.title = _("Total Unfrozen")
                    elif i == FREEZE_ALL:
                        p.title = _("Total Frozen")
                    elif i  == FREEZE_ADV:
                        p.title = _("Configuration Frozen")
                    else:
                        p.title = _("No name")
                    p.valid = False
                
                if i < BLOCKED_PROFILES:
                    p.edited = False
                                   
                try:
                    p.saved_source = str2bool(xProfile.getElementsByTagName("source")[0].getAttribute("active"))
                    p.source = xProfile.getElementsByTagName("source")[0].getAttribute("value")
                except:
                    p.saved_source = False
                    print_error("Corrupted source tag, taking defaults",WARNING)
                    p.valid = False
                
                try:
                    p.deposit = xProfile.getElementsByTagName("deposit")[0].getAttribute("value")
                except:
                    p.deposit = ""
                    print_error("Corrupted deposit tag, taking defaults",WARNING)
                    p.valid = False
                    
                try:   
                    for xRule in xProfile.getElementsByTagName("rules")[0].getElementsByTagName("rule"):
                        r = rule(xRule.getAttribute("title"),xRule.getAttribute("pattern"),str2int(xRule.getAttribute("value")))
                        p.rules.append(r)
                except:
                    print_error("Corrupted or empty rules tag, taking defaults",WARNING)
                    if i == FREEZE_NONE:
                        r = rule(_("Everything"),".",ACTION_KEEP)
                        p.rules.append(r)
                    elif i == FREEZE_ALL:
                        r = rule(_("Everything"),".",ACTION_RESTORE)
                        p.rules.append(r)
                    elif i  == FREEZE_ADV:
                        r = rule(_("Configuration"),"^\.",ACTION_RESTORE)
                        p.rules.append(r)
                        r = rule(_("Everything"),".",ACTION_KEEP)
                        p.rules.append(r)
                    p.valid = False
                self.profiles.append(p)
        
        try:
            xFreeze = xdoc.getElementsByTagName("freeze")[0]
        except:
            print_error("Corrupted freeze tag, taking defaults",WARNING) 
            
        try:
            self.time = str2int(xFreeze.getAttribute("time"))
        except:
            self.time = TIME_MANUAL
            print_error("Corrupted time attribute on freeze tag, taking defaults",WARNING)
        
        try:
            if str2bool(xFreeze.getElementsByTagName("all")[0].getAttribute("active")):
                self.option = OPTION_ALL
            elif str2bool(xFreeze.getElementsByTagName("users")[0].getAttribute("active")):
                self.option = OPTION_USERS
            elif str2bool(xFreeze.getElementsByTagName("groups")[0].getAttribute("active")):
                self.option = OPTION_GROUPS
        except:
            self.option = OPTION_ALL
            self.all = FREEZE_NONE
            print_error("Corrupted option tag, taking defaults",WARNING)
        else:
            try:
                self.all = str2int(xFreeze.getElementsByTagName("all")[0].getAttribute("value"))
            except:
                self.option = OPTION_ALL
                self.all = FREEZE_NONE
                print_error("Corrupted all tag, taking defaults",WARNING)
        try:
            del self.users
            self.users = []
            for xUser in xdoc.getElementsByTagName("users")[0].getElementsByTagName("user"):
                user = user_group(xUser.getAttribute("uid"),int(xUser.getAttribute("value")))
                self.users.append(user)
        except:
            print_error("Corrupted or empty users tag, taking defaults",WARNING)
            
        try:
            del self.groups
            self.groups = []
            for xGroup in xdoc.getElementsByTagName("groups")[0].getElementsByTagName("group"):
                group = user_group(xGroup.getAttribute("gid"),int(xGroup.getAttribute("value")))
                self.groups.append(group)
        except:
            print_error("Corrupted or empty groups tag, taking defaults",WARNING)

    def load_defaults(self):
        del self.sources
        self.sources = []
        
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        try:   
            os.makedirs(dirname,0755)
        except OSError as (errno, strerror):
            print_error(dirname + " " + strerror,WARNING)
        
        files = os.listdir(dirname)
        for file in files:
            path = os.path.join (dirname, file)
            if not os.path.isdir(path) or os.path.islink(path):
                try:
                    tar = tarfile.open(path,'r')
                    tar.close()
                except:
                    print_error(_("Unreadable tar file, ignoring..."), WARNING)
                else:
                    s = source()
                    s.name = file.split(".",1)[0]
                    s.file = file
                    self.sources.append(s)
            
        del self.profiles
        self.profiles = []
                                  
        p = profile()
        p.edited = False
        p.title = _("Total Unfrozen")
        r = rule(_("Everything"),".",ACTION_KEEP)
        p.rules.append(r)
        self.profiles.append(p)
        
        p = profile()
        p.title = _("Total Frozen")
        p.edited = False
        r = rule(_("Everything"),".",ACTION_RESTORE)
        p.rules.append(r)
        self.profiles.append(p)

        p = profile()
        p.title = _("Configuration Frozen")
        p.edited = False
        r = rule(_("Configuration"),"^\.",ACTION_RESTORE)
        p.rules.append(r)
        r = rule(_("Everything"),".",ACTION_KEEP)
        p.rules.append(r)
        self.profiles.append(p)
            
        self.time = TIME_MANUAL
        self.option = OPTION_ALL
        self.all = FREEZE_NONE
        
        del self.users
        self.users = []
        del self.groups
        self.groups = []
    
    def get_frozen_users(self,time = TIME_INDEFFERENT):
        debug('Entering config.load',DEBUG_LOW)
       
        #IF requested time is not indifferent
        #AND time requested is different  of the configured time
        if time != TIME_INDEFFERENT and self.time != time:
            #Return and don't parse more
            return []
        
        del self.frozen_users
        self.frozen_users = []
        #ALL
        if self.option == OPTION_ALL:
            debug('  ALL SYSTEM',DEBUG_LOW)
            if self.all != FREEZE_NONE and self.all < len(self.profiles):
                profile = self.init_profile(self.all)
                self.get_all_frozen(profile)
        #BY USERS
        elif self.option == OPTION_USERS:
            debug('  USERS',DEBUG_LOW)
            for user in self.users:
                if user.profile != FREEZE_NONE and user.profile < len(self.profiles):
                    profile = self.init_profile(user.profile)
                    self.get_user_frozen(profile, user.id)
        #BY GROUPS
        elif self.option == OPTION_GROUPS:
            debug('  GROUPS',DEBUG_LOW)
            for group in self.groups:
                if group.profile != FREEZE_NONE and group.profile < len(self.profiles):
                    profile = self.init_profile(group.profile)
                    self.group(profile, group.id)
        
        return self.frozen_users
    
    def init_profile(self, prof):

        uf = user_frozen()
        p = self.profiles[prof]
        uf.name =  p.title
        
        if(p.saved_source):
            uf.source = p.source
        else:   uf.source = ""
 
        uf.deposit = p.deposit
        
        for rule in p.rules:
            uf.filters.append([rule.action,rule.filter])
            
        for filter in uf.filters:
            debug(filter[1])
        
        return uf
    
    def get_all_frozen(self, profile):
        
        #Exec for all users in the permitted uid range
        for user in pwd.getpwall():
            uid = user.pw_uid
            if uid >= minUID and uid < maxUID:
                newConf = profile.copy()
                newConf.username = user.pw_name
                newConf.homedir = user.pw_dir
                newConf.uid = user.pw_uid
                newConf.gid = user.pw_gid
                
                self.frozen_users.append(newConf)
                
        #TODO: ldap
        try:
            con = ldap.initialize(ldap_host)
            filter = '(objectclass=posixAccount)'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
         
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for person in result:
                newConf = profile.copy()
                newConf.username = person[1]['uid'][0]
                newConf.homedir = person[1]['homeDirectory'][0]
                newConf.uid = person[1]['uidNumber'][0]
                newConf.gid = person[1]['gidNumber'][0]
            
                self.frozen_users.append(newConf)
                
        except ldap.LDAPError, e:
            print e
            exit
        return
    
    def get_user_frozen(self, profile, uid):
        debug("   " +str(uid),DEBUG_LOW)
        
        if uid < minUID or uid >= maxUID:  return
        
        try:
            user = pwd.getpwuid(uid)
        except:
            print_error("User " + uid + " not found")
        else:        
            newConf = profile.copy()
            newConf.username = user.pw_name
            newConf.homedir = user.pw_dir
            newConf.uid = user.pw_uid
            newConf.gid = user.pw_gid
            
            self.frozen_users.append(newConf)
            return
        
        #If not found, try ldap
        #TODO: ldap
        try:
            con = ldap.initialize(ldap_host)
            filter = '(&(objectclass=posixAccount)(uidNumber='+str(uid)+'))'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            if len(result) > 0:
                newConf = profile.copy()
                newConf.username = result[0][1]['uid'][0]
                newConf.homedir = result[0][1]['homeDirectory'][0]
                newConf.uid = result[0][1]['uidNumber'][0]
                newConf.gid = result[0][1]['gidNumber'][0]
            
                self.frozen_users.append(newConf)
                return
                
        except ldap.LDAPError, e:
            print e
            exit

        return
    
    def get_group_frozen(self, profile, gid):
        debug("   " +str(gid),DEBUG_LOW)
        
        if gid < minUID or gid >= maxUID:  return
        
        #Usuari primari del grup
        for user in pwd.getpwall():
            if gid == user.pw_gid:
                uid = user.pw_uid
                if uid >= minUID and uid < maxUID:
                    newConf = profile.copy()
                    newConf.username = user.pw_name
                    newConf.homedir = user.pw_dir
                    newConf.uid = user.pw_uid
                    newConf.gid = user.pw_gid
                    
                    self.frozen_users.append(newConf)
                break
            
        #Usuaris secuntaris del grup
        try:
            group = grp.getgrgid(gid)
        except:
            print_error("Group " + gid + " not found")
        else:
            for username in group.gr_mem:
                try:
                    user = pwd.getpwname(username)
                except:
                    print_error("User " + user + " not found",WARNING)
                else:
                    uid = user.pw_uid
                    if uid >= minUID and uid < maxUID: 
                        newConf = profile.copy()
                        newConf.username = user.pw_name
                        newConf.homedir = user.pw_dir
                        newConf.uid = user.pw_uid
                        newConf.gid = user.pw_gid
                        
                        self.frozen_users.append(newConf)
        
        #TODO: if not in local
        #TODO: ldap
        #Primary and secontaries group user
        try:
            con = ldap.initialize(ldap_host)
            filter = '(&(objectclass=posixGroup)(gidNumber='+str(gid)+'))'
            attrs = ['memberUid']
         
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            print len(result)
            
            secondaries = ''
            if len(result) > 0:
                try:
                    secondaries = '(&(objectclass=posixAccount)(|'
                    for uid in result[0][1]['memberUid']:
                        secondaries = secondaries + '(uid='+uid+')'
                    secondaries = secondaries + '))'
                except:
                    secondaries = ''
                
            con = ldap.initialize(ldap_host)
            filter = '(|(&(objectclass=posixAccount)(gidNumber='+str(gid)+'))'+secondaries+')'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
         
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for person in result:
                newConf = profile.copy()
                newConf.username = person['uid'][0]
                newConf.homedir = person['homeDirectory'][0]
                newConf.uid = person['uidNumber'][0]
                newConf.gid = person['gidNumber'][0]

                self.frozen_users.append(newConf)
                    
        except ldap.LDAPError, e:
            print e
            return
        
        return