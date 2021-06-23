import FreeCAD
import Part
import Draft
import FreeCADGui
import os
from quantum_round import *
from vector_extras import *

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, 'Icons')


class ViewProviderGridBox:
	def __init__(self, vobj):
		"""
		Set this object to the proxy object of the actual view provider
		"""
		vobj.Proxy = self

		vobj.ShapeColor = (1.00, 0.67, 0.00)
		vobj.Transparency = 85
		vobj.LineColor = (1.00, 0.67, 0.00)
		vobj.DrawStyle = u"Dashed"

	def getDefaultDisplayMode(self):
		"""
		Return the name of the default display mode. It must be defined in getDisplayModes.
		"""
		return "Flat Lines"

	def getIcon(self):
		"""
		Return the icon in XMP format which will appear in the tree view. This method is optional and if not defined a default icon is shown.
		"""
		return os.path.join(iconPath, 'GridBox.svg')

	def attach(self, vobj):
		self.ViewObject = vobj
		self.Object = vobj.Object

	# def setEdit(self,vobj,mode):
	#     return False

	# def unsetEdit(self,vobj,mode):
	#     return

	def __getstate__(self):
		return None

	def __setstate__(self, state):
		return None

	def claimChildren(self):
		return self.Object.Shapes

	def onDelete(self, feature, subelements):
		try:
			for shape in self.Object.Shapes:
				shape.ViewObject.show()
		except Exception as err:
			FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
		return True


class GridBox:
	def __init__(self, obj, selection):
		self.Type = "GridBox"

		obj.addProperty("App::PropertyLinkList", "Shapes",
						"Base", "Objects to Wrap the GridBox around")
		obj.Shapes = selection

		obj.addProperty("App::PropertyVectorDistance", "Pitch",
						"Base", "Quantisation Pitch")
		obj.Pitch.x = 10.00
		for dim in ['y', 'z']:
			obj.setExpression(".Pitch.{}".format(dim), u".Pitch.x")

		for side in ["Start", "End"]:
			group = "Config" + side

			obj.addProperty("App::PropertyVector", "GridAdj" + side,
							group, "Adjust Segment Count")

			obj.addProperty("App::PropertyVectorDistance",
							"Offset" + side, group, "Offset per dimension")

			for dim in ["x", "y", "z"]:
				if side == "Start":
					obj.setExpression(".Offset{}.{}".format(
						side, dim), u".Pitch.{} / 2".format(dim))
				else:
					obj.setExpression(".Offset{}.{}".format(
						side, dim), ".OffsetStart.{}".format(dim))

				name = "Mode" + side + dim.upper()

				description = "Select mode for {}".format(name)
				obj.addProperty("App::PropertyEnumeration", name,
								group, description)
				setattr(obj, name, ["ceil", "floor", "round", "touch"])

		# expose results as readonly props
		for result in ["GridBox", "Box", "Grid"]:
			group = "Result" + result

			if result == "Grid":
				proptype = "App::PropertyVector"
			else:
				proptype = "App::PropertyVectorDistance"

			for vec in ["Start", "Center", "End", "Size"]:
				if result == "Grid" and vec == "Center":
					continue

				prop = result + vec
				obj.addProperty(proptype, prop, group,
								"{} of {}".format(vec, result))
				obj.setEditorMode(prop, 1)  # read-only

		# Additionally expose .BoxSize like primitive "Part::Box"
		for dimension in ["Length", "Width", "Height"]:
			obj.addProperty("App::PropertyLength", dimension, "Box")
			obj.setEditorMode(dimension, 1)  # read-only

		obj.Proxy = self
		self.Object = obj

	def __getstate__(self):
		return self.Type

	def __setstate__(self, state):
		if state:
			self.Type = state

	def TargetsBoundBox(self, obj, dir, dim):
		minmax_map = {
			"Start": "Min",
			"End": "Max"
		}

		val = []
		for shape in obj.Shapes:
			val.append(getattr(shape.Shape.BoundBox,
								dim.upper() + minmax_map[dir]))

		return max(val) if dir == "End" else min(val)

	def onChanged(self, fp, prop):
		return

	def VecGridBox(self, obj, dir):
		v = FreeCAD.Vector()

		for dim in ['x', 'y', 'z']:
			base = self.TargetsBoundBox(obj, dir, dim)
			pitch = getattr(obj.Pitch, dim)
			mode = getattr(obj, "Mode" + dir + dim.upper())

			if dir == "Start":
				offset = getattr(obj.OffsetStart, dim)
				adjust = getattr(obj.GridAdjStart, dim)
				val = base + offset - adjust * pitch

				qfunc = {
					"ceil": qfloor,
					"round": qround,
					"floor": qceil,
					"touch": qceil
				}
				boundary = qfunc[mode](val, pitch)
			elif dir == "End":
				offset = getattr(obj.OffsetEnd, dim)
				adjust = getattr(obj.GridAdjEnd, dim)
				val = base - offset + adjust * pitch

				qfunc = {
					"ceil": qceil,
					"round": qround,
					"floor": qfloor,
					"touch": qfloor
				}
				boundary = qfunc[mode](val, pitch)

			setattr(v, dim, boundary)

		return v

	def VecBox(self, obj, dir):
		v = FreeCAD.Vector()

		for dim in ['x', 'y', 'z']:
			offset = getattr(getattr(obj, "Offset" + dir), dim)
			grid = getattr(getattr(obj, "GridBox" + dir), dim)
			mode = getattr(obj, "Mode" + dir + dim.upper())

			if mode == "touch":
				boundary = self.TargetsBoundBox(obj, dir, dim)
			else:
				boundary = grid

			boundary += offset if dir == "End" else -offset
			setattr(v, dim, boundary)

		return v

	def execute(self, obj):
		"""
		Called on document recompute
		"""
		for result in ["GridBox", "Box"]:
			for side in ["Start", "End"]:
				vec = getattr(self, "Vec" + result)(obj, side)
				# vec = self.VecGridBox(obj, side)
				setattr(obj, result + side, vec)
			setattr(obj, result + "Size", getattr(obj, result +
													"End") - getattr(obj, result + "Start"))
			setattr(obj, result + "Center", getattr(obj, result +
													"Start") + getattr(obj, result + "Size") / 2)

		# 2. Calculate the Grid by simple Vector component Division of obj.GridBox[...]
		obj.GridStart = vecCompDiv(obj.GridBoxStart, obj.Pitch)
		obj.GridEnd = vecCompDiv(obj.GridBoxEnd, obj.Pitch)
		obj.GridSize = vecCompDiv(obj.GridBoxSize, obj.Pitch) + FreeCAD.Vector([1, 1, 1])

		obj.Length = obj.BoxSize.x
		obj.Width = obj.BoxSize.y
		obj.Height = obj.BoxSize.z

		obj.Shape = Part.makeBox(
			obj.Length, obj.Width, obj.Height, obj.BoxStart)

