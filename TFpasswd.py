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
import ldap


class pwduser():
    def __init__(self, name, uid, gid, homedir):
        self.pw_name = name
        self.pw_uid = uid
        self.pw_gid = gid
        self.pw_dir = homedir
        
class pwdgroup():
    def __init__(self,name,gid,usernames):
        self.gr_name = name
        self.gr_gid = gid
        self.usernames = []
        for username in usernames.split(','):
            username = username.strip()
            if username != "":
                self.usernames.append(username)
        self.users = dict()
    
    def adduser(self,user):
        self.users[user.pw_uid] = user

class ldap_tester():
    def try_ldap(self, server, dn):
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
            if int(fields[2]) >= minUID and int(fields[2]) < maxUID:
                group = pwdgroup(fields[0],fields[2],fields[3])
                self.groups[fields[2]] = group
        file.close()
        
        self.users = dict()
        file = open("/etc/passwd", "r")
        for line in file:
            fields = line.split(':')
            if int(fields[2]) >= minUID and int(fields[2]) < maxUID:
                user = pwduser(fields[0],fields[2],fields[3],fields[5])
                self.users[fields[2]] = user
                if fields[3] in self.groups:
                    self.groups.get(fields[3]).adduser(user)
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
        uid = str(uid)
        return self.users.get(uid)
    
    def getpwgruid(self, gid):
        gid = str(gid)
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
                    gid = ldgroup[1]['gidNumber'][0]
                    try:
                        usernames = ""
                        for uid in ldgroup[1]['memberUid']:
                            usernames = usernames + uid + ','
                    except:
                        secusers = ""
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
                    uid = person[1]['uidNumber'][0]
                    gid = person[1]['gidNumber'][0]
                    user = pwduser(username,uid,gid,homedir)
                    self.users[uid] = user
                    if gid in self.groups:
                        self.groups.get(gid).adduser(user)
            
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
        uid = str(uid)
        return self.users.get(uid)
    
    def getpwgruid(self, gid):
        gid = str(gid)
        return self.groups.get(gid).users.itervalues()
    