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

from TFglobals import *
import ldap

class pwduser():
    "System user class"
    
    #User name
    pw_name = ""
    #User ID
    pw_uid = 0
    #GROUP ID
    pw_gid = 0
    #Home directory
    pw_dir = ""
    
    def __init__(self, name, uid, gid, homedir):
        self.pw_name = name
        self.pw_uid = int(uid)
        self.pw_gid = int(gid)
        self.pw_dir = homedir
        
class pwdgroup():
    "System group class"
    
    #Group name
    gr_name = ""
    #Group ID
    gr_gid = 0
    #List of user names in the group
    usernames = []
    #Dictionary of users in the group
    users = dict()
    
    def __init__(self,name,gid,usernames):
        self.gr_name = name
        self.gr_gid = int(gid)
        
        self.usernames = []
        for username in usernames.split(','):
            username = username.strip()
            if username != "":
                self.usernames.append(username)
                
        #We will fill it later
        self.users = dict()
    
    #Adds a user to the list of users
    def adduser(self,user):
        self.users[user.pw_uid] = user

class ldap_tester():
    "Class to test if LDAP works"
    
    #TODO class method
    def try_ldap(self,server, dn):
        "Tries to connect LDAP and returns if it could"
        try:
            con = ldap.initialize(server)
            filter = '(objectclass=posixAccount)'
            attrs = ['uidNumber']
         
            result = con.search_s(dn, ldap.SCOPE_SUBTREE, filter, attrs)
            if len(result) < 1:
                return False
            else:
                return True
                
        except ldap.LDAPError, e:
            return False

class passwd():
    def __init__(self):
        
        self.groups = dict()
        file = open("/etc/group", "r")
        for line in file:
            fields = line.split(':')
            gid = int(fields[2])
            if gid >= minUID and gid < maxUID:
                group = pwdgroup(fields[0],gid,fields[3])
                self.groups[gid] = group
        file.close()
        
        self.users = dict()
        file = open("/etc/passwd", "r")
        for line in file:
            fields = line.split(':')
            uid = int(fields[2])
            if uid >= minUID and uid < maxUID:
                user = pwduser(fields[0],uid,fields[3],fields[5])
                self.users[uid] = user
                if user.pw_gid in self.groups:
                    self.groups.get(user.pw_gid).adduser(user)
        file.close()
        
        #Secondary user groups
        
        for group in self.groups.itervalues():
            for username in group.usernames:
                for user in self.users.itervalues():
                    if user.pw_name == username:
                        group.adduser(user)
                        break

    def getpwall(self):
        return self.users.itervalues()
    
    def getgrall(self):
        return self.groups.itervalues()
    
    def getpwuid(self, uid):
        uid = int(uid)
        return self.users.get(uid)
    
    def getpwgruid(self, gid):
        gid = int(gid)
        return self.groups.get(gid).users.itervalues()
    
    
class ldappasswd():
    def __init__(self, server, dn):
        
        self.groups = dict()
        try:
            con = ldap.initialize(server)
            filter = '(objectclass=posixGroup)'
            attrs = ['cn','gidNumber','memberUid']
         
            result = con.search_s(dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for ldgroup in result:
                gid = int(ldgroup[1]['gidNumber'][0])
                if gid >= minUID and gid < maxUID:
                    name = ldgroup[1]['cn'][0]
                    try:
                        usernames = ""
                        for uid in ldgroup[1]['memberUid']:
                            usernames = usernames + uid + ','
                    except:
                        usernames = ""
                    group = pwdgroup(name,gid,usernames)
                    self.groups[gid] = group
                
        except ldap.LDAPError, e:
            print_error(e,WARNING)
            self.groups = dict()
        
        self.users = dict()
        try:
            con = ldap.initialize(server)
            filter = '(objectclass=posixAccount)'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
            result = con.search_s(dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for person in result:
                uid = int(person[1]['uidNumber'][0])
                if uid >= minUID and uid < maxUID:
                    username = person[1]['uid'][0]
                    homedir = person[1]['homeDirectory'][0]
                    gid = person[1]['gidNumber'][0]
                    user = pwduser(username,uid,gid,homedir)
                    self.users[uid] = user
                    if user.pw_gid in self.groups:
                        self.groups.get(user.pw_gid).adduser(user)
            
        except ldap.LDAPError, e:
            print_error(e,WARNING)
            self.users = dict()
        
        #Secondary user groups
        for group in self.groups.itervalues():
            for username in group.usernames:
                for user in self.users.itervalues():
                    if user.pw_name == username:
                        group.adduser(user)
                        break

    def getpwall(self):
        return self.users.itervalues()
    
    def getgrall(self):
        return self.groups.itervalues()
    
    def getpwuid(self, uid):
        uid = int(uid)
        return self.users.get(uid)
    
    def getpwgruid(self, gid):
        gid = int(gid)
        return self.groups.get(gid).users.itervalues()
    