def isGridBox(obj):
	return obj.TypeId == 'Part::FeaturePython' and hasattr(obj.Proxy, 'Type') and obj.Proxy.Type == 'GridBox'
class GridBoxCommand:
	def GetResources(self):
		icon = os.path.join(iconPath, 'GridBox.svg')
		return {'Pixmap': icon,
				'Accel': "Shift+G",
				'MenuText': "GridBox",
				'ToolTip': "Generate a GridBox"}

	def Activated(self):
		obj = FreeCAD.ActiveDocument.addObject(
			'Part::FeaturePython', "GridBox")
		selection = FreeCADGui.Selection.getSelection()
		if not selection:
			FreeCAD.Console.PrintError(
				"\nAt least one object has to be selected first.")

		GridBox(obj, selection)
		ViewProviderGridBox(obj.ViewObject)
		FreeCAD.ActiveDocument.recompute()
		FreeCADGui.SendMsgToActiveView("ViewFit")

		return

	def IsActive(self):
		if FreeCAD.ActiveDocument == None:
			return False
		else:
			return True


if FreeCAD.GuiUp:
    FreeCADGui.addCommand("GridBox", GridBoxCommand())

class GridBoxArrayCommand:
	def GetResources(self):
		return {'Pixmap': os.path.join(iconPath, 'GridBox Array.svg'),
				'Accel': "Shift+A",
				'MenuText': "GridBox Array",
				'ToolTip': "Generate Array(s) of Objects on Face(s) of a GridBox."}

	def createArray(self, feature, gridbox, face=None, facename=None):
		if face.Orientation == 'Forward':
			side = 'End'
			face_normal = face.Surface.normal(0, 0)
		else:
			side = 'Start'
			face_normal = face.Surface.normal(0, 0).negative()

		box_labels = {
			'Face1': 'left',
			'Face2': 'right',
			'Face3': 'front',
			'Face4': 'rear',
			'Face5': 'bottom',
			'Face6': 'top',
		}
		label = box_labels.get(facename, 'solid')

		# linked_base = FreeCAD.ActiveDocument.addObject("App::Link", "Link")
		# linked_base.setLink(feature)
		# linked_base.Label = "{0} {1}.{2}".format(feature.Label, 'GridBox', label)
		# linked_base.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), face_normal)
		feature.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), face_normal)

		dummy = FreeCAD.Vector(0, 0, 0)
		array = Draft.make_array(feature, dummy, dummy, dummy, 1, 1, 1, use_link=True)
		# array = Draft.make_array(linked_base, dummy, dummy, dummy, 1, 1, 1, use_link=True)
		array.Label = "Array {}.{}".format(gridbox.Name, label)

		for dim in ['x', 'y', 'z']:
			array.setExpression('.Interval{}.{}'. format(dim.upper(), dim), '{}.Pitch.{}'.format(gridbox.Name, dim))

			if getattr(face_normal, dim):
				# In this dim, transform to Face of GridBox
				array.setExpression(
					'.Placement.Base.{}'.format(dim), '{0}.Box{1}.{2}'.format(gridbox.Name, side, dim)
				)
			else:
			# In this dim, transform Array to GridBoxStart and equalize Occurencies/Numbers/Count
				array.setExpression(
					'.Placement.Base.{0}'.format(dim), '{0}.GridBoxStart.{2}'.format(gridbox.Name, side, dim)
				)
				array.setExpression(
					'Number{0}'. format(dim.upper()), '{0}.GridSize.{1}'.format(gridbox.Name, dim)
				)

		return array

	def Activated(self):
		selections = FreeCADGui.Selection.getSelectionEx()
		FreeCADGui.Selection.clearSelection()
		feature = selections.pop(0).Object

		if isGridBox(feature):
			FreeCAD.Console.PrintError(
				"First selection must be the Feature. GridBox is not allowed as Feature")
			return

		for selection in selections:
			gridbox = selection.Object
			
			if not isGridBox(gridbox):
				FreeCAD.Console.PrintError(
					"Second and further Objects must be a GridBox or Faces of a GridBox")
				return

			if(selection.HasSubObjects):
				subElements = dict(
					zip(selection.SubElementNames, selection.SubObjects))
				for facename, face in subElements.items():
					self.createArray(feature, gridbox, face, facename)
			else:
				self.createArray(feature, gridbox)
		
		FreeCAD.ActiveDocument.recompute()
		return

	def IsActive(self):
		if FreeCAD.ActiveDocument == None:
			return False
		else:
			return True

