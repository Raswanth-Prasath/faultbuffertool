# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fault_buffer_tool_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from qgis.PyQt import QtCore, QtGui, QtWidgets
from .ui_FaultBufferTool_dialog import Ui_FaultBufferToolDialogBase

class FaultBufferToolDialog(QtWidgets.QDialog, Ui_FaultBufferToolDialogBase):
    def __init__(self, parent=None):
        """Constructor."""
        super(FaultBufferToolDialog, self).__init__(parent)
        # Set up the user interface from Designer through QGIS Plugin Builder:
        self.setupUi(self)
        
        # Connect radio button toggle signals to slots
        self.generalUncertaintyRadioButton.toggled.connect(self.update_checkbox_state)
        self.uncertaintyWithRankingRadioButton.toggled.connect(self.update_checkbox_state)
        self.geologicJudgementRadioButton.toggled.connect(self.update_checkbox_state)
        
        # Set initial state of checkboxes
        self.update_checkbox_state()
        
    def update_checkbox_state(self):
        """Update the enabled state of checkboxes based on which radio button is selected"""
        # Only enable checkboxes if "Uncertainty with ranking" is selected
        is_ranking_enabled = self.uncertaintyWithRankingRadioButton.isChecked()
        
        self.confidenceCheckBox.setEnabled(is_ranking_enabled)
        self.primarySecondaryCheckBox.setEnabled(is_ranking_enabled)
        self.simpleComplexCheckBox.setEnabled(is_ranking_enabled)
        
        # If the checkboxes become disabled, we can also store their state and uncheck them
        # Or keep their state but show them as disabled - commenting this out as it's optional
        # if not is_ranking_enabled:
        #     self.confidenceCheckBox.setChecked(False)
        #     self.primarySecondaryCheckBox.setChecked(False)
        #     self.simpleComplexCheckBox.setChecked(False)