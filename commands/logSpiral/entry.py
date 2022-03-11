from ast import arg
from distutils.log import debug
from xmlrpc.client import boolean
import adsk.core, adsk.fusion, traceback, math
import os
from ...lib import fusion360utils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_spirale_create'
CMD_NAME = 'Spirale'
CMD_Description = 'Create Spirale'
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')


WORKSPACE_ID = config.design_workspace
PANEL_ID = config.sketch_create_panel_id
IS_PROMOTED = False


local_handlers = []

def start():
    # Create a command Definition.
    command_definition = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(command_definition.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    #listControlName(panel)
    control = panel.controls.addCommand(command_definition)
    control.isPromoted = IS_PROMOTED

def listControlName(panel: adsk.core.ToolbarPanel):
    for i in range(panel.controls.count):
        futil.log(panel.controls.item(i).id)


def stop():
    futil.log(f'{CMD_NAME} AddIn Stop Event')
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    control = panel.controls.itemById(CMD_ID)

    # Delete the button command control
    if control:
        control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')    
    
    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers) 
    futil.add_handler(args.command.executePreview, command_execute_preview, local_handlers=local_handlers)  
    
    inputs = args.command.commandInputs
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('16')

    selectedPointInput: adsk.core.SelectionCommandInput = inputs.addSelectionInput('mid_point', 'MidPoint', 'Please select a point')
    selectedPointInput.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints)
    selectedPointInput.setSelectionLimits(1,1)
    inputs.addIntegerSliderCommandInput('points_count', 'Count of Points',5,150,False)
    inputs.addValueInput('min_value','Minumum Value of Spirale',defaultLengthUnits,adsk.core.ValueInput.createByString('60'))
    inputs.addValueInput('max_value','Maximum Value of Spirale', defaultLengthUnits,adsk.core.ValueInput.createByString('120'))
    inputs.addAngleValueCommandInput('start_angle','Starting Angle',adsk.core.ValueInput.createByReal(50 * (math.pi/180.0)))
    inputs.addAngleValueCommandInput('end_angle','Ending Angle',adsk.core.ValueInput.createByReal(260 * (math.pi/180.0)))
    cb : adsk.core.BoolValueCommandInput =  inputs.addBoolValueInput ('splineTrue', 'spline', True)
    cb.value = True

def command_execute_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Preview Event')
    inputs = args.command.commandInputs
    points_count: adsk.core.IntegerSliderCommandInput  = inputs.itemById('points_count')
    min_value : adsk.core.ValueCommandInput = inputs.itemById('min_value')
    max_value : adsk.core.ValueCommandInput = inputs.itemById('max_value')
    start_angle : adsk.core.ValueCommandInput = inputs.itemById('start_angle')
    end_angle : adsk.core.ValueCommandInput = inputs.itemById('end_angle')
    splineTrue: adsk.core.BoolValueCommandInput= inputs.itemById('splineTrue')
    mid_point: adsk.core.SelectionCommandInput = inputs.itemById('mid_point')
    point: adsk.fusion.SketchPoint = mid_point.selection(0).entity

    draw_spirale(  points_count=points_count.valueOne,
                    min_value= min_value.value,
                    max_value=max_value.value,
                    start_angle=start_angle.value,
                    end_angle=end_angle.value,
                    splineTrue1=splineTrue.value,
                    mid_point=point.geometry)

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs
    points_count: adsk.core.IntegerSliderCommandInput  = inputs.itemById('points_count')
    min_value : adsk.core.ValueCommandInput = inputs.itemById('min_value')
    max_value : adsk.core.ValueCommandInput = inputs.itemById('max_value')
    start_angle : adsk.core.ValueCommandInput = inputs.itemById('start_angle')
    end_angle : adsk.core.ValueCommandInput = inputs.itemById('end_angle')
    splineTrue: adsk.core.BoolValueCommandInput= inputs.itemById('splineTrue')
    mid_point: adsk.core.SelectionCommandInput = inputs.itemById('mid_point')
    point: adsk.fusion.SketchPoint = mid_point.selection(0).entity

    draw_spirale(  points_count=points_count.valueOne,
                    min_value= min_value.value,
                    max_value=max_value.value,
                    start_angle=start_angle.value,
                    end_angle=end_angle.value,
                    splineTrue1=splineTrue.value,
                    mid_point=point.geometry)

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')


def draw_spirale(points_count: int,min_value:float,max_value:float,start_angle:float,end_angle:float,splineTrue1: bool,
                  mid_point: adsk.core.Point3D      ):
    futil.log(f'{CMD_NAME} draw_spirale')
    diff_angle = (end_angle-start_angle)/points_count
    points = adsk.core.ObjectCollection.create()
    i=0

    k = calculate_logarithm(math.e,(max_value/min_value))/(end_angle-start_angle)
    a = min_value / math.exp(start_angle*k)
    while i <= points_count:
        phi = start_angle + diff_angle*i
        x = a* math.exp(k*phi)* math.cos(phi)+ mid_point.x
        y = a* math.exp(k*phi)* math.sin(phi)+ mid_point.y
        points.add(adsk.core.Point3D.create(x,y,0))
        i = i + 1

    app = adsk.core.Application.get()
    design: adsk.core.Product = app.activeProduct

    rootComp: adsk.fusion.Component = design.rootComponent
    sketch: adsk.fusion.Sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
    if splineTrue1:
        sketch.sketchCurves.sketchFittedSplines.add(points)
    else:
        for i in range(points.count-1):
            pt1 = points.item(i)
            pt2 = points.item(i+1)
            sketch.sketchCurves.sketchLines.addByTwoPoints(pt1, pt2)

def calculate_logarithm(log_base, x):
    a = math.log(x)
    b = math.log(log_base)
    return a / b