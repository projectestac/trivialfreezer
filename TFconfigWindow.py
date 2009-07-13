from TFglobals import *
from TFprofileTab import *
import gtk

import os

import gettext
gettext.bindtextdomain('tfreezer', './locale')
gettext.textdomain('tfreezer')
_ = gettext.gettext

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

    #TO ERASE
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
        
