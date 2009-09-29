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
    
    def __init__(self,tars,win):
        threading.Thread.__init__(self)
        self.stopthread = threading.Event()
        
        self.tars = tars
        self.win = win
        
    def run ( self ):
        debug("Entering tar_thread.run",DEBUG_MEDIUM)
        
        errors = False
        
        sys.settrace(self.globaltrace)
        max = float(len(self.tars) * 2)
        
        
        #Create thread that create tars
        gtk.gdk.threads_enter()
        for i, froze in enumerate(self.tars):
            self.win.PBprogress.set_text("Freezing "+froze.username)
            i = (i + 1) * 2
            self.win.PBprogress.set_fraction((i-1)/max)
            
            gtk.gdk.threads_leave()
            
            try:
                froze.create_tar()
            except:
                errors = True
            
            gtk.gdk.threads_enter()
            
            self.win.PBprogress.set_text("User " + froze.username + " frozen")
            self.win.PBprogress.set_fraction(i/max)
            
        self.win.PBprogress.set_fraction(1.0)
        
        if errors:
            self.win.PBprogress.set_text(_("WARNING: There were errors on frozen"))
        else:
            self.win.PBprogress.set_text(_("Frozen successfully done"))
            
        self.win.Bstop.set_sensitive(False)
        self.win.table.set_sensitive(True)
        self.win.TBtoolbar.set_sensitive(True)
        self.win.Hbuttons.set_sensitive(True)
        gtk.gdk.threads_leave()
        
        debug("Exiting tar_thread.run",DEBUG_MEDIUM)

    def globaltrace(self, frame, why, arg):
        if self.stopthread.isSet():
            debug("Killed tar_thread",DEBUG_MEDIUM)
            raise SystemExit()
        if why == 'call':
            return self.globaltrace
        else:
            return None

    def kill(self):
        debug("Killing tar_thread",DEBUG_MEDIUM)
        self.stopthread.set()