class GridBoxIndexCommand:
    FreeCADGui.addCommand("GridBox Array", GridBoxArrayCommand())

class GridBoxIndexCommand:
	def GetResources(self):
		return {'Pixmap': os.path.join(iconPath, 'GridBox Index.svg'),
			'Accel': "Shift+I",
			'MenuText': "GridBox Index",
			'ToolTip': "Place selected object(s) at XZY-Index of GridBox"}

	def Activated(self):
		selection = FreeCADGui.Selection.getSelection()
		gridbox = selection.pop(0)

		if not isGridBox(gridbox):
			FreeCAD.Console.PrintError("Select GridBox first, then the Target(s)")
			return


		for obj in selection:
			obj.addProperty("App::PropertyLink", "GridBox", "Base", "GriBox to Take the Index from.")
			obj.addProperty("App::PropertyVector", "GridIndex", "Base", "Index Vector with position in Grid")
			
			obj.GridBox = gridbox
			dimensions = ['x', 'y', 'z']

			# For Arrays, don't overwrite dim being already placed via GridBox.BoxStart
			if obj.TypeId == 'Part::FeaturePython' and obj.Proxy.Type == 'Array':
				for expression in obj.ExpressionEngine:
					if ".BoxStart." in expression[1]:
						dimensions.remove(expression[1][-1])

			for dim in dimensions:
				obj.setExpression('Placement.Base.{0}'.format(
					dim), "GridIndex.{0} * .GridBox.Pitch.{0}".format(dim))

		FreeCAD.ActiveDocument.recompute()

	def IsActive(self):
		if FreeCAD.ActiveDocument == None:
			return False
		else:
			return True

if FreeCAD.GuiUp:
    FreeCADGui.addCommand("GridBox Index", GridBoxIndexCommand())