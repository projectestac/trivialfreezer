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

import threading
import os
import tarfile
import re
import shutil


def move(src,dst):
    
    auxPath = 0 
        
    dstComplete = dst
    
    while os.path.exists(dst):
        dstComplete = dst + "_" + str(auxPath)
        auxPath = auxPath + 1

    shutil.move(src, dstComplete)
    return dst

class user_frozen ( threading.Thread ):
            
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = ""
        self.filters = []
        self.username = ""
        self.homedir = ""
        self.network = ""
        self.source = ""
        self.deposit = ""
        self.uid = 0
        self.gid = 0
        
    def create_tar(self):
        debug("Entering profile.create_tar",DEBUG_LOW)
        debug("User " + self.username + ":" + self.name + ":" + self.homedir + ":" + self.source,DEBUG_LOW)
        
        #SOURCE  ALREADY SPECIFIED
        if len(self.source) > 0: return
        
        dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
        tarpath = os.path.join (dir, self.username + TAR_EXTENSION)
        try:
            tar = tarfile.open(tarpath,'w:gz')
        except:
            print_error("on create_tar")
        else:
            #arcname is "" to avoid homedir folders to be included 
            tar.add(self.homedir,arcname="",exclude=self.exclude_from_tar)
            tar.close()
          
    def restore_tar(self):
        debug("Entering profile.restore_tar",DEBUG_LOW)
        debug("User " + self.username + ":" + self.name + ":" + self.homedir + ":" + self.source,DEBUG_LOW)
        
        #SOURCE ALREADY SPECIFIED
        if len(self.source) < 1:
            dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
            tarpath = os.path.join (dir, self.username + TAR_EXTENSION)
        else:
            dir = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
            tarpath = os.path.join (dir, self.source)
            

        #OPEN THE TAR TO KNOW IF IT EXISTS AND IS READABLE    
        try:
            tar = tarfile.open(tarpath,'r')
        except:
            print_error("on restore_tar")
        else:
            #PREPARE COPY THE LOST AND FOUND
            if len(self.deposit) == 0:
                self.deposit = DEFAULT_DEPOSIT
            
                #FOR EACH HOMEDIR
            if not self.deposit.startswith('/'):
                self.deposit = path.join(self.homedir,self.deposit)
            
            try:   
                os.makedirs(self.deposit,0755)
            except OSError as (errno, strerror):
                debug("Warning: " + self.deposit + " " + strerror,DEBUG_LOW)
            else:
                if self.deposit.startswith(self.homedir):
                    os.chown(self.deposit, self.uid, self.gid)
            
            #APPLY EXCLUDING AND LOST FILTERS
            self.apply_filters(self.homedir)
            
            
            #do not extract ".." or "/" members
            to_extract = []
            for file in tar.getmembers():
                if not file.name.startswith("..") and not file.name.startswith("/"):
                    to_extract.append(file)
                    
            #EXTRACT THE TAR
            tar.extractall(self.homedir,to_extract)
            tar.close()
            
            #Apply user permissions for extracted files
            for file in to_extract:
                name = os.path.join(self.homedir,file.name)
                os.chown(name, self.uid, self.gid)
            
    def exclude_from_tar(self, path):
        path = path[len(self.homedir)+1:]
        
        if len(path) < 1 or len(self.filters) < 1:
            return False
        
        excludeMatch = False
        exclude = False
        action = ACTION_KEEP
        
        for filter in self.filters:
            if re.search(filter[1],path) != None:
                action = filter[0]
                
                if action == ACTION_KEEP or action == ACTION_ERASE:
                    debug("Exclude  path: " + path,DEBUG_HIGH)
                    return True
                elif action == ACTION_RESTORE:
                    debug("Maintain path: " + path,DEBUG_HIGH)
                    return False
                #else action == ACTION_LOST: do not affect
        
        #Default option is KEEP
        debug("Exclude  path: " + path,DEBUG_HIGH)
        return True
    
    def apply_filters_to_file(self,path):
        
        pathAux = path[len(self.homedir)+1:]
        
        if len(pathAux) <= 0: return True
            
        #Do not erase the deposit if it's inside home    
        if self.deposit == path:
            debug('Deposit path: ' + path,DEBUG_MEDIUM)
            return False
            
        for filter in self.filters:
            if re.search(filter[1],path) != None:
                action = filter[0]
                if action == ACTION_KEEP:
                    debug('Keep path: ' + path,DEBUG_MEDIUM)
                    return False
                elif action == ACTION_LOST:
                    debug('Lost path: ' + path,DEBUG_MEDIUM)
                    move(path, self.deposit)
                    return False
                elif action == ACTION_RESTORE or action == ACTION_ERASE:
                    return True
        
        #Default option is KEEP
        debug('Keep path: ' + path,DEBUG_MEDIUM)
        return False
    
    def restore_or_erase(self,path):
        pathAux = path[len(self.homedir)+1:]
         
        #Go on with the home directory
        if len(pathAux) <= 0: return True
         
        #Do nothing with the deposit if it's inside home    
        if self.deposit == path:
            debug('Deposit path: ' + path,DEBUG_MEDIUM)
            return False
        
        for filter in self.filters:
            if re.search(filter[1],path) != None:
                action = filter[0]
                if action == ACTION_KEEP:
                    debug('Keep path: ' + path,DEBUG_MEDIUM)
                    return False
                elif action == ACTION_LOST:
                    debug('Lost path: ' + path,DEBUG_MEDIUM)
                    move(path, self.deposit)
                    return False
                elif action == ACTION_RESTORE or action == ACTION_ERASE:
                    return True
        return True
             
    
    def apply_filters(self, dirname):
        
        if self.restore_or_erase(dirname):
            files = os.listdir(dirname)
            for file in files:
                path = os.path.join (dirname, file)
                if os.path.isdir(path) and not os.path.islink(path):
                    self.apply_filters(path)
                else:
                    debug('Removing file: ' + path,DEBUG_HIGH)
                    if self.restore_or_erase(path):
                        os.unlink(path)
                
            if dirname != self.homedir:
                if len(os.listdir(dirname)) == 0:
                    debug('Removing directory: ' + dirname,DEBUG_HIGH)
                    os.rmdir(dirname)
                    