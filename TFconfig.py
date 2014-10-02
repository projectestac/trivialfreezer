#-*- coding: utf-8 -*-
#@authors: Pau Ferrer Ocaña
#@authors: Modified TICxCAT 

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

from TFglobals import *
from TFuser_frozen import *
from TFpasswd import *

from xml.dom import minidom

import os
import tarfile

from datetime import datetime

_ = load_locale()

class source:
    "Source class with the restoring tar file for the repository"
    
    #Name of the source
    name = ""
    #Where is the source
    file = ""
    
class profile:
    "Frozen profile class"
    
    #Name of the profile
    title = ""
    #Rule filters to apply to the profile
    rules = []
    #Select if the profile can be edited in the configuration window
    could_be_edited = True
    #Select if the source is from the repository of sources
    saved_source = False
    #Where is the source
    source = ""
    #Where leave the lost+found files
    deposit = ""
    #Is execution enabled
    execute_enabled = False
    #What to execute after restoring
    execute = ""
    
    def __init__(self, title = ""):
        self.title = title
        self.rules = []
        self.could_be_edited = True
        self.saved_source = False
        self.source = ""
        self.deposit = ""
        self.execute = ""
        execute_enabled = False
            
class rule:
    "Filter rules for frozen profiles"
    
    #Name of the rule
    name = ""
    #Regular Expression to apply
    filter = ""
    #Action to apply to the rule
    action = ACTION_KEEP
    
    def __init__(self, name, filter, action):
        self.name = name
        self.filter = filter
        self.action = action

class user_group:
    "User or group, profile assigned and if it's from ldap"
    
    #Uid for users of gid for groups
    id = ""
    #User or group name
    name = ""
    #Profile to apply
    profile = FREEZE_NONE
    #Choose if the user/group is from external or local machine
    ldap = False
    
    def __init__(self, id, name, profile=FREEZE_NONE, ldap=False):
        self.id = id
        self.name = name
        self.profile = profile
        self.ldap = ldap

    def set_profile(self,profile):
        "Sets a profile to the user or group"
        
        self.profile = profile
    
