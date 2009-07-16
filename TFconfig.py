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

from TFglobals import *
from TFuser_frozen import *

from xml.dom import minidom

import pwd, grp
import os
import tarfile
import ldap

from datetime import datetime

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext

class source:
    def __init__(self):
        self.name = ""
        self.file = ""
    
class profile:
    def __init__(self, title=""):
        self.title = title
        self.rules = []
        self.could_be_edited = True
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
    name = ""
    profile = FREEZE_NONE
    ldap = False
    
    def __init__(self, id, name, profile=FREEZE_NONE, ldap=False):
        self.id = id
        self.name = name
        self.profile = profile
        self.ldap = ldap

    def set_profile(self,profile):
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
        self.ldap_enabled = False
        self.ldap_server = ""
        self.ldap_dn = ""
        
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
            debug(dirname + " " + strerror,DEBUG_HIGH)
            
        del self.sources [:]
        
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
            
        
        try:
            xProfiles = xdoc.getElementsByTagName("profile")
        except:
            print_error("Corrupted profile tag, taking defaults",WARNING)
            self.load_profile_defaults()
        else:
            self.profiles[:]
            for i, xProfile in enumerate(xProfiles):
                p = profile()
                try:
                    p.title = xProfile.getAttribute("name")
                except:
                    print_error("Corrupted name attribute on profile tag, taking defaults",WARNING)
                    p.title = self.get_profile_name_defaults(i)
                    p.valid = False
                
                if i < BLOCKED_PROFILES:
                    p.could_be_edited = False
                                   
                try:
                    p.saved_source = str2bool(xProfile.getElementsByTagName("source")[0].getAttribute("active"))
                    p.source = xProfile.getElementsByTagName("source")[0].getAttribute("value")
                except:
                    print_error("Corrupted source tag, taking defaults",WARNING)
                    p.saved_source = False
                    p.valid = False
                
                try:
                    p.deposit = xProfile.getElementsByTagName("deposit")[0].getAttribute("value")
                except:
                    print_error("Corrupted deposit tag, taking defaults",WARNING)
                    p.deposit = ""
                    p.valid = False
                    
                try:   
                    for xRule in xProfile.getElementsByTagName("rules")[0].getElementsByTagName("rule"):
                        r = rule(xRule.getAttribute("title"),xRule.getAttribute("pattern"),str2int(xRule.getAttribute("value")))
                        p.rules.append(r)
                except:
                    print_error("Corrupted or empty rules tag, taking defaults",WARNING)
                    p.rules = self.get_profile_rules_defaults(i)
                    p.valid = False
                self.profiles.append(p)
        
        try:
            xFreeze = xdoc.getElementsByTagName("freeze")[0]
        except:
            print_error("Corrupted freeze tag, taking defaults",WARNING) 
            
        try:
            self.time = str2int(xFreeze.getAttribute("time"))
        except:
            print_error("Corrupted time attribute on freeze tag, taking defaults",WARNING)
            self.load_time_defaults()
        
        try:
            if str2bool(xFreeze.getElementsByTagName("all")[0].getAttribute("active")):
                self.option = OPTION_ALL
            elif str2bool(xFreeze.getElementsByTagName("users")[0].getAttribute("active")):
                self.option = OPTION_USERS
            elif str2bool(xFreeze.getElementsByTagName("groups")[0].getAttribute("active")):
                self.option = OPTION_GROUPS
        except:
            print_error("Corrupted option tag, taking defaults",WARNING)
            self.load_freeze_defaults()
        else:
            try:
                self.all = str2int(xFreeze.getElementsByTagName("all")[0].getAttribute("value"))
            except:
                print_error("Corrupted all tag, taking defaults",WARNING)
                self.load_freeze_defaults()
        
        try:
            self.ldap_server = "ldap://localhost"
            self.ldap_dn = "dc=iescopernic,dc=com"
            self.ldap_enabled = True
        except:
            self.load_ldap_defaults()
        
        self.load_users()
        
        #CHANGE PROFILES FOR SAVED USERS
        try:
            for xUser in xdoc.getElementsByTagName("users")[0].getElementsByTagName("user"):
                uid = int(xUser.getAttribute("uid"))
                for user in self.users:
                    if user.id == uid:
                        value = int(xUser.getAttribute("value"))
                        user.set_profile(value)
                        break
        except:
            print_error("Corrupted or empty users tag, taking defaults",WARNING)
        
        self.load_groups()
        
        #CHANGE PROFILES FOR SAVED GROUPS
        try:
            for xGroup in xdoc.getElementsByTagName("groups")[0].getElementsByTagName("group"):
                gid = int(xGroup.getAttribute("gid"))
                for group in self.groups:
                    if group.id == gid:
                        value = int(xGroup.getAttribute("value"))
                        group.set_profile(value)
                        break
        except:
            print_error("Corrupted or empty groups tag, taking defaults",WARNING)
            
    def get_profile_rules_defaults(self,index):
        rules = []
        if index == FREEZE_NONE:
            r = rule(_("Everything"),".",ACTION_KEEP)
            rules.append(r)
        elif index == FREEZE_ALL:
            r = rule(_("Everything"),".",ACTION_RESTORE)
            rules.append(r)
        elif index  == FREEZE_ADV:
            r = rule(_("Configuration"),"^\.",ACTION_RESTORE)
            rules.append(r)
            r = rule(_("Everything"),".",ACTION_KEEP)
            rules.append(r)
        return rules
    
    def get_profile_name_defaults(self,index):
        if index == FREEZE_NONE:
            return _("Total Unfrozen")
        
        if index == FREEZE_ALL:
            return _("Total Frozen")
        
        if index  == FREEZE_ADV:
            return _("Configuration Frozen")
        
        return _("No name")
        
    def load_profile_defaults(self):
        self.profiles[:]
        
        p = profile(self.get_profile_name_defaults(FREEZE_NONE))
        p.could_be_edited = False
        p.rules = self.get_profile_rules_defaults(FREEZE_NONE)
        self.profiles.append(p)
        
        p = profile(self.get_profile_name_defaults(FREEZE_ALL))
        p.could_be_edited = False
        p.rules = self.get_profile_rules_defaults(FREEZE_ALL)
        self.profiles.append(p)

        p = profile(self.get_profile_name_defaults(FREEZE_ADV))
        p.could_be_edited = False
        p.rules = self.get_profile_rules_defaults(FREEZE_ADV)
        self.profiles.append(p)
        
    def load_time_defaults(self):
        self.time = TIME_MANUAL
        
    def load_freeze_defatuls(self):
        self.option = OPTION_ALL
        self.all = FREEZE_NONE
        
    def load_ldap_defaults(self):
        self.ldap_enabled = False
        self.ldap_server = ""
        self.ldap_dn = ""
        
    def load_defaults(self):
        
        self.sources[:]
        
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        try:   
            os.makedirs(dirname,0755)
        except OSError as (errno, strerror):
            debug(dirname + " " + strerror,DEBUG_HIGH)
        
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
            
        self.load_profile_defaults()
            
        self.load_time_defaults()
        self.load_freeze_defaults()
        
        self.load_ldap_defaults()
        
        self.load_users()
        self.load_groups()
    
    def save(self):
        debug("Entering config.save",DEBUG_LOW)
        
        #DESAR EN XML
        #Create the minidom document
        xdoc = minidom.Document()
        
        xtf = xdoc.createElement("tfreezer")
        xtf.setAttribute("date", str(datetime.now()))
        xdoc.appendChild(xtf)
        
        xFreeze = xdoc.createElement("freeze")
        xFreeze.setAttribute("time", str(self.time))
        
        xall = xdoc.createElement("all")
        xall.setAttribute("active", str(self.option == OPTION_ALL))  
        xall.setAttribute("value", str(self.all))
        xFreeze.appendChild(xall)
        
        xusers = xdoc.createElement("users")
        xusers.setAttribute("active", str(self.option == OPTION_USERS))
        for user in self.users:
            xuser = xdoc.createElement("user")
            xuser.setAttribute("uid", str(user.id))
            xuser.setAttribute("value", str(user.profile)) 
            xusers.appendChild(xuser)
        xFreeze.appendChild(xusers)
        
        xgroups = xdoc.createElement("groups")
        xgroups.setAttribute("active", str(self.option == OPTION_GROUPS))
        for group in self.groups:
            xgroup = xdoc.createElement("group")
            xgroup.setAttribute("gid", group.id)
            xgroup.setAttribute("value", str(group.profile)) 
            xgroups.appendChild(xgroup) 
        xFreeze.appendChild(xgroups)
        
        xtf.appendChild(xFreeze)
        
        xProfiles = xdoc.createElement("profiles")
        xProfiles.setAttribute("numProfiles", str(len(self.profiles)))
        xtf.appendChild(xProfiles) 
        
        for i, prof in enumerate(self.profiles):
            xProfile = xdoc.createElement("profile")
            xProfile.setAttribute("profileNum", str(i))
            xProfile.setAttribute("name", prof.title)
                        
            xsource = xdoc.createElement("source")
            xsource.setAttribute("active", str(prof.saved_source))
            xsource.setAttribute("value", prof.source)
            xProfile.appendChild(xsource)
            
            xdeposit = xdoc.createElement("deposit")
            xdeposit.setAttribute("value", prof.deposit)
            xProfile.appendChild(xdeposit)
            
            xrules = xdoc.createElement("rules")
              
            for r in prof.rules:
                xchild = xdoc.createElement("rule")
                xchild.setAttribute("title", str(r.name))
                xchild.setAttribute("pattern", str(r.filter))
                xchild.setAttribute("value", str(r.action))
                xrules.appendChild(xchild)
            
            xProfile.appendChild(xrules)
            
            
            xProfiles.appendChild(xProfile)
        
        xSource = xdoc.createElement("sources")
        for s in self.sources:
            xchild = xdoc.createElement("source")
            xchild.setAttribute("title", str(s.name))
            xchild.setAttribute("file", str(s.file))
            xSource.appendChild(xchild)
        xtf.appendChild(xSource)
        
        try:   
            os.makedirs(CONFIG_DIRECTORY,0755)
        except OSError as (errno, strerror):
            debug(CONFIG_DIRECTORY + " " + strerror,DEBUG_HIGH)
            
        try:
            file = open(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE), "w")
            file.write(xdoc.toxml())
            file.close()
        except:
            print_error(_("Can't save the configuration file"))
            raise
    
    def get_frozen_users(self,time = TIME_INDEFFERENT):
        debug('Entering config.get_frozen_users',DEBUG_LOW)
       
        #IF requested time is not indifferent
        #AND time requested is different  of the configured time
        if time != TIME_INDEFFERENT and self.time != time:
            #Return and don't parse more
            return []
        
        #ALL
        if self.option == OPTION_ALL:
            debug('  ALL SYSTEM',DEBUG_LOW)
            return self.get_all_frozen()
        
        #BY USERS
        if self.option == OPTION_USERS:
            debug('  USERS',DEBUG_LOW)
            return self.get_users_frozen()
        
        #BY GROUPS
        if self.option == OPTION_GROUPS:
            debug('  GROUPS',DEBUG_LOW)
            return self.get_groups_frozen()
    
    def init_profile(self, prof):

        uf = user_frozen()
        p = self.profiles[prof]
        uf.name =  p.title
        
        if(p.saved_source):
            uf.source = p.source
        else:
            uf.source = ""
 
        uf.deposit = p.deposit
        
        for rule in p.rules:
            uf.filters.append([rule.action,rule.filter])
            
        return uf
    
    def get_all_frozen(self):
        if self.all == FREEZE_NONE or self.all >= len(self.profiles):
            return []
        
        frozen_users = []
        
        #Exec for all users in the permitted uid range
        for user in pwd.getpwall():
            uid = user.pw_uid
            if uid >= minUID and uid < maxUID:
                newConf = self.init_profile(self.all)
                newConf.username = user.pw_name
                newConf.homedir = user.pw_dir
                newConf.uid = user.pw_uid
                newConf.gid = user.pw_gid
                
                frozen_users.append(newConf)
                
        #TODO: ldap
        if self.ldap_enabled:
            try:
                con = ldap.initialize(self.ldap_server)
                filter = '(objectclass=posixAccount)'
                attrs = ['uid','homeDirectory','gidNumber','uidNumber']
             
                result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                for person in result:
                    newConf = self.init_profile(self.all)
                    newConf.username = person[1]['uid'][0]
                    newConf.homedir = person[1]['homeDirectory'][0]
                    newConf.uid = person[1]['uidNumber'][0]
                    newConf.gid = person[1]['gidNumber'][0]
                
                    frozen_users.append(newConf)
                    
            except ldap.LDAPError, e:
                print e
            
        return frozen_users
    
    def get_users_frozen(self):
        
        frozen_users = []
        
        for user in self.users:
            if user.profile == FREEZE_NONE or user.profile >= len(self.profiles):
                continue
            if user.id < minUID or user.id >= maxUID:  continue
            
            debug("   " +str(user.id),DEBUG_LOW)
            
            try:
                pwuser = pwd.getpwuid(user.id)
            except:
                print_error("User " + user.id + " not found")
            else:        
                prof = self.init_profile(user.profile)
                prof.username = pwuser.pw_name
                prof.homedir = pwuser.pw_dir
                prof.uid = pwuser.pw_uid
                prof.gid = pwuser.pw_gid
                
                frozen_users.append(prof)
                continue
            
            #If not found, try ldap
            if self.ldap_enabled:
                try:
                    con = ldap.initialize(self.ldap_server)
                    filter = '(&(objectclass=posixAccount)(uidNumber='+str(user.id)+'))'
                    attrs = ['uid','homeDirectory','gidNumber','uidNumber']
                    result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                    if len(result) > 0:
                        prof = self.init_profile(user.profile)
                        prof.username = result[0][1]['uid'][0]
                        prof.homedir = result[0][1]['homeDirectory'][0]
                        prof.uid = result[0][1]['uidNumber'][0]
                        prof.gid = result[0][1]['gidNumber'][0]
                    
                        frozen_users.append(prof)
                        continue
                except ldap.LDAPError, e:
                    print e
                    continue
        
        return frozen_users
                
    
    def get_groups_frozen(self):
        
        frozen_users = []
        
        for group in self.groups:
            if group.profile == FREEZE_NONE or group.profile >= len(self.profiles):
                continue
            if group.id < minUID or group.id >= maxUID:  continue
            
            debug("   " +str(group.id),DEBUG_LOW)
        
            #Usuari primari del grup
            for pwuser in pwd.getpwall():
                if group.id == user.pw_gid:
                    uid = pwuser.pw_uid
                    if uid >= minUID and uid < maxUID:
                        prof = self.init_profile(group.profile)
                        prof.username = pwuser.pw_name
                        prof.homedir = pwuser.pw_dir
                        prof.uid = pwuser.pw_uid
                        prof.gid = pwuser.pw_gid
                        
                        frozen_users.append(prof)
                    break
                
            #Usuaris secuntaris del grup
            try:
                pwgroup = grp.getgrgid(group.id)
            except:
                print_error("Group " + group.id + " not found")
            else:
                for username in pwgroup.gr_mem:
                    try:
                        pwuser = pwd.getpwname(username)
                    except:
                        print_error("User " + pwuser + " not found",WARNING)
                    else:
                        uid = pwuser.pw_uid
                        if uid >= minUID and uid < maxUID: 
                            prof = self.init_profile(group.profile)
                            prof.username = pwuser.pw_name
                            prof.homedir = pwuser.pw_dir
                            prof.uid = pwuser.pw_uid
                            prof.gid = pwuser.pw_gid
                            
                            frozen_users.append(prof)
            
            #TODO: if not in local
            #TODO: ldap
            #Primary and secontaries group user
            if self.ldap_enabled:
                try:
                    con = ldap.initialize(self.ldap_server)
                    filter = '(&(objectclass=posixGroup)(gidNumber='+str(group.id)+'))'
                    attrs = ['memberUid']
                 
                    result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
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
                        
                    filter = '(|(&(objectclass=posixAccount)(gidNumber='+str(group.id)+'))'+secondaries+')'
                    attrs = ['uid','homeDirectory','gidNumber','uidNumber']
                 
                    result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                    for person in result:
                        prof = self.init_profile(group.profile)
                        prof.username = person['uid'][0]
                        prof.homedir = person['homeDirectory'][0]
                        prof.uid = person['uidNumber'][0]
                        prof.gid = person['gidNumber'][0]
        
                        frozen_users.append(prof)
                            
                except ldap.LDAPError, e:
                    print e
                    continue
            
        return frozen_users
    
    def try_ldap(self):
        if self.ldap_enabled:
            try:
                con = ldap.initialize(self.ldap_server)
                filter = '(objectclass=posixAccount)'
                attrs = ['uidNumber']
             
                result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                if len(result) < 1:
                    self.ldap_enabled = False
                    
            except ldap.LDAPError, e:
                self.ldap_enabled = False
                
    #TOFIX: new users?
    def reload_users(self):
        
        to_remove = []
        for user in self.users:
            try:
                pwuser = pwd.getpwuid(user.id)
            except:
                trobat = False
                if(self.ldap_enabled):
                    try:
                        con = ldap.initialize(self.ldap_server)
                        filter = '(objectclass=posixAccount)'
                        attrs = ['uidNumber']
                     
                        result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                        for lduser in result:
                            uid = lduser[1]['uidNumber'][0]
                            if uid == user.id:
                                trobat = True
                                break
                            
                    except ldap.LDAPError, e:
                        print_error(e,WARNING) 
                if not trobat:
                    to_remove.append(user)
                        
        for user in to_remove:
            self.users.remove(user)

    #TOFIX: new groups?
    def reload_groups(self):
        
        to_remove = []
        for group in self.groups:
            try:
                pwgroup = grp.getgrgid(group.id)
            except:
                trobat = False
                if(self.ldap_enabled):
                    try:
                        con = ldap.initialize(self.ldap_server)
                        filter = '(objectclass=posixGroup)'
                        attrs = ['gidNumber']
                     
                        result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                        for ldgroup in result:
                            gid = ldgroup[1]['gidNumber'][0]
                            if gid == group.id:
                                trobat = True
                                break
                        
                    except ldap.LDAPError, e:
                        print_error(e,WARNING)
                        
                if not trobat:
                    to_remove.append(group)
                        
        for group in to_remove:
            self.groups.remove(group)  
                        
    def load_users(self):
        del self.users[:]
         
        for pwuser in pwd.getpwall():
            uid = pwuser.pw_uid
            if uid >= minUID and uid < maxUID:
                user = user_group(pwuser.pw_uid, pwuser.pw_name)
                self.users.append(user)
                
        #LDAP users
        if(self.ldap_enabled):
            try:
                con = ldap.initialize(self.ldap_server)
                filter = '(objectclass=posixAccount)'
                attrs = ['uid','uidNumber']
             
                result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                for lduser in result:
                    usern = lduser[1]['uid'][0]
                    uid = lduser[1]['uidNumber'][0]
                    user = user_group(uid, usern, ldap=True)
                    self.users.append(user)
                    
            except ldap.LDAPError, e:
                print_error(e,WARNING)
                
    def load_groups(self):
        del self.groups[:]
         
        for pwgroup in grp.getgrall():
            gid = pwgroup.gr_gid
            if gid >= minUID and gid < maxUID:
                group = user_group(pwgroup.gr_gid, pwgroup.gr_name)
                self.groups.append(group)
                
        #LDAP groups
        if(self.ldap_enabled):
            try:
                con = ldap.initialize(self.ldap_server)
                filter = '(objectclass=posixGroup)'
                attrs = ['cn','gidNumber']
             
                result = con.search_s(self.ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
                for ldgroup in result:
                    groupn = ldgroup[1]['cn'][0]
                    gid = ldgroup[1]['gidNumber'][0]
                    group = user_group(gid, groupn, ldap=True)
                    self.groups.append(group)
                    
            except ldap.LDAPError, e:
                print_error(e,WARNING)
    