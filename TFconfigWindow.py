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
from TFprofileTab import *
from TFconfig import *
import gtk

import os

import tarfile

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext

class configWindow(gtk.Dialog):
    
    def __init__(self, config, win):
        gtk.Dialog.__init__(self,title="Trivial Freezer"+_(" - Settings"),
                                 parent=win,
                                 flags=0,
                                 buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_icon_from_file(NORMAL_ICONS[FREEZE_ADV])
        
        self.config = config
        mainBox = gtk.HBox()
        
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        toolbar.set_style(gtk.TOOLBAR_BOTH)
        
        item = gtk.RadioToolButton(None,gtk.STOCK_SELECT_COLOR)
        item.set_label(_('Profiles'))
        item.set_tooltip_text(_('Configure profiles'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_profiles)
        toolbar.insert(item,0)
        
        item = gtk.RadioToolButton(item,gtk.STOCK_COLOR_PICKER)
        item.set_label(_('Sources'))
        item.set_tooltip_text(_('Configure sources'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_sources)
        toolbar.insert(item,1)
        
        item = gtk.RadioToolButton(item,gtk.STOCK_CONNECT)
        item.set_label(_('LDAP'))
        item.set_tooltip_text(_('Configure LDAP'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_ldap)
        toolbar.insert(item,2)
        
        toolbar.show_all()
        
        mainBox.pack_start(toolbar, False)
        
        self.init_profiles()
        mainBox.pack_start(self.profiles, True)
        self.profiles.show_all()
        
        self.init_sources()
        mainBox.pack_start(self.sources, True)
        
        self.init_ldap()
        mainBox.pack_start(self.ldap, True)
        
        
        self.load()
        
        self.get_content_area().add(mainBox)
        mainBox.show()
        self.show()
    
    def init_profiles(self):
        self.profiles = gtk.VBox()
        
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
        
        self.profiles.pack_start(toolbar, False)
        
        #Config tabs
        self.tabs = gtk.Notebook()
        self.tabs.set_scrollable(True)
        self.profiles.pack_start(self.tabs, True)
    
    def init_sources(self):
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
        
    def init_ldap(self):
        self.ldap = gtk.Table()
        self.ldap.set_row_spacings(5)
        self.ldap.set_col_spacings(5)
        self.ldap.set_border_width(5)
        
        label = gtk.Label("<b>"+_("LDAP configuration")+"</b>")
        label.set_use_markup(True)
        self.ldap.attach(label, 0, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        self.CBldapenable = gtk.CheckButton(_("Enable LDAP support"))
        self.CBldapenable.connect("toggled",self.CBldapenable_toggled)
        self.ldap.attach(self.CBldapenable, 0, 3, 1, 2, gtk.FILL, gtk.SHRINK)
        
        label = gtk.Label(_("LDAP Server"))
        self.ldap.attach(label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        
        self.Eserver = gtk.Entry()
        self.Eserver.set_sensitive(False)
        self.ldap.attach(self.Eserver, 1, 3, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        label = gtk.Label(_("Distinguished Name (dn)"))
        self.ldap.attach(label, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        
        self.Edn = gtk.Entry()
        self.Edn.set_sensitive(False)
        self.ldap.attach(self.Edn, 1, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
    def load(self):
        
        for source in self.config.sources:
            self.LSsources.append([source.name,source.file])
            
        for profile in self.config.profiles:
            newTab = self.add_tab(data = profile.title)
            newTab.set_sensitive(profile.could_be_edited)
            newTab.Edeposit.set_text(profile.deposit)
            
            newTab.set_source(profile.source)
            if not profile.saved_source:
                newTab.CBfile.set_active(-1)         
                                 
            newTab.RBhome.set_active(not profile.saved_source)
            newTab.RBfile.set_active(profile.saved_source)
            newTab.CBfile.set_sensitive(profile.saved_source)
            
            for rule in profile.rules:
                newTab.LSfilter.append([rule.name,
                    rule.filter,
                    newTab.LSactions[rule.action][0],
                    newTab.LSactions[rule.action][1],
                    rule.action])
                
        self.CBldapenable.set_active(self.config.ldap_enabled)
        self.Eserver.set_text(self.config.ldap_server)
        self.Edn.set_text(self.config.ldap_dn)
        
        return
    
    def get_config(self):
        del self.config.profiles[:]
        
        self.config.load_profile_defaults()
        
        numProfiles = self.tabs.get_n_pages()
        for i in range(numProfiles - BLOCKED_PROFILES):
            tab = self.tabs.get_nth_page(i + BLOCKED_PROFILES)
            p = profile(tab.Ename.get_text())
            p.saved_source = tab.RBfile.get_active()
            p.source = tab.get_source()
            p.deposit = tab.Edeposit.get_text()
            
            for row in tab.LSfilter:
                r = rule(row[0], row[2], row[4])
                p.rules.append(r)
            
            self.config.profiles.append(p)
            
        del self.config.sources[:]
        
        for row in self.LSsources:
            s = source()
            s.name = row[0]
            s.file = row[1]
            self.config.sources.append(s)
            
        self.config.ldap_enabled = self.CBldapenable.get_active()
        self.config.ldap_dn = self.Edn.get_text()
        self.config.ldap_server = self.Eserver.get_text()
            
        return self.config
    
    def add_tab(self, widget=None, data=_("New Profile")):
        newTab = profileTab(self,data)
        label = gtk.Label(data)
        self.tabs.append_page(newTab, label)
        
        return newTab
    
    def remove_tab(self, widget=None):
        i = self.tabs.get_current_page()
        if i >= BLOCKED_PROFILES:
            self.tabs.remove_page(i)
            
    def tab_name_modified(self, widget, data=None):
        name = widget.get_text()
        tab = widget.get_parent()
        self.tabs.set_tab_label_text(tab, name)

    def show_hide_sources(self,widget):
        if widget.get_active():
            self.sources.show_all()
        else:
            self.sources.hide_all()
            
    def show_hide_profiles(self,widget):
        if widget.get_active():
            self.profiles.show_all()
        else:
            self.profiles.hide_all()
    
    def show_hide_ldap(self,widget):
        if widget.get_active():
            self.ldap.show_all()
        else:
            self.ldap.hide_all()
    
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
                debug(repo + " " + strerror,DEBUG_HIGH)
                
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
                debug(repo + " " + strerror,DEBUG_HIGH)
                
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
            #TODO: fer que avisi si està en ús
            #mark to erase
            #self.config.sources_to_erase.append(file)
            
            self.LSsources.remove(iter)
            
    def CBldapenable_toggled(self, widget=None):
        self.Eserver.set_sensitive(widget.get_active())
        self.Edn.set_sensitive(widget.get_active())