class config:
    "Class to manage all the configuration of the Freezer"
    
    #Sources repository
    sources = []
    #Sources to erase from disk when saving
    sources_to_erase = []
    #Profiles to erase when importing users
    profiles_to_erase = []
    
    #Existing frozen profiles
    profiles = []
    #Time of restoring (session, will restore for every logged session
    #or system for the whole system)
    time = TIME_SYSTEM #Value modified by TICxCAT from TIME_SESSION to TIME_SYSTEM
    
    #Option of freezing, all to freeze all the system together,
    #user to select each user or group for each group
    option = OPTION_ALL
    #Profile selected for ALL OPTION
    all = FREEZE_NONE
    #List of users and its selected profiles
    users = []
    #List of groups and its selected profiles
    groups = []
    
    #Select if the ldap is enabled
    ldap_enabled = False
    #Where is the server
    ldap_server = ""
    #Which domain name of the ldap server
    ldap_dn = ""
    
    #Choose if I'm in the NFS home server or I'm a client
    home_server = False
    #If I'm the client, who is the server?
    home_server_ip = ""
    #To which port I have to connect to ssh?
    home_server_port = "22"
    #Which user is going to connect to the server
    home_server_user = "tfreezer"
        
    def load(self):
        "Loads from the XML the configuration from the file"
        
        try:  
            xdoc = minidom.parse(os.path.join(CONFIG_DIRECTORY, CONFIG_FILE))
        except:
            print_error(_("Corrupted config file, taking defaults"),WARNING)
    
        #Load the saved sources of the repository
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        try:   
            os.makedirs(dirname,0755)
        except OSError , (errno, strerror):
            debug(dirname + " " + strerror,DEBUG_HIGH)
            
        del self.sources [:]
        
        try:
            xSources = xdoc.getElementsByTagName("sources")[0].getElementsByTagName("source")
        except:
            print_error(_("Corrupted or empty sources tag, taking defaults"),WARNING)
        else:
            for xSource in xSources:
                s = source()
                try:
                    s.name = xSource.getAttribute("title")
                    s.file = xSource.getAttribute("file")
                    filename = os.path.join (dirname, s.file)
                    tar = tarfile.open(filename,'r')
                    tar.close()
                except:
                    print_error(_("Corrupted source file tag, ignoring..."),WARNING)
                else:
                    self.sources.append(s)
        
        #Load the not saved source files, it means, the tars that are not saved
        #but are present in the repository path
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
                        #Take the name from the file
                        s.name = file.split(".",1)[0]
                        s.file = file
                        self.sources.append(s)
            
        
        #Load the frozen profiles
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
                    p.title = self.__get_profile_name_defaults(i)
                
                if i < BLOCKED_PROFILES:
                    p.could_be_edited = False
                                   
                try:
                    p.saved_source = str2bool(xProfile.getElementsByTagName("source")[0].getAttribute("active"))
                    p.source = xProfile.getElementsByTagName("source")[0].getAttribute("value")
                except:
                    print_error("Corrupted source tag, taking defaults",WARNING)
                    p.saved_source = False
                    
                try:
                    p.execute_enabled = str2bool(xProfile.getElementsByTagName("execute")[0].getAttribute("active"))
                    p.execute = xProfile.getElementsByTagName("execute")[0].getAttribute("value")
                except:
                    print_error("Corrupted execute tag, taking defaults",WARNING)
                    p.execute_enabled = False
                    
                try:
                    p.deposit = xProfile.getElementsByTagName("deposit")[0].getAttribute("value")
                except:
                    print_error("Corrupted deposit tag, taking defaults",WARNING)
                    p.deposit = ""
                    
                try:   
                    for xRule in xProfile.getElementsByTagName("rules")[0].getElementsByTagName("rule"):
                        r = rule(xRule.getAttribute("title"),xRule.getAttribute("pattern"),str2int(xRule.getAttribute("value")))
                        p.rules.append(r)
                except:
                    print_error("Corrupted or empty rules tag, taking defaults",WARNING)
                    p.rules = self.__get_profile_rules_defaults(i)
                self.profiles.append(p)
        
        #Load general options
        try:
            xFreeze = xdoc.getElementsByTagName("freeze")[0]
        except:
            print_error("Corrupted freeze tag, taking defaults",WARNING) 
            
        try:
            self.time = str2int(xFreeze.getAttribute("time"))
        except:
            print_error("Corrupted time attribute on freeze tag, taking defaults",WARNING)
            self.__load_time_defaults()
        
        try:
            if str2bool(xFreeze.getElementsByTagName("all")[0].getAttribute("active")):
                self.option = OPTION_ALL
            elif str2bool(xFreeze.getElementsByTagName("users")[0].getAttribute("active")):
                self.option = OPTION_USERS
            elif str2bool(xFreeze.getElementsByTagName("groups")[0].getAttribute("active")):
                self.option = OPTION_GROUPS
        except:
            print_error("Corrupted option tag, taking defaults",WARNING)
            self.__load_freeze_defaults()
        else:
            try:
                self.all = str2int(xFreeze.getElementsByTagName("all")[0].getAttribute("value"))
            except:
                print_error("Corrupted all tag, taking defaults",WARNING)
                self.__load_freeze_defaults()
        
        #Load Ldap and nfs configuration
        try:
            xLdap = xdoc.getElementsByTagName("ldap")[0]
            self.ldap_enabled = str2bool(xLdap.getAttribute("active"))
            self.ldap_server = xLdap.getAttribute("server")
            self.ldap_dn = xLdap.getAttribute("dn")
            
            xHomeServer = xdoc.getElementsByTagName("homserver")[0]
            self.home_server_ip = xHomeServer.getAttribute("ip")
            self.home_server_port = xHomeServer.getAttribute("port")
            self.home_server = str2bool(xHomeServer.getAttribute("server"))
            self.home_server_user = xHomeServer.getAttribute("user")
        except:
            print_error("Corrupted ldap or homserver tag, taking defaults",WARNING)
            self.__load_ldap_defaults()
        
        #Load users and it's profiles
        try:
            self.__load_users()
            #Change profiles for saved users
            users = xdoc.getElementsByTagName("users")[0].getElementsByTagName("user")
        except:
            print_error("Corrupted or empty users tag, ignoring...",WARNING)
        else:
            for xUser in users:
                try:
                    uid = int(xUser.getAttribute("uid"))
                    ldap = str2bool(xUser.getAttribute("ldap"))
                except:
                    print_error("Corrupted user tag, ignoring...",WARNING)
                else:
                    for user in self.users:
                        if user.id == uid and ldap == user.ldap:
                            try:
                                value = int(xUser.getAttribute("value"))
                            except:
                                print_error("Corrupted user tag, ignoring...",WARNING)
                            else:
                                user.set_profile(value)
                            break
        
        #Load groups and it's profiles
        try:
            self.__load_groups()
            #Change profiles for saved groups
            groups = xdoc.getElementsByTagName("groups")[0].getElementsByTagName("group")
        except:
            print_error("Corrupted or empty groups tag, ignoring...",WARNING)
        else:
            for xGroup in groups:
                try:
                    gid = int(xGroup.getAttribute("gid"))
                    ldap = str2bool(xGroup.getAttribute("ldap"))
                except:
                    print_error("Corrupted group tag, ignoring...",WARNING)
                else:
                    for group in self.groups:
                        if group.id == gid and ldap == group.ldap:
                            try:
                                value = int(xGroup.getAttribute("value"))
                            except:
                                print_error("Corrupted group tag, ignoring...",WARNING)
                            else:
                                group.set_profile(value)
                            break
        
            
    def __get_profile_rules_defaults(self,index):
        "Gets the default profile rules"
        
        rules = []
        #For Unfrozen profile
        if index == FREEZE_NONE:
            r = rule(_("Everything"),".",ACTION_KEEP)
            rules.append(r)
        #For total frozen profile
        elif index == FREEZE_ALL:
            r = rule(_("Everything"),".",ACTION_RESTORE)
            rules.append(r)
        #For Only configuration frozen profile
        elif index  == FREEZE_ADV:
            r = rule(_("Configuration"),"^\.",ACTION_RESTORE)
            rules.append(r)
            r = rule(_("Everything"),".",ACTION_KEEP)
            rules.append(r)
        return rules
    
    def __get_profile_name_defaults(self,index):
        "Gets the default title of the profile"
        
        #For Unfrozen profile
        if index == FREEZE_NONE:
            return _("Total Unfrozen")
        #For total frozen profile
        if index == FREEZE_ALL:
            return _("Total Frozen")
        #For Only configuration frozen profile
        if index  == FREEZE_ADV:
            return _("Configuration Frozen")
        #For Freeze LDAP
        if index == FREEZE_LDAP:
            return _("Frozen in the server")
        
        #For other profile, gets the number
        return _("Profile") + " " + str(index + 1)
        
    def load_profile_defaults(self):
        "Gets the default configuration for all profiles"
        
        self.profiles[:]
        #For Unfrozen profile
        p = profile(self.__get_profile_name_defaults(FREEZE_NONE))
        p.could_be_edited = False
        p.rules = self.__get_profile_rules_defaults(FREEZE_NONE)
        self.profiles.append(p)
        #For total frozen profile
        p = profile(self.__get_profile_name_defaults(FREEZE_ALL))
        p.could_be_edited = False
        p.rules = self.__get_profile_rules_defaults(FREEZE_ALL)
        self.profiles.append(p)
        #For Only configuration frozen profile
        p = profile(self.__get_profile_name_defaults(FREEZE_ADV))
        p.could_be_edited = False
        p.rules = self.__get_profile_rules_defaults(FREEZE_ADV)
        self.profiles.append(p)
        
    def __load_time_defaults(self):
        "Gets the default time of restoring"
        self.time = TIME_SYSTEM #Value modified by TICxCAT from TIME_SESSION to TIME_SYSTEM
        
    def __load_freeze_defaults(self):
        "Gets the default general freezing options"
        self.option = OPTION_ALL
        self.all = FREEZE_NONE
        
    def __load_ldap_defaults(self):
        "Gets the default ldap and NFS configuration"
        self.ldap_enabled = False
        self.ldap_server = ""
        self.ldap_dn = ""
        self.home_server = False
        self.home_server_ip = ""
        self.home_server_port = "22"
        self.home_server_user = "tfreezer"
    
    def __load_defaults(self):
        "Gets all the default configuration"
        
        #Load the source repository
        self.sources[:]
        
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        try:   
            os.makedirs(dirname,0755)
        except OSError , (errno, strerror):
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
            
        self.__load_time_defaults()
        self.__load_freeze_defaults()
        
        self.__load_ldap_defaults()
        
        self.__load_users()
        self.__load_groups()
    
    def save(self):
        "Saves in XML the generated configuration"
          
        #Create the minidom document
        xdoc = minidom.Document()
        
        xtf = xdoc.createElement("tfreezer")
        #Save the date
        xtf.setAttribute("date", str(datetime.now()))
        xdoc.appendChild(xtf)
        
        #Save the general options
        xFreeze = xdoc.createElement("freeze")
        #xFreeze.setAttribute("time", str(self.time))
       	xFreeze.setAttribute("time", "0") #Modified by TICxCAT
        
        xall = xdoc.createElement("all")
        xall.setAttribute("active", str(self.option == OPTION_ALL))  
        xall.setAttribute("value", str(self.all))
        xFreeze.appendChild(xall)
        
        #Save users
        xusers = xdoc.createElement("users")
        xusers.setAttribute("active", str(self.option == OPTION_USERS))
        for user in self.users:
            xuser = xdoc.createElement("user")
            xuser.setAttribute("uid", str(user.id))
            xuser.setAttribute("value", str(user.profile))
            xuser.setAttribute("ldap", str(user.ldap))  
            xusers.appendChild(xuser)
        xFreeze.appendChild(xusers)
        
        #Save groups
        xgroups = xdoc.createElement("groups")
        xgroups.setAttribute("active", str(self.option == OPTION_GROUPS))
        for group in self.groups:
            xgroup = xdoc.createElement("group")
            xgroup.setAttribute("gid", str(group.id))
            xgroup.setAttribute("value", str(group.profile))
            xgroup.setAttribute("ldap", str(group.ldap))
            xgroups.appendChild(xgroup) 
        xFreeze.appendChild(xgroups)
        
        xtf.appendChild(xFreeze)
        
        #Save profiles
        xProfiles = xdoc.createElement("profiles")
        xProfiles.setAttribute("numProfiles", str(len(self.profiles)))
        xtf.appendChild(xProfiles) 
        
        for i, prof in enumerate(self.profiles):
            xProfile = xdoc.createElement("profile")
            xProfile.setAttribute("profileNum", str(i))
            xProfile.setAttribute("name", prof.title)
                        
            xsource = xdoc.createElement("source")
            if prof.source == "":
                xsource.setAttribute("active", str(False))
            else:
                xsource.setAttribute("active", str(prof.saved_source))
            xsource.setAttribute("value", prof.source)
            xProfile.appendChild(xsource)
            
            xdeposit = xdoc.createElement("deposit")
            xdeposit.setAttribute("value", prof.deposit)
            xProfile.appendChild(xdeposit)
            
            xexecute = xdoc.createElement("execute")
            if prof.execute == "":
                xexecute.setAttribute("active", str(False))
            else:
                xexecute.setAttribute("active", str(prof.execute_enabled))
            xexecute.setAttribute("value", prof.execute)
            xProfile.appendChild(xexecute)
            
            xrules = xdoc.createElement("rules")
              
            for r in prof.rules:
                xchild = xdoc.createElement("rule")
                xchild.setAttribute("title", str(r.name))
                xchild.setAttribute("pattern", str(r.filter))
                xchild.setAttribute("value", str(r.action))
                xrules.appendChild(xchild)
            
            xProfile.appendChild(xrules)
            
            
            xProfiles.appendChild(xProfile)
            
        #Save sources
        xSource = xdoc.createElement("sources")
        for s in self.sources:
            xchild = xdoc.createElement("source")
            xchild.setAttribute("title", str(s.name))
            xchild.setAttribute("file", str(s.file))
            xSource.appendChild(xchild)
        xtf.appendChild(xSource)
        
        #Save ldap and NFS configuration
        xLdap = xdoc.createElement("ldap")
        xLdap.setAttribute("active", str(self.ldap_enabled))
        xLdap.setAttribute("server", str(self.ldap_server))
        xLdap.setAttribute("dn", str(self.ldap_dn))
        xtf.appendChild(xLdap)
        
        xHomeServer = xdoc.createElement("homserver")
        xHomeServer.setAttribute("ip", str(self.home_server_ip))
        xHomeServer.setAttribute("port", str(self.home_server_port))
        xHomeServer.setAttribute("server", str(self.home_server))
        xHomeServer.setAttribute("user", str(self.home_server_user))
        xtf.appendChild(xHomeServer)
        
        #Save the file
        try:   
            os.makedirs(CONFIG_DIRECTORY,0755)
        except OSError , (errno, strerror):
            debug(CONFIG_DIRECTORY + " " + strerror,DEBUG_HIGH)
        
        try:
            file = open(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE), "w")
            file.write(xdoc.toxml("utf-8"))
            file.close()
        except:
            print_error(_("Can't save the configuration file"))
            raise
        
        #Erase the deleted sources from the filesystem
        for path in self.sources_to_erase:
            os.unlink(path)
            
        del self.sources_to_erase[:]
    
    def get_frozen_users(self, action):
        "Gets a list of users and its frozen configuration"
       
        #ALL
        if self.option == OPTION_ALL:
            debug('GET ALL SYSTEM',DEBUG_LOW)
            return self.__get_all_frozen(action)
        
        #BY USERS
        if self.option == OPTION_USERS:
            debug('GET USERS',DEBUG_LOW)
            return self.__get_users_frozen(action)
        
        #BY GROUPS
        if self.option == OPTION_GROUPS:
            debug('GET GROUPS',DEBUG_LOW)
            return self.__get_groups_frozen(action)
    
    def __init_profile(self, prof):
        "Initializes a user_frozen with the selected options"
        
        p = self.profiles[prof]
        
        if(p.saved_source):
            source = p.source
        else:
            source = ""
        
        if(p.execute_enabled):
            execute = p.execute
        else:
            execute = ""
            
        return user_frozen(p.title,p.deposit,p.rules,source,execute)  
    
    def __get_all_frozen(self, action):
        "Gets the profile configuration of all users in the system"
        
        #If it's unfrozen or the selected profile does not exists...
        if self.all == FREEZE_NONE or self.all >= len(self.profiles):
            return []
        
        frozen_users = []
        
        #Init for all users
        userlist = passwd()
        for pwuser in userlist.getpwall():
            #Set up options for the current user
            prof = self.__init_profile(self.all)
            prof.username = pwuser.pw_name
            prof.homedir = pwuser.pw_dir
            prof.uid = pwuser.pw_uid
            prof.gid = pwuser.pw_gid
            prof.hostname = ""
            
            frozen_users.append(prof)

        
        #If I'm the client, I can't create tars
        if action == TAR_CREATE and not self.home_server:
            return frozen_users
        
        #LDAP enabled?
        if not self.ldap_enabled:
            return frozen_users
        
        #The same for ldap users
        ldaplist = ldappasswd(self.ldap_server,self.ldap_dn)
        for pwuser in ldaplist.getpwall():
            prof = self.__init_profile(self.all)
            prof.username = pwuser.pw_name
            prof.homedir = pwuser.pw_dir
            prof.uid = pwuser.pw_uid
            prof.gid = pwuser.pw_gid
            
            #If I'm restoring from the client, I have to say where is the server
            if action == TAR_RESTORE and not self.home_server:
                prof.hostname = self.home_server_ip
                prof.port = self.home_server_port
                prof.server_user = self.home_server_user
            else:
                prof.hostname = ""
        
            frozen_users.append(prof)
            
        return frozen_users
    
    def __get_users_frozen(self, action):
        "Gets the user profile settings of every user in the system"
        
        frozen_users = []
        userlist = passwd()
        #Load ldap list of users
        if self.ldap_enabled:
            ldaplist = ldappasswd(self.ldap_server,self.ldap_dn)
            #If I'm the client, I can't create tars
            if action == TAR_CREATE and not self.home_server:
                ldap_ok = False
            else:
                ldap_ok = True
        else:
            ldap_ok = False
        
        for user in self.users:
            #If it's unfrozen or the selected profile does not exists...
            if user.profile == FREEZE_NONE or user.profile >= len(self.profiles):
                continue
            
            #Is an ldap user?
            if(not user.ldap):
                pwuser = userlist.getpwuid(user.id)
                if pwuser == None:
                    print_error("User " + str(user.id) + " not found")
                else:        
                    prof = self.__init_profile(user.profile)
                    prof.username = pwuser.pw_name
                    prof.homedir = pwuser.pw_dir
                    prof.uid = pwuser.pw_uid
                    prof.gid = pwuser.pw_gid
                    prof.hostname = ""
                    
                    debug("User "+prof.username+"("+str(prof.uid)+":"+str(prof.gid)+")"+" with profile " + self.__get_profile_name_defaults(user.profile),DEBUG_LOW)
                    
                    frozen_users.append(prof)
            #Is ldap and can access to ldap
            elif ldap_ok:

                pwuser = ldaplist.getpwuid(user.id)
                if pwuser == None:
                    print_error("User " + str(user.id) + " not found")
                else:        
                    prof = self.__init_profile(user.profile)
                    prof.username = pwuser.pw_name
                    prof.homedir = pwuser.pw_dir
                    prof.uid = pwuser.pw_uid
                    prof.gid = pwuser.pw_gid
                    
                    #If I'm restoring from the client, I have to say where is the server
                    if action == TAR_RESTORE and not self.home_server:
                        prof.hostname = self.home_server_ip
                        prof.port = self.home_server_port
                        prof.server_user = self.home_server_user
                    else:
                        prof.hostname = ""
                        
                    debug("User "+prof.username+"("+str(prof.uid)+":"+str(prof.gid)+")"+" with profile " + self.__get_profile_name_defaults(user.profile),DEBUG_LOW)
                    
                    frozen_users.append(prof)
        
        return frozen_users
    
    def __get_groups_frozen(self, action):
        "Gets the group profile settings of every user in the system"
        
        frozen_users = []
        userlist = passwd()
        #Load ldap list of users
        if self.ldap_enabled:
            ldaplist = ldappasswd(self.ldap_server,self.ldap_dn)
            #If I'm the client, I can't create tars
            if action == TAR_CREATE and not self.home_server:
                ldap_ok = False
            else:
                ldap_ok = True
        else:
            ldap_ok = False
        
        for group in self.groups:
            #If it's unfrozen or the selected profile does not exists...
            if group.profile == FREEZE_NONE or group.profile >= len(self.profiles):
                continue
            
            #Is an ldap group?
            if(not group.ldap):
                users = userlist.getpwgruid(group.id)
                #All users in the group
                for pwuser in users:
                    prof = self.__init_profile(group.profile)
                    prof.username = pwuser.pw_name
                    prof.homedir = pwuser.pw_dir
                    prof.uid = pwuser.pw_uid
                    prof.gid = pwuser.pw_gid
                    prof.hostname = ""
                    
                    debug("User "+prof.username+"("+str(prof.uid)+":"+str(prof.gid)+")"+" with profile " + self.__get_profile_name_defaults(group.profile),DEBUG_LOW)
                    
                    frozen_users.append(prof)
            #Is ldap and can access to ldap     
            elif ldap_ok:      
            
                users = ldaplist.getpwgruid(group.id)
                #All users in the group
                for pwuser in users:
                    prof = self.__init_profile(group.profile)
                    prof.username = pwuser.pw_name
                    prof.homedir = pwuser.pw_dir
                    prof.uid = pwuser.pw_uid
                    prof.gid = pwuser.pw_gid
                    
                    #If I'm restoring from the client, I have to say where is the server
                    if action == TAR_RESTORE and not self.home_server:
                        prof.hostname = self.home_server_ip
                        prof.port = self.home_server_port
                        prof.server_user = self.home_server_user
                    else:
                        prof.hostname = ""
                        
                    debug("User "+prof.username+"("+str(prof.uid)+":"+str(prof.gid)+")"+" with profile " + self.__get_profile_name_defaults(group.profile),DEBUG_LOW)
                    
                    frozen_users.append(prof)
            
        return frozen_users
    
    def reload_users(self):
        "Reloads users applying their old profile"
        
        oldusers = self.users[:]
        self.__load_users()
        
        #Apply the old profile (if possible)
        for user in self.users:
            for olduser in oldusers:
                if user.id == olduser.id and user.ldap == olduser.ldap:
                    erase = 0
                    for prof in self.profiles_to_erase:
                        if prof < olduser.profile:
                            erase += 1
                            
                    if olduser.profile in self.profiles_to_erase:
                        user.profile = FREEZE_NONE
                    else:
                        user.profile = olduser.profile - erase
                    break
                
    def reload_groups(self):
        "Reloads groups applying their old profile"
        
        oldgroups = self.groups[:]
        self.__load_groups()
        
        #Apply the old profile (if possible)
        for group in self.groups:
            for oldgroup in oldgroups:
                if group.id == oldgroup.id and group.ldap == oldgroup.ldap:
                    erase = 0
                    for prof in self.profiles_to_erase:
                        if prof < oldgroup.profile:
                            erase += 1
                            
                    if oldgroup.profile in self.profiles_to_erase:
                        group.profile = FREEZE_NONE
                    else:
                        group.profile = oldgroup.profile - erase
                    break
                        
    def __load_users(self):
        "Load system users"
        
        del self.users[:]
         
        userlist = passwd()
        
        #System users
        for pwuser in userlist.getpwall():
            user = user_group(pwuser.pw_uid, pwuser.pw_name)
            self.users.append(user)
             
        #LDAP users
        if(self.ldap_enabled):
            ldaplist = ldappasswd(self.ldap_server,self.ldap_dn)
        
            for pwuser in ldaplist.getpwall():
                user = user_group(pwuser.pw_uid, pwuser.pw_name, ldap=True)
                self.users.append(user)

                
    def __load_groups(self):
        "Load system groups"
        
        del self.groups[:]
        
        grouplist = passwd()
        
        #System groups
        for pwgroup in grouplist.getgrall():
            group = user_group(pwgroup.gr_gid, pwgroup.gr_name)
            self.groups.append(group)
             
        #LDAP groups
        if(self.ldap_enabled):
            ldaplist = ldappasswd(self.ldap_server,self.ldap_dn)
        
            for pwgroup in ldaplist.getgrall():
                group = user_group(pwgroup.gr_gid, pwgroup.gr_name, ldap=True)
                self.groups.append(group)
                
