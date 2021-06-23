import os

import gridkitwb_locator
gridkitWBpath = os.path.dirname(gridkitwb_locator.__file__)
gridkitWB_icons_path =  os.path.join( gridkitWBpath, 'Icons')

global GridKit_WB_icon
GridKit_WB_icon = os.path.join( gridkitWB_icons_path , 'GridBox.svg')

class GridKitWorkbench (Workbench):
	global GridKit_WB_icon

	MenuText = "GridKit"
	ToolTip = "3D-Grid-tools for creation of modular, intercompatible geometry."
	Icon = GridKit_WB_icon

	def Initialize(self):
		"""This function is executed when FreeCAD starts"""
		import GridKit # import here all the needed files that create your FreeCAD commands
		self.list = ["GridBox", "GridBox Array", "GridBox Index"] # A list of command names created in the line above
		self.appendToolbar("GridKit",self.list) # creates a new toolbar with your commands
		self.appendMenu("GridKit",self.list) # creates a new menu
		# self.appendMenu(["An existing Menu","My submenu"],self.list) # appends a submenu to an existing menu

	def Activated(self):
		"""This function is executed when the workbench is activated"""
		return

	def Deactivated(self):
		"""This function is executed when the workbench is deactivated"""
		return

	# def ContextMenu(self, recipient):
	# 	"""This is executed whenever the user right-clicks on screen"""
	# 	# "recipient" will be either "view" or "tree"
	# 	self.appendContextMenu("GridKit",self.list) # add commands to the context menu

	def GetClassName(self): 
		# This function is mandatory if this is a full python workbench
		# This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
		return "Gui::PythonWorkbench"

Gui.addWorkbench(GridKitWorkbench())