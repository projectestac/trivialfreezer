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

import pygtk
pygtk.require( '2.0' )
import gtk

import paramiko, binascii

import os, shutil
import pwd

import tarfile

_ = load_locale()

def copy( src, dst ):
    "Copies a file to a directory without overwritting them"

    auxPath = 0
    #Take the filename and the extension
    fileName = os.path.basename( src )
    ( file, extension ) = fileName.split( ".", 1 )

    #Destination
    dstComplete = os.path.join ( dst, fileName )
    #If it exists, appends a number 
    while os.path.exists( dstComplete ):
        fileName = file + "_" + str( auxPath ) + "." + extension
        dstComplete = os.path.join ( dst, fileName )
        auxPath = auxPath + 1

    #When decided the destination, copy it
    shutil.copy( src, dstComplete )
    return fileName

class configWindow( gtk.Dialog ):
    "Config window class"

    #Sources to erase when applying the form
    sources_to_erase = []
    #Profiles to erase
    profiles_to_erase = []
    #Tab to config the profiles
    profiles = None
    #Tab to config the sources
    sources = None
    #Tab to config the server and remote tasks
    remote = None
    #Tab to config the about
    about = None

    #ListStore of the actions in the profiles
    LSactions = None
    #Profile tabs
    tabs = None

    #ListStore with the sources of the repository
    LSsources = None
    #Treeview for the sources of the repository
    TVsources = None
    #TreeModel from the sources of the repository
    TMsources = None

    #ComboBox to enable/disable the LDAP support
    CBldapenable = None
    #Server path
    Eserver = None
    #Distinguished name of the server
    Edn = None
    #Button to test the server
    Btest = None
    #Label with the result of the test
    Ltest = None
    #RadioButton, works as a client?
    RBclient = None
    #Button to adquire the key
    Bkeys = None
    #Label with the result of the adquisition
    Lkeys = None
    #RadioButton, works as a server?
    RBserver = None

    #Connecting info
    #Host,user and port
    hostname = ""
    port = ""
    server_user = ""

    #Has key?
    key = False

    def __init__( self, config, win ):
        "Inits all the window"

        #This window is treated as a dialog
        gtk.Dialog.__init__( self, title = "Trivial Freezer" + _( " - Settings" ),
                                 parent = win,
                                 flags = 0,
                                 buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                          gtk.STOCK_OK, gtk.RESPONSE_ACCEPT ) )
        self.set_icon_from_file( NORMAL_ICONS[FREEZE_ADV] )

        self.sources_to_erase = []
        self.profiles_to_erase = []

        mainBox = gtk.HBox()

        #Toolbar buttons on the left
        toolbar = gtk.Toolbar()
        toolbar.set_orientation( gtk.ORIENTATION_VERTICAL )
        toolbar.set_style( gtk.TOOLBAR_BOTH )

        item = gtk.RadioToolButton( None, gtk.STOCK_SELECT_COLOR )
        item.set_label( _( 'Profiles' ) )
        try:
            item.set_tooltip_text( _( 'Configure profiles' ) )
        except:
            pass
        item.set_is_important( True )
        item.connect( "toggled", self.__show_hide_profiles )
        toolbar.insert( item, 0 )

        item = gtk.RadioToolButton( item, gtk.STOCK_COLOR_PICKER )
        item.set_label( _( 'Sources' ) )
        try:
            item.set_tooltip_text( _( 'Configure sources' ) )
        except:
            pass
        item.set_is_important( True )
        item.connect( "toggled", self.__show_hide_sources )
        toolbar.insert( item, 1 )

        item = gtk.RadioToolButton( item, gtk.STOCK_CONNECT )
        item.set_label( _( 'Remote users' ) )
        try:
            item.set_tooltip_text( _( 'Configure Remote users' ) )
        except:
            pass
        item.set_is_important( True )
        item.connect( "toggled", self.__show_hide_remote )
        toolbar.insert( item, 2 )

        sep = gtk.ToolItem()
        sep.set_expand( True )
        toolbar.insert( sep, 3 )

        item = gtk.RadioToolButton( item, gtk.STOCK_ABOUT )
        item.set_label( _( 'About' ) )
        try:
            item.set_tooltip_text( _( 'About Trivial Freezer' ) )
        except:
            pass
        item.set_is_important( True )
        item.connect( "toggled", self.__show_hide_about )
        toolbar.insert( item, 4 )

        toolbar.show_all()

        mainBox.pack_start( toolbar, False )

        #Init all the "tabs"
        self.__init_profiles()
        mainBox.pack_start( self.profiles, True )
        self.profiles.show_all()

        self.__init_sources()
        mainBox.pack_start( self.sources, True )

        self.__init_remote()
        mainBox.pack_start( self.remote, True )

        self.__init_about()
        mainBox.pack_start( self.about, True )

        #Load configuration
        self.load( config )

        #Pygtk 2.14 and above
        #self.get_content_area().add(mainBox)
        #Pygtk 2.12 and bellow
        self.vbox.pack_start( mainBox )

        mainBox.show()
        self.show()

    def __init_profiles( self ):
        "Inits the profile tab"

        #Treated as a Vertical Box
        self.profiles = gtk.VBox()
        self.profiles.set_spacing( 5 )
        self.profiles.set_border_width( 5 )

        #Title
        label = gtk.Label( "<b>" + _( "Freeze profiles" ) + "</b>" )
        label.set_use_markup( True )
        self.profiles.pack_start( label, False )

        #ToolBar
        toolbar = gtk.HBox()

        item = gtk.Button( _( 'Add profile' ), gtk.STOCK_ADD )
        try:
            item.set_tooltip_text( _( 'Adds a new Frozen Profile' ) )
        except:
            pass
        item.connect( "clicked", self.__add_tab )
        toolbar.pack_start( item )

        item = gtk.Button( _( 'Remove profile' ), gtk.STOCK_REMOVE )
        try:
            item.set_tooltip_text( _( 'Removes the selected Frozen Profile' ) )
        except:
            pass
        item.connect( "clicked", self.__remove_tab )
        toolbar.pack_start( item )

        self.profiles.pack_start( toolbar, False )

        #ListStore of the actions in the profiles
        self.LSactions = gtk.ListStore( str, str, int )
        self.LSactions.append( [gtk.STOCK_REVERT_TO_SAVED, _( "Restore (Frozen)" ), ACTION_RESTORE] )
        self.LSactions.append( [gtk.STOCK_STOP, _( "Keep (Unfrozen)" ), ACTION_KEEP] )
        self.LSactions.append( [gtk.STOCK_DELETE, _( "Erase" ), ACTION_ERASE] )
        self.LSactions.append( [gtk.STOCK_FIND, _( "Move to Lost+Found" ), ACTION_LOST] )

        #Config tabs, empty because it will be filled on load
        self.tabs = gtk.Notebook()
        self.tabs.set_scrollable( True )
        self.profiles.pack_start( self.tabs, True )

    def __init_sources( self ):
        "Inits the sources tab"

        #Treated as a Vertical Box
        self.sources = gtk.VBox()
        self.sources.set_spacing( 5 )
        self.sources.set_border_width( 5 )

        label = gtk.Label( "<b>" + _( "Sources repository" ) + "</b>" )
        label.set_use_markup( True )
        self.sources.pack_start( label, False )

        self.LSsources = gtk.ListStore( str, str )

        #Create the TreeView using liststore
        self.TVsources = gtk.TreeView( self.LSsources )
        self.TMsources = self.TVsources.get_model()

        #Fields of the repository
        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn( _( "Name" ), cell, text = 0 )
        cell.set_property( 'editable', True )
        cell.connect( 'edited', self.__Cname_edited )
        self.TVsources.append_column( tv )
        tv.set_sort_column_id( 0 )
        tv.set_expand( True )
        tv.set_resizable( True )

        cell = gtk.CellRendererText()
        tv = gtk.TreeViewColumn( _( "Source" ), cell, text = 1 )
        self.TVsources.append_column( tv )
        tv.set_sort_column_id( 0 )
        tv.set_expand( True )
        tv.set_resizable( True )

        tv.set_sort_column_id( 0 )

        #Can search in the name column
        self.TVsources.set_search_column( 0 )

        self.sources.pack_start( self.TVsources )

        #Buttons to add and delete sources
        image = gtk.Image()
        image.set_from_stock( gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON )
        button = gtk.Button( _( "Add from a directory" ) )
        button.set_image( image )
        button.connect( "clicked", self.__add_from_directory )
        self.sources.pack_start( button, False )

        image = gtk.Image()
        image.set_from_stock( gtk.STOCK_HARDDISK, gtk.ICON_SIZE_BUTTON )
        button = gtk.Button( _( "Add from a tar file" ) )
        button.set_image( image )
        button.connect( "clicked", self.__add_from_tar )
        self.sources.pack_start( button, False )

        image = gtk.Image()
        image.set_from_stock( gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON )
        button = gtk.Button( _( "Remove a source" ) )
        button.set_image( image )
        button.connect( "clicked", self.__remove_source )
        self.sources.pack_start( button, False )

    def __init_remote( self ):
        "Inits the server and remote tasks tab"
        #Treated as a table"
        self.remote = gtk.Table()
        self.remote.set_row_spacings( 5 )
        self.remote.set_col_spacings( 5 )
        self.remote.set_border_width( 5 )

        #Remote users configuration"
        label = gtk.Label( "<b>" + _( "Remote users configuration" ) + "</b>" )
        label.set_use_markup( True )
        self.remote.attach( label, 0, 3, 0, 1, gtk.FILL, gtk.FILL )

        self.CBldapenable = gtk.CheckButton( _( "Enable LDAP support" ) )
        self.CBldapenable.connect( "toggled", self.__CBldapenable_toggled )
        self.remote.attach( self.CBldapenable, 0, 3, 1, 2, gtk.FILL, gtk.SHRINK )

        label = gtk.Label( _( "LDAP Server" ) )
        self.remote.attach( label, 0, 1, 2, 3, gtk.FILL, gtk.FILL )

        self.Eserver = gtk.Entry()
        self.Eserver.set_sensitive( False )
        self.remote.attach( self.Eserver, 1, 3, 2, 3, gtk.EXPAND | gtk.FILL, gtk.FILL )

        label = gtk.Label( _( "Distinguished Name (dn)" ) )
        self.remote.attach( label, 0, 1, 3, 4, gtk.FILL, gtk.FILL )

        self.Edn = gtk.Entry()
        self.Edn.set_sensitive( False )
        self.remote.attach( self.Edn, 1, 3, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL )

        image = gtk.Image()
        image.set_from_stock( gtk.STOCK_CONNECT, gtk.ICON_SIZE_BUTTON )
        self.Btest = gtk.Button( _( "Test connection" ) )
        self.Btest.set_image( image )
        self.Btest.connect( "clicked", self.__test_ldap )
        self.Btest.set_sensitive( False )
        self.remote.attach( self.Btest, 0, 3, 4, 5, gtk.EXPAND | gtk.FILL, gtk.FILL )

        self.Ltest = gtk.Label()
        self.Ltest.set_use_markup( True )
        self.Ltest.set_sensitive( False )
        self.remote.attach( self.Ltest, 0, 3, 5, 6, gtk.FILL, gtk.FILL )

        label = gtk.Label( "<b>" + _( "Remote homes" ) + "</b>" )
        label.set_use_markup( True )
        self.remote.attach( label, 0, 3, 6, 7, gtk.FILL, gtk.FILL )

        self.RBclient = gtk.RadioButton( None, _( "Work as a client" ) )
        self.RBclient.set_sensitive( False )
        self.RBclient.connect( "toggled", self.__RBclient_toggled )
        self.remote.attach( self.RBclient, 0, 3, 7, 8, gtk.FILL, gtk.FILL )

        image = gtk.Image()
        image.set_from_stock( gtk.STOCK_DIALOG_AUTHENTICATION, gtk.ICON_SIZE_BUTTON )
        self.Bkeys = gtk.Button( _( "Generate authorization keys" ) )
        self.Bkeys.set_image( image )
        self.Bkeys.connect( "clicked", self.__generate_keys )
        self.Bkeys.set_sensitive( False )
        self.remote.attach( self.Bkeys, 0, 3, 9, 10, gtk.EXPAND | gtk.FILL, gtk.FILL )

        self.Lkeys = gtk.Label()
        self.Lkeys.set_use_markup( True )
        self.Lkeys.set_sensitive( False )
        self.remote.attach( self.Lkeys, 0, 3, 10, 11, gtk.FILL, gtk.FILL )

        self.RBserver = gtk.RadioButton( self.RBclient, _( "Work as a server" ) )
        self.RBserver.set_sensitive( False )
        self.remote.attach( self.RBserver, 0, 3, 11, 12, gtk.FILL, gtk.FILL )

    def __init_about( self ):
        "Inits the about tab"

        #Treated as a table"
        self.about = gtk.Table()
        self.about.set_row_spacings( 5 )
        self.about.set_col_spacings( 5 )
        self.about.set_border_width( 5 )

        label = gtk.Label( "<b>" + _( "About Trivial Freezer" ) + "</b>" )
        label.set_use_markup( True )
        self.about.attach( label, 0, 3, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL )

        iconw = gtk.Image() # icon widget
        iconw.set_from_file( HUGE_ICONS[1] )
        iconw.show()
        self.about.attach( iconw, 0, 1, 1, 2, gtk.FILL, gtk.EXPAND | gtk.FILL )

        text = "<b>Trivial Freezer</b>\n"
        text += _( "Version" ) + ": " + VERSION + "\n\n"
        text += "<b>" + _( "Author" ) + ":</b>\n"
        text += "Pau Ferrer Ocaña\n\n"
        text += "<b>" + _( "Special greetings" ) + ":</b>\n"
        text += "Carlos Álvarez Martínez\n"
        text += "Joan de Gràcia\n\n"
        text += "<b>" + _( "With the support of " ) + ":</b>\n"
        text += "Departament d'Educació\n de la Generalitat de Catalunya\n"
        text += "IES Nicolau Copèrnic\n\n"
        text += "License: GPL v3\n\n"
        text += "Trivial Freezer is free software:\n"
        text += "you can redistribute it and/or\n"
        text += "modify it under the terms of the\n"
        text += "GNU General Public License as\n"
        text += "published by the Free Software\n"
        text += "Foundation, either version 3 of\n"
        text += "the License, or (at your option)\n"
        text += "any later version.\n\n"
        text += "Copyright (C) 2010  Pau Ferrer Ocaña"

        label = gtk.Label( text )
        label.set_use_markup( True )
        self.about.attach( label, 1, 2, 1, 2, gtk.FILL, gtk.FILL )

    def load( self, config ):
        "Loads configuration from the config class"

        #Load repository sources
        for source in config.sources:
            self.LSsources.append( [source.name, source.file] )

        #Load profiles
        for profile in config.profiles:
            newTab = self.__add_tab( data = profile.title )
            newTab.set_sensitive( profile.could_be_edited )
            newTab.Edeposit.set_text( profile.deposit )

            newTab.set_source( profile.source )
            if not profile.saved_source:
                newTab.CBfile.set_active( -1 )

            newTab.RBhome.set_active( not profile.saved_source )
            newTab.RBfile.set_active( profile.saved_source )
            newTab.CBfile.set_sensitive( profile.saved_source )

            newTab.Eexecute.set_text( profile.execute )
            newTab.CBexecuteenable.set_active( profile.execute_enabled )
            newTab.Eexecute.set_sensitive( profile.execute_enabled )

            #With their rules
            for rule in profile.rules:
                newTab.LSfilter.append( [rule.name,
                    rule.filter,
                    self.LSactions[rule.action][0],
                    self.LSactions[rule.action][1],
                    rule.action] )

        #Load server configuracion
        self.CBldapenable.set_active( config.ldap_enabled )
        self.Eserver.set_text( config.ldap_server )
        self.Edn.set_text( config.ldap_dn )

        self.RBserver.set_active( config.home_server )
        self.hostname = config.home_server_ip
        self.port = config.home_server_port
        self.server_user = config.home_server_user

        #Test the server configuration and ldap
        self.__test_home_server()
        self.__test_ldap()

        return

    def update_config( self, config ):
        "Saves configuration to the config class"

        #Save the profiles settings
        del config.profiles[:]

        config.load_profile_defaults()

        numProfiles = self.tabs.get_n_pages()
        for i in range( numProfiles - BLOCKED_PROFILES ):
            tab = self.tabs.get_nth_page( i + BLOCKED_PROFILES )
            config.profiles.append( tab.get_config() )

        #Save the sources repository
        del config.sources[:]

        for row in self.LSsources:
            s = source()
            s.name = row[0]
            s.file = row[1]
            config.sources.append( s )

        config.sources_to_erase.extend( self.sources_to_erase )

        del config.profiles_to_erase[:]
        config.profiles_to_erase.extend( self.profiles_to_erase )

        #Save the server configuration    
        config.ldap_dn = self.Edn.get_text()
        config.ldap_server = self.Eserver.get_text()

        config.ldap_enabled = self.CBldapenable.get_active() and self.__test_ldap()

        config.home_server = self.RBserver.get_active()
        config.home_server_ip = self.hostname
        config.home_server_port = self.port
        config.home_server_user = self.server_user


    def __add_tab( self, widget = None, data = _( "New Profile" ) ):
        "Adds a tab profile"

        newTab = profileTab( self, data )
        label = gtk.Label( data )
        page_num = self.tabs.append_page( newTab, label )
        self.tabs.set_current_page( page_num )

        return newTab

    def __remove_tab( self, widget = None ):
        "Removes the current tab"

        i = self.tabs.get_current_page()
        if i >= BLOCKED_PROFILES:
            self.tabs.remove_page( i )
            self.profiles_to_erase.append( i )

    def tab_name_modified( self, widget, data = None ):
        "On tab name modified event, change the tab label"

        name = widget.get_text()
        tab = widget.get_parent()
        self.tabs.set_tab_label_text( tab, name )

    def __show_hide_sources( self, widget ):
        "Shows/Hides sources tab"

        if widget.get_active():
            self.sources.show_all()
        else:
            self.sources.hide_all()

    def __show_hide_profiles( self, widget ):
        "Shows/Hides profiles tab"

        if widget.get_active():
            self.profiles.show_all()
        else:
            self.profiles.hide_all()

    def __show_hide_remote( self, widget ):
        "Shows/Hides server and remote config tab"

        if widget.get_active():
            self.remote.show_all()
        else:
            self.remote.hide_all()

    def __show_hide_about( self, widget ):
        "Shows/Hides about tab"

        if widget.get_active():
            self.about.show_all()
        else:
            self.about.hide_all()

    def __Cname_edited( self, cellrenderertext, path, new_text ):
        "Event handler for editing the name of a resource"

        self.LSsources[path][0] = new_text

    def __add_from_directory( self, widget = None ):
        "Adds a source from a repository and creates the tar"

        #Choose the directory
        dialog = gtk.FileChooserDialog( _( "Choose source file" ), action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK ) )
        dialog.set_default_response( gtk.RESPONSE_OK )

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            sourcefile = dialog.get_filename()

            dir = sourcefile.rsplit( "/", 1 )[1]

            #Choose the name
            fileName = dir + TAR_EXTENSION

            #Where to save the tar
            repo = os.path.join ( TAR_DIRECTORY, TAR_REPOSITORY )
            dst = os.path.join ( repo, fileName )
            auxPath = 0

            try:
                os.makedirs( repo, 0755 )
            except OSError , ( errno, strerror ):
                debug( repo + " " + strerror, DEBUG_HIGH )

            #Not to overwrite another tar...
            while os.path.exists( dst ):
                fileName = dir + "_" + str( auxPath ) + TAR_EXTENSION
                dst = os.path.join ( repo, fileName )
                auxPath = auxPath + 1

            #Create the tar file
            try:
                tar = tarfile.open( dst, 'w:gz' )
            except:
                print_error( "on add_from_directory" )
                warning = gtk.MessageDialog( parent = self,
                                      type = gtk.MESSAGE_WARNING,
                                      buttons = gtk.BUTTONS_OK,
                                      message_format = _( "The freezer was unable to create the tar file" )
                                      )
                res = warning.run()
                warning.destroy()
            else:
                #arcname = "" to avoid parent folders to be included
                tar.add( sourcefile, arcname = "" )
                tar.close()
                name = fileName.split( ".", 1 )[0]
                self.LSsources.append( [name, fileName] )

        dialog.destroy()
        return

    def __add_from_tar( self, widget = None ):
        "Adds a source from a repository"

        #Choose the tar file
        dialog = gtk.FileChooserDialog( _( "Choose source file" ), buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK ) )
        dialog.set_default_response( gtk.RESPONSE_OK )

        filter = gtk.FileFilter()
        filter.set_name( _( "Tar files" ) )
        filter.add_mime_type( "application/x-compressed-tar" )
        filter.add_mime_type( "application/x-tar" )
        filter.add_mime_type( "application/x-bzip-compressed-tar" )
        dialog.add_filter( filter )

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            sourcefile = dialog.get_filename()
            repo = os.path.join ( TAR_DIRECTORY, TAR_REPOSITORY )

            try:
                os.makedirs( repo, 0755 )
            except OSError , ( errno, strerror ):
                debug( repo + " " + strerror, DEBUG_HIGH )

            try:
                tar = tarfile.open( sourcefile, 'r' )
                tar.close()
                #Not to overwrite the tar
                dst = copy( sourcefile, repo )
            except Exception, e:
                print e
                warning = gtk.MessageDialog( parent = self,
                                      type = gtk.MESSAGE_WARNING,
                                      buttons = gtk.BUTTONS_OK,
                                      message_format = _( "The selected file is unreadable or malformed" )
                                      )
                res = warning.run()
                warning.destroy()
            else:
                #Add it to source repository
                name = dst.split( ".", 1 )[0]
                self.LSsources.append( [name, dst] )

        dialog.destroy()
        return

    def __remove_source( self, widget = None ):
        "Removes a source of the repository"

        ( view, iter ) = self.TVsources.get_selection().get_selected()
        if iter != None:
            path = self.TMsources.get_path( iter )[0]
            repo = os.path.join ( TAR_DIRECTORY, TAR_REPOSITORY )
            file = os.path.join ( repo, self.LSsources[path][1] )

            #Search for the profiles that use the selected source
            tabs_in_use = []
            for i in range( self.tabs.get_n_pages() ):
                tab = self.tabs.get_nth_page( i )
                if tab.is_source_in_use( path ):
                    tabs_in_use.append( i )

            if len( tabs_in_use ) > 0:
                #Warn the user
                d = gtk.MessageDialog( parent = self,
                                      type = gtk.MESSAGE_QUESTION,
                                      buttons = gtk.BUTTONS_YES_NO,
                                      message_format = _( "This source is in use in some profiles, do you want to continue?" )
                                      )
                response = d.run()
                if response == gtk.RESPONSE_YES:
                    #WARN because is in use
                    #Mark to erase when applying
                    self.sources_to_erase.append( file )

                    for i in tabs_in_use:
                        tab = self.tabs.get_nth_page( i )
                        tab.set_source( "" )

                    self.LSsources.remove( iter )
                d.destroy()
            #Not in use
            else:
                #Mark to erase when applying
                self.sources_to_erase.append( file )
                self.LSsources.remove( iter )

    def __CBldapenable_toggled( self, widget ):
        "Enables and disables options when toggling ldap support"
        self.Eserver.set_sensitive( widget.get_active() )
        self.Edn.set_sensitive( widget.get_active() )
        self.Ltest.set_sensitive( widget.get_active() )
        self.Btest.set_sensitive( widget.get_active() )
        self.RBclient.set_sensitive( widget.get_active() )
        self.RBserver.set_sensitive( widget.get_active() )
        self.Lkeys.set_sensitive( widget.get_active() and self.RBclient.get_active() )
        self.Bkeys.set_sensitive( widget.get_active() and self.RBclient.get_active() )

    def __RBclient_toggled( self, widget ):
        "Enables and disables options when toggling the kind of working"
        self.Lkeys.set_sensitive( widget.get_active() )
        self.Bkeys.set_sensitive( widget.get_active() )

    def __test_ldap( self, widget = None ):
        "Tests Ldap server by connecting it"
        from TFpasswd import ldap_tester
        if ldap_tester.try_ldap( self.Eserver.get_text(), self.Edn.get_text() ):
            self.Ltest.set_markup( '<span foreground="#007700" size="large">' + _( "Connection successfully established" ) + '</span>' )
            return True
        else:
            self.Ltest.set_markup( '<span foreground="#770000" size="large">' + _( "Connection failed" ) + '</span>' )
            return False


    def __test_home_server( self ):
        "Tests Home directory server by connecting it"

        roothome = pwd.getpwuid( 0 ).pw_dir

        try:
            pkey = paramiko.DSSKey.from_private_key_file( roothome + '/' + ID_DSA_PATH, "" )
            ssh = paramiko.SSHClient()
            try:
                ssh.load_system_host_keys( roothome + '/' + KNOWN_HOSTS_PATH )
            except:
                pass
            ssh.connect( self.hostname, int( self.port ), username = self.server_user, pkey = pkey, look_for_keys = False )
        except:
            self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Client not connected" ) + '</span>' )
            self.key = False
            return False
        ssh.close()
        self.key = True
        self.Lkeys.set_markup( '<span foreground="#007700" size="large">' + _( "Client connected to " ) + self.hostname + '</span>' )
        return True

    def __generate_keys( self, widget = None ):
        "Generates the keys to connect to the Home directory server"

        if self.key == True:
            #Warn that the key already exists
            warning = gtk.MessageDialog( parent = self, type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_YES_NO )
            warning.set_markup( _( "The keys already exists, do you want to overwrite them?" ) )
            warning.show_all()
            response = warning.run()

            if response == gtk.RESPONSE_NO:
                warning.destroy()
                return
            warning.destroy()

        #Take the root home directory
        roothome = pwd.getpwuid( 0 ).pw_dir
        #Private Key generation
        id_dsa = roothome + '/' + ID_DSA_PATH
        try:
            dss = paramiko.DSSKey.generate()
            dss.write_private_key_file( id_dsa, "" )
        except:
            self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Error creating private key." ) + "\n" + _( "Client not connected" ) + '</span>' )
            return

        #Public Key generation
        id_dsa_pub = id_dsa + '.pub'
        from socket import gethostname;
        public_key = "ssh-dss " + binascii.b2a_base64( dss.__str__() )[:-1] + " " + self.server_user + "@" + gethostname() + "\n"
        try:
            file = open( id_dsa_pub , "w" )
            file.write( public_key )
            file.close()
        except:
            self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Error creating public key." ) + "\n" + _( "Client not connected" ) + '</span>' )
            return

        ssh = paramiko.SSHClient()

        get_connect = False
        get_info = False
        while not get_connect:
            #I don't have the info to connect
            if not get_info:
                #Dialog to get information
                dialog = gtk.Dialog( title = _( "Configure the server" ), parent = self, flags = 0, buttons = ( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                                  gtk.STOCK_OK, gtk.RESPONSE_ACCEPT ) )

                table = gtk.Table()
                table.set_row_spacings( 5 )
                table.set_col_spacings( 5 )
                table.set_border_width( 5 )

                label = gtk.Label( _( "Server hostname" ) )
                table.attach( label, 0, 1, 0, 1, gtk.FILL, gtk.FILL )

                Ehostname = gtk.Entry()
                Ehostname.set_text( self.hostname )
                table.attach( Ehostname, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.FILL )

                label = gtk.Label( _( "Port" ) )
                table.attach( label, 0, 1, 1, 2, gtk.FILL, gtk.FILL )

                Eport = gtk.Entry()
                Eport.set_text( str( self.port ) )
                table.attach( Eport, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.FILL )

                label = gtk.Label( _( "Enter a username with privileges in the server" ) )
                table.attach( label, 0, 2, 2, 3, gtk.FILL, gtk.FILL )

                label = gtk.Label( _( "Username" ) )
                table.attach( label, 0, 1, 3, 4, gtk.FILL, gtk.FILL )

                Euser = gtk.Entry()
                Euser.set_text( str( self.server_user ) )
                table.attach( Euser, 1, 2, 3, 4, gtk.EXPAND | gtk.FILL, gtk.FILL )

                label = gtk.Label( _( "Password" ) )
                table.attach( label, 0, 1, 4, 5, gtk.FILL, gtk.FILL )

                Epasswd = gtk.Entry()
                Epasswd.set_visibility( False )
                table.attach( Epasswd, 1, 2, 4, 5, gtk.EXPAND | gtk.FILL, gtk.FILL )

                dialog.vbox.pack_start( table, True )

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

            #I've got the info

            #Load keys from known hosts
            try:
                ssh.load_system_host_keys( roothome + '/' + KNOWN_HOSTS_PATH )
            except:
                pass

            #Connect
            try:
                ssh.connect( hostname, int( port ), user, passwd )
            except paramiko.AuthenticationException, e :
                passwd = ""
                debug( "AuthenticationException " + str( e ), DEBUG_LOW )
                #User/password error
                warning = gtk.MessageDialog( parent = self, type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_OK )
                warning.set_markup( _( "Permission denied, please verify the user name and password" ) )
                warning.show_all()
                response = warning.run()
                warning.destroy()
                get_info = False
                get_connect = False
            except ( paramiko.BadHostKeyException, paramiko.SSHException ), e:
                #Ca'nt connect
                get_info = True
                get_connect = False
                debug( "SSHException or BadHostKeyException " + str( e ), DEBUG_LOW )
                hosts = ssh.get_host_keys()
                t = ssh.get_transport()
                key = t.get_remote_server_key()
                if not hosts.check( hostname, key ):
                    #Host key is not the same
                    warning = gtk.MessageDialog( parent = self, type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_YES_NO )
                    fingerprinthex = paramiko.util.hexify( key.get_fingerprint() )
                    fingerprint = ""
                    for i, v in enumerate( fingerprinthex ):
                        fingerprint += v
                        if i % 2 == 1 and i + 1 < len( fingerprinthex ):
                            fingerprint += ":"
                    text = _( "The authenticity of host '%(host)s' can't be established. %(key)s key fingerprint is %(fprint)s." ) % {'host': hostname, "key": key.get_name(), "fprint" : fingerprint}
                    warning.set_markup( text )
                    warning.show_all()
                    response = warning.run()

                    if response == gtk.RESPONSE_YES:
                        try:
                            hosts.add( hostname, key.get_name(), key )
                            hosts.save( roothome + '/' + KNOWN_HOSTS_PATH )
                        except:
                            debug( "Can't write in the known_hosts file", DEBUG_LOW )
                            ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
                    else:
			passwd = ""
                        warning.destroy()
                        return
                    warning.destroy()
            else:
                #Connected!
                get_connect = True
                passwd = ""
                debug("Connected to the server",DEBUG_HIGH)

        #After connecting...
        try:
            #Send the public key to the server
            sftp = ssh.open_sftp()
            sftp.put( id_dsa_pub, "/tmp/tfpubkey" )
            sftp.close()
        except:
            ssh.close()
            self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Errors connecting to SFTP server." ) + "\n" + _( "Client not connected" ) + '</span>' )
            return

        try:
            #Adds the key to authorized_keys
            stdin, stdout, stderr = ssh.exec_command( "echo '#!/bin/bash\n if [ ! -d ~"+user+"/.ssh ]; then\n mkdir ~"+user+"/.ssh\n fi\n cat /tmp/tfpubkey >> ~"+user+"/.ssh/authorized_keys\n rm -f /tmp/tfpubkey*' > /tmp/tfpubkey.sh" )
            stdin, stdout, stderr = ssh.exec_command( "chmod +x /tmp/tfpubkey.sh" )
            stdin, stdout, stderr = ssh.exec_command( "/tmp/tfpubkey.sh" )
            errors = stderr.read()
            if(len(errors) > 0):
                debug(errors,DEBUG_LOW)
                #Close the connection and exit
                ssh.close()
                self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Something executing commands goes wrong." ) + "\n" + _( "Client not connected" ) + '</span>' )
                return
            self.Lkeys.set_markup( '<span foreground="#007700" size="large">' + _( "Client connected to " ) + hostname + '</span>' )
            self.hostname = hostname
            self.port = port
            self.server_user = user
            self.key = True

        except:
            if(len(errors) <= 0):
		errors = stderr.read()
            #Close the connection and exit
            debug(errors,DEBUG_LOW)
            ssh.close()
            self.Lkeys.set_markup( '<span foreground="#770000" size="large">' + _( "Something executing commands goes wrong." ) + "\n" + _( "Client not connected" ) + '</span>' )
            return

        #Close the connection and exit
        ssh.close()

        return
