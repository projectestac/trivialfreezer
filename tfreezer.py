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
import os
import datetime
import sys
import copy

#from xml.dom import minidom
from xml.dom import minidom
import xml.dom.minidom
from xml.dom.minidom import Document

#Converts an string to boolean
def str2bool(v):
  return v.lower() in ["yes", "true", "t", "1"]


class desktop:
	
	def __init__(self,parent):
		self.parent = parent

	def new(self):
		#crea un tar del directori home incloent aquells directoris sel·leccionats
		return
		
	def ui(self, widget, data=None):
		self.parent.push_status('Desktop:ui')
		
		#Preparar la UI
		self.parent.vbox.remove(self.parent.mainBox)
		self.parent.mainBox = gtk.VBox()
		
		table = gtk.Table()
		
		label = gtk.Label("Desktop profile name")
		label.show()
		table.attach(label,0,1,0,1)
		
		self.Ename = gtk.Entry()
		self.Ename.show()
		table.attach(self.Ename,1,2,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		table.show()		
		self.parent.mainBox.pack_start(table, False)
	
		#Config Files
		frame = gtk.Frame("Save these files")
		
		config = gtk.VBox()
		
		self.CBBfiles = gtk.CheckButton("Normal files: docs and images")
		self.CBBfiles.show()
		self.CBBfiles.set_active(True)
		config.add(self.CBBfiles)
		
		self.CBBbackground = gtk.CheckButton("Background")
		self.CBBbackground.show()
		self.CBBbackground.set_active(True)
		config.add(self.CBBbackground)
		
		self.CBBfirefox = gtk.CheckButton("Firefox Configuration")
		self.CBBfirefox.show()
		self.CBBfirefox.set_active(True)
		config.add(self.CBBfirefox)
		
		config.show()
		frame.add(config)
		
		frame.show()
		table.attach(frame,0,2,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL)
		#END of Config Files
	
		self.parent.mainBox.show()
		self.parent.vbox.pack_start(self.parent.mainBox, True, True)
		
			
	def load(self, widget, data=None):
		self.parent.push_status('Desktop:load')
		
		dialog = gtk.FileChooserDialog("Open...",None,gtk.FILE_CHOOSER_ACTION_OPEN,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
	   
		filter = gtk.FileFilter()
		filter.set_name("Text files")
		filter.add_mime_type("text/plain")
		filter.add_pattern("*.tfd")
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.filename = dialog.get_filename()
			self.ui(None)
			xmldoc = minidom.parse(self.filename)
			
			print xmldoc.toprettyxml(indent="  ")
			
			value = xmldoc.getElementsByTagName("desktop")[0].getAttribute("name")
			self.Ename.set_text(value)
			value = xmldoc.getElementsByTagName("files")[0].getAttribute("value")
			self.CBBfiles.set_active(str2bool(value))
			value = xmldoc.getElementsByTagName("background")[0].getAttribute("value")
			self.CBBbackground.set_active(str2bool(value))
			elem = xmldoc.getElementsByTagName("firefox")[0]
			#if not elem.hasAttribute("value"):
				#missatge = gtk.Dialog("Error",dialog,0,(gtk.STOCK_OK, gtk.RESPONSE_OK))
				#response = missatge.run()
				#missatge.destroy()
				#dialog.destroy()
			value = elem.getAttribute("value")
			self.CBBfirefox.set_active(str2bool(value))
				
		elif response == gtk.RESPONSE_CANCEL:
			self.parent.push_status('No files selected')
		dialog.destroy()
	
	def save(self, widget, data=None):
		self.parent.push_status('Desktop:save')
		
		dialog = gtk.FileChooserDialog("Save As...",None,gtk.FILE_CHOOSER_ACTION_SAVE,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
	   
		filter = gtk.FileFilter()
		filter.set_name("Text files")
		filter.add_mime_type("text/plain")
		filter.add_pattern("*.tfd")
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.filename = dialog.get_filename()
			
			#DESAR EN XML
			# Create the minidom document
			doc = Document()
			
			fre = doc.createElement("desktop")
			fre.setAttribute("name", self.Ename.get_text())
			doc.appendChild(fre)
			
			child = doc.createElement("files")
			child.setAttribute("value", str(self.CBBfiles.get_active()))
			fre.appendChild(child)
			
			
			child = doc.createElement("background")
			child.setAttribute("value", str(self.CBBbackground.get_active()))
			fre.appendChild(child)
			
			child = doc.createElement("firefox")
			child.setAttribute("value", str(self.CBBfirefox.get_active()))
			fre.appendChild(child)

			# Print our newly created XML
			print doc.toprettyxml(indent="  ")

			self.fitxer = open(self.filename, "w")
			self.fitxer.write(doc.toxml())#toxml()toprettyxml(indent="  ")
			self.fitxer.close()
			
			self.parent.push_status('File saved')
			
		elif response == gtk.RESPONSE_CANCEL:
			self.parent.push_status('No files selected')
		dialog.destroy()
		
		
class freeze:
	def __init__(self,parent):
		self.parent = parent
        
	def new(self):
		#crea un fitxer de configuració amb les opcions necessaries
		return
		
	def ui(self, widget, data=None):
		self.parent.push_status('Freeze:ui')
		
		#Preparar la UI
		self.parent.vbox.remove(self.parent.mainBox)
		self.parent.mainBox = gtk.VBox()
		
		table = gtk.Table()
		
		label = gtk.Label("Freeze profile name")
		label.show()
		table.attach(label,0,1,0,1)
		
		self.Ename = gtk.Entry()
		self.Ename.show()
		table.attach(self.Ename,1,2,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		label = gtk.Label("Files")
		label.show()
		table.attach(label,0,1,1,2)
		
		
		self.CBfiles = self.get_config_actions()
		self.CBfiles.show()
		table.attach(self.CBfiles,1,2,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		label = gtk.Label("All configuration")
		label.show()
		table.attach(label,0,1,2,3)
		
		self.CBconfig = gtk.combo_box_new_text()
		self.CBconfig.append_text("Individual configuration")
		self.CBconfig.append_text("Restore all")
		self.CBconfig.append_text("Block all")
		self.CBconfig.set_active(0)
		self.CBconfig.show()
		table.attach(self.CBconfig,1,2,2,3,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		#Config Files
		frame = gtk.Frame("Configuration files")
		
		config = gtk.Table()
		
		label = gtk.Label("Background")
		label.show()
		config.attach(label,0,1,0,1)
		
		self.CBbackground = self.get_config_actions()
		self.CBbackground.show()
		config.attach(self.CBbackground,1,2,0,1,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		label = gtk.Label("Firefox")
		label.show()
		config.attach(label,0,1,1,2)
		
		self.CBfirefox = self.get_config_actions()
		self.CBfirefox.show()
		config.attach(self.CBfirefox,1,2,1,2,gtk.EXPAND|gtk.FILL,gtk.EXPAND)
		
		config.show()
		frame.add(config)
		
		frame.show()
		table.attach(frame,0,2,3,4,gtk.EXPAND|gtk.FILL,gtk.EXPAND|gtk.FILL)
		#END of Config Files
		
		
		table.show()		
		self.parent.mainBox.pack_start(table, False)
	
		self.parent.mainBox.show()
		self.parent.vbox.pack_start(self.parent.mainBox, True, True)
		
	def get_config_actions(self):
		comboOptions = gtk.combo_box_new_text()
		comboOptions.append_text("Don't do nothing")
		comboOptions.append_text("Restore")
		comboOptions.append_text("Block")
		comboOptions.set_active(0)
		return comboOptions
	
	def load(self, widget, data=None):
		self.parent.push_status('Freeze:load')
		
		dialog = gtk.FileChooserDialog("Open...",None,gtk.FILE_CHOOSER_ACTION_OPEN,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
	   
		filter = gtk.FileFilter()
		filter.set_name("Text files")
		filter.add_mime_type("text/plain")
		filter.add_pattern("*.tff")
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.filename = dialog.get_filename()
			self.ui(None)
			xmldoc = minidom.parse(self.filename)
			
			print xmldoc.toprettyxml(indent="  ")
			
			value = xmldoc.getElementsByTagName("freeze")[0].getAttribute("name")
			self.Ename.set_text(value)
			value = xmldoc.getElementsByTagName("files")[0].getAttribute("value")
			self.CBfiles.set_active(int(value))
			value = xmldoc.getElementsByTagName("all")[0].getAttribute("value")
			self.CBconfig.set_active(int(value))
			value = xmldoc.getElementsByTagName("background")[0].getAttribute("value")
			self.CBbackground.set_active(int(value))
			elem = xmldoc.getElementsByTagName("firefox")[0]
			#if not elem.hasAttribute("value"):
				#missatge = gtk.Dialog("Error",dialog,0,(gtk.STOCK_OK, gtk.RESPONSE_OK))
				#response = missatge.run()
				#missatge.destroy()
				#dialog.destroy()
			value = elem.getAttribute("value")
			self.CBfirefox.set_active(int(value))
				
		elif response == gtk.RESPONSE_CANCEL:
			self.parent.push_status('No files selected')
		dialog.destroy()
	
	def save(self, widget, data=None):
		self.parent.push_status('Freeze:save')
		
		dialog = gtk.FileChooserDialog("Save As...",None,gtk.FILE_CHOOSER_ACTION_SAVE,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
	   
		filter = gtk.FileFilter()
		filter.set_name("Text files")
		filter.add_mime_type("text/plain")
		filter.add_pattern("*.tff")
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			self.filename = dialog.get_filename()
			
			#DESAR EN XML
			# Create the minidom document
			doc = Document()
			
			fre = doc.createElement("freeze")
			fre.setAttribute("name", self.Ename.get_text())
			doc.appendChild(fre)
			
			child = doc.createElement("files")
			child.setAttribute("value", str(self.CBfiles.get_active()))
			fre.appendChild(child)
			
			child = doc.createElement("all")
			child.setAttribute("value", str(self.CBconfig.get_active()))
			fre.appendChild(child)
			
			child = doc.createElement("background")
			child.setAttribute("value", str(self.CBbackground.get_active()))
			fre.appendChild(child)
			
			child = doc.createElement("firefox")
			child.setAttribute("value", str(self.CBfirefox.get_active()))
			fre.appendChild(child)

			# Print our newly created XML
			print doc.toprettyxml(indent="  ")

			self.fitxer = open(self.filename, "w")
			self.fitxer.write(doc.toxml())#toxml()toprettyxml(indent="  ")
			self.fitxer.close()
			
			self.parent.push_status('File saved')
			
		elif response == gtk.RESPONSE_CANCEL:
			self.parent.push_status('No files selected')
		dialog.destroy()

class tfreezer:

	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("Trivial Freezer v0.1")
		self.window.connect("destroy", lambda w: gtk.main_quit())
   		self.window.set_size_request(500, 500)

   		self.vbox = gtk.VBox()
		self.vbox.show()
		
		self.desktop = desktop(self)
		self.freeze = freeze(self)
		
		#MenuBar
		self.get_main_menu()
		self.ui_home(None)

		self.window.add(self.vbox)
		self.window.show()	
	
	def main(self):
		if len(sys.argv) < 2 :
			terminal().main()		
		elif sys.argv[1] == "-x" :
			gtk.main()
		else :
			terminal().help()
	
	def destroy(self, widget, data=None):
		gtk.main_quit()

	def delete_event(self, widget, event, data=None):
		return False

	def push_status(self,text):
		self.statusbar.push(0,text)
	
	#Initializes te Menu Bar
	def get_main_menu(self):

		ui = '''<ui>
		<menubar name="MenuBar">
		  <menu action="File">
		  	<menuitem action="NewDesktop"/>
		  	<menuitem action="NewFreeze"/>
		  	<menuitem action="OpenDesktop"/>
		  	<menuitem action="OpenFreeze"/>
		  	<menuitem action="SaveDesktop"/>
		  	<menuitem action="SaveFreeze"/>
			<menuitem action="Quit"/>
		  </menu>
		</menubar>
		<toolbar name="Toolbar">
		  <toolitem action="Home"/>
		  <separator/>
		  <toolitem action="Quit"/>
		  <separator/>
		</toolbar>
		</ui>'''
		
		# Create a UIManager instance
		uimanager = gtk.UIManager()

		# Add the accelerator group to the toplevel window
		accelgroup = uimanager.get_accel_group()
		self.window.add_accel_group(accelgroup)

		# Create an ActionGroup
				# Create an ActionGroup
		actiongroup = gtk.ActionGroup('UIManagertFreezer')
		self.actiongroup = actiongroup

		# Create actions
		actiongroup.add_actions([('NewDesktop', gtk.STOCK_NEW, '_New Desktop Profile...', None,
								  'Creates a New Desktop Profile', self.desktop.ui),
								  ('NewFreeze', gtk.STOCK_NEW, 'New _Freeze Profile...', '<control>f',
								  'Creates a New Freeze Profile', self.freeze.ui),
								  ('OpenDesktop', gtk.STOCK_OPEN, '_Open Desktop Profile...', None,
								  'Open a Desktop Profile', self.desktop.load),
								  ('OpenFreeze', gtk.STOCK_OPEN, 'Open F_reeze Profile...', '<control>r',
								  'Open a Freeze Profile', self.freeze.load),
								  ('SaveDesktop', gtk.STOCK_SAVE, 'Save Desktop Profile...', None,
								  'Save a Desktop Profile', self.desktop.save),
								  ('SaveFreeze', gtk.STOCK_SAVE, 'Save Fr_eeze Profile...', '<control>e',
								  'Save a Freeze Profile', self.freeze.save),
								  ('Quit', gtk.STOCK_QUIT, '_Quit', None,
								  'Quit the Program', gtk.main_quit),
								  ('Home', gtk.STOCK_HOME, '_Home', None,
								  'Go home', self.ui_home),
								 ('File', None, '_File')])
		actiongroup.get_action('Home').set_property('short-label', '_Home')

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)
		
		# Add a UI description
		uimanager.add_ui_from_string(ui)
		
		menubar = uimanager.get_widget('/MenuBar')
		toolbar = uimanager.get_widget('/Toolbar')
		self.vbox.pack_start(menubar, False)
		self.vbox.pack_start(toolbar, False)
		
		self.mainBox = gtk.VBox()
		self.mainBox.show()
		self.vbox.pack_start(self.mainBox, True, True)
		
		self.statusbar = gtk.Statusbar()
		self.statusbar.show()
		self.vbox.pack_end(self.statusbar, False)
	
	def ui_home(self, widget, data=None):
		self.push_status('Home:ui')
		
		#read data
		self.vbox.remove(self.mainBox)
		self.mainBox = gtk.VBox()
	
		label = gtk.Label("Home")
		label.show()	
		self.mainBox.pack_start(label, False)
	
		self.mainBox.show()
		self.vbox.pack_start(self.mainBox, True, True)


class terminal:

	def help(self):
		print "Trivial Freezer v0.1 HELP"
		print "========================="
		return
	
	def main(self):
		print "Trivial Freezer v0.1"
		print "===================="
		return

if __name__ == "__main__":
	window = tfreezer()
	window.main()
