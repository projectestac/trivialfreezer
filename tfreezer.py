#!/usr/bin/env python
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



import pygtk
pygtk.require('2.0')
import gtk

import pwd, grp

import os, sys
from os import path
from datetime import datetime
#import trace
#import time
#import copy
#import dircache
import tarfile
import re
import shutil

import threading

from xml.dom import minidom

import sexy

import ldap

## i18n

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext


################## CONSTANTS ##################

VERSION = "v0.5"

CONFIG_DIRECTORY = "/etc/tfreezer/"
CONFIG_FILE = "config.xtf"
TAR_DIRECTORY = "/var/backups/tfreezer/"
TAR_HOMES = "homes"
TAR_REPOSITORY = "repository"
TAR_EXTENSION = ".tar.gz"
DEFAULT_DEPOSIT = "/lost+found"

minUID = 1001
maxUID = 65534

SMALL_ICONS = ["pixmaps/drop-16.png", "pixmaps/ice-16.png", "pixmaps/drops-16.png"]
NORMAL_ICONS = ["pixmaps/drop-32.png", "pixmaps/ice-32.png", "pixmaps/drops-32.png"]
BIG_ICONS = ["pixmaps/drop-64.png", "pixmaps/ice-64.png", "pixmaps/drops-64.png"]
HUGE_ICONS = ["pixmaps/drop-128.png", "pixmaps/ice-128.png", "pixmaps/drops-128.png"]

FREEZE_NONE = 0
FREEZE_ALL = 1
FREEZE_ADV = 2

TIME_INDEFFERENT = -1
TIME_MANUAL = 0
TIME_SESSION = 1
TIME_SYSTEM = 2

ACTION_RESTORE = 0
ACTION_KEEP = 1
ACTION_ERASE = 2
ACTION_LOST = 3

BLOCKED_PROFILES = 3

TAR_CREATE = 0
TAR_RESTORE = 1

DEBUG_DISABLED = 0
DEBUG_LOW = 1
DEBUG_MEDIUM = 2
DEBUG_HIGH = 3

WARNING = 0
ERROR = 1

debug_level = DEBUG_DISABLED

###############################################

def debug(text, level=DEBUG_LOW):
    #if debug_level == DEBUG_DISABLED:
    #    return

    if level <= debug_level:
        if level == DEBUG_LOW:
            print "Debug L: "+ str(text)
        if level == DEBUG_MEDIUM:
            print "Debug M: "+ str(text)
        if level == DEBUG_HIGH:
            print "Debug H: "+ str(text)

def print_error(text,level=ERROR):
    if level == WARNING:
        print "Warning: "+ str(text)
        return
    
    print "Error  : "+ str(text)
    
    
#Converts an string to boolean
def str2bool(v):
    return v.lower() in ["yes", "true", "t", "1"]

def str2int(v):
    if v != None:
        return int(v)
    else:
        return 0

def check_root():
    if os.geteuid() != 0:
        print_error("You don't have enough privileges to run this program.")
        sys.exit()
        
def move(src,dst):
    
    auxPath = 0 
        
    dstComplete = dst
    
    while os.path.exists(dst):
        dstComplete = dst + "_" + str(auxPath)
        auxPath = auxPath + 1

    shutil.move(src, dstComplete)
    return dst

#COPY A FILE TO A DIRECTORY WITHOUT OVERWRITTING THEM
def copy(src,dst):
    
    auxPath = 0
    fileName = os.path.basename(src)
    (file,extension) = fileName.split(".",1)
                 
    dstComplete = os.path.join (dst, fileName)     
    while os.path.exists(dstComplete):
        fileName = file + "_" + str(auxPath) + "." + extension
        dstComplete = os.path.join (dst, fileName)
        auxPath = auxPath + 1     
        
    shutil.copy(src, dstComplete)
    return fileName

def recursive_delete(dirname):
    if not os.path.exists(dirname):
        return
    files = os.listdir(dirname)
    for file in files:
        path = os.path.join (dirname, file)
        if os.path.isdir(path) and not os.path.islink(path):
            recursive_delete(path)
        else:
            debug("Removing file: " + path,DEBUG_HIGH)
            retval = os.unlink(path)
            
    debug("Removing directory: " + dirname,DEBUG_HIGH)        
    os.rmdir(dirname)
        

