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
import pwd


def move(src,dst):
    
    auxPath = 0 
        
    dstComplete = dst
    
    while os.path.exists(dst):
        dstComplete = dst + "_" + str(auxPath)
        auxPath = auxPath + 1

    shutil.move(src, dstComplete)
    return dst

class user_frozen ():
    def __init__(self):
        self.name = ""
        self.filters = []
        self.username = ""
        self.homedir = ""
        self.network = ""
        self.source = ""
        self.deposit = ""
        self.uid = 0
        self.gid = 0
        self.hostname = ""
        
    def create_tar(self):
        debug("Entering profile.create_tar",DEBUG_LOW)
        debug("User " + self.username + ":" + self.name + ":" + self.homedir + ":" + self.source,DEBUG_LOW)
        
        if not os.access(self.homedir, os.R_OK):
            print_error("on create_tar. " + self.homedir + "does not exists")
            raise
        
        #SOURCE  ALREADY SPECIFIED
        if len(self.source) > 0: return
        
        dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
        tarpath = os.path.join (dir, self.username + TAR_EXTENSION)
        try:
            tar = tarfile.open(tarpath,'w:gz')
        except:
            print_error("on create_tar. Can't create tar file")
            raise
        else:
            #arcname is "" to avoid homedir folders to be included 
            tar.add(self.homedir,arcname="",exclude=self.exclude_from_tar)
            tar.close()
    
    def restore_external_tar(self):
        #TODO
        #CONNECT WITH THE SERVER
        #Mirar si el profile == -1(FREEZE_LDAP) funciona... :S
#===============ORIGINAL========================================
#        if [ ! -f $DIRECTORI_PERSONAL/.ssh/.congela_ssh ]; then
#              sudo -u $USER  ssh-keygen -t dsa -P "" -N "" -f $DIRECTORI_PERSONAL/.ssh/id_dsa > /dev/null
#              sudo -u $USER  cp $DIRECTORI_PERSONAL/.ssh/id_dsa.pub $DIRECTORI_PERSONAL/.ssh/authorized_keys
#              sudo -u $USER  ssh-keyscan -p 22 -t rsa $SERVIDOR > $DIRECTORI_PERSONAL/.ssh/known_hosts #2>/dev/null
#              sudo -u $USER  ssh-keyscan -p 22 -t rsa $CLIENT >> $DIRECTORI_PERSONAL/.ssh/known_hosts #2>/dev/null
#              chown $USER:$PROPIETARI_GRUP $DIRECTORI_PERSONAL/.ssh/known_hosts
#           fi
#           sudo -u $USER  ssh $USER@$SERVIDOR 'sh -x /srv/exports/S/restaura/restaura_servidor.sh'
#        fi
#===============================================================================
#BUSCAR IP'S (no cal)
#===============================================================================
#        debug ('EXECUTING: ping -c1 localhost |grep PING |cut -d "(" -f 2 | cut -d ")" -f 1',DEBUG_LOW) 
#        result = os.popen('ping -c1 localhost |grep PING |cut -d "(" -f 2 | cut -d ")" -f 1').read()
#        ipclient = result.splitlines()[0]
#        debug ('RESULT: ' + ipclient , DEBUG_LOW)
#        
#        debug ('EXECUTING: ping -c1 ' + self.hostname + ' |grep PING |cut -d "(" -f 2 | cut -d ")" -f 1',DEBUG_LOW) 
#        result = os.popen('ping -c1 ' + self.hostname + ' |grep PING |cut -d "(" -f 2 | cut -d ")" -f 1').read()
#        ipserver = result.splitlines()[0]
#        debug ('RESULT: ' + ipserver , DEBUG_LOW)
#===============================================================================
        
        roothome = pwd.getpwuid(0).pw_dir
        debug (roothome, DEBUG_LOW)
        
        id_dsa = roothome + '/.ssh/id_dsa'
        if os.access(id_dsa, os.R_OK):
            os.unlink(id_dsa)
        id_dsa_pub = roothome + '/.ssh/id_dsa.pub'
        if os.access(id_dsa_pub, os.R_OK):
            os.unlink(id_dsa_pub)
        
        #Create the new key
        debug ('EXECUTING: ssh-keygen -t dsa -P "" -N "" -f ' + id_dsa,DEBUG_LOW)
        result = os.popen('ssh-keygen -t dsa -P "" -N "" -f ' + id_dsa).read()
        for line in result.splitlines():
            debug ('RESULT: ' + line , DEBUG_LOW)
        
        #Search the user@host in the authorized_keys to be replaced
        file= open(id_dsa_pub, 'r')
        new_key = file.readline()
        file.close()
        string = new_key.split(" ")[2][:-1]
        
        newList = []
        
        authorized_keys = roothome + '/.ssh/authorized_keys'
        if os.access(authorized_keys, os.R_OK):
            file = open(authorized_keys, 'r')
            list = file.readlines()
            file.close()
        
            
            for i,text in enumerate(list):
                match = re.search(string,text)
                if match == None:
                    newList.append(text)
        
        newList.append(new_key)
        file = open(authorized_keys, 'w')
        file.writelines(newList)
        file.close()
        
        #Search server and client rsa in known_hosts to be replaced
        newList = []
        
        known_hosts = roothome + '/.ssh/known_hosts'
        if os.access(known_hosts, os.R_OK):
            file = open(known_hosts, 'r')
            list = file.readlines()
            file.close()
            
            for i,text in enumerate(list):
                match = re.search(self.hostname,text)
                if match == None:
                    match = re.search('localhost',text)
                    if match == None:
                        newList.append(text)
        
        if self.hostname != 'localhost':   
            debug ('EXECUTING: ssh-keyscan -p 22 -t rsa ' + self.hostname,DEBUG_LOW)
            server_rsa = os.popen('ssh-keyscan -p 22 -t rsa ' + self.hostname).read().splitlines()[0]
            newList.append(server_rsa)
        
        debug ('EXECUTING: ssh-keyscan -p 22 -t rsa localhost',DEBUG_LOW)
        client_rsa = os.popen('ssh-keyscan -p 22 -t rsa localhost').read().splitlines()[0]          
        newList.append(client_rsa)
        
        file = open(known_hosts, 'w')
        file.writelines(newList)
        file.close()
        
        debug ("EXECUTING: ssh " + self.hostname + " 'tfreezer -s " + self.username + "'",DEBUG_LOW)
        result = os.popen("ssh " + self.hostname + " 'echo " + self.username + " > /tmp/prova'").read()
        for line in result.splitlines():
            debug ('RESULT: ' + line , DEBUG_LOW)  
        
        return
        
    def restore_tar(self):
        debug("Entering profile.restore_tar",DEBUG_LOW)
        debug("User " + self.username + ":" + self.name + ":" + self.homedir + ":" + self.source,DEBUG_LOW)
        
        if len(self.hostname) > 0:
            self.restore_external_tar()
            return
        
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
            print_error("on restore_tar from user: " + self.username)
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
                    