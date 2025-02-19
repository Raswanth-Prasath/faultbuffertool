# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FaultBufferTool
                                 A QGIS plugin
 This plugin will create buffers based on the provided lookup table and attributes in the input shapefile.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2025-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2025 by ASU
        email                : raswanth@asu.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog, QPushButton
from qgis import processing

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsVectorFileWriter,
    QgsSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsMessageLog,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsPointXY,
    QgsGeometry
)
from qgis.gui import QgsFileWidget

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .FaultBufferTool_dialog import FaultBufferToolDialog
import os.path


class FaultBufferTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FaultBufferTool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&FaultBufferTool')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.dlg = None
        self.buffer_distances = {
            ('P', 1): 200,  # Primary, Quality 1
            ('P', 2): 80,   # Primary, Quality 2
            ('P', 3): 30,   # Primary, Quality 3
            ('P', 4): 10,   # Primary, Quality 4
            ('S', 1): 300,  # Secondary, Quality 1
            ('S', 2): 100,  # Secondary, Quality 2
            ('S', 3): 70,   # Secondary, Quality 3
            ('S', 4): 20    # Secondary, Quality 4
        }

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('FaultBufferTool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/FaultBufferTool/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Fault Buffer Tool'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&FaultBufferTool'),
                action)
            self.iface.removeToolBarIcon(action)

    def get_utm_crs(self, longitude, latitude):
        """Calculate the appropriate UTM CRS based on coordinates"""
        # Calculate UTM zone
        # The Earth is divided into 60 UTM zones, each 6 degrees wide
        # We add 180 to shift from (-180,180) range to (0,360) range
        # Then divide by 6 to get the zone number (1-60)
        zone = int((longitude + 180) / 6) + 1
        
        # Determine if Northern or Southern hemisphere
        # - 326xx for Northern hemisphere (latitude > 0)
        # - 327xx for Southern hemisphere (latitude < 0)
        if latitude > 0:
            epsg = f"326{zone:02d}"  # Northern hemisphere
        else:
            epsg = f"327{zone:02d}"  # Southern hemisphere
        
        return QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
    
    def create_asymmetric_buffer(self, geometry, distance, dip_direction, input_crs, segments):
        """
        Creates an asymmetric buffer by:
        1. Translating the fault line based on dip direction
        2. Using QGIS's built-in buffer function
        
        Args:
            geometry: The input fault line geometry
            distance: Base buffer distance
            dip_direction: Direction of dip (N/S/E/W)
            segments: Number of segments for smoothing curves
            
        Returns:
            QgsGeometry: An asymmetric buffer created using QGIS's buffer function
        """
        try:
            from qgis.core import QgsFeature, QgsGeometry, QgsVectorLayer, QgsWkbTypes

            # Log initial parameters
            QgsMessageLog.logMessage(f"Starting asymmetric buffer creation: distance={distance}, dip={dip_direction}", "FaultBufferTool")

            #Buffer ratio
            buffer_ratio = 1/4
            translation_dist = distance * ((1-buffer_ratio)/(1+buffer_ratio))
            
            # Calculate translation offsets
            if dip_direction.upper() == 'N':
                dx, dy = 0, translation_dist
            elif dip_direction.upper() == 'S':
                dx, dy = 0, -translation_dist
            elif dip_direction.upper() == 'E':
                dx, dy = translation_dist, 0
            else:  # West
                dx, dy = -translation_dist, 0

            QgsMessageLog.logMessage(f"Translation values: dx={dx}, dy={dy}", "FaultBufferTool")

            # Create temporary layer 
            temp_layer = QgsVectorLayer(f"LineString?crs={input_crs.authid()}", "temp", "memory")
            if not temp_layer.isValid():
                QgsMessageLog.logMessage("Failed to create temporary layer", "FaultBufferTool")
                return None

            # Add feature to temp layer
            temp_provider = temp_layer.dataProvider()
            temp_feat = QgsFeature()
            temp_feat.setGeometry(geometry)
            if not temp_provider.addFeatures([temp_feat]):
                QgsMessageLog.logMessage("Failed to add feature to temporary layer", "FaultBufferTool")
                return None

            # Run translate algorithm
            translate_params = {
                'INPUT': temp_layer,
                'DELTA_X': dx,
                'DELTA_Y': dy,
                'DELTA_Z': 0,
                'DELTA_M': 0,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }

            QgsMessageLog.logMessage("Running translate algorithm...", "FaultBufferTool")
            translated_result = processing.run("native:translategeometry", translate_params)
            
            if not translated_result or 'OUTPUT' not in translated_result:
                QgsMessageLog.logMessage("Translation algorithm failed", "FaultBufferTool")
                return None

            # Get translated geometry
            translated_layer = translated_result['OUTPUT']
            translated_geom = None
            for feat in translated_layer.getFeatures():
                translated_geom = feat.geometry()
                break

            if not translated_geom:
                QgsMessageLog.logMessage("Failed to get translated geometry", "FaultBufferTool")
                return None

            QgsMessageLog.logMessage("Creating buffer...", "FaultBufferTool")
            
            # Create buffer
            buffer_geom = translated_geom.buffer(distance, segments)
            
            if not buffer_geom or not buffer_geom.isGeosValid():
                QgsMessageLog.logMessage("Failed to create valid buffer geometry", "FaultBufferTool")
                return None
            
            QgsMessageLog.logMessage(f"Buffer created successfully. Type: {buffer_geom.wkbType()}", "FaultBufferTool")
            return buffer_geom

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in create_asymmetric_buffer: {str(e)}", "FaultBufferTool")
            import traceback
            QgsMessageLog.logMessage(f"Traceback: {traceback.format_exc()}", "FaultBufferTool")
            return None
    
    def run(self):
        """Run method that performs all the real work"""
        
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = FaultBufferToolDialog()
        
        # Ensure one option is always selected
        self.dlg.symmetricRadioButton.setChecked(True)
            
        self.dlg.setupUi(self.dlg)
    
        # Configure the file widget explicitly
        self.dlg.mQgsFileWidget.setStorageMode(QgsFileWidget.SaveFile)
        self.dlg.mQgsFileWidget.setFilter("Shapefiles (*.shp)")
        self.dlg.mQgsFileWidget.setFilePath("")  # Clear any previous path


        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            
            try:
                # Get the input layer
                input_layer = self.dlg.mMapLayerComboBox.currentLayer()
                if not input_layer:
                    QMessageBox.critical(self.dlg, "Error", "Please select an input layer")
                    return
                
                # Get the output path
                output_path = self.dlg.mQgsFileWidget.filePath()
                if not output_path:
                    QMessageBox.critical(self.dlg, "Error", "Please select an output location")
                    return
                
                if not output_path.endswith('.shp'):
                    output_path += '.shp'
    
                # Get and check the layer's CRS
                source_crs = input_layer.crs()
                               
                # If the CRS is isgeographic, (like EPSG:4326), we'll need to transform to a projected CRS
                if source_crs.isGeographic():
                    # Print some debug information
                    QgsMessageLog.logMessage(f"Source CRS is geographic: {source_crs.description()}", "Buffer Tool")
                    
                    # Get the UTM zome for the layer's extent
                    center_point = input_layer.extent().center()
                    utm_crs = self.get_utm_crs(center_point.x(), center_point.y())
  

                    QgsMessageLog.logMessage(f"Selected UTM CRS: {utm_crs.description()}", "Buffer Tool")
                    
                    # Create transform context
                    transform = QgsCoordinateTransform(source_crs, utm_crs, QgsProject.instance())
                    
                    # Create new layer in UTM projection
                    buffer_layer = QgsVectorLayer(f"Polygon?crs={utm_crs.authid()}", "buffers", "memory")
                else:
                    # Use the same CRS as input if it's already projected
                    QgsMessageLog.logMessage(f"Source CRS is projected: {source_crs.description()}", "Buffer Tool")
                    buffer_layer = QgsVectorLayer(f"Polygon?crs={source_crs.authid()}", "buffers", "memory")
                    transform = None
                
                QgsMessageLog.logMessage(f"Input CRS: {source_crs.authid()}", "FaultBufferTool")
                QgsMessageLog.logMessage(f"Buffer layer CRS: {buffer_layer.crs().authid()}", "FaultBufferTool")
                # QgsMessageLog.logMessage(f"UTM CRS for calculations: {utm_crs.authid()}", "FaultBufferTool")
                
                # Add this debugging code to the plugin just before the field check
                QgsMessageLog.logMessage("Checking for required fields...", "FaultBufferTool")
                QgsMessageLog.logMessage(f"Available fields: {[f.name() for f in input_layer.fields()]}", "FaultBufferTool")

                # Checking for required fields
                required_fields = ["P or S", "Quality"]
                for field in required_fields:
                    idx = input_layer.fields().indexFromName(field)
                    QgsMessageLog.logMessage(f"Checking field '{field}': index = {idx}", "FaultBufferTool")
   
                # Verify required fields exist
                for field in required_fields:
                    if input_layer.fields().indexFromName(field) == -1:
                        QMessageBox.critical(self.dlg, "Error", 
                            f"Required field '{field}' not found in input layer!")
                        return
                    
                # # Create output layer
                available_fields = [f.name() for f in input_layer.fields()]
                
                # Update field names to match actual fields in the layer
                p_or_s_field = "P or S"  # Changed from "P or S"
                quality_field = "Quality"
                
                # Verify required fields exist
                if p_or_s_field not in available_fields or quality_field not in available_fields:
                    QMessageBox.critical(self.dlg, "Error", 
                        f"Required fields '{p_or_s_field}' and/or '{quality_field}' not found in input layer!")
                    return
                QgsMessageLog.logMessage("Verified required fields exist", "FaultBufferTool")
                
                # Create output layer
                buffer_provider = buffer_layer.dataProvider()
                
                # Add attributes using the new QgsField syntax
                buffer_provider.addAttributes([
                    QgsField("original_id", QVariant.Int, "Integer"),
                    QgsField("P or S", QVariant.String, "String"),
                    QgsField("Quality", QVariant.Int, "Integer"),
                    QgsField("Buffer_Dist", QVariant.Double, "Double"),
                    QgsField("Dip_Direction", QVariant.String, "String")
                ])
                buffer_layer.updateFields()
                QgsMessageLog.logMessage("Adding attributes", "FaultBufferTool")
                
                # Process features             
                for feature in input_layer.getFeatures():
                    # Get P/S classification and quality using updated field names
                    p_or_s = feature[p_or_s_field].strip().upper()
                    dip_direction = feature['Dip_direct'].strip().upper()
                    
                    try:
                        quality = int(feature[quality_field])
                    except (ValueError, TypeError):
                        continue
                    
                    # Look up buffer distance
                    distance = self.buffer_distances.get((p_or_s, quality), 0)
                    if distance <= 0:
                        continue
                    
                    # Create buffer geometry
                    geometry = feature.geometry()
                    if transform:
                        # Transform to UTM
                        geometry.transform(transform)
                
                        # Create buffer (distance is now in meters)
                        buffer_geom = geometry.buffer(distance, 5)
                        
                        # Create reverse transform for going back to original CRS                      
                        QgsCoordinateTransform(
                            utm_crs,  # From UTM
                            source_crs,  # Back to source CRS
                            QgsProject.instance()
                        )
                        
                        # Create reverse transform for going back to original CRS
                        reverse_transform = QgsCoordinateTransform(
                            buffer_layer.crs(),  # From buffer layer CRS (UTM)
                            source_crs,          # Back to source CRS
                            QgsProject.instance()
                        )
                        
                        # Transform back to original CRS
                        buffer_geom.transform(reverse_transform)
                    
                    # Set number of segments for buffer
                    segments = 5  # Default value

                    # Create asymmetric buffer if asymmetric is selected
                    if self.dlg.asymmetricRadioButton.isChecked():
                        # Create two buffers and merge them
                        QgsMessageLog.logMessage(f"Creating asymmetric buffer for feature {feature.id()}", "FaultBufferTool")
                        input_crs = input_layer.crs()  # Get CRS from input layer
                        buffer_geom = self.create_asymmetric_buffer(
                            geometry, 
                            distance, 
                            dip_direction,
                            input_crs, 
                            segments# Pass the CRS 
                        )
                        
                    else:
                        # If no transform needed, just create the buffer
                        buffer_geom = geometry.buffer(distance, segments)
                        
                    # Create new feature with buffer
                    buffer_feature = QgsFeature(buffer_layer.fields())
                    buffer_feature.setGeometry(buffer_geom)
                    
                    # Set attributes
                    buffer_feature.setAttribute("original_id", feature.id())
                    buffer_feature.setAttribute("P or S", p_or_s)  # Note: Changed from "P or S" to match field name
                    buffer_feature.setAttribute("Quality", quality)
                    buffer_feature.setAttribute("Buffer_Dist", distance)
                    buffer_feature.setAttribute("Dip_Direction", dip_direction)
                    
                    buffer_provider.addFeature(buffer_feature)
                    
                
                QgsMessageLog.logMessage("Buffer created", "FaultBufferTool")
                    
                # Write the layer to file
                error = QgsVectorFileWriter.writeAsVectorFormat(
                    buffer_layer, 
                    output_path, 
                    "UTF-8", 
                    driverName="ESRI Shapefile"
                )
                QgsMessageLog.logMessage("file created", "FaultBufferTool")
                
            
                # Save the buffer layer
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "ESRI Shapefile"
                options.fileEncoding = "UTF-8"
                
                error = QgsVectorFileWriter.writeAsVectorFormat(
                    buffer_layer,
                    output_path,
                    options=options
                )

                if error[0] != QgsVectorFileWriter.NoError:
                    QMessageBox.critical(self.dlg, "Error", f"Failed to save buffer layer: {error}")
                    return

                # Add the new layer to the map
                output_name = os.path.splitext(os.path.basename(output_path))[0]
                buffer_layer = QgsVectorLayer(output_path, output_name, "ogr")
                if buffer_layer.isValid():
                    # Set opacity for the buffer layer
                    renderer = buffer_layer.renderer()
                    if isinstance(renderer, QgsCategorizedSymbolRenderer):
                        for category in renderer.categories():
                            symbol = category.symbol()
                            symbol.setOpacity(0.5)
                    else:
                        # If not categorized, set opacity for single symbol
                        symbol = renderer.symbol()
                        if symbol:
                            symbol.setOpacity(0.5)

                    # Get the layer tree and input layer's node
                    root = QgsProject.instance().layerTreeRoot()
                    input_node = root.findLayer(input_layer.id())
                    
                    # Insert buffer layer below input layer
                    if input_node:
                        QgsProject.instance().addMapLayer(buffer_layer, False)  # False = don't add to legend
                        buffer_node = root.insertLayer(root.children().index(input_node) + 1, buffer_layer)
                    else:
                        # Fallback: just add the layer normally
                        QgsProject.instance().addMapLayer(buffer_layer)

                    buffer_layer.triggerRepaint()
                    QMessageBox.information(self.dlg, "Success", 
                        f"Buffer created successfully with symbology!")
                else:
                    QMessageBox.critical(self.dlg, "Error", "Failed to load output layer")

            except Exception as e:
                QMessageBox.critical(self.dlg, "Error", f"An unexpected error occurred: {str(e)}")
                return

