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

import gtk
import sexy

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext

class profileTab(gtk.Table):
    
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
        return
    
