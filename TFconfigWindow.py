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
from TFprofileTab import *
from TFconfig import *
import gtk

import paramiko, binascii

import os
import pwd

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
        
        self.sources_to_erase = []
        
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
        item.set_label(_('Remote users'))
        item.set_tooltip_text(_('Configure Remote users'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_remote)
        toolbar.insert(item,2)
        
        item = gtk.RadioToolButton(item,gtk.STOCK_ABOUT)
        item.set_label(_('About'))
        item.set_tooltip_text(_('About Trivial Freezer'))
        item.set_is_important(True)
        item.connect("toggled",self.show_hide_about)
        toolbar.insert(item,3)
        
        toolbar.show_all()
        
        mainBox.pack_start(toolbar, False)
        
        self.init_profiles()
        mainBox.pack_start(self.profiles, True)
        self.profiles.show_all()
        
        self.init_sources()
        mainBox.pack_start(self.sources, True)
        
        self.init_remote()
        mainBox.pack_start(self.remote, True)
        
        self.init_about()
        mainBox.pack_start(self.about, True)
        
        self.load(config)
        
        self.get_content_area().add(mainBox)
        mainBox.show()
        self.show()
    
    def init_profiles(self):
        self.profiles = gtk.VBox()
        self.profiles.set_spacing(5)
        self.profiles.set_border_width(5)
        
        label = gtk.Label("<b>"+_("Freeze profiles")+"</b>")
        label.set_use_markup(True)
        self.profiles.pack_start(label,False)
        
        #ToolBar
        toolbar = gtk.HBox()
        
        item = gtk.Button(_('Add profile'), gtk.STOCK_ADD)
        item.set_tooltip_text(_('Adds a new Frozen Profile'))
        item.connect("clicked",self.add_tab)
        toolbar.pack_start(item)
        
        item = gtk.Button(_('Remove profile'), gtk.STOCK_REMOVE)
        item.set_tooltip_text(_('Removes the selected Frozen Profile'))
        item.connect("clicked",self.remove_tab)
        toolbar.pack_start(item)
        
        self.profiles.pack_start(toolbar, False)
        
        #ListStore of the actions in the profiles
        self.LSactions = gtk.ListStore(str,str,int)
        self.LSactions.append([gtk.STOCK_REVERT_TO_SAVED,_("Restore (Frozen)"), ACTION_RESTORE])
        self.LSactions.append([gtk.STOCK_STOP,_("Keep (Unfrozen)"),ACTION_KEEP])
        self.LSactions.append([gtk.STOCK_DELETE,_("Erase"),ACTION_ERASE])
        self.LSactions.append([gtk.STOCK_FIND,_("Move to Lost+Found"),ACTION_LOST])
        
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
        
    def init_remote(self):
        
        self.remote = gtk.Table()
        self.remote.set_row_spacings(5)
        self.remote.set_col_spacings(5)
        self.remote.set_border_width(5)
        
        label = gtk.Label("<b>"+_("Remote users configuration")+"</b>")
        label.set_use_markup(True)
        self.remote.attach(label, 0, 3, 0, 1, gtk.FILL, gtk.FILL)
        
        self.CBldapenable = gtk.CheckButton(_("Enable LDAP support"))
        self.CBldapenable.connect("toggled",self.CBldapenable_toggled)
        self.remote.attach(self.CBldapenable, 0, 3, 1, 2, gtk.FILL, gtk.SHRINK)
        
        label = gtk.Label(_("LDAP Server"))
        self.remote.attach(label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
        
        self.Eserver = gtk.Entry()
        self.Eserver.set_sensitive(False)
        self.remote.attach(self.Eserver, 1, 3, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        label = gtk.Label(_("Distinguished Name (dn)"))
        self.remote.attach(label, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
        
        self.Edn = gtk.Entry()
        self.Edn.set_sensitive(False)
        self.remote.attach(self.Edn, 1, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CONNECT,gtk.ICON_SIZE_BUTTON)
        self.Btest = gtk.Button(_("Test connection"))
        self.Btest.set_image(image)
        self.Btest.connect("clicked", self.test_ldap)
        self.Btest.set_sensitive(False)
        self.remote.attach(self.Btest, 0, 3, 4, 5, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        self.Ltest = gtk.Label()
        self.Ltest.set_use_markup(True)
        self.Ltest.set_sensitive(False)
        self.remote.attach(self.Ltest, 0, 3, 5, 6, gtk.FILL, gtk.FILL)
        
        label = gtk.Label("<b>"+_("Remote homes")+"</b>")
        label.set_use_markup(True)
        self.remote.attach(label, 0, 3, 6, 7, gtk.FILL, gtk.FILL)
        
        self.RBclient = gtk.RadioButton(None,_("Work as a client"))
        self.RBclient.set_sensitive(False)
        self.RBclient.connect("toggled",self.RBclient_toggled)
        self.remote.attach(self.RBclient, 0, 3, 7, 8, gtk.FILL, gtk.FILL)
        
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_DIALOG_AUTHENTICATION,gtk.ICON_SIZE_BUTTON)
        self.Bkeys = gtk.Button(_("Generate authorization keys"))
        self.Bkeys.set_image(image)
        self.Bkeys.connect("clicked", self.generate_keys)
        self.Bkeys.set_sensitive(False)
        self.remote.attach(self.Bkeys, 0, 3, 9, 10, gtk.EXPAND | gtk.FILL, gtk.FILL)
        
        self.Lkeys = gtk.Label()
        self.Lkeys.set_use_markup(True)
        self.Lkeys.set_sensitive(False)
        self.remote.attach(self.Lkeys, 0, 3, 10, 11, gtk.FILL, gtk.FILL)
        
        self.RBserver = gtk.RadioButton(self.RBclient,_("Work as a server"))
        self.RBserver.set_sensitive(False)
        self.remote.attach(self.RBserver, 0, 3, 11, 12, gtk.FILL, gtk.FILL)
    
    def init_about(self):
        
        self.about = gtk.Table()
        self.about.set_row_spacings(5)
        self.about.set_col_spacings(5)
        self.about.set_border_width(5)
        
        label = gtk.Label("<b>"+_("About Trivial Freezer")+"</b>")
        label.set_use_markup(True)
        self.about.attach(label, 0, 3, 0, 1, gtk.EXPAND |gtk.FILL, gtk.FILL)
        
        iconw = gtk.Image() # icon widget
        iconw.set_from_file(HUGE_ICONS[1])
        iconw.show()
        self.about.attach(iconw, 0, 1, 1, 2, gtk.FILL, gtk.EXPAND |gtk.FILL)
        
        text = "<b>Trivial Freezer</b>\n"
        text += _("Version") + ": " + VERSION + "\n\n"
        text += "<b>"+_("Author")+":</b>\n"
        text += "Pau Ferrer Ocaña\n\n"
        text += "<b>"+_("Special greetings")+":</b>\n"
        text += "Carlos Álvarez Martínez\n"
        text += "Joan de Gràcia\n\n"
        text += "<b>"+_("With the support of ")+":</b>\n"
        text += "Departament d'Educació. Generalitat de Catalunya\n\n"
        text += "License: GPL v3\n\n"
        text += "Trivial Freezer is free software:\n"
        text += "you can redistribute it and/or\n"
        text += "modify it under the terms of the\n"
        text += "GNU General Public License as\n"
        text += "published by the Free Software\n"
        text += "Foundation, either version 3 of\n"
        text += "the License, or (at your option)\n"
        text += "any later version.\n\n"
        text += "Copyright (C) 2009  Pau Ferrer Ocaña"
        
        
        label = gtk.Label(text)
        label.set_use_markup(True)
        self.about.attach(label, 1, 2, 1, 2, gtk.FILL, gtk.FILL)

    
    def load(self, config):
        
        for source in config.sources:
            self.LSsources.append([source.name,source.file])
            
        for profile in config.profiles:
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
                    self.LSactions[rule.action][0],
                    self.LSactions[rule.action][1],
                    rule.action])
                
        self.CBldapenable.set_active(config.ldap_enabled)
        self.Eserver.set_text(config.ldap_server)
        self.Edn.set_text(config.ldap_dn)
        
        self.RBserver.set_active(config.home_server)
        self.hostname = config.home_server_ip
        self.port = config.home_server_port
        
        self.test_home_server()
        
        return
    
    def update_config(self, config):
        del config.profiles[:]
        
        config.load_profile_defaults()
        
        numProfiles = self.tabs.get_n_pages()
        for i in range(numProfiles - BLOCKED_PROFILES):
            tab = self.tabs.get_nth_page(i + BLOCKED_PROFILES)
            config.profiles.append(tab.get_config())
            
        del config.sources[:]
        
        for row in self.LSsources:
            s = source()
            s.name = row[0]
            s.file = row[1]
            config.sources.append(s)
            
        config.sources_to_erase.extend(self.sources_to_erase)
            
        config.ldap_dn = self.Edn.get_text()
        config.ldap_server = self.Eserver.get_text()
        
        config.ldap_enabled = self.CBldapenable.get_active() and self.test_ldap()
        
        config.home_server = self.RBserver.get_active()
        config.home_server_ip = self.hostname
        config.home_server_port = self.port
            
            
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
    
    def show_hide_remote(self,widget):
        if widget.get_active():
            self.remote.show_all()
        else:
            self.remote.hide_all()
            
    def show_hide_about(self,widget):
        if widget.get_active():
            self.about.show_all()
        else:
            self.about.hide_all()
    
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
                warning = gtk.MessageDialog(parent=self,
                                      type=gtk.MESSAGE_WARNING,
                                      buttons=gtk.BUTTONS_OK,
                                      message_format= _("The freezer is unable to create the tar file")
                                      )
                res = warning.run()
                warning.destroy()
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
                warning = gtk.MessageDialog(parent=self,
                                      type=gtk.MESSAGE_WARNING,
                                      buttons=gtk.BUTTONS_OK,
                                      message_format= _("The selected file is unreadable or malformed")
                                      )
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
            
            tabs_in_use = []
            for i in range(self.tabs.get_n_pages()):
                tab = self.tabs.get_nth_page(i)
                if tab.is_source_in_use(path):
                    tabs_in_use.append(i)
            
            if len(tabs_in_use) > 0:
                d = gtk.MessageDialog(parent=self,
                                      type=gtk.MESSAGE_QUESTION,
                                      buttons=gtk.BUTTONS_YES_NO,
                                      message_format= _("This source is in use in some profiles, do you want to continue?")
                                      )
                response = d.run()
                if response == gtk.RESPONSE_YES:
                    #WARN because is in use
                    #mark to erase
                    self.sources_to_erase.append(file)
                    
                    for i in tabs_in_use:
                        tab = self.tabs.get_nth_page(i)
                        tab.set_source("")
                    
                    self.LSsources.remove(iter)
                d.destroy()
                
            else:
                #mark to erase
                self.sources_to_erase.append(file)
                self.LSsources.remove(iter)
            
    def CBldapenable_toggled(self, widget):
        self.Eserver.set_sensitive(widget.get_active())
        self.Edn.set_sensitive(widget.get_active())
        self.Ltest.set_sensitive(widget.get_active())
        self.Btest.set_sensitive(widget.get_active())
        self.RBclient.set_sensitive(widget.get_active())
        self.RBserver.set_sensitive(widget.get_active())
        self.Lkeys.set_sensitive(widget.get_active() and self.RBclient.get_active())
        self.Bkeys.set_sensitive(widget.get_active() and self.RBclient.get_active()) 
    
    def RBclient_toggled(self, widget):
        self.Lkeys.set_sensitive(widget.get_active())
        self.Bkeys.set_sensitive(widget.get_active())  
        
    def test_ldap(self, widget=None):
        try:
            con = ldap.initialize(self.Eserver.get_text())
            filter = '(objectclass=posixAccount)'
            attrs = ['uid']
         
            result = con.search_s(self.Edn.get_text(), ldap.SCOPE_SUBTREE, filter, attrs)
            self.Ltest.set_markup('<span foreground="#007700" size="large">' + _("Connection successfully established")+ '</span>')
            return True
        except ldap.LDAPError, e:
            self.Ltest.set_markup('<span foreground="#770000" size="large">' + _("Connection failed")+ '</span>')
            return False
    
    def test_home_server(self):
        #TODO
        roothome = pwd.getpwuid(0).pw_dir
        
        try:
            pkey = paramiko.DSSKey.from_private_key_file(roothome + '/' + ID_DSA_PATH,"")
            ssh = paramiko.SSHClient()
            try:
                ssh.load_system_host_keys(roothome + '/' + KNOWN_HOSTS_PATH)
            except:
                pass
            ssh.connect(self.hostname,int(self.port),pkey=pkey)
        except:
            self.Lkeys.set_markup('<span foreground="#770000" size="large">' + _("Client not connected") + '</span>')
            self.key = False
            return False
        ssh.close()
        self.key = True
        self.Lkeys.set_markup('<span foreground="#007700" size="large">' + _("Client connected to ") + self.hostname + '</span>')
        return True
    
    def generate_keys(self, widget=None):
        #TODO
        if self.key == True:
            warning = gtk.MessageDialog(parent=self,type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_YES_NO)
            warning.set_markup(_("The keys already exists, do you want to overwrite them?"))
            warning.show_all()
            response = warning.run()

            if response == gtk.RESPONSE_NO:
                warning.destroy()
                return
            warning.destroy()
        
        roothome = pwd.getpwuid(0).pw_dir
        #Private Key generation
        id_dsa = roothome + '/' + ID_DSA_PATH
        try:
            dss = paramiko.DSSKey.generate()
            dss.write_private_key_file(id_dsa,"")
        except:
            self.Lkeys.set_markup('<span foreground="#770000" size="large">' + _("Error creating private key.")+ "<br/>" + _("Client not connected")+ '</span>')
            return
        
        #Public Key generation
        id_dsa_pub = id_dsa + '.pub'
        from socket import gethostname;
        public_key = "ssh-dss " + binascii.b2a_base64(dss.__str__())[:-1] + " root@"+gethostname()+"\n"
        try:
            file = open(id_dsa_pub ,"w")
            file.write(public_key)
            file.close()
        except:
            self.Lkeys.set_markup('<span foreground="#770000" size="large">' + _("Error creating public key.")+ "<br/>" + _("Client not connected")+ '</span>')
            return    
    
        ##OLD MANNER
        #debug ('EXECUTING: ssh-keygen -t dsa -P "" -N "" -f ' + id_dsa,DEBUG_LOW)
        #os.popen('ssh-keygen -t dsa -P "" -N "" -f ' + id_dsa).read()
        
        ssh = paramiko.SSHClient()
        
        get_connect = False
        get_info = False
        while not get_connect:
            if not get_info:
                dialog = gtk.Dialog(title=_("Configure the server"), parent=self, flags=0, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                                  gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                
                table = gtk.Table()
                table.set_row_spacings(5)
                table.set_col_spacings(5)
                table.set_border_width(5)
                
                label = gtk.Label(_("Server hostname"))
                table.attach(label, 0, 1, 0, 1, gtk.FILL, gtk.FILL)
                
                Ehostname = gtk.Entry()
                Ehostname.set_text(self.hostname)
                table.attach(Ehostname, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL)
                
                label = gtk.Label(_("Port"))
                table.attach(label, 0, 1, 1, 2, gtk.FILL, gtk.FILL)
                
                Eport = gtk.Entry()
                Eport.set_text(str(self.port))
                table.attach(Eport, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL)
                
                label = gtk.Label(_("Username"))
                table.attach(label, 0, 1, 2, 3, gtk.FILL, gtk.FILL)
                
                Euser = gtk.Entry()
                table.attach(Euser, 1, 2, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL)
                
                label = gtk.Label(_("Password"))
                table.attach(label, 0, 1, 3, 4, gtk.FILL, gtk.FILL)
                
                Epasswd = gtk.Entry()
                Epasswd.set_visibility(False)
                table.attach(Epasswd, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL)
                
                dialog.vbox.pack_start(table, True)
                
                dialog.vbox.show_all()
                
                response = dialog.run()
    
                if response == gtk.RESPONSE_ACCEPT:
                    user = Euser.get_text()
                    passwd = Epasswd.get_text()
                    hostname = Ehostname.get_text()
                    port = Eport.get_text()
                else:
                    dialog.destroy()
                    return
                dialog.destroy()
            
            try:
                ssh.load_system_host_keys(roothome + '/' + KNOWN_HOSTS_PATH)
            except:
                pass
            
            try:
                ssh.connect(hostname,int(port),user,passwd)
            except paramiko.AuthenticationException,e :
                debug("AuthenticationException "+str(e), DEBUG_LOW)
                warning = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_WARNING,buttons=gtk.BUTTONS_OK)
                warning.set_markup(_("Permission denied, please verify the username and password."))
                warning.show_all()
                response = warning.run()
                warning.destroy()
                get_info = False
                get_connect = False
            except (paramiko.BadHostKeyException, paramiko.SSHException), e:
                get_info = True
                get_connect = False
                debug("SSHException or BadHostKeyException "+str(e), DEBUG_LOW)
                hosts = ssh.get_host_keys()
                t = ssh.get_transport()
                key = t.get_remote_server_key() 
                if not hosts.check(hostname,key):
                    warning = gtk.MessageDialog(parent=self,type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_YES_NO)
                    fingerprinthex = paramiko.util.hexify(key.get_fingerprint())
                    fingerprint = ""
                    for i, v in enumerate(fingerprinthex):
                        fingerprint += v
                        if i%2 == 1 and i+1 < len(fingerprinthex):
                            fingerprint += ":"
                        
                    warning.set_markup(_("The authenticity of host '"+hostname+"' can't be established. "+key.get_name()+" key fingerprint is "+fingerprint+"."))
                    warning.show_all()
                    response = warning.run()
        
                    if response == gtk.RESPONSE_YES:
                        try:
                            hosts.add(hostname, key.get_name(), key)
                            hosts.save(roothome + '/' + KNOWN_HOSTS_PATH)
                        except:
                            debug("Can't write in the known_hosts file.", DEBUG_LOW)
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    else:
                        warning.destroy()
                        return
                    warning.destroy()
            else:
                get_connect = True

        try:
            #Send the public key to the server
            sftp = ssh.open_sftp()
            sftp.put(id_dsa_pub,"/tmp/tfpubkey")
            sftp.close()
        except:
            ssh.close()
            self.Lkeys.set_markup('<span foreground="#770000" size="large">' + _("Errors connecting to SFTP server.")+ "<br/>" + _("Client not connected")+ '</span>')
            return
        
        try:
            stdin,stdout,stderr = ssh.exec_command("echo '#!/bin/bash\n cat /tmp/tfpubkey >> ~root/.ssh/authorized_keys\n rm -f /tmp/tfpubkey*' > /tmp/tfpubkey.sh")
            stdin,stdout,stderr = ssh.exec_command("chmod +x /tmp/tfpubkey.sh")
            stdin,stdout,stderr = ssh.exec_command("sudo /tmp/tfpubkey.sh")
            stdin.write(passwd+'\n')
            stdin.flush()
            self.Lkeys.set_markup('<span foreground="#007700" size="large">' + _("Client connected to ") + hostname + '</span>')
            self.hostname = hostname
            self.port = port
            self.key = True
        except:
            ssh.close()
            self.Lkeys.set_markup('<span foreground="#770000" size="large">' + _("Something executing commands goes wrong.")+ "<br/>" + _("Client not connected")+ '</span>')
            return
        
        ssh.close()
        
        return
        