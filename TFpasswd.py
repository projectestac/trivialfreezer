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

class pwduser():
    def __init__(self, name, uid,gid, homedir):
        self.pw_name = name
        self.pw_uid = uid
        self.pw_gid = gid
        self.pw_dir = homedir
        
class pwdgroup():
    def __init__(self,name,gid,usernames):
        self.gr_name = name
        self.gr_gid = gid
        self.usernames = usernames
        self.users = dict()
    
    def adduser(self,user):
        self.users[user.pw_uid] = user
        

class passwd():
    def __init__(self):
        
        self.groups = dict()
        file = open("/etc/group", "r")
        for line in file:
            fields = line.split(':')
            if int(fields[2]) >= minUID and int(fields[2]) < maxUID:
                group = pwdgroup(fields[0],fields[2],fields[3].split(','))
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
                    self.groups.get(fields[3]).add_user(user)
        file.close()
        
        #Secondary user groups
        for group in self.groups:
            for username in group.usernames:
                for user in self.users:
                    if user.pw_name == username:
                        group.adduser(user)
                        break

    def getall(self):
        return self.users
    
    def getuser(self, uid):
        return self.users.get(uid)
    
    def getusergroup(self, gid):
        return self.groups.get(gid).users
    
    
#TODO: LDAP USERS
class ldapusers():
    def __init__(self):
        
        self.groups = dict()
        file = open("/etc/group", "r")
        for line in file:
            fields = line.split(':')
            if int(fields[2]) >= minUID and int(fields[2]) < maxUID:
                group = pwdgroup(fields[0],fields[2],fields[3].split(','))
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
                    self.groups.get(fields[3]).add_user(user)
        file.close()
        
        #Secondary user groups
        for group in self.groups:
            for username in group.usernames:
                for user in self.users:
                    if user.pw_name == username:
                        group.adduser(user)
                        break

    def getall(self):
        return self.users
    
    def getuser(self, uid):
        return self.users.get(uid)
    
    def getusergroup(self, gid):
        return self.groups.get(gid).users
    
         