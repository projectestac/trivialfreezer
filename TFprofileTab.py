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
from TFconfig import rule,profile
from TFpasswd import *

import gtk
try:
    import sexy
    sexy_style = True
except:
    sexy_style = False

_ = load_locale()

class profileTab(gtk.Table):
    
    #Parent window
    mother = None
    #Entry with the title of the profile
    Ename = None
    #RadioButton, indicates that the source is from the current home
    RBhome = None
    #RadioButton, indicates that the source is a file selected from the repository
    RBfile = None
    #ComboBox, with the selected source
    CBfile = None
    #LisStore for the filter rules
    LSfilter = None
    #TreeView for the filter rules
    TVfilter = None
    #TreeModel of the filter rules
    TMfilter = None
    #SexyEntry for the lost+found deposit
    Edeposit = None
    
    def __init__(self, parent, name):
        #Treat the tab as a table
        gtk.Table.__init__(self)
        self.set_row_spacings(5)
        self.set_col_spacings(5)
        self.set_border_width(5)
        
        #Take the parent window
        self.mother = parent
        
        #Title
        label = gtk.Label(_("Profile name"))
        self.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
        
        self.Ename = gtk.Entry()
        self.Ename.set_text(name)
        self.Ename.connect("key-press-event",parent.tab_name_modified)
        self.Ename.connect("key-release-event",parent.tab_name_modified)
        self.attach(self.Ename, 1, 3, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        separator = gtk.HSeparator()
        self.attach(separator, 0, 3, 1, 6, gtk.EXPAND | gtk.FILL, gtk.FILL)

        #Where to take the tar
        label = gtk.Label("<b>"+_("Restoration source")+"</b>")
        label.set_use_markup(True)
        self.attach(label, 0, 3, 6, 7, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        self.RBhome = gtk.RadioButton(None, _("Use the current home directory"))
        self.attach(self.RBhome, 0, 3, 7, 8, gtk.EXPAND |gtk.FILL, gtk.FILL)
        
        self.RBfile = gtk.RadioButton(self.RBhome, _("Use this source from the repository"))
        self.RBfile.connect("toggled",self.__RBfile_toggled)
        self.attach(self.RBfile, 0, 1, 8, 9, gtk.FILL, gtk.FILL)
        
        self.CBfile = gtk.ComboBox(parent.LSsources)
        self.CBfile.connect("changed",self.__CBfile_changed)
        cell = gtk.CellRendererText()
        self.CBfile.pack_start(cell, True)
        self.CBfile.set_attributes(cell, text=0)
        self.CBfile.set_active(-1)
        self.CBfile.set_sensitive(False)
        self.attach(self.CBfile, 1, 3, 8, 9, gtk.EXPAND | gtk.FILL, gtk.SHRINK)
        
        self.CBexecuteenable = gtk.CheckButton(_("Execute a command after restoring"))
        self.CBexecuteenable.connect("toggled",self.__CBexecuteenable_toggled)
        self.attach(self.CBexecuteenable, 0, 1, 10, 11, gtk.FILL, gtk.FILL)
        
        if sexy_style:
            #Sexy entry
            self.Eexecute = sexy.IconEntry()
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_BUTTON)
            self.Eexecute.set_icon(sexy.ICON_ENTRY_PRIMARY, image)
            self.Eexecute.connect("icon-pressed", self.__choose_execute)
            self.Eexecute.add_clear_button()
            self.Eexecute.set_sensitive(False)
            self.attach(self.Eexecute, 1, 3, 10, 11, gtk.EXPAND | gtk.FILL, gtk.FILL)
        else:
            #No sexy entry
            self.Eexecute = gtk.Entry()
            self.Eexecute.set_sensitive(False)
            self.attach(self.Eexecute, 1, 2, 10, 11, gtk.EXPAND | gtk.FILL, gtk.FILL)
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_BUTTON)
            self.Bexecute = gtk.Button()
            self.Bexecute.add(image)
            self.Bexecute.connect("clicked", self.__choose_execute)
            self.Bexecute.set_sensitive(False)
            self.attach(self.Bexecute, 2, 3, 10, 11, gtk.FILL, gtk.SHRINK)
        
        separator = gtk.HSeparator()
        self.attach(separator, 0, 3, 11, 12, gtk.EXPAND | gtk.FILL, gtk.FILL)
                        
        #RULES
        label = gtk.Label("<b>"+_("Rules")+"</b>")
        label.set_use_markup(True)
        self.attach(label, 0, 3, 12, 13, gtk.EXPAND | gtk.FILL, gtk.FILL)
        self.LSfilter = gtk.ListStore(str,str,str,str,int)
        
        #Treeview of the Liststore
        self.TVfilter = gtk.TreeView(self.LSfilter)
        self.TMfilter = self.TVfilter.get_model()
        
        #Filter fields
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.__Cfiltertitle_edited)
        tv = gtk.TreeViewColumn(_("Name"),cell,text=0)
        self.TVfilter.append_column(tv)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.__Cfilter_edited)
        tv = gtk.TreeViewColumn(_("Filter"),cell,text=1)
        self.TVfilter.append_column(tv)
        tv.set_expand(True)
        tv.set_resizable(True)
        
        cellpb = gtk.CellRendererPixbuf()
        
        #The action has two fields: the text, the pixmap and
        cell = gtk.CellRendererCombo()
        cell.set_property("model",self.mother.LSactions)
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
        
        cell.connect('changed', self.__Cfilter_changed)
        
        self.TVfilter.append_column(tv)
        
        self.TVfilter.set_search_column(0)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(self.TVfilter)
        
        self.attach(scroll, 0, 2, 13, 18, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
        
        #Buttons to change order, add and delete
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.__add_filter)
        self.attach(button, 2, 3, 13, 14, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REMOVE,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.__remove_filter)
        self.attach(button, 2, 3, 14, 15, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_UP,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.__up_filter)
        self.attach(button, 2, 3, 15, 16, gtk.FILL, gtk.SHRINK)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_DOWN,gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(image)
        button.connect("clicked", self.__down_filter)
        self.attach(button, 2, 3, 16, 17, gtk.FILL, gtk.SHRINK)
        
        #Lost and found deposit
        label = gtk.Label(_("Deposit for Lost+Found"))
        self.attach(label, 0, 1, 18, 19, gtk.FILL, gtk.FILL)
        
        #Sexy entry
        self.Edeposit = sexy.IconEntry()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_BUTTON)
        self.Edeposit.set_icon(sexy.ICON_ENTRY_PRIMARY, image)
        self.Edeposit.connect("icon-pressed", self.__choose_deposit)
        self.Edeposit.add_clear_button()
        self.attach(self.Edeposit, 1, 3, 18, 19, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        #Some help...
        label = gtk.Label("<i>"+_("Enter ~ to replace the home directory of the user")+"</i>")
        label.set_use_markup(True)
        self.attach(label, 0, 3, 19, 20, gtk.FILL, gtk.FILL)
                
        label = gtk.Label()
        self.attach(label, 1, 2, 17, 18, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        label = gtk.Label()
        self.attach(label, 2, 3, 17, 18, gtk.FILL, gtk.EXPAND | gtk.FILL)

        self.show_all()
        
            
    def __RBfile_toggled(self, widget, data=None):
        "Enable/disable the repo comboBox when the radiobutton is togled"
        self.CBfile.set_sensitive(widget.get_active())
    
    def __CBfile_changed(self, widget, data=None):
        "If the resource is deleted, togle RBfile/RBhome"
        if self.CBfile.get_active() == -1:
            self.RBhome.set_active(True)
    def __CBexecuteenable_toggled(self, widget, data=None):
        "Enable/disable the execution entry when the checkbox is togled"
        self.Eexecute.set_sensitive(widget.get_active())
        if not sexy_style:
            self.Bexecute.set_sensitive(widget.get_active())
        
    def __Cfilter_changed(self, cell, path, iter):
        "When a filter has changed, change the image and all the fields"
        state = cell.get_property("model").get_value(iter,2)
        self.TMfilter[path][2] = self.mother.LSactions[state][0]
        self.TMfilter[path][3] = self.mother.LSactions[state][1]
        self.TMfilter[path][4] = self.mother.LSactions[state][2]
        
    def __Cfilter_edited(self,cellrenderertext, path, new_text):
        "When the regular expression is edited, set it"
        self.LSfilter[path][1] = new_text
        
    def __Cfiltertitle_edited(self,cellrenderertext, path, new_text):
        "When the title is edited, set it"
        self.LSfilter[path][0] = new_text
        
    def __add_filter(self, widget=None, data=_("Eveything")):
        "Adds a filter to the rules list"       
        self.LSfilter.append([data,".",self.mother.LSactions[ACTION_KEEP][0],self.mother.LSactions[ACTION_KEEP][1],ACTION_KEEP])
        
    def __remove_filter(self, widget=None):
        "Removes the selected filter from the rules list"
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            self.LSfilter.remove(iter)
        
    def __up_filter(self, widget=None, data=_("New Filter")):
        "Moves upwards a filter in the rules list"
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            path = self.TMfilter.get_path(iter)[0] - 1
            if path < 0:
                return
            iterPrev = self.TMfilter.get_iter(self.TMfilter.get_path(iter)[0] - 1)
            self.LSfilter.move_before(iter, iterPrev)
        
    def __down_filter(self, widget=None):
        "Moves downwards a filter in the rules list"
        (view, iter) = self.TVfilter.get_selection().get_selected()
        if iter != None:
            path = self.TMfilter.get_path(iter)[0] + 1
            if path >= self.TMfilter.iter_n_children(None):
                return
            iterNext = self.TMfilter.get_iter(path)
            self.LSfilter.move_after(iter, iterNext)
    
    def __choose_deposit(self,widget=None,button=None,data=None):
        "Choose deposit for lost+found"
        #Only the right button
        if button != sexy.ICON_ENTRY_PRIMARY:
            return
        
        #File chooser dialog for directories
        dialog = gtk.FileChooserDialog(_("Choose source file"),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),parent=self.mother)
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            depositfile = dialog.get_filename()
            
            #If deposit file is inside a home directory, it ask to be inside each home
            userlist = passwd()
            for pwuser in userlist.getpwall():
                uid = pwuser.pw_uid
                if depositfile.startswith(pwuser.pw_dir):
                    #Ask it!
                    warning = gtk.MessageDialog(parent=self.mother,type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
                    warning.set_markup(_("The folder you have selected is inside a home directory.\nDo you want to use create a deposit inside each home directory?"))
                    warning.show_all()
                    response = warning.run()
                    if response == gtk.RESPONSE_NO:
                        #Response NO
                        warning.destroy()
                        break
                    #Response YES
                    warning.destroy()
                    depositfile = "~/"+depositfile[len(pwuser.pw_dir)+1:]
                    break

            self.Edeposit.set_text(depositfile)
            
        dialog.destroy()
        return
    
    def __choose_execute(self,widget=None,button=None,data=None):
        "Choose the command to execute"
        #Only the right button
        if sexy_style and button != sexy.ICON_ENTRY_PRIMARY:
            return
        
        #File chooser dialog
        dialog = gtk.FileChooserDialog(_("Choose a command to execute"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK),parent=self.mother)
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name(_("Command files"))
        filter.add_mime_type("application/x-shellscript")
        filter.add_mime_type("application/x-executable")
        dialog.add_filter(filter)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            commandfile = dialog.get_filename()
            
            self.Eexecute.set_text(commandfile)
            
        dialog.destroy()
        return
    
    def set_source(self, source):
        "Sets the source file from the reposiroty"
        
        #If is nothing, deselect all
        if source == "":
            self.CBfile.set_active(-1)
            return
        
        
        for path, sourceAux in enumerate(self.mother.LSsources):
            if sourceAux[1] == source:
                self.CBfile.set_active(path)
                return
            
        self.CBfile.set_active(-1)
        return
    
    def get_config(self):
        "Gets the current profile config for this tab"
        
        p = profile(self.Ename.get_text())
        p.saved_source = self.RBfile.get_active()
        
        path = self.CBfile.get_active()
        if path >= 0:
            p.source = self.mother.LSsources[path][1]
        else:
            p.source = ""
            
        p.deposit = self.Edeposit.get_text()
        
        p.execute = self.Eexecute.get_text()
        p.execute_enabled = self.CBexecuteenable.get_active()
        
        for row in self.LSfilter:
            r = rule(row[0], row[1], row[4])
            p.rules.append(r)
            
        return p
    
    def is_source_in_use(self, path):
        "To know if the selected source is in use for any profile"
        return self.CBfile.get_active() == path
    
