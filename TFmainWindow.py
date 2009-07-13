from TFglobals import *
from TFconfigWindow import *
from TFconfig import *
from TFtar_thread import *

import pygtk
pygtk.require('2.0')
import gtk

import pwd, grp

import ldap

from xml.dom import minidom

from datetime import datetime

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext


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

class mainWindow:

    def __init__(self):
        
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
        self.Brestore.connect("clicked", self.load_config)
        self.Hbuttons.pack_start(self.Brestore, True)
        
        but = gtk.Button(_("Quit"),gtk.STOCK_QUIT)
        but.connect("clicked",self.close,0)
        but.show()
        self.Hbuttons.pack_start(but, True)
        
        self.mainBox.pack_start(self.Hbuttons, False)
        
        self.sources_to_erase = []
        
        self.load_config()
        
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

    def load_config(self, widget=None):
        
        self.set_enabled_to_load(False)
        
        j = self.configW.tabs.get_n_pages()
        for i in range(j):
            self.configW.tabs.remove_page(0)
            self.LSfreeze_settings.remove(self.LSfreeze_settings.get_iter(0))
        
        self.configW.LSsources.clear()
        
        cfg = config()
        
        sources = self.configW.LSsources
        for source in cfg.sources:
            sources.append([source.name,source.file])
        
        for profile in cfg.profiles:
            newTab = self.configW.add_tab(data = profile.title)
            newTab.set_sensitive(profile.edited)
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
        
        self.CBtime.set_active(cfg.time)
        
        self.RBall.set_active(cfg.option == OPTION_ALL)
        self.RBusers.set_active(cfg.option == OPTION_USERS)
        self.RBgroups.set_active(cfg.option == OPTION_GROUPS)
        self.CBall.set_active(cfg.all)
            
        #ACTIVATE THE TOOLBAR BUTTON
        if(cfg.option == OPTION_ALL):
            if (cfg.all == FREEZE_NONE):
                self.RTBnone.set_active(True)
                self.set_freeze_all(data = FREEZE_NONE, save = False)
            elif (cfg.all == FREEZE_ALL and time == TIME_SESSION):
                self.RTBall.set_active(True)
                self.set_freeze_all(data = FREEZE_ALL, save = False)
            else:
                self.RTBadvanced.set_active(True)
                self.set_freeze_all(data = FREEZE_ADV, save = False)
        else:
            self.RTBadvanced.set_active(True)
            self.set_freeze_all(data = FREEZE_ADV, save = False)
            
        for user in cfg.users:
            for path, row in enumerate(self.LSusers):
                if row[1] == user.id:
                    self.set_state(self.TMusers, path, None, user.profile)
        
        for group in cfg.groups:
            for path, row in enumerate(self.LSgroups):
                if row[1] == group.id:
                    self.set_state(self.TMgroups, path, None, group.profile)

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
            
            xexclude = xdoc.createElement("rules")
              
            for row in tab.LSfilter:
                xchild = xdoc.createElement("rule")
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
            #TODO: treure warning
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
        
        tars = config().get_frozen_users()
        
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
                self.LSusers.append([user.pw_name,user.pw_uid,icon.get_pixbuf(),_("Total Unfrozen"),FREEZE_NONE,False])
                
        #TODO: ldap
        try:
            con = ldap.initialize(ldap_host)
            filter = '(objectclass=posixAccount)'
            attrs = ['uid','homeDirectory','gidNumber','uidNumber']
         
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            for person in result:
                usern = person[1]['uid'][0]
                gid = person[1]['gidNumber'][0]
                home = person[1]['homeDirectory'][0]
                uid = person[1]['uidNumber'][0]
                #if uid >= minUID and uid < maxUID:
                self.LSusers.append([usern,uid,icon.get_pixbuf(),_("Total Unfrozen"),FREEZE_NONE,True])
                    
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


        cell = gtk.CellRendererToggle()
        tv = gtk.TreeViewColumn(_("LDAP"),cell,active=5)
        self.TVusers.append_column(tv)
        tv.set_sort_column_id(0)
        
        # Camps d'usuari
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
        
        cell.connect('changed', self.Cuser_changed)
        
        self.TVusers.append_column(tv)
        tv.set_sort_column_id(2)
        
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
        self.Ball_users.connect("clicked", self.Ball_users_clicked)
        self.table.attach(self.Ball_users, 1, 2, 6, 7, gtk.FILL, gtk.SHRINK)
        
        self.Bsel_users = gtk.Button(_("Apply selected"))
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
                self.LSgroups.append([group.gr_name,group.gr_gid,icon.get_pixbuf(),_("Total Unfrozen"),FREEZE_NONE,False])

                        
        #TODO: ldap
        try:
            con = ldap.initialize(ldap_host)
            filter = '(objectclass=posixGroup)'
            attrs = ['cn','gidNumber']
         
            result = con.search_s(ldap_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            print len(result)
            for person in result:
                groupn = person[1]['cn'][0]
                gid = person[1]['gidNumber'][0]
                #if gid >= minUID and gid < maxUID:
                self.LSgroups.append([groupn,gid,icon.get_pixbuf(),_("Total Unfrozen"),FREEZE_NONE,True])
                    
        except ldap.LDAPError, e:
            print e
            exit

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
        
        # Camps de grup
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
        
        cell.connect('changed', self.Cgroup_changed)
        
        self.TVgroups.append_column(tv)
        tv.set_sort_column_id(2)
        
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
        self.Ball_groups.connect("clicked", self.Ball_groups_clicked)
        self.table.attach(self.Ball_groups, 1, 2, 10, 11, gtk.FILL, gtk.SHRINK)
        
        self.Bsel_groups = gtk.Button(_("Apply selected"))
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
        self.RTBsettings.set_label(_('Settings'))
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