class configTab(gtk.Table):
    
    def __init__(self, parent, name):
        #Taula i botons
        gtk.Table.__init__(self)
        self.set_row_spacings(5)
        self.set_col_spacings(5)
        self.set_border_width(5)
        
        
        self.pare = parent
        
        #ListStore of the profiles
        self.LSactions = gtk.ListStore(str,str,int)
        self.LSactions.append([gtk.STOCK_REVERT_TO_SAVED,_("Restore (Frozen)"), ACTION_RESTORE])
        self.LSactions.append([gtk.STOCK_STOP,_("Keep (Unfrozen)"),ACTION_KEEP])
        self.LSactions.append([gtk.STOCK_DELETE,_("Erase"),ACTION_ERASE])
        self.LSactions.append([gtk.STOCK_FIND,_("Move to Lost+Found"),ACTION_LOST])
        
        label = gtk.Label(_("Profile name"))
        self.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        
        self.Ename = gtk.Entry()
        self.Ename.set_text(name)
        self.Ename.connect("key-press-event",parent.tab_name_modified)
        self.Ename.connect("key-release-event",parent.tab_name_modified)
        self.attach(self.Ename, 1, 3, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        separator = gtk.HSeparator()
        self.attach(separator, 0, 3, 1, 6, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        label = gtk.Label("<b>"+_("Restoration source")+"</b>")
        label.set_use_markup(True)
        self.attach(label, 0, 3, 6, 7, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        self.RBhome = gtk.RadioButton(None, _("Use the actual home directory"))
        self.attach(self.RBhome, 0, 3, 7, 8, gtk.EXPAND |gtk.FILL, gtk.FILL)
        
        self.RBfile = gtk.RadioButton(self.RBhome, _("Use this source from the repository"))
        self.RBfile.connect("toggled",self.RBfile_toggled)
        self.attach(self.RBfile, 0, 1, 8, 9, gtk.FILL, gtk.FILL)
        
        self.CBfile = gtk.ComboBox(parent.LSsources)
        self.CBfile.connect("changed",self.CBfile_changed)
        cell = gtk.CellRendererText()
        self.CBfile.pack_start(cell, True)
        self.CBfile.set_attributes(cell, text=0)
        self.CBfile.set_active(0)
        self.attach(self.CBfile, 1, 3, 8, 9, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
        
        separator = gtk.HSeparator()
        self.attach(separator, 0, 3, 10, 11, gtk.EXPAND | gtk.FILL, gtk.FILL)
                        
        #FILTERS
        label = gtk.Label("<b>"+_("Rules")+"</b>")
        label.set_use_markup(True)
        self.attach(label, 0, 3, 11, 12, gtk.EXPAND | gtk.FILL, gtk.FILL)
        #LOAD GROUPS
        self.LSfilter = gtk.ListStore(str,str,str,str,int)
        
        # create the TreeView using liststore
        self.TVfilter = gtk.TreeView(self.LSfilter)
        self.TMfilter = self.TVfilter.get_model()
        
        # Camps de filter
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.Cfiltertitle_edited)
        tv = gtk.TreeViewColumn(_("Title"),cell,text=0)
        self.TVfilter.append_column(tv)
        tv.set_sort_column_id(0)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.Cfilter_edited)
        tv = gtk.TreeViewColumn(_("Filter"),cell,text=1)
        self.TVfilter.append_column(tv)
        tv.set_sort_column_id(1)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        cellpb = gtk.CellRendererPixbuf()
               
        cell = gtk.CellRendererCombo()
        cell.set_property("model",self.LSactions)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        cell.set_property('has-entry',False)
        tv = gtk.TreeViewColumn(_("Action"))
        tv.set_expand(True)
        tv.set_resizable(True)
        
        tv.pack_start(cellpb, False)
        tv.set_attributes(cellpb, stock_id=2)
        
        tv.pack_start(cell, True)
        tv.set_attributes(cell, text=3)
        
        cell.connect('changed', self.Cfilter_changed)
        
        self.TVfilter.append_column(tv)
        tv.set_sort_column_id(3)
        
        self.TVfilter.set_search_column(0)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(self.TVfilter)
        
        self.attach(scroll, 0, 2, 12, 17, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.add_filter)
        self.attach(button, 2, 3, 12, 13, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.remove_filter)
        self.attach(button, 2, 3, 13, 14, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_UP,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.up_filter)
        self.attach(button, 2, 3, 14, 15, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_DOWN,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.down_filter)
        self.attach(button, 2, 3, 15, 16, gtk.FILL, gtk.SHRINK)
        
        self.Ldeposit = gtk.Label(_("Deposit for Lost+Found"))
        self.attach(self.Ldeposit, 0, 1, 17, 18, gtk.FILL, gtk.FILL)
        
        self.Edeposit = sexy.IconEntry()
        #self.Edeposit.connect("key-press-event", self.blocked_writing)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_BUTTON)
        self.Edeposit.set_icon(sexy.ICON_ENTRY_PRIMARY, image)
        self.Edeposit.connect("icon-pressed", self.choose_deposit)
        self.Edeposit.add_clear_button()
        self.attach(self.Edeposit, 1, 3, 17, 18, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        
        label = gtk.Label()
        self.attach(label, 1, 2, 16, 17, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        label = gtk.Label()
        self.attach(label, 2, 3, 16, 17, gtk.FILL, gtk.EXPAND | gtk.FILL)

        self.show_all()
        
        #END of Config Files
            
    def RBnetwork_toggled(self, widget, data=None):
        self.Emachine.set_sensitive(widget.get_active())
    
    def RBfile_toggled(self, widget, data=None):
        self.CBfile.set_sensitive(widget.get_active())
    
    def CBfile_changed(self, widget, data=None):
        if self.CBfile.get_active() == -1:
            self.RBhome.set_active(True)
        
    def Cfilter_changed(self, cell, path, iter):
        state = cell.get_property("model").get_value(iter,2)
        self.TMfilter[path][2] = self.LSactions[state][0]
        self.TMfilter[path][3] = self.LSactions[state][1]
        self.TMfilter[path][4] = self.LSactions[state][2]
        
    def Cfilter_edited(self,cellrenderertext, path, new_text):
        self.LSfilter[path][1] = new_text
        
    def Cfiltertitle_edited(self,cellrenderertext, path, new_text):
        self.LSfilter[path][0] = new_text
        
    def add_filter(self, widget=None, data=_("Eveything")):       
        self.LSfilter.append([data,".",self.LSactions[ACTION_KEEP][0],self.LSactions[ACTION_KEEP][1],ACTION_KEEP])
        
    def remove_filter(self, widget=None):
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            self.LSfilter.remove(iter)
        
    def up_filter(self, widget=None, data=_("New Filter")):
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            path = self.TMfilter.get_path(iter)[0] - 1
            if path < 0:
                print_error("The filter have reached the top of the list",WARNING)
                return
            iterPrev = self.TMfilter.get_iter(self.TMfilter.get_path(iter)[0] - 1)
            self.LSfilter.move_before(iter, iterPrev)
        
    def down_filter(self, widget=None):
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            path = self.TMfilter.get_path(iter)[0] + 1
            if path >= self.TMfilter.iter_n_children(None):
                print_error("The filter have reached the bottom of the list",WARNING)
                return
            iterNext = self.TMfilter.get_iter(path)
            self.LSfilter.move_after(iter, iterNext)
    
    def choose_deposit(self,widget=None,button=None,data=None):
        if button != sexy.ICON_ENTRY_PRIMARY:
            return
        dialog = gtk.FileChooserDialog(_("Choose source file"),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            depositfile = dialog.get_filename()
            
            #If depositfile is inside a home directory, it will be inside each home
            for user in pwd.getpwall():
                uid = user.pw_uid
                if uid >= minUID and uid < maxUID:
                    if depositfile.startswith(user.pw_dir):
                        depositfile = depositfile[len(user.pw_dir)+1:]
                        break
            self.Edeposit.set_text(depositfile)
            
        dialog.destroy()
        return
    
    def get_source(self):
        path = self.CBfile.get_active()
        if path >= 0:
            return self.pare.LSsources[path][1]
        
        return ""
    
    def set_source(self, source):
        if source == "":
            self.CBfile.set_active(-1)
            return
        
        for path, sourceAux in enumerate(self.pare.LSsources):
            if sourceAux[1] == source:
                self.CBfile.set_active(path)
                return
            
        self.CBfile.set_active(-1)
        raise
    
    #TODO use it in another place and erase
    #self.Emachine = gtk.Entry()
    #self.Emachine.set_sensitive(False)
    #self.Emachine.set_text('0.0.0.0')
    #self.Emachine.connect("key-press-event", self.Emachine_key_pressed)
    #self.attach(self.Emachine, 1, 3, 4, 5, gtk.EXPAND | gtk.FILL, gtk.FILL)
    def Emachine_key_pressed(self,widget,event):
        #up, down, left, right, backspace, delete
        permited_key_vals = [65362, 65364, 65361, 65363, 65288, 65535]
        #Tab keys
        tabs = [65289, 65056]

        if event.string.isdigit():
            
            text = widget.get_text()
            selection = widget.get_selection_bounds()
            
            #Replace selection
            if len(selection) == 2:
                pos = selection[0]
                end = selection[1]
                text = text[0:pos] + event.string + text[end:]
            else:
                pos = widget.get_position()
                end = text.find('.',pos)
                
                #DOT NOT FOUND (FINAL NUMBER)
                if end == -1:
                    if text[pos:].isdigit():
                        text = text[0:pos] + event.string
                    else:
                        text = text[0:pos] + event.string + text[pos:]
                else:
                    if not text[pos:end].isdigit():
                        end = pos
                    text = text[0:pos] + event.string + text[end:]
                    
            pos = pos + 1
            
            #SPLIT IN FOUR NUMBERS
            numbers = text.split('.',4)
            for i in range(4 - len(numbers)):
                numbers.append('0')
                
            off = -1
            for i, number in enumerate(numbers):
                if not number.isdigit():
                    if off >= 0:
                        num = off
                        pos = pos + 1
                        off = -1
                    else:
                        num = 0
                else:
                    num = int(number)
                    if off >= 0:
                        if num > 0:
                            num = int(str(off) + number)
                        else:
                            num = off
                        pos = pos + 1
                        off = -1
                        number = str(num)
                    if num > 999:
                        num = int(number[0:3])
                        if len(text) > pos and text[pos] == '.':
                            off = int(number[3])
                    if num > 255:
                        num = 255
                numbers[i] = str(num)
            
            text = ".".join(numbers)
            widget.set_text(text)
            widget.set_position(pos)

        
        elif event.keyval in permited_key_vals:
            return False
        #Tab or dot
        elif event.keyval in tabs or event.string == '.':
            
            #Set cursor position
            pos = widget.get_position()
            start = widget.get_text().find('.',pos) + 1
            if start > -1:
                end = widget.get_text().find('.',start)
                widget.select_region(start, end)
        
        return True
    

class configWindow(gtk.Window):
    
    def __init__(self,mainWin):
        gtk.Window.__init__(self)
        self.connect("delete_event", self.close)
        self.connect("destroy_event", lambda *w: self.close)
        self.set_title("Trivial Freezer"+_(" - Profiles"))
        self.set_icon_from_file(NORMAL_ICONS[FREEZE_ADV])
        
        self.mainWin = mainWin
        self.mainBox = gtk.VBox()
        self.add(self.mainBox)
        
        #ToolBar
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
        
        item = gtk.ToolButton(gtk.STOCK_ADD)
        item.set_label(_('Add profile'))
        item.set_tooltip_text(_('Adds a new Frozen Profile'))
        item.set_is_important(True)
        item.connect("clicked",self.add_tab)
        toolbar.insert(item,0)
        
        item = gtk.ToolButton(gtk.STOCK_REMOVE)
        item.set_label(_('Remove profile'))
        item.set_tooltip_text(_('Removes the selected Frozen Profile'))
        item.set_is_important(True)
        item.connect("clicked",self.remove_tab)
        toolbar.insert(item,1)
        
        item = gtk.SeparatorToolItem()
        toolbar.insert(item,2)
        
        item = gtk.ToggleToolButton(gtk.STOCK_EDIT)
        item.set_label(_('Manage sources'))
        item.set_tooltip_text(_('Add/Remove sources from repository'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_sources)
        toolbar.insert(item,3)
        
        item = gtk.ToolItem()
        item.set_expand(True)
        toolbar.insert(item,4)
        
        item = gtk.ToolButton(gtk.STOCK_CLOSE)
        item.set_is_important(True)
        item.connect("clicked",self.close)
        toolbar.insert(item,5)
        
        self.mainBox.pack_start(toolbar, False)
        
        panes = gtk.HPaned()
        self.mainBox.pack_start(panes, True)
        
        #Config tabs
        self.tabs = gtk.Notebook()
        self.tabs.set_scrollable(True)
        panes.pack1(self.tabs, True,False)
        
        self.init_repository()
        panes.pack2(self.sources, True,False)
        
        self.mainBox.show()
        panes.show()
        self.tabs.show_all()
        toolbar.show_all()
        
    def init_repository(self):
        self.sources = gtk.VBox()
        self.sources.set_spacing(5)
        self.sources.set_border_width(5)

        label = gtk.Label("<b>"+_("Sources repository")+"</b>")
        label.set_use_markup(True)
        self.sources.pack_start(label,False)
        
        self.LSsources = gtk.ListStore(str,str)
        
        # create the TreeView using liststore
        self.TVsources = gtk.TreeView(self.LSsources)
        self.TMsources = self.TVsources.get_model()
        
        # Camps de filter
        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn(_("Name"),cell,text=0)
        cell.set_property('editable', True)
        cell.connect('edited', self.Cname_edited)
        self.TVsources.append_column(tv)
        tv.set_sort_column_id(0)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        # Camps de filter
        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn(_("Source"),cell,text=1)
        self.TVsources.append_column(tv)
        tv.set_sort_column_id(0)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        tv.set_sort_column_id(0)
        
        self.TVsources.set_search_column(0)
        
        self.sources.pack_start(self.TVsources)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIRECTORY,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button(_("Add from a directory"))
        button.set_image(image)
        button.connect("clicked", self.add_from_directory)
        self.sources.pack_start(button,False)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_HARDDISK,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button(_("Add from a tar file"))
        button.set_image(image)
        button.connect("clicked", self.add_from_tar)
        self.sources.pack_start(button,False)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button(_("Remove a source"))
        button.set_image(image)
        button.connect("clicked", self.remove_source)
        self.sources.pack_start(button,False)
        
    def close(self, widget=None, data=None):
        self.hide()
        return True
    
    def add_tab(self, widget=None, data=_("New Profile")):
        
        newTab = configTab(self,data)
        label = gtk.Label(data)
        self.tabs.append_page(newTab, label)
        
        self.mainWin.LS_add(data)
        
        return newTab
    
    def remove_tab(self, widget=None):
        i = self.tabs.get_current_page()
        if i >= BLOCKED_PROFILES:
            self.tabs.remove_page(i)
            self.mainWin.LS_remove(i)
            
    def tab_name_modified(self, widget, data=None):
        name = widget.get_text()
        tab = widget.get_parent()
        self.tabs.set_tab_label_text(tab, name)
        self.mainWin.set_all_states_label(self.tabs.page_num(tab), name)

    def show_hide_sources(self,widget):
        if widget.get_active():
            self.sources.show_all()
        else:
            self.sources.hide_all()
            
    def Cname_edited(self,cellrenderertext, path, new_text):
        self.LSsources[path][0] = new_text
    
    def add_from_directory(self, widget=None):
        dialog = gtk.FileChooserDialog(_("Choose source file"),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            sourcefile = dialog.get_filename()
            
            dir = sourcefile.rsplit("/",1)[1]
            
            fileName = dir + TAR_EXTENSION
            repo = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
            dst = os.path.join (repo, fileName)
            auxPath = 0
            
            try:   
                os.makedirs(repo,0755)
            except OSError as (errno, strerror):
                print_error(repo + " " + strerror,WARNING)
                
            while os.path.exists(dst):
                fileName = dir + "_" + str(auxPath) + TAR_EXTENSION
                dst = os.path.join (repo, fileName)
                auxPath = auxPath + 1   
                
            try:
                tar = tarfile.open(dst,'w:gz')
            except:
                print_error("on add_from_directory")
                warning = gtk.Dialog(_("Unable to create tar file"),buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))
                label = gtk.Label(_("The freezer is unable to create the tar file"))
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_padding(20,20)
                label.show()
            else:
                tar.add(sourcefile,arcname="")
                tar.close()
                name = fileName.split(".",1)[0]
                self.LSsources.append([name,fileName])
            
        dialog.destroy()
        return
    
    def add_from_tar(self, widget=None):
        
        dialog = gtk.FileChooserDialog(_("Choose source file"),buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name(_("Tar files"))
        filter.add_mime_type("application/x-compressed-tar")
        filter.add_mime_type("application/x-tar")
        filter.add_mime_type("application/x-bzip-compressed-tar")
        dialog.add_filter(filter)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            sourcefile = dialog.get_filename()
            repo = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
            
            try:   
                os.makedirs(repo,0755)
            except OSError as (errno, strerror):
                print_error(repo + " " + strerror,WARNING)
                
            try:
                tar = tarfile.open(sourcefile,'r')
                tar.close()
                dst = copy(sourcefile,repo)
            except:
                warning = gtk.Dialog(_("Unreadable tar file"),buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK))
                label = gtk.Label(_("The selected file is unreadable or malformed"))
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_padding(20,20)
                label.show()
                
                warning.vbox.pack_start(label,True,True,0)
                
                res = warning.run()
                warning.destroy()
                
            else:
                name = dst.split(".",1)[0]
                self.LSsources.append([name,dst])
            
        dialog.destroy()
        return
    
    def remove_source(self, widget=None):
        (view, iter) = self.TVsources.get_selection().get_selected()
        if iter != None:
            path = self.TMsources.get_path(iter)[0]
            repo = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
            file = os.path.join (repo, self.LSsources[path][1])
            #mark to erases
            self.mainWin.sources_to_erase.append(file)
            
            self.LSsources.remove(iter)
            
    def load_non_saved_sources(self):
        dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
        
        try:   
            os.makedirs(dirname,0755)
        except OSError as (errno, strerror):
            print_error(dirname + " " + strerror,WARNING)
        
        files = os.listdir(dirname)
        for file in files:
            path = os.path.join (dirname, file)
            if not os.path.isdir(path) or os.path.islink(path):
                trobat = False
                
                for nameAux, fileAux in self.LSsources:
                    if file == fileAux:
                        trobat = True
                        break
                
                if not trobat:
                    try:
                        tar = tarfile.open(path,'r')
                        tar.close()
                    except:
                        print_error(_("Unreadable tar file"), WARNING)
                    else:
                        name = file.split(".",1)[0]
                        self.LSsources.append([name,file])
        
class tfreezer:

    def __init__(self):
        
        self.window = gtk.Window()
        self.window.set_title("Trivial Freezer "+VERSION)
        self.window.connect("delete_event", self.close)
        self.window.connect("destroy_event", lambda *w: self.close)
        self.window.set_icon_from_file(NORMAL_ICONS[FREEZE_ALL])
        self.window.set_size_request(-1,-1)
        self.window.set_property("resizable",False)
        
        self.mainBox = gtk.VBox()
        self.mainBox.show()

        #ListStore of the profiles
        self.LSfreeze_settings = gtk.ListStore(gtk.gdk.Pixbuf,str,int)
        
        #Init config Window
        self.configW = configWindow(self)
        
        #Init and add ToolBar
        self.init_toolbar()
        
        #Init and add user Form
        self.init_form()
        
        progress = gtk.HBox()
        progress.set_border_width(5)
        progress.show()
        
        self.PBprogress = gtk.ProgressBar()
        self.PBprogress.show()
        progress.pack_start(self.PBprogress, True)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_STOP,gtk.ICON_SIZE_BUTTON)
        image.show()
        self.Bstop = gtk.Button()
        self.Bstop.add(image)
        self.Bstop.connect("clicked", self.stop_tars)
        self.Bstop.show()
        self.Bstop.set_sensitive(False)
        progress.pack_start(self.Bstop, False)

        self.mainBox.pack_start(progress,False)
        
        #Apply and restore buttons
        self.Hbuttons = gtk.HBox()
        self.Hbuttons.set_border_width(5)
        self.Hbuttons.show()
                
        self.Bapply = gtk.Button(_("Apply"), gtk.STOCK_APPLY)
        self.Bapply.connect("clicked", self.save_file)
        self.Hbuttons.pack_start(self.Bapply, True)
        
        self.Brestore = gtk.Button(_("Restore"), gtk.STOCK_REVERT_TO_SAVED)
        self.Brestore.connect("clicked", self.load_file)
        self.Hbuttons.pack_start(self.Brestore, True)
        
        but = gtk.Button(_("Quit"),gtk.STOCK_QUIT)
        but.connect("clicked",self.close,0)
        but.show()
        self.Hbuttons.pack_start(but, True)
        
        self.mainBox.pack_start(self.Hbuttons, False)
        
        self.sources_to_erase = []
        
        self.load_file()
        
        self.window.add(self.mainBox)
        
        gtk.gdk.threads_init()
    
    def main(self):
        self.window.show()
        gtk.main()
    
    def close(self, widget=None, data=None):
        
        try:
            self.TTtar.kill()
        except:
            debug("No threads to kill",DEBUG_MEDIUM)
            
        gtk.main_quit()
        return False

    def show_settings(self, widget=None, data=None):
        self.configW.show()

    def load_file(self, widget=None):
        
        self.set_enabled_to_load(False)
        
        j = self.configW.tabs.get_n_pages()
        for i in range(j):
            self.configW.tabs.remove_page(0)
            self.LSfreeze_settings.remove(self.LSfreeze_settings.get_iter(0))
        
        self.configW.LSsources.clear()
        
        try:  
            xdoc = minidom.parse(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE))
        except:
            print_error("Corrupted config file",WARNING)
        
        #Load the saved sources
        try:
            xSources = xdoc.getElementsByTagName("sources")[0].getElementsByTagName("source")
        except:
            print_error("Corrupted sources tag",WARNING)
        else:
            sources = self.configW.LSsources
            for xSource in xSources:
                try:
                    name = xSource.getAttribute("title")
                    dst = xSource.getAttribute("file")
                    dirname = os.path.join (TAR_DIRECTORY, TAR_REPOSITORY)
                    filename = os.path.join (dirname, dst)
                    tar = tarfile.open(filename,'r')
                    tar.close()
                except:
                    print_error("Corrupted source file tag",WARNING)
                else:
                    sources.append([name,dst])
        #Load the non-saved sources
        self.configW.load_non_saved_sources()
        
        try:
            xProfiles = xdoc.getElementsByTagName("profile")
        except:
            print_error("Corrupted profile tag",WARNING)
            newTab = self.configW.add_tab(data=_("Total Unfrozen"))
            newTab.set_sensitive(False)
            newTab.LSfilter.append([_("Everything"),
                        ".",
                        newTab.LSactions[ACTION_KEEP][0],
                        newTab.LSactions[ACTION_KEEP][1],
                        ACTION_KEEP])
            
            newTab = self.configW.add_tab(data=_("Total Frozen"))
            newTab.set_sensitive(False)
            newTab.LSfilter.append([_("Everything"),
                        ".",
                        newTab.LSactions[ACTION_RESTORE][0],
                        newTab.LSactions[ACTION_RESTORE][1],
                        ACTION_RESTORE])
            
            newTab = self.configW.add_tab(data=_("Configuration Frozen"))
            newTab.set_sensitive(False)
            newTab.LSfilter.append([_("Configuration"),
                        "^\.",
                        newTab.LSactions[ACTION_RESTORE][0],
                        newTab.LSactions[ACTION_RESTORE][1],
                        ACTION_RESTORE])
            newTab.LSfilter.append([_("Everything"),
                        ".",
                        newTab.LSactions[ACTION_KEEP][0],
                        newTab.LSactions[ACTION_KEEP][1],
                        ACTION_KEEP])
            
        else:
            for i, xProfile in enumerate(xProfiles):
                try:
                    newTab = self.configW.add_tab(data=xProfile.getAttribute("name"))
                except:
                    print_error("Corrupted name attribute on profile tag",WARNING)
                    if i == FREEZE_NONE:
                        newTab = self.configW.add_tab(data=_("Total Unfrozen"))
                        newTab.set_sensitive(False)
                    elif i == FREEZE_ALL:
                        newTab = self.configW.add_tab(data=_("Total Frozen"))
                        newTab.set_sensitive(False)
                    elif i  == FREEZE_ADV:
                        newTab = self.configW.add_tab(data=_("Configuration Frozen"))
                        newTab.set_sensitive(False)
                
                if i < BLOCKED_PROFILES:
                    newTab.set_sensitive(False)
                                   
                try:
                    active = str2bool(xProfile.getElementsByTagName("source")[0].getAttribute("active"))
                    value = xProfile.getElementsByTagName("source")[0].getAttribute("value")
                    newTab.set_source(value)
                except:
                    active = False
                    print_error("Corrupted source tag",WARNING)
                    newTab.CBfile.set_active(-1)
                    
                newTab.RBhome.set_active(not active)
                newTab.RBfile.set_active(active)
                newTab.CBfile.set_sensitive(active)
                
                try:
                    value = xProfile.getElementsByTagName("deposit")[0].getAttribute("value")
                except:
                    value = ""
                    print_error("Corrupted deposit tag",WARNING)
                newTab.Edeposit.set_text(value)
                
                    
                try:   
                    for xexclude in xProfile.getElementsByTagName("excludes")[0].getElementsByTagName("exclude"):
                    
                        title = xexclude.getAttribute("title")
                        pattern = xexclude.getAttribute("pattern")
                        value = str2int(xexclude.getAttribute("value"))
                        
                        newTab.LSfilter.append([title,
                                                pattern,
                                                newTab.LSactions[value][0],
                                                newTab.LSactions[value][1],
                                                value])
                except:
                    print_error("Corrupted excludes tag",WARNING)
                    if i == FREEZE_NONE:
                        newTab.LSfilter.append([_("Everything"),
                                                ".",
                                                newTab.LSactions[ACTION_KEEP][0],
                                                newTab.LSactions[ACTION_KEEP][1],
                                                ACTION_KEEP])
                    elif i == FREEZE_ALL:
                        newTab.LSfilter.append([_("Everything"),
                                                ".",
                                                newTab.LSactions[ACTION_RESTORE][0],
                                                newTab.LSactions[ACTION_RESTORE][1],
                                                ACTION_RESTORE])
                    elif i  == FREEZE_ADV:
                        newTab.LSfilter.append([_("Configuration"),
                                                "^\.",
                                                newTab.LSactions[ACTION_RESTORE][0],
                                                newTab.LSactions[ACTION_RESTORE][1],
                                                ACTION_RESTORE])
                        newTab.LSfilter.append([_("Everything"),
                                                ".",
                                                newTab.LSactions[ACTION_KEEP][0],
                                                newTab.LSactions[ACTION_KEEP][1],
                                                ACTION_KEEP])
        
        try:
            xFreeze = xdoc.getElementsByTagName("freeze")[0]
        except:
            print_error("Corrupted freeze tag",WARNING) 

        try:
            time = str2int(xFreeze.getAttribute("time"))
        except:
            time = TIME_MANUAL
            print_error("Corrupted time attribute on freeze tag",WARNING)
        self.CBtime.set_active(time)
        
        try:
            activeAll = str2bool(xFreeze.getElementsByTagName("all")[0].getAttribute("active"))
            valueAll = str2int(xFreeze.getElementsByTagName("all")[0].getAttribute("value"))
        except:
            activeAll = True
            valueAll = FREEZE_NONE
            print_error("Corrupted all tag",WARNING)
            
        self.RBall.set_active(activeAll)
        self.CBall.set_active(valueAll)
            
        #ACTIVATE THE TOOLBAR BUTTON
        if(activeAll):
            if (valueAll == FREEZE_NONE):
                self.RTBnone.set_active(True)
                self.set_freeze_all(data = FREEZE_NONE, save = False)
            elif (valueAll == FREEZE_ALL and time == TIME_SESSION):
                self.RTBall.set_active(True)
                self.set_freeze_all(data = FREEZE_ALL, save = False)
            else:
                self.RTBadvanced.set_active(True)
                self.set_freeze_all(data = FREEZE_ADV, save = False)
        else:
            self.RTBadvanced.set_active(True)
            self.set_freeze_all(data = FREEZE_ADV, save = False)
        
        try:
            self.RBusers.set_active(str2bool(xFreeze.getElementsByTagName("users")[0].getAttribute("active")))
            for xUser in xdoc.getElementsByTagName("users")[0].getElementsByTagName("user"):
                for path, row in enumerate(self.LSusers):
                    uid = xUser.getAttribute("uid")
                    if row[1] == uid:
                        self.set_state(self.TMusers, path, None, int(xUser.getAttribute("value")))
        except:
            print_error("Corrupted users tag",WARNING)
            
        try:
            self.RBgroups.set_active(str2bool(xFreeze.getElementsByTagName("groups")[0].getAttribute("active")))           
            for xGroup in xdoc.getElementsByTagName("groups")[0].getElementsByTagName("group"):
                for path, row in enumerate(self.LSgroups):
                    gid = xGroup.getAttribute("gid")
                    if row[1] == gid:
                        self.set_state(self.TMgroups, path, None, int(xGroup.getAttribute("value")))
        except:
            print_error("Corrupted groups tag",WARNING)

        self.CBgroups.set_active(0)
        self.CBusers.set_active(0)
        
        del self.sources_to_erase[:]
        
        self.set_enabled_to_load(True)
    
    def save_file(self, widget=None, data=None):
        debug("Entering tfreezer.save_file",DEBUG_LOW)
        
        #DESAR EN XML
        #Create the minidom document
        xdoc = minidom.Document()
        
        xtf = xdoc.createElement("tfreezer")
        xtf.setAttribute("date", str(datetime.now()))
        xdoc.appendChild(xtf)
        
        xFreeze = xdoc.createElement("freeze")
        xFreeze.setAttribute("time", str(self.CBtime.get_active()))
        
        xall = xdoc.createElement("all")
        xall.setAttribute("active", str(self.RBall.get_active()))  
        xall.setAttribute("value", str(self.CBall.get_active()))
        xFreeze.appendChild(xall)
        
        xusers = xdoc.createElement("users")
        xusers.setAttribute("active", str(self.RBusers.get_active()))
        for row in self.LSusers:
            xuser = xdoc.createElement("user")
            xuser.setAttribute("uid", str(row[1]))
            xuser.setAttribute("value", str(row[4])) 
            xusers.appendChild(xuser)
        xFreeze.appendChild(xusers)
        
        xgroups = xdoc.createElement("groups")
        xgroups.setAttribute("active", str(self.RBgroups.get_active()))
        for row in self.LSgroups:
            xgroup = xdoc.createElement("group")
            xgroup.setAttribute("gid", str(row[1]))
            xgroup.setAttribute("value", str(row[4])) 
            xgroups.appendChild(xgroup) 
        xFreeze.appendChild(xgroups)
        
        xtf.appendChild(xFreeze)
        
        xProfiles = xdoc.createElement("profiles")
        numProfiles = self.configW.tabs.get_n_pages()
        xProfiles.setAttribute("numProfiles", str(numProfiles))
        xtf.appendChild(xProfiles) 
        
        for i in range(numProfiles):
            tab = self.configW.tabs.get_nth_page(i)
            xProfile = xdoc.createElement("profile")
            xProfile.setAttribute("profileNum", str(i))
            xProfile.setAttribute("name", tab.Ename.get_text())
                        
            xsource = xdoc.createElement("source")
            xsource.setAttribute("active", str(tab.RBfile.get_active()))
            xsource.setAttribute("value", tab.get_source())
            xProfile.appendChild(xsource)
            
            xdeposit = xdoc.createElement("deposit")
            xdeposit.setAttribute("value", tab.Edeposit.get_text())
            xProfile.appendChild(xdeposit)
            
            xexclude = xdoc.createElement("excludes")
              
            for row in tab.LSfilter:
                xchild = xdoc.createElement("exclude")
                xchild.setAttribute("title", str(row[0]))
                xchild.setAttribute("pattern", str(row[1]))
                xchild.setAttribute("value", str(row[4]))
                xexclude.appendChild(xchild)
            
            xProfile.appendChild(xexclude)
            
            
            xProfiles.appendChild(xProfile)
        
        xSource = xdoc.createElement("sources")
        for row in self.configW.LSsources:
            xchild = xdoc.createElement("source")
            xchild.setAttribute("title", str(row[0]))
            xchild.setAttribute("file", str(row[1]))
            xSource.appendChild(xchild)
        xtf.appendChild(xSource)
        
        for path in self.sources_to_erase:
            os.unlink(path)
        del self.sources_to_erase[:]

         
        try:   
            os.makedirs(CONFIG_DIRECTORY,0755)
        except OSError as (errno, strerror):
            print_error(CONFIG_DIRECTORY + " " + strerror,WARNING)
            
        try:
            fitxer = open(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE), "w")
            fitxer.write(xdoc.toxml())
            fitxer.close()
        except:
            print_error("Can't save the configuration file")
            self.PBprogress.set_text(_('WARNING: Errors in the fridge'))
        else:
            self.make_tars()        
        
    
    def make_tars(self):
        debug("Entering tfreezer.make_tars",DEBUG_LOW)
        
        tars = tar_list().get_tar_list()
        
        dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
        recursive_delete(dir)
        
        try:   
            os.makedirs(dir,0755)
        except OSError as (errno, strerror):
            print_error(dir + " " + strerror,WARNING)
        
        #TOERASE 2
        for froze in tars:
            debug(froze.username,DEBUG_LOW)
            
        self.PBprogress.set_fraction(0.0)
        self.PBprogress.set_text(_("Starting"))
        
        self.Bstop.set_sensitive(True)
        self.table.set_sensitive(False)
        self.TBtoolbar.set_sensitive(False)
        self.Hbuttons.set_sensitive(False)

        self.TTtar = tar_thread(tars,self)
        self.TTtar.start()
        
        return
    
    def stop_tars(self, widget=None):
        try:
            self.TTtar.kill()
        except:
            debug("No threads to kill",DEBUG_MEDIUM)
            
        self.Bstop.set_sensitive(False)
        self.table.set_sensitive(True)
        self.TBtoolbar.set_sensitive(True)
        self.Hbuttons.set_sensitive(True)
        self.PBprogress.set_text(_("WARNING: Stopped by the user"))
        
    def init_form(self):
        
        self.table = gtk.Table()
        self.table.set_row_spacings(5)
        self.table.set_col_spacings(5)
        self.table.set_border_width(5)
        
        label = gtk.Label(_("Time of restoration"))
        self.table.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        
        self.CBtime = gtk.combo_box_new_text()
        self.CBtime.append_text(_("Manual"))
        self.CBtime.append_text(_("At Session startup (GDM only)"))
        self.CBtime.append_text(_("At System startup"))

        self.CBtime.set_active(1)
        self.table.attach(self.CBtime, 1, 3, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)     
        
        separator = gtk.HSeparator()
        self.table.attach(separator, 0, 3, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        self.RBall = gtk.RadioButton(None, _("Freeze system"))
        self.RBall.connect("toggled",self.RBall_toggled)
        self.table.attach(self.RBall, 0, 1, 2, 3, gtk.FILL, gtk.SHRINK)
        
        self.CBall = gtk.ComboBox(self.LSfreeze_settings)
        cellpb = gtk.CellRendererPixbuf()
        self.CBall.pack_start(cellpb, False)
        self.CBall.set_attributes(cellpb, pixbuf=0)
        cell = gtk.CellRendererText()
        self.CBall.pack_start(cell, True)
        self.CBall.set_attributes(cell, text=1)
        self.CBall.set_active(0)
        self.table.attach(self.CBall, 1, 3, 2, 3, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
        
        self.RBusers = gtk.RadioButton(self.RBall, _("Freeze by user"))
        self.RBusers.connect("toggled",self.RBusers_toggled)
        self.table.attach(self.RBusers, 0, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
        
        icon = gtk.Image()
        icon.set_from_file(SMALL_ICONS[0])
        
        #LOAD USERS
        self.LSusers = gtk.ListStore(str,str,gtk.gdk.Pixbuf,str,int,bool)
        for user in pwd.getpwall():
            uid = user.pw_uid
            if uid >= minUID and uid < maxUID:
                self.LSusers.append([user.pw_name,user.pw_uid,icon.get_pixbuf(),_("None"),FREEZE_NONE,False])
                
        #TODO: ldap
        try:
            con = ldap.initialize("ldap://localhost")
            base_dn = 'ou=people,dc=iescopernic,dc=com'
            filter = '(objectclass=person)'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
         
            result = con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for person in result:
                usern = person[1]['uid'][0]
                gid = person[1]['gidNumber'][0]
                home = person[1]['homeDirectory'][0]
                uid = person[1]['uidNumber'][0]
                #if uid >= minUID and uid < maxUID:
                self.LSusers.append([usern,uid,icon.get_pixbuf(),_("None"),FREEZE_NONE,True])
                    
        except ldap.LDAPError, e:
            print e
            exit
            
        #DIRECTORI_PERSONAL=$(ldapsearch -x uid=$USER homeDirectory |grep homeDirectory: |cut -d ":" -f 2 | sed 's/^ //g')
        # Create the TreeView using liststore
        self.TVusers = gtk.TreeView(self.LSusers)
        self.TVusers.set_sensitive(False)
        self.TMusers = self.TVusers.get_model()
        self.TSusers = self.TVusers.get_selection()
        self.TSusers.set_mode(gtk.SELECTION_MULTIPLE)

        # Camps d'usuari
        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn(_("User"),cell,text=0)
        self.TVusers.append_column(tv)
        tv.set_sort_column_id(0)
        
        cellpb = gtk.CellRendererPixbuf()
               
        cell = gtk.CellRendererCombo()
        cell.set_property("model",self.LSfreeze_settings)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        cell.set_property('has-entry',False)
        tv = gtk.TreeViewColumn(_("State"))
        
        tv.pack_start(cellpb, False)
        tv.set_attributes(cellpb, pixbuf=2)
        
        tv.pack_start(cell, True)
        tv.set_attributes(cell, text=3)
        
        cell.connect('changed', self.Cuser_changed)
        
        self.TVusers.append_column(tv)
        tv.set_sort_column_id(1)
        
        cell = gtk.CellRendererToggle()
        tv = gtk.TreeViewColumn(_("LDAP"),cell,active=5)
        self.TVusers.append_column(tv)
        
        # make treeview searchable
        self.TVusers.set_search_column(0)
        self.TVusers.show()
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(self.TVusers)
        
        self.table.attach(scroll, 0, 3, 4, 6)
        
        self.CBusers = gtk.ComboBox(self.LSfreeze_settings)
        cellpb = gtk.CellRendererPixbuf()
        self.CBusers.pack_start(cellpb, False)
        self.CBusers.set_attributes(cellpb, pixbuf=0)
        cell = gtk.CellRendererText()
        self.CBusers.pack_start(cell, True)
        self.CBusers.set_attributes(cell, text=1)
        self.CBusers.set_active(0)
        self.CBusers.set_sensitive(False)
        self.table.attach(self.CBusers, 0, 1, 6, 7, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
           
        self.Ball_users = gtk.Button(_("Apply to all"))
        self.Ball_users.set_sensitive(False)
        self.Ball_users.connect("clicked", self.Ball_users_clicked)
        self.table.attach(self.Ball_users, 1, 2, 6, 7, gtk.FILL, gtk.SHRINK)
        
        self.Bsel_users = gtk.Button(_("Apply to selected"))
        self.Bsel_users.set_sensitive(False)
        self.Bsel_users.connect("clicked", self.Bsel_users_clicked)
        self.table.attach(self.Bsel_users, 2, 3, 6, 7, gtk.FILL, gtk.SHRINK)

        
        #GROUPS
        self.RBgroups = gtk.RadioButton(self.RBall, _("Freeze by group"))
        self.RBgroups.connect("toggled",self.RBgroup_toggled)
        self.table.attach(self.RBgroups, 0, 3, 7, 8, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
       
        #LOAD GROUPS
        self.LSgroups = gtk.ListStore(str,str,gtk.gdk.Pixbuf,str,int,bool)
        for group in grp.getgrall():
            gid = group.gr_gid
            if gid >= minUID and gid < maxUID:
                self.LSgroups.append([group.gr_name,group.gr_gid,icon.get_pixbuf(),_("None"),FREEZE_NONE,False])

                        
        #TODO: ldap
        try:
            con = ldap.initialize("ldap://localhost")
            base_dn = 'ou=groups,dc=iescopernic,dc=com'
            filter = '(objectclass=posixGroup)'
            attrs = ['cn','gidNumber']
         
            result = con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            print len(result)
            for person in result:
                groupn = person[1]['cn'][0]
                gid = person[1]['gidNumber'][0]
                #if gid >= minUID and gid < maxUID:
                self.LSgroups.append([groupn,gid,icon.get_pixbuf(),_("None"),FREEZE_NONE,True])
                    
        except ldap.LDAPError, e:
            print e
            exit

        # create the TreeView using liststore
        self.TVgroups = gtk.TreeView(self.LSgroups)
        self.TVgroups.set_sensitive(False)
        self.TMgroups = self.TVgroups.get_model()
        self.TSgroups = self.TVgroups.get_selection()
        self.TSgroups.set_mode(gtk.SELECTION_MULTIPLE)
        
        # Camps de grup
        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn(_("Group"),cell,text=0)
        self.TVgroups.append_column(tv)
        tv.set_sort_column_id(0)
        
        cellpb = gtk.CellRendererPixbuf()
               
        cell = gtk.CellRendererCombo()
        cell.set_property("model",self.LSfreeze_settings)
        cell.set_property('text-column', 1)
        cell.set_property('editable', True)
        cell.set_property('has-entry',False)
        tv = gtk.TreeViewColumn(_("State"))
        
        tv.pack_start(cellpb, False)
        tv.set_attributes(cellpb, pixbuf=2)
        
        tv.pack_start(cell, True)
        tv.set_attributes(cell, text=3)
        
        cell.connect('changed', self.Cgroup_changed)
        
        self.TVgroups.append_column(tv)
        tv.set_sort_column_id(1)
        
        cell = gtk.CellRendererToggle()
        tv = gtk.TreeViewColumn(_("LDAP"),cell,active=5)
        self.TVgroups.append_column(tv)
        
        # make treeview searchable
        self.TVgroups.set_search_column(0)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(self.TVgroups)
        
        self.table.attach(scroll, 0, 3, 8, 10)
        
        self.CBgroups = gtk.ComboBox(self.LSfreeze_settings)
        cellpb = gtk.CellRendererPixbuf()
        self.CBgroups.pack_start(cellpb, False)
        self.CBgroups.set_attributes(cellpb, pixbuf=0)
        cell = gtk.CellRendererText()
        self.CBgroups.pack_start(cell, True)
        self.CBgroups.set_attributes(cell, text=1)
        self.CBgroups.set_active(0)
        self.CBgroups.set_sensitive(False)
        self.table.attach(self.CBgroups, 0, 1, 10, 11, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
           
        self.Ball_groups = gtk.Button(_("Apply to all"))
        self.Ball_groups.set_sensitive(False)
        self.Ball_groups.connect("clicked", self.Ball_groups_clicked)
        self.table.attach(self.Ball_groups, 1, 2, 10, 11, gtk.FILL, gtk.SHRINK)
        
        self.Bsel_groups = gtk.Button(_("Apply to selected"))
        self.Bsel_groups.set_sensitive(False)
        self.Bsel_groups.connect("clicked", self.Bsel_groups_clicked)
        self.table.attach(self.Bsel_groups, 2, 3, 10, 11, gtk.FILL, gtk.SHRINK) 
        
        self.mainBox.pack_start(self.table, True) 
    
    def init_toolbar(self):
        
        self.TBtoolbar = gtk.Toolbar()
        self.TBtoolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.TBtoolbar.set_style(gtk.TOOLBAR_BOTH)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[1])
        iconw.show()
        self.RTBall = gtk.RadioToolButton()
        self.RTBall.set_icon_widget(iconw)
        self.RTBall.set_label(_('Freeze All'))
        self.RTBall.set_tooltip_text(_('Freezes All the system'))
        self.RTBall.set_is_important(True)
        self.RTBall.set_expand(True)
        self.Sall = self.RTBall.connect("clicked",self.set_freeze_all,1)
        self.RTBall.show()
        self.TBtoolbar.insert(self.RTBall,0)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[0])
        iconw.show()
        self.RTBnone = gtk.RadioToolButton(self.RTBall)
        self.RTBnone.set_icon_widget(iconw)
        self.RTBnone.set_label(_('Unfreeze All'))
        self.RTBnone.set_tooltip_text(_('Unfreezes All the system'))
        self.RTBnone.set_is_important(True)
        self.RTBnone.set_expand(True)
        self.Snone = self.RTBnone.connect("clicked",self.set_freeze_all,0)
        self.RTBnone.show()
        self.TBtoolbar.insert(self.RTBnone,1)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[2])
        iconw.show()
        self.RTBadvanced = gtk.RadioToolButton(self.RTBall)
        self.RTBadvanced.set_icon_widget(iconw)
        self.RTBadvanced.set_label(_('Advanced'))
        self.RTBadvanced.set_tooltip_text(_('Advanced freeze'))
        self.RTBadvanced.set_is_important(True)
        self.RTBadvanced.set_expand(True)
        self.Sadv = self.RTBadvanced.connect("clicked",self.set_freeze_all,2)
        self.RTBadvanced.show()
        self.TBtoolbar.insert(self.RTBadvanced,2)
        
        self.STIsep = gtk.SeparatorToolItem()
        self.STIsep.show()
        self.TBtoolbar.insert(self.STIsep,3)
        
        self.RTBsettings = gtk.ToolButton(gtk.STOCK_EDIT)
        self.RTBsettings.set_label(_('Show Settings'))
        self.RTBsettings.set_tooltip_text(_('Shows the settings window'))
        self.RTBsettings.set_is_important(True)
        self.RTBsettings.connect("clicked",self.show_settings)
        self.TBtoolbar.insert(self.RTBsettings,4)
        
        self.TBtoolbar.show()
        
        self.mainBox.pack_start(self.TBtoolbar, False)
        
        #self.mainBox.child_set_property(self.TBtoolbar,"expand",True)
    
    def RBall_toggled(self, widget, data=None):
        self.CBall.set_sensitive(widget.get_active())
        
    def RBusers_toggled(self, widget, data=None):
        self.TVusers.set_sensitive(widget.get_active())
        self.Ball_users.set_sensitive(widget.get_active())
        self.Bsel_users.set_sensitive(widget.get_active())
        self.CBusers.set_sensitive(widget.get_active())
    
    def RBgroup_toggled(self, widget, data=None):
        self.TVgroups.set_sensitive(widget.get_active())
        self.Ball_groups.set_sensitive(widget.get_active())
        self.Bsel_groups.set_sensitive(widget.get_active())
        self.CBgroups.set_sensitive(widget.get_active())
        
    def Ball_users_clicked(self, widget=None, data=None):
        self.TMusers.foreach(self.set_state, self.CBusers.get_active())
        
    def Ball_groups_clicked(self, widget=None, data=None):
        self.TMgroups.foreach(self.set_state, self.CBgroups.get_active())
        
    def Bsel_users_clicked(self, widget=None, data=None):
        self.TSusers.selected_foreach(self.set_state, self.CBusers.get_active())
        
    def Bsel_groups_clicked(self, widget=None, data=None):
        self.TSgroups.selected_foreach(self.set_state, self.CBgroups.get_active())
        
    def LS_add(self,name):
        #Afegir-ho al LS
        index = len(self.LSfreeze_settings)
        
        icon = gtk.Image()
        
        if index == 0:
            icon.set_from_file(SMALL_ICONS[FREEZE_NONE])
        elif index > 0 and index < 3:
            icon.set_from_file(SMALL_ICONS[FREEZE_ALL])
        else:
            icon.set_from_file(SMALL_ICONS[FREEZE_ADV])
            
        self.LSfreeze_settings.append([icon.get_pixbuf(),name,index])
    
    def LS_remove(self, index):
        self.unset_all_states(index)
        self.LSfreeze_settings.remove(self.LSfreeze_settings.get_iter(index))        
                
    def Cuser_changed(self, cell, path, iter):
        state = cell.get_property("model").get_value(iter,2)
        self.set_state(self.TMusers,path,None,state)
   
    def Cgroup_changed(self, cell, path, iter):
        state = cell.get_property("model").get_value(iter,2)
        self.set_state(self.TMgroups,path,None,state)
    
    def unset_all_states(self,state):
        if self.CBall.get_active() == state:
            self.CBall.set_active(0)
        if self.CBusers.get_active() == state:
             self.CBusers.set_active(0)
        if self.CBgroups.get_active() == state:
            self.CBgroups.set_active(0)
        self.TMusers.foreach(self.unset_state, state)
        self.TMgroups.foreach(self.unset_state, state)
        
    def set_state(self, model, path, iter, state):
        model[path][2] = self.LSfreeze_settings[state][0]
        model[path][3] = self.LSfreeze_settings[state][1]
        model[path][4] = self.LSfreeze_settings[state][2]
    
    def unset_state(self, model, path, iter, state):
        if model[path][4] == state:
            self.set_state(model,path,iter,0)
            
    def set_state_label(self, model, path, iter, state):
        if model[path][4] == state:
            model[path][3] = self.LSfreeze_settings[state][1]
            
    def set_all_states_label(self, path, label):
        self.LSfreeze_settings[path][1] = label
        self.TMusers.foreach(self.set_state_label, path)
        self.TMgroups.foreach(self.set_state_label, path)
    
    def set_freeze_all(self, widget = None, data = 0, save = True):
        if widget == None or widget.get_active():
            
            self.window.set_icon_from_file(NORMAL_ICONS[data])
                        
            show = self.RTBadvanced.get_active()
            self.table.set_sensitive(show)
            self.window.set_property("resizable",show)
            
            self.PBprogress.set_fraction(0.0)
            
            if data == FREEZE_NONE:
                self.PBprogress.set_text(_("System unfrozen"))
                self.CBall.set_active(FREEZE_NONE)
                self.CBtime.set_active(TIME_MANUAL)
                self.RBall.set_active(True)
                self.configW.hide()
            elif data == FREEZE_ALL:
                self.PBprogress.set_text(_("System frozen"))
                self.CBall.set_active(FREEZE_ALL)
                self.CBtime.set_active(TIME_SESSION)
                self.RBall.set_active(True)
                self.configW.hide()
            elif data >= FREEZE_ADV:   
                self.PBprogress.set_text(_("Advanced frozen"))
            
            if show:
                #SHOW ADVANCED
                self.table.show_all()
                
                
                iconw = gtk.Image()
                iconw.set_from_file(NORMAL_ICONS[FREEZE_ALL])
                iconw.show()
                self.RTBall.set_icon_widget(iconw)
                self.RTBall.set_expand(False)
                
                iconw = gtk.Image()
                iconw.set_from_file(NORMAL_ICONS[FREEZE_NONE])
                iconw.show()
                self.RTBnone.set_icon_widget(iconw)
                self.RTBnone.set_expand(False)
                
                iconw = gtk.Image()
                iconw.set_from_file(NORMAL_ICONS[FREEZE_ADV])
                iconw.show()
                self.RTBadvanced.set_icon_widget(iconw)
                self.RTBadvanced.set_expand(False)
                
                self.RTBsettings.show()
                self.Bapply.show()
                self.Brestore.show()
                self.STIsep.show()
                
                self.TBtoolbar.set_size_request(480,-1)
                self.TBtoolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
                
            else:
                #HIDE ADVANCED
                self.table.hide()
                self.window.unmaximize()
                
                iconw = gtk.Image()
                iconw.set_from_file(HUGE_ICONS[FREEZE_ALL])
                iconw.show()
                self.RTBall.set_icon_widget(iconw)
                self.RTBall.set_expand(True)
                
                iconw = gtk.Image()
                iconw.set_from_file(HUGE_ICONS[FREEZE_NONE])
                iconw.show()
                self.RTBnone.set_icon_widget(iconw)
                self.RTBnone.set_expand(True)
                
                iconw = gtk.Image()
                iconw.set_from_file(HUGE_ICONS[FREEZE_ADV])
                iconw.show()
                self.RTBadvanced.set_icon_widget(iconw)
                self.RTBadvanced.set_expand(True)
                
                self.RTBsettings.hide()
                self.Bapply.hide()
                self.Brestore.hide()
                self.STIsep.hide()
                
                
                self.TBtoolbar.set_size_request(425,-1)
                self.TBtoolbar.set_style(gtk.TOOLBAR_BOTH)
                
                if save:
                    #Save file
                    self.save_file()
                    
    def set_enabled_to_load(self,enable):
        if enable:
            self.Sall = self.RTBall.connect("clicked",self.set_freeze_all,1)
            self.Snone = self.RTBnone.connect("clicked",self.set_freeze_all,0)
            self.Sadv = self.RTBadvanced.connect("clicked",self.set_freeze_all,2)
        else:
            self.RTBall.disconnect(self.Sall)
            self.RTBnone.disconnect(self.Snone)
            self.RTBadvanced.disconnect(self.Sadv)
            
class tar_thread ( threading.Thread ):
    
    def __init__(self,tars,win):
        threading.Thread.__init__(self)
        self.stopthread = threading.Event()
        
        self.tars = tars
        self.win = win
        
    def run ( self ):
        debug("Entering tar_thread.run",DEBUG_MEDIUM)
        
        sys.settrace(self.globaltrace)
        max = float(len(self.tars) * 2)
        
        #Create thread that create tars
        gtk.gdk.threads_enter()
        for i, froze in enumerate(self.tars):
            self.win.PBprogress.set_text("Freezing "+froze.username)
            i = (i + 1) * 2
            self.win.PBprogress.set_fraction((i-1)/max)
            
            gtk.gdk.threads_leave()
            
            froze.create_tar()
            
            gtk.gdk.threads_enter()
            
            self.win.PBprogress.set_text("User " + froze.username + " frozen")
            self.win.PBprogress.set_fraction(i/max)
            
        self.win.PBprogress.set_fraction(1.0)
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
        
    
class profile ( threading.Thread ):
            
    name = ""
    filters = []
    username = ""
    homedir = ""
    network = ""
    source = ""
    deposit = ""
    uid = 0
    gid = 0
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
        
    def copy(self):
        newCopy = profile()
        newCopy.name = self.name
        newCopy.filters = self.filters
        newCopy.username = self.username
        newCopy.network = self.network
        newCopy.source = self.source
        newCopy.deposit = self.deposit
        newCopy.uid = self.uid
        newCopy.gid = self.gid
        
        return newCopy
    
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
                name = path.join(self.homedir,file.name)
                os.chown(name, self.uid, self.gid)
            
    def exclude_from_tar(self, path):
        path = path[len(self.homedir)+1:]
        
        if len(path) < 1 or len(self.filters) < 1: return False
        
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
        
class tar_list:
    
    def get_tar_list(self, time = TIME_INDEFFERENT): 
        debug('Entering tar_list.get_tar_list',DEBUG_LOW)
       
        try:
            xdoc = minidom.parse(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE))
            xFreeze = xdoc.getElementsByTagName("freeze")[0]
            xProfiles = xdoc.getElementsByTagName("profiles")[0]
            xMax = int(xProfiles.getAttribute("numProfiles"))
            timeConf = str2int(xFreeze.getAttribute("time"))
        except: 
            print_error("Corrupted configuration file")
            return []
        
        #IF requested time is not indifferent
        #AND time requested is different  of the configured time
        if time != TIME_INDEFFERENT and timeConf != time:
            #Return and don't parse more
            return []
        
        self.freeze = []
        
        try:
            #ALL
            if str2bool(xFreeze.getElementsByTagName("all")[0].getAttribute("active")):
                debug('  ALL SYSTEM',DEBUG_LOW)
                value = str2int(xFreeze.getElementsByTagName("all")[0].getAttribute("value"))
                if value != FREEZE_NONE:
                    config = self.init_config(xProfiles,value,xMax)
                    self.get_all_frozen(config)
            
            #BY USERS
            elif str2bool(xFreeze.getElementsByTagName("users")[0].getAttribute("active")):
                debug('  USERS',DEBUG_LOW)
                for xUser in xdoc.getElementsByTagName("users")[0].getElementsByTagName("user"):
                    value = str2int(xUser.getAttribute("value"))
                    if value != FREEZE_NONE:
                        config = self.init_config(xProfiles,value,xMax)
                        uid = str2int(xUser.getAttribute("uid"))
                        self.get_user_frozen(config, uid)
                    
            #BY GROUPS
            elif str2bool(xFreeze.getElementsByTagName("groups")[0].getAttribute("active")):
                debug('  GROUPS',DEBUG_LOW)
                for xGroup in xdoc.getElementsByTagName("groups")[0].getElementsByTagName("group"):
                    value = str2int(xGroup.getAttribute("value"))
                    if value != FREEZE_NONE:
                        config = self.init_config(xProfiles,value,xMax)
                        gid = str2int(xGroup.getAttribute("gid"))
                        self.get_group_frozen(config, gid)
        except:
            return []
        
        return self.freeze
    
    def init_config(self, xConfig, value, xMax):
        if value >= xMax:
            print_error("Profile "+str(value)+" not avalaible")
            raise

        
        xProfile = xConfig.getElementsByTagName("profile")[value]
        valueAux = int(xProfile.getAttribute("profileNum"))
        
        if value != valueAux:
            print_error("Corrupted config file")
            raise

        
        prof = profile()
        
        prof.name =  xProfile.getAttribute("name")
        
        if(str2bool(xProfile.getElementsByTagName("network")[0].getAttribute("active"))):
            prof.network = xProfile.getElementsByTagName("network")[0].getAttribute("value")
        else: prof.network = ""
        
        if(str2bool(xProfile.getElementsByTagName("source")[0].getAttribute("active"))):
            filename = xProfile.getElementsByTagName("source")[0].getAttribute("value")
            prof.source = filename
        else:   prof.source = ""
 
        prof.deposit = xProfile.getElementsByTagName("deposit")[0].getAttribute("value")
        
        for xexclude in xProfile.getElementsByTagName("excludes")[0].getElementsByTagName("exclude"):
            
            valueExclude = str2int(xexclude.getAttribute("value"))
            title = xexclude.getAttribute("title")
            pattern = xexclude.getAttribute("pattern")
            
            prof.filters.append([valueExclude,pattern])
                
        for filter in prof.filters:
            debug(filter[1])
        
        return prof
    
    def get_all_frozen(self, config):
        
        #Exec for all users in the permitted uid range
        for user in pwd.getpwall():
            uid = user.pw_uid
            if uid >= minUID and uid < maxUID:
                newConf = config.copy()
                newConf.username = user.pw_name
                newConf.homedir = user.pw_dir
                newConf.uid = user.pw_uid
                newConf.gid = user.pw_gid
                
                self.freeze.append(newConf)
        
        return
    
    def get_user_frozen(self, config, uid):
        debug("   " +str(uid),DEBUG_LOW)
        
        if uid < minUID or uid >= maxUID:  return
        
        try:
            user = pwd.getpwuid(uid)
        except:
            print_error("User " + uid + " not found")
        else:        
            newConf = config.copy()
            newConf.username = user.pw_name
            newConf.homedir = user.pw_dir
            newConf.uid = user.pw_uid
            newConf.gid = user.pw_gid
            
            self.freeze.append(newConf)

        return
    
    def get_group_frozen(self, config, gid):
        debug("   " +str(gid),DEBUG_LOW)
        
        if gid < minUID or gid >= maxUID:  return
        
        #Usuari primari del grup
        for user in pwd.getpwall():
            if gid == user.pw_gid:
                uid = user.pw_uid
                if uid >= minUID and uid < maxUID:
                    newConf = config.copy()
                    newConf.username = user.pw_name
                    newConf.homedir = user.pw_dir
                    newConf.uid = user.pw_uid
                    newConf.gid = user.pw_gid
                    
                    self.freeze.append(newConf)
                break
            
        #Usuaris secuntaris del grup
        try:
            group = grp.getgrgid(gid)
        except:
            print_error("Group " + gid + " not found")
        else:
            for username in group.gr_mem:
                try:
                    user = pwd.getpwname(username)
                except:
                    print_error("User " + user + " not found",WARNING)
                else:
                    uid = user.pw_uid
                    if uid >= minUID and uid < maxUID: 
                        newConf = config.copy()
                        newConf.username = user.pw_name
                        newConf.homedir = user.pw_dir
                        newConf.uid = user.pw_uid
                        newConf.gid = user.pw_gid
                        
                        self.freeze.append(newConf)
        return
                
class terminal:

    def print_config(self):
        try:
            xdoc = minidom.parse(os.path.join (CONFIG_DIRECTORY, CONFIG_FILE))
        except: 
            print_error("Corrupted configuration file")
            exit(0)
        
        print xdoc.toprettyxml(indent="  ")
        return
    
    def main(self, time = TIME_INDEFFERENT, username = ""):
        print "Trivial Freezer "+VERSION
        print "===================="
        
        tars = tar_list().get_tar_list(time)
        
        if len(tars) > 0:
            debug(" RESTORE",DEBUG_LOW)
            if len(username) == 0:
                debug("  SYSTEM or MANUAL",DEBUG_LOW)
                for froze in tars:
                    froze.restore_tar()
            elif time == TIME_SESSION:
                debug("  SESSION",DEBUG_LOW)
                for froze in tars:
                    if username == froze.username:
                        froze.restore_tar()
                        break
            else: debug("  ERROR",DEBUG_LOW)
                
        debug("DONE",DEBUG_LOW)
            
    def help(self):
        print "Trivial Freezer "+VERSION+" HELP"
        print "========================="
        print "Usage: "+sys.argv[0]+"  [OPTION]\n"
        print " Options:"
        print "  -x,-c       Open the configuration window (DEFAULT OPTION)"
        print "  -m          Runs manual restoration profiles"
        print "  -S          Runs starting system restoration profiles"
        print "  -s username Runs starting session restoration profiles for the specified uid"
        print "  -p          Print the XML configuration file"
        print "  -h          Show this help"
        return
    
if __name__ == "__main__":
    
    args = len(sys.argv)
    
    action_ok = False
    show_help = False
    print_config = False
    configure = False
    restore = False
    user = ""
    time = TIME_INDEFFERENT
    
    for i, arg in enumerate(sys.argv):
        if arg.startswith("-"):
            if arg == "-x" or arg == "-c":
               if action_ok:
                   show_help = True
                   configure = False
                   restore = False
               else:
                   #CONFIGURATION
                   configure = True
                   action_ok = True
            elif arg == "-m":
                if action_ok:
                   show_help = True
                   configure = False
                   restore = False
                else:
                   #MANUAL RESTORATION
                   restore = True
                   time = TIME_MANUAL
                   action_ok = True
            elif arg == "-s":
                if action_ok or args <= i + 1:
                    show_help = True
                    configure = False
                    restore = False
                else:
                    #SESSION RESTORATION
                    user = sys.argv[i]
                    restore = True
                    time = TIME_SESSION
                    action_ok = True
            elif arg == "-S":
                if action_ok:
                    show_help = True
                    configure = False
                    restore = False
                else:
                    #SYSTEM RESTORATION
                    restore = True
                    time = TIME_SYSTEM
                    action_ok = True
            elif arg == "-d":
                if args > i + 1:
                    #DEBUG LEVEL
                    debug_level = str2int(sys.argv[i+1])
                else:
                    show_help = True
            elif arg == "-p":
                #PRINT CONFIG
                print_config = True
            else:
                #PRINT HELP
                show_help = True


    debug(gtk.gtk_version,DEBUG_MEDIUM)
    
    if not action_ok and not show_help and not print_config:
        configure = True
        action_ok = True
        
    if action_ok:
        if restore:
            check_root()
            terminal().main(time,user)
        elif configure:
            check_root()
            window = tfreezer()
            window.main()
        else:
            show_help = True
    else:
        show_help = True
        
    if show_help:
        terminal().help()
    
    if print_config:
        terminal().print_config()
        