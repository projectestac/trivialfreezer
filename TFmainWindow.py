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
from TFconfigWindow import *
from TFconfig import *
from TFtar_thread import *

import pygtk
pygtk.require('2.0')
import gtk

import os

_ = load_locale()


def recursive_delete(dirname):
    "Recursive deletes a directory and its contents"
    
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

class mainWindow:
    
    #Window instance
    window = None
    #mainBox in the window
    mainBox = None
    #ListStore with the freezeing profiles
    LSfreeze_settings = None
    #Progress bar of the freezing
    PBprogress = None
    #Stop button of the freezing
    Bstop = None
    #Apply and close buttons
    Hbuttons = None
    #Apply button
    Bapply = None
    #Current config class
    config = None
    #GUI Table of the form
    table = None
    
    #ComBox of the time of automatic restoration
    CBtime = None
    #RadioButton for freezing all system
    RBall = None
    #ComboBox with the selected profile for all system
    CBall = None
    
    #RadioButton for freezing by user
    RBusers = None
    #ListStore with the user configuration
    LSusers = None
    #TreeView of the user config
    TVusers = None
    #TreeModel from the user ListStore
    TMusers = None
    #User selection
    TSusers = None
    #Action to apply to users
    CBusers = None
    #Button that applies the action to all users
    Ball_users = None
    #Button that applies the action to selected users
    Bsel_users  = None
    
    #RadioButton for freezing by groups
    RBgroups = None
    #ListStore with the group configuration
    LSgroups = None
    #TreeView of the group config
    TVgroups = None
    #TreeModel from the group ListStore
    TMgroups = None
    #Group selection
    TSgroups = None
    #Action to apply to groups
    CBgroups = None
    #Button that applies the action to all groups
    Ball_groups = None
    #Button that applies the action to selected groups
    Bsel_groups = None
    
    #Main Toolbar
    TBtoolbar = None
    #Radio Toolbar Button with Freeze all action
    RTBall = None
    #All action connector
    Sall = None
    #Radio Toolbar Button with Freeze none action
    RTBnone = None
    #None action connector
    Snone = None
    #Radio Toolbar Button with Advanced freezing action
    RTBadvanced = None
    #Advanced action connector
    Sadv = None
    #Separator in the toolbar
    STIsep = None
    #Radio Toolbar Button with settings window action
    RTBsettings = None
    
    #Tar Thread
    TTtar = None

    def __init__(self):
        "Inits the window"
        
        debug("GTK version: " + str(gtk.gtk_version), DEBUG_MEDIUM)
        
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
        self.LSfreeze_settings = gtk.ListStore(gtk.gdk.Pixbuf,str)
        
        #Init and add ToolBar
        self.__init_toolbar()
        
        #Init and add user Form
        self.__init_form()
        
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
        self.Bstop.connect("clicked", self.__stop_tars)
        self.Bstop.show()
        self.Bstop.set_sensitive(False)
        progress.pack_start(self.Bstop, False)

        self.mainBox.pack_start(progress,False)
        
        #Apply and restore buttons
        self.Hbuttons = gtk.HBox()
        self.Hbuttons.set_border_width(5)
        self.Hbuttons.show()
                
        self.Bapply = gtk.Button(_("Apply"), gtk.STOCK_APPLY)
        self.Bapply.connect("clicked", self.__save_config)
        self.Hbuttons.pack_start(self.Bapply, True)
        
        but = gtk.Button(_("Quit"),gtk.STOCK_QUIT)
        but.connect("clicked",self.close,0)
        but.show()
        self.Hbuttons.pack_start(but, True)
        
        self.mainBox.pack_start(self.Hbuttons, False)
        
        self.config = config()
        self.config.load()
        self.__load_config()
        
        self.window.add(self.mainBox)
        
        gtk.gdk.threads_init()
    
    def main(self):
        "Shows the main Window"
        self.window.show()
        gtk.main()
    
    def close(self, widget=None, data=None):
        "Closes the main window and kill the threads"
        try:
            self.TTtar.kill()
        except:
            debug("No threads to kill",DEBUG_MEDIUM)
            
        gtk.main_quit()
        return False

    def __show_settings(self, widget=None, data=None):
        "Shows settings window and load configuration after closing"
        
        #Init config Window
        configW = configWindow(self.config, self.window)
        response = configW.run()
        if response == gtk.RESPONSE_ACCEPT:
            #Apply config
            configW.update_config(self.config)
            
            self.config.reload_users()
            self.config.reload_groups()
            self.__load_config()
            
        configW.destroy()

    def __load_config(self, widget=None):
        "Loads configuration from the config class"
        
        self.__set_enabled_to_load(False)
        
        #Create profiles
        self.LSfreeze_settings.clear()
        
        for profile in self.config.profiles:
            self.__LS_add(profile.title)
        
        self.CBtime.set_active(self.config.time)
        
        self.RBall.set_active(self.config.option == OPTION_ALL)
        self.RBusers.set_active(self.config.option == OPTION_USERS)
        self.RBgroups.set_active(self.config.option == OPTION_GROUPS)
        self.CBall.set_active(self.config.all)
            
        #Enable or disable the big toolbar button
        if(self.config.option == OPTION_ALL):
            if (self.config.all == FREEZE_NONE):
                self.RTBnone.set_active(True)
                self.__set_freeze_all(data = FREEZE_NONE, save = False)
            elif (self.config.all == FREEZE_ALL and self.config.time == TIME_SESSION):
                self.RTBall.set_active(True)
                self.__set_freeze_all(data = FREEZE_ALL, save = False)
            else:
                self.RTBadvanced.set_active(True)
                self.__set_freeze_all(data = FREEZE_ADV, save = False)
        else:
            self.RTBadvanced.set_active(True)
            self.__set_freeze_all(data = FREEZE_ADV, save = False)
        
        #LOAD USERS
        self.LSusers.clear()
        for user in self.config.users:
            if user.ldap and not self.config.home_server:
                self.LSusers.append([user.name,
                                 user.id,
                                 None,
                                 _("Not editable (Defined by the server)"),
                                 FREEZE_LDAP,
                                 user.ldap])
            else:
                self.LSusers.append([user.name,
                     user.id,
                     self.LSfreeze_settings[user.profile][0],
                     self.LSfreeze_settings[user.profile][1],
                     user.profile,
                     user.ldap])
        self.CBusers.set_active(0)         
          
        #LOAD GROUPS
        self.LSgroups.clear()
        for group in self.config.groups:
            if group.ldap and not self.config.home_server:
                self.LSgroups.append([group.name,
                                 group.id,
                                 None,
                                 _("Not editable (Defined by the server)"),
                                 FREEZE_LDAP,
                                 group.ldap])
            else:
                self.LSgroups.append([group.name,
                     group.id,
                     self.LSfreeze_settings[group.profile][0],
                     self.LSfreeze_settings[group.profile][1],
                     group.profile,
                     group.ldap])
        self.CBgroups.set_active(0)
        
        self.__set_enabled_to_load(True)
    
    def __save_config(self, widget=None, data=None):
        "Saves config class from the interface"
        
        #General options
        self.config.time = self.CBtime.get_active()
        if self.RBall.get_active():
            self.config.option = OPTION_ALL
        elif self.RBusers.get_active():
            self.config.option = OPTION_USERS
        elif self.RBgroups.get_active():
            self.config.option = OPTION_GROUPS
        
        self.config.all = self.CBall.get_active()
        
        #Users
        del self.config.users [:]
        
        for row in self.LSusers:
            u = user_group(row[1],row[0],row[4],row[5])
            self.config.users.append(u)
        
        #Groups
        del self.config.groups [:]
          
        for row in self.LSgroups:
            g = user_group(row[1],row[0],row[4],row[5])
            self.config.groups.append(g)
            
        #Save the file and create the user tars
        try:
            self.config.save()
        except:
            self.PBprogress.set_text(_('WARNING: Errors in the fridge'))
        else:
            self.__make_tars()        
        
    def __make_tars(self):
        "Creates the tar files from home directories"
        
        #Get users to make tars
        fu = self.config.get_frozen_users(TAR_CREATE)
        
        #Delete the old tars
        dir = os.path.join (TAR_DIRECTORY, TAR_HOMES)
        recursive_delete(dir)
        
        try:   
            os.makedirs(dir,0755)
        except OSError, (errno, strerror):
            print_error(dir + " " + strerror,WARNING)
        
        #Start
        self.PBprogress.set_fraction(0.0)
        self.PBprogress.set_text(_("Starting"))
        
        #Disable options
        self.Bstop.set_sensitive(True)
        self.table.set_sensitive(False)
        self.TBtoolbar.set_sensitive(False)
        self.Hbuttons.set_sensitive(False)

        #Go,go,go! start creating tars with the tar_thread
        self.TTtar = tar_thread(fu,self)
        self.TTtar.start()
        
        return
    
    def __stop_tars(self, widget=None):
        "Stops creating tars"
        
        try:
            self.TTtar.kill()
        except:
            debug("No threads to kill",DEBUG_MEDIUM)
            
        #Reenable options
        self.Bstop.set_sensitive(False)
        self.table.set_sensitive(True)
        self.TBtoolbar.set_sensitive(True)
        self.Hbuttons.set_sensitive(True)
        self.PBprogress.set_text(_("WARNING: Stopped by the user"))
        
        
        
    def __init_form(self):
		"Initializes the form with the advanced config"

		self.table = gtk.Table()
		self.table.set_row_spacings(5)
		self.table.set_col_spacings(5)
		self.table.set_border_width(5)

		#Time of restoration
		label = gtk.Label(_("Restoration mode"))
		self.table.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)

		self.CBtime = gtk.combo_box_new_text()
		#self.CBtime.append_text(_("Manual"))
		self.CBtime.append_text(_("Every session (GDM only)"))
		self.CBtime.append_text(_("Every restart"))
		try:
			self.CBtime.set_tooltip_text(_("Every session (GDM only)")+_(": will restore the logged in user (through GDM)")+"\n"+
					_("Every restart")+_(": will restore all the users but not remote ones when the system starts"))
		except:
			pass


		self.CBtime.set_active(1)
		self.table.attach(self.CBtime, 1, 3, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)     

		separator = gtk.HSeparator()
		self.table.attach(separator, 0, 3, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)

		#By system, user o group freezing
		self.RBall = gtk.RadioButton(None, _("Freeze all the users"))
        
		try:
			self.RBall.set_tooltip_text(_("Freeze all the local users with the selected profile. It will restore the remote users also."))
		except:
			pass
		#SYSTEM
		self.RBall.connect("toggled",self.__RBall_toggled)
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
        
        #USERS
		self.RBusers = gtk.RadioButton(self.RBall, _("Freeze by user"))
		try:
			self.RBusers.set_tooltip_text(_("Freeze only the selected users with the selected profile"))
		except:
			pass
		self.RBusers.connect("toggled",self.__RBusers_toggled)
		self.table.attach(self.RBusers, 0, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.SHRINK)

		self.LSusers = gtk.ListStore(str,str,gtk.gdk.Pixbuf,str,int,bool)
			
		# Create the TreeView using liststore
		self.TVusers = gtk.TreeView(self.LSusers)
		self.TVusers.set_sensitive(False)
		self.TMusers = self.TVusers.get_model()
		self.TSusers = self.TVusers.get_selection()
		self.TSusers.set_mode(gtk.SELECTION_MULTIPLE)

		cell = gtk.CellRendererToggle()
		tv = gtk.TreeViewColumn(_("LDAP"),cell,active=5)
		self.TVusers.append_column(tv)
		tv.set_sort_column_id(0)

		#USER FIELDS
		cell = gtk.CellRendererText()
		tv = gtk.TreeViewColumn(_("User"),cell,text=0)
		self.TVusers.append_column(tv)
		tv.set_sort_column_id(1)

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
        
		try:
			cell.connect('changed', self.__Cuser_changed)
		except:
			cell.connect('edited', self.__Cuser_edit)
		cell.connect('editing-started', self.__Cuser_edited)

		self.TVusers.append_column(tv)

		# make treeview searchable
		self.TVusers.set_search_column(1)
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
		   
		self.Ball_users = gtk.Button(_("Apply all"))
		self.Ball_users.set_sensitive(False)
		self.Ball_users.connect("clicked", self.__Ball_users_clicked)
		self.table.attach(self.Ball_users, 1, 2, 6, 7, gtk.FILL, gtk.SHRINK)

		self.Bsel_users = gtk.Button(_("Apply selected"))
		self.Bsel_users.set_sensitive(False)
		self.Bsel_users.connect("clicked", self.__Bsel_users_clicked)
		self.table.attach(self.Bsel_users, 2, 3, 6, 7, gtk.FILL, gtk.SHRINK)

		#GROUPS
		self.RBgroups = gtk.RadioButton(self.RBall, _("Freeze by group"))
		try:
			self.RBgroups.set_tooltip_text(_("Freeze only the selected group of users with the selected profile.\nWARNING: If a user is included in two frozen groups you could have unexpedted results."))
		except:
			pass
		self.RBgroups.connect("toggled",self.__RBgroup_toggled)
		self.table.attach(self.RBgroups, 0, 3, 7, 8, gtk.EXPAND | gtk.FILL, gtk.SHRINK)

		self.LSgroups = gtk.ListStore(str,str,gtk.gdk.Pixbuf,str,int,bool)

		# create the TreeView using liststore
		self.TVgroups = gtk.TreeView(self.LSgroups)
		self.TVgroups.set_sensitive(False)
		self.TMgroups = self.TVgroups.get_model()
		self.TSgroups = self.TVgroups.get_selection()
		self.TSgroups.set_mode(gtk.SELECTION_MULTIPLE)
				
		cell = gtk.CellRendererToggle()
		tv = gtk.TreeViewColumn(_("LDAP"),cell,active=5)
		self.TVgroups.append_column(tv)
		tv.set_sort_column_id(0)

		#GROUP FIELDS
		cell = gtk.CellRendererText()
		tv = gtk.TreeViewColumn(_("Group"),cell,text=0)
		self.TVgroups.append_column(tv)
		tv.set_sort_column_id(1)

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

		try:
			cell.connect('changed', self.__Cgroup_changed)
		except:
			cell.connect('edited', self.__Cgroup_edit)
		cell.connect('editing-started', self.__Cgroup_edited)

		self.TVgroups.append_column(tv)

		# make treeview searchable
		self.TVgroups.set_search_column(1)

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
		   
		self.Ball_groups = gtk.Button(_("Apply all"))
		self.Ball_groups.set_sensitive(False)
		self.Ball_groups.connect("clicked", self.__Ball_groups_clicked)
		self.table.attach(self.Ball_groups, 1, 2, 10, 11, gtk.FILL, gtk.SHRINK)

		self.Bsel_groups = gtk.Button(_("Apply selected"))
		self.Bsel_groups.set_sensitive(False)
		self.Bsel_groups.connect("clicked", self.__Bsel_groups_clicked)
		self.table.attach(self.Bsel_groups, 2, 3, 10, 11, gtk.FILL, gtk.SHRINK) 

		self.mainBox.pack_start(self.table, True) 
    
    def __init_toolbar(self):
        "Inits the toolbar, huge by default"
        
        self.TBtoolbar = gtk.Toolbar()
        self.TBtoolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.TBtoolbar.set_style(gtk.TOOLBAR_BOTH)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[1])
        iconw.show()
        self.RTBall = gtk.RadioToolButton()
        self.RTBall.set_icon_widget(iconw)
        self.RTBall.set_label(_('Freeze All'))
        try:
            self.RTBall.set_tooltip_text(_("Freeze all the local and remote users and apply the changes. The users will be restored on log in"))
        except:
            pass
        self.RTBall.set_is_important(True)
        self.RTBall.set_expand(True)
        self.Sall = self.RTBall.connect("clicked",self.__set_freeze_all,1)
        self.RTBall.show()
        self.TBtoolbar.insert(self.RTBall,0)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[0])
        iconw.show()
        self.RTBnone = gtk.RadioToolButton(self.RTBall)
        self.RTBnone.set_icon_widget(iconw)
        self.RTBnone.set_label(_('Unfreeze All'))
        try:
            self.RTBnone.set_tooltip_text(_("Unfreeze all the local and remote users and apply the changes"))
        except:
            pass
        self.RTBnone.set_is_important(True)
        self.RTBnone.set_expand(True)
        self.Snone = self.RTBnone.connect("clicked",self.__set_freeze_all,0)
        self.RTBnone.show()
        self.TBtoolbar.insert(self.RTBnone,1)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[2])
        iconw.show()
        self.RTBadvanced = gtk.RadioToolButton(self.RTBall)
        self.RTBadvanced.set_icon_widget(iconw)
        self.RTBadvanced.set_label(_('Advanced'))
        try:
            self.RTBadvanced.set_tooltip_text(_('Select advance parameters to freeze the users'))
        except:
            pass
        self.RTBadvanced.set_is_important(True)
        self.RTBadvanced.set_expand(True)
        self.Sadv = self.RTBadvanced.connect("clicked",self.__set_freeze_all,2)
        self.RTBadvanced.show()
        self.TBtoolbar.insert(self.RTBadvanced,2)
        
        self.STIsep = gtk.SeparatorToolItem()
        self.STIsep.show()
        self.TBtoolbar.insert(self.STIsep,3)
        
        self.RTBsettings = gtk.ToolButton(gtk.STOCK_EDIT)
        self.RTBsettings.set_label(_('Settings'))
        try:
            self.RTBsettings.set_tooltip_text(_('Shows the settings window'))
        except:
            pass
        self.RTBsettings.set_is_important(True)
        self.RTBsettings.connect("clicked",self.__show_settings)
        self.TBtoolbar.insert(self.RTBsettings,4)
        
        self.TBtoolbar.show()
        
        self.mainBox.pack_start(self.TBtoolbar, False)
        
        #self.mainBox.child_set_property(self.TBtoolbar,"expand",True)
    
    def __RBall_toggled(self, widget, data=None):
        "Advanced All radio button toggled"
        self.CBall.set_sensitive(widget.get_active())
        
    def __RBusers_toggled(self, widget, data=None):
        "Advanced Users radio button toggled"
        self.TVusers.set_sensitive(widget.get_active())
        self.Ball_users.set_sensitive(widget.get_active())
        self.Bsel_users.set_sensitive(widget.get_active())
        self.CBusers.set_sensitive(widget.get_active())
    
    def __RBgroup_toggled(self, widget, data=None):
        "Advanced Groups radio button toggled"
        self.TVgroups.set_sensitive(widget.get_active())
        self.Ball_groups.set_sensitive(widget.get_active())
        self.Bsel_groups.set_sensitive(widget.get_active())
        self.CBgroups.set_sensitive(widget.get_active())
        
    def __Ball_users_clicked(self, widget=None, data=None):
        "Applies selected config to all users"
        self.TMusers.foreach(self.__set_state, self.CBusers.get_active())
        
    def __Ball_groups_clicked(self, widget=None, data=None):
        "Applies selected config to all groups"
        self.TMgroups.foreach(self.__set_state, self.CBgroups.get_active())
        
    def __Bsel_users_clicked(self, widget=None, data=None):
        "Applies selected config to selected users"
        self.TSusers.selected_foreach(self.__set_state, self.CBusers.get_active())
        
    def __Bsel_groups_clicked(self, widget=None, data=None):
        "Applies selected config to selected groups"
        self.TSgroups.selected_foreach(self.__set_state, self.CBgroups.get_active())
        
    def __LS_add(self,name):
        "Adds a frozen profile to LSfreese_settings"
        
        #where it goes?
        index = len(self.LSfreeze_settings)
        
        icon = gtk.Image()
        
        #Add the corresponding icon
        if index == 0:
            icon.set_from_file(SMALL_ICONS[FREEZE_NONE])
        elif index > 0 and index < 3:
            icon.set_from_file(SMALL_ICONS[FREEZE_ALL])
        else:
            icon.set_from_file(SMALL_ICONS[FREEZE_ADV])
        
        #Add it to ListStore
        self.LSfreeze_settings.append([icon.get_pixbuf(),name])
    
    def __Cuser_changed(self, cell, path, iter):
        "User state cell changed"
        
        state = cell.get_property("model").get_path(iter)[0]
        self.__set_state(self.TMusers,path,None,state)
        for user in self.config.users:
           if str(self.TMusers[path][1]) == str(user.id):
               user.profile = state
               break
           
    def __Cuser_edit(self, cell, path, text):    
        "User state cell edited"
        
        state = self.__get_state(cell,text)
        if state == None:
            return
        
        self.__set_state(self.TMusers,path,None,state)
        for user in self.config.users:
           if str(self.TMusers[path][1]) == str(user.id):
               user.profile = state
               break
           
    def __Cuser_edited(self, cell, editable, path):
        "User state cell changed, but is LDAP"

        if self.TMusers[path][4] == FREEZE_LDAP:
            editable.set_model()
            
    def __Cgroup_changed(self, cell, path, iter):
        "Group state cell changed"
        
        state = cell.get_property("model").get_path(iter)[0]
        self.__set_state(self.TMgroups,path,None,state)
        for group in self.config.groups:
            if str(self.TMgroups[path][1]) == str(group.id):
                group.profile = state
                break
            
    def __Cgroup_edit(self, cell, path, text):    
        "Group state cell edited"
        
        state = self.__get_state(cell,text)
        if state == None:
            return
        
        self.__set_state(self.TMgroups,path,None,state)
        for group in self.config.groups:
            if str(self.TMgroups[path][1]) == str(group.id):
                group.profile = state
                break
        
    def __Cgroup_edited(self, cell, editable, path):
        "Group state cell changed, but is LDAP"
        if self.TMgroups[path][4] == FREEZE_LDAP:
            editable.set_model()
         
    def __get_state(self,cell,text):
        
        model = cell.get_property("model")
        iter = model.get_iter_first()
        while iter != None :
            state = model.get_path(iter)[0]
            if self.LSfreeze_settings[state][1] == text:
                return state
            iter = model.iter_next(iter)
        return None
    
    def __set_state(self, model, path, iter, state):
        "Sets selected state to the selected row"
        #If not LDAP...
        if model[path][4] == FREEZE_LDAP:
            return
        model[path][2] = self.LSfreeze_settings[state][0]
        model[path][3] = self.LSfreeze_settings[state][1]
        model[path][4] = state
    
    def __set_freeze_all(self, widget = None, data = 0, save = True):
        "Set the kind of toolbar to show and save config if needed"
        
        if widget == None or widget.get_active():
            
            self.window.set_icon_from_file(NORMAL_ICONS[data])
                        
            show = self.RTBadvanced.get_active()
            self.table.set_sensitive(show)
            self.window.set_property("resizable",show)
            
            self.PBprogress.set_fraction(0.0)
            
            if data == FREEZE_NONE:
                self.PBprogress.set_text(_("System unfrozen"))
                self.CBall.set_active(FREEZE_NONE)
                self.CBtime.set_active(TIME_SESSION)
                self.RBall.set_active(True)
            elif data == FREEZE_ALL:
                self.PBprogress.set_text(_("System frozen"))
                self.CBall.set_active(FREEZE_ALL)
                self.CBtime.set_active(TIME_SESSION)
                self.RBall.set_active(True)
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
                self.STIsep.show()
                
                self.TBtoolbar.set_size_request(500,-1)
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
                self.STIsep.hide()
                
                self.TBtoolbar.set_size_request(425,-1)
                self.TBtoolbar.set_style(gtk.TOOLBAR_BOTH)
                
                if save:
                    #Save file
                    self.__save_config()
                    
    def __set_enabled_to_load(self,enable):
        "Set if is enabled to load config or not, connecting and disconnecting from interface"
        if enable:
            self.Sall = self.RTBall.connect("clicked",self.__set_freeze_all,1)
            self.Snone = self.RTBnone.connect("clicked",self.__set_freeze_all,0)
            self.Sadv = self.RTBadvanced.connect("clicked",self.__set_freeze_all,2)
        else:
            self.RTBall.disconnect(self.Sall)
            self.RTBnone.disconnect(self.Snone)
            self.RTBadvanced.disconnect(self.Sadv)
