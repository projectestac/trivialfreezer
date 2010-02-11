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

import threading, sys, gtk

_ = load_locale()

class tar_thread ( threading.Thread ):
    "Subclass of Thread to manage the creating tar thread"
    
    #frozen_user profiles to create tar
    tars = None
    #Parent window to send status messages
    win = None
    #To stop the tars
    stopthread = None
    
    
    def __init__(self,tars,win):
        
        #Create the subclass
        threading.Thread.__init__(self)
        
        self.stopthread = threading.Event()
        
        self.tars = tars
        self.win = win
        set_thread_killed(False)
        
    def run ( self ):
        "The run function creates the tar files of the frozen users"
        
        debug("Creating tars...",DEBUG_MEDIUM)
        
        #Indicates if an error exists
        errors = False
        set_thread_killed(False)
        sys.settrace(self.globaltrace)
        
        #Number of steps to do (to indicate in the progress bar)
        max = float(len(self.tars) * 2)
        
        #Create thread that create tars
        gtk.gdk.threads_enter()
        #For every frozen user
        for i, froze in enumerate(self.tars):
            
            #Sets the status in the progress bar
            text = _("Freezing '%(username)s'") % {'username': froze.username}
            self.win.PBprogress.set_text(text)
            #Current step
            i = (i + 1) * 2
            #Set the progress bar
            self.win.PBprogress.set_fraction((i-1)/max)
            
            #Stop the old thread, if not
            gtk.gdk.threads_leave()
            
            try:
                #Try to create the tar
                froze.create_tar()
            except:
                errors = True
            
            #Run another thread instance to change the GUI
            gtk.gdk.threads_enter()
            
            if get_thread_killed():
                gtk.gdk.threads_leave()
                return
            
            text = _("User '%(username)s' frozen") % {'username': froze.username}
            self.win.PBprogress.set_text(text)
            self.win.PBprogress.set_fraction(i/max)
        
        #Complete!
        self.win.PBprogress.set_fraction(1.0)
        
        #Return the previous state
        self.win.Bstop.set_sensitive(False)
        self.win.table.set_sensitive(True)
        self.win.TBtoolbar.set_sensitive(True)
        self.win.Hbuttons.set_sensitive(True)
        
        if errors:
            self.win.PBprogress.set_text(_("WARNING: There were errors on frozen"))
        else:
            self.win.PBprogress.set_text(_("Frozen successfully done"))
        
        gtk.gdk.threads_leave()
        
        debug("Tars created!",DEBUG_MEDIUM)

    def globaltrace(self, frame, why, arg):
        "Function to trace the state of the thread"
        
        if self.stopthread.isSet():
            debug("Killed tar_thread",DEBUG_MEDIUM)
            raise SystemExit()
        
        if why == 'call':
            return self.globaltrace
        else:
            return None

    def kill(self):
        "Function to kill the thread"
        set_thread_killed(True)
        debug("Killing tar_thread",DEBUG_MEDIUM)
        self.stopthread.set()
