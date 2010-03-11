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

import os
import tarfile
import re
import shutil
import paramiko, pwd

_ = load_locale()


def move(src,dst):
    "Moves a file without overwritting it, appends a number at the end of the name"
    
    auxPath = 0 
        
    dstComplete = dst
    
    #If the destination already exists, change the filename appending a number
    while os.path.exists(dst):
        dstComplete = dst + "_" + str(auxPath)
        auxPath = auxPath + 1

    shutil.move(src, dstComplete)

class user_frozen:
    "Class to create and restore the user frozen profiles"
    
    #Profile Name
    name = ""
    #Profile Filters
    filters = []
    #If specified, what file use to save/restore
    source = ""
    #If specified, Lost+found directory, if not, use defaults
    deposit = DEFAULT_DEPOSIT
    #Command to execute after restoring
    execute = ""
    
    #User name
    username = ""
    #User Home Directory
    homedir = ""
    #User ID
    uid = 0
    #Group ID
    gid = 0
    
    #If specified, Hostname/IP of the ssh/nfs server where the user will be restored
    hostname = ""
    #If specified, Port of the ssh/nfs server where the user will be restored
    port = "22"
    #If specified, user of the ssh/nfs server who has privileges to execute tfreezer
    server_user = "tfreezer"
    
    def __init__(self, title, deposit, rules, source = "", execute = ""):
        "Initializes a user_frozen with the selected options"
        
        self.name =  title
        self.source = source
        self.execute = execute
        self.deposit = deposit
        for rule in rules:
            self.filters.append([rule.action,rule.filter])
     
    def create_tar(self):
        "Creates a tar for the frozen user"
        
        #If the source is specified, no need to create nothing
        if len(self.source) > 0: return
        
        debug("Creating tar for " + self.username + " with profile " + self.name,DEBUG_LOW)
        
        #Can't access home directory
        if not os.access(self.homedir, os.R_OK):
            print_error("on create_tar. Can't access " + self.homedir)
            raise
        
        #Path of the tar
        dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
        tarpath = os.path.join (dir, self.username + TAR_EXTENSION)
        
        try:
            tar = tarfile.open(tarpath,'w:gz')
        except:
            print_error("on create_tar. Can't create tar file")
            raise
        else:
            #arcname is "" to avoid root folders (./home/username) to be included
            #Exclude from tar is a function that indicates if a file  needs to be excluded from the tar
            tar.add(self.homedir,arcname="",exclude=self.__exclude_from_tar)
            tar.close()
    
    def restore_tar(self):
        "Restores a tar for the frozen user. If the hostname is specified, it \
        restores on an external server"
        
        #If the hostname is specified, restore in the external server
        if len(self.hostname) > 0:
            self.__restore_external_tar()
            return
        
        debug("Restoring tar for " + self.username + " with profile " + self.name,DEBUG_LOW)
        
        #If the source is not specified, use the user tar
        if len(self.source) < 1:
            dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
            tarpath = os.path.join (dir, self.username + TAR_EXTENSION)
        #If the source is specified, use it
        else:
            dir = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
            tarpath = os.path.join (dir, self.source)

        #Open the tar to know if it exists and is readable    
        try:
            tar = tarfile.open(tarpath,'r')
        except:
            print_error("on restore_tar. Can't access file: " + tarpath)
        else:
            #Prepare copy the lost+found
            if len(self.deposit) == 0:
                self.deposit = DEFAULT_DEPOSIT
            
            #If the deposit is in the home directory, replace with the correct home
            self.deposit = str(self.deposit.replace('~',self.homedir,1))
            if self.deposit.endswith("/"):
                self.deposit = self.deposit[:-1]
            
            #Create the deposit directory, if exists, doesn't matter...
            try:
                os.makedirs(self.deposit,0755)
            except OSError , (errno, strerror):
                pass
            else:
                #If the deposit is inside a home directory, change the owner to the user
                if self.deposit.startswith(self.homedir):
                    os.chown(self.deposit, self.uid, self.gid)
            
            #Apply the MAINTAIN and LOST+FOUND filters
            self.__apply_filters(self.homedir)
            
            #This is useful to not extract ".." or "/" members
            to_extract = []
            for file in tar.getmembers():
                if not file.name.startswith("..") and not file.name.startswith("/"):
                    to_extract.append(file)
                    
            #Extract the tar (excluding / and ..)
            tar.extractall(self.homedir,to_extract)
            tar.close()
            
            #Apply owner to the extracted files
            for file in to_extract:
                name = os.path.join(self.homedir,file.name)
                if os.path.exists(name):
                    os.chown(name, self.uid, self.gid)
            
            #Execute the command
            debug ('EXECUTING: ' + self.execute,DEBUG_HIGH)
            result = os.popen(self.execute).read()
            for line in result.splitlines():
                debug ('RESULT: ' + line , DEBUG_HIGH)
                   
    def __restore_external_tar(self):
        "Restores a tar on an external server"
        
        #If the hostname is localhost, I'm the server, so all is locally
        #This kind of restoring is not permitted to avoid loops
        if self.hostname == 'localhost':
            print_error(_("Localhost external restoration not permitted to avoid loops"),WARNING)
            return
        
        debug("Restoring external tar for " + self.username + " with profile " + self.name + " on "+self.hostname,DEBUG_LOW)
        
        #Get the root hoem directory            
        roothome = pwd.getpwuid(0).pw_dir
        try:
            #Read the private key SSH file and the SSH Client
            pkey = paramiko.DSSKey.from_private_key_file(roothome + '/'+ID_DSA_PATH,"")
            ssh = paramiko.SSHClient()
            try:
                #Load the known hosts for the root user
                ssh.load_system_host_keys(roothome + '/'+KNOWN_HOSTS_PATH)
            except:
                pass
            #Connect to the server with the root user. Do not look for keys, use the specified pkey
            ssh.connect(self.hostname,int(self.port),username=self.server_user,pkey=pkey,look_for_keys=False)
        except Exception , e:
            debug("Exception " + str(type(e)) + ": " + str(e), DEBUG_LOW)
            print_error(_("Can't connect to the server, please review your settings"))
            return

        #Create the command line
        if NEEDS_SUDO:
            command = 'sudo tfreezer -a -r ' + self.username + ' -d ' + str(get_debug_level()) + ' 2>&1'
        else:
            command = 'tfreezer -a -r ' + self.username + ' -d ' + str(get_debug_level()) + ' 2>&1'
        debug("Executing command " +command + " on server", DEBUG_LOW)   
        
        #TOERASE 2
        import time
        start = time.time()
        
        #Run the command and print its results in debug mode.
        try:
            stdin,stdout,stderr = ssh.exec_command(command)
            for line in stdout.readlines():
                debug("Server: " + line,DEBUG_MEDIUM)
            stdout.close() 
        except Exception , e:
            debug("Exception " + str(type(e)) + ": " + str(e), DEBUG_LOW)
            print_error(_("Can't execute the command"))
            
        #TOERASE 2
        end = time.time()
        print "Time elapsed restoring = ", end - start, "seconds"
            
        ssh.close()
        return
    
            
    def __exclude_from_tar(self, path):
        "Files to be excluded from the tar"
        "Applies the KEEP, ERASE, and RESTORE filters"
        "Returns True to exlude and False to include"
        
        if get_thread_killed():
            return False
        
        #Cut the path over the home directory
        path = path[len(self.homedir)+1:]
        
        #If the path and the filters are not empty, carry on
        if len(path) < 1 or len(self.filters) < 1:
            return False
        
        #Apply every filter
        for filter in self.filters:
            #if get_thread_killed():
            #    return False

            #If the path matches the filter
            if re.search(filter[1],path) != None:
                #Take the action of the filter
                action = filter[0]
                
                #For KEEP and ERASE action, exclude from the tar
                if action == ACTION_KEEP or action == ACTION_ERASE:
                    debug("Exclude  path: " + path,DEBUG_HIGH)
                    return True
                #For RESTORE action, include in the tar
                elif action == ACTION_RESTORE:
                    debug("Maintain path: " + path,DEBUG_HIGH)
                    return False
                #The LOST action does not affect
        
        #Default option is KEEP, so return True
        debug("Exclude  path: " + path,DEBUG_HIGH)
        return True
    
    
    def __restore_or_erase(self,path):
        "Returns True to carry on or erase and False to maintain"
        
        #Do nothing with the deposit if it's inside a home directory
        if path.startswith(self.deposit):
            debug('Deposit path: ' + path,DEBUG_MEDIUM)
            return False
        
        #Cut the path over the home directory
        path = path[len(self.homedir)+1:]
         
        #Go on with the home directory (not to be erased, but go on)
        if len(path) <= 0: return True
        
        #For every filter
        for filter in self.filters:
            #If the path matches the filter
            if re.search(filter[1],path) != None:
                #Take the action of the filter
                action = filter[0]
                
                #For KEEP action, do not remove it
                if action == ACTION_KEEP:
                    debug('Keep path: ' + path,DEBUG_HIGH)
                    return False
                #For LOST action, move it to deposit
                elif action == ACTION_LOST:
                    debug('Lost path: ' + path,DEBUG_HIGH)
                    move(path, self.deposit)
                    return False
                #For RESTORE and ERASE action, remove
                elif action == ACTION_RESTORE or action == ACTION_ERASE:
                    return True
                
        #Default action is KEEP, so return false
        return False
             
    
    def __apply_filters(self, dirname):
        "Applies filters for restoring a tar"
        
        #It has to be erased? (Directory)
        if self.__restore_or_erase(dirname):
            #YES! Erase it, but first look inside it...
            files = os.listdir(dirname)
            for file in files:
                path = os.path.join (dirname, file)
                #If it's a directory or a link, recursive call
                if os.path.isdir(path) and not os.path.islink(path):
                    self.__apply_filters(path)
                #If it's a file, see if it has to be removed
                else:
                    debug('Removing file: ' + path,DEBUG_HIGH)
                    #It has to be erased? (File)
                    if self.__restore_or_erase(path):
                        os.unlink(path)
            
            #If we're not in the home directory and is an empty directory, erase it
            if dirname != self.homedir:
                if len(os.listdir(dirname)) == 0:
                    debug('Removing directory: ' + dirname,DEBUG_HIGH)
                    os.rmdir(dirname)
                    