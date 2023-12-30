# -*- coding: utf-8 -*-

"""
***************************************************************************
    splitOnDayBreakAlgorithm.py
    ---------------------
    Date                 : January 2019
    Copyright            : (C) 2019 by Anita Graser
    Email                : anitagraser@gmx.at
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import sys 
from movingpandas import TemporalSplitter

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsField,QgsFields,
                       QgsGeometry,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsFeatureRequest,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterEnum,
                       QgsWkbTypes
                      )

sys.path.append("..")

from .qgisUtils import tc_from_pt_layer

pluginPath = os.path.dirname(__file__)


class SplitOnDayBreakAlgorithm(QgsProcessingAlgorithm):
    # script parameters
    INPUT = 'INPUT'
    TRAJ_ID_FIELD = 'OBJECT_ID_FIELD'
    TIMESTAMP_FIELD = 'TIMESTAMP_FIELD'
    TIMESTAMP_FORMAT = 'TIMESTAMP_FORMAT'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def name(self):
        return "split_on_day_break"

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "icon.png"))

    def tr(self, text):
        return QCoreApplication.translate("split_on_day_break", text)

    def displayName(self):
        return self.tr("Day trajectories from point layer")

    def group(self):
        return self.tr("Basic")

    def groupId(self):
        return "TrajectoryBasic"

    def shortHelpString(self):
        return self.tr(
            "<p>Splits trajectories at midnight.</p>")

    def helpUrl(self):
        return "https://github.com/anitagraser/processing-trajectory"

    def createInstance(self):
        return type(self)()

    def initAlgorithm(self, config=None):
        # input layer
        self.addParameter(QgsProcessingParameterFeatureSource(
            name=self.INPUT,
            description=self.tr("Input point layer"),
            types=[QgsProcessing.TypeVectorPoint]))
        # fields
        self.addParameter(QgsProcessingParameterField(
            name=self.TRAJ_ID_FIELD,
            description=self.tr("Trajectory ID field"),
            defaultValue="trajectory_id",
            parentLayerParameterName=self.INPUT,
            type=QgsProcessingParameterField.Any,
            allowMultiple=False,
            optional=False))
        self.addParameter(QgsProcessingParameterField(
            name=self.TIMESTAMP_FIELD,
            description=self.tr("Timestamp field"),
            defaultValue="t",
            parentLayerParameterName=self.INPUT,
            type=QgsProcessingParameterField.Any,
            allowMultiple=False,
            optional=False))
        self.addParameter(QgsProcessingParameterString(
            name=self.TIMESTAMP_FORMAT,
            description=self.tr("Timestamp format"),
            defaultValue="%Y-%m-%d %H:%M:%S+00",
            optional=False))
        # output layer
        self.addParameter(QgsProcessingParameterFeatureSink(
            name=self.OUTPUT,
            description=self.tr("Trajectories"),
            type=QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        input_layer = self.parameterAsSource(parameters, self.INPUT, context)
        traj_id_field = self.parameterAsFields(parameters, self.TRAJ_ID_FIELD, context)[0]
        timestamp_field = self.parameterAsFields(parameters, self.TIMESTAMP_FIELD, context)[0]
        timestamp_format = self.parameterAsString(parameters, self.TIMESTAMP_FORMAT, context)

        output_fields = QgsFields()
        output_fields.append(QgsField(traj_id_field, QVariant.String))
        output_fields.append(QgsField('date', QVariant.DateTime))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               output_fields,
                                               QgsWkbTypes.LineStringM,
                                               input_layer.sourceCrs())
        
        tc = tc_from_pt_layer(input_layer, timestamp_field, traj_id_field, timestamp_format)

        for traj in tc.trajectories:
            for split in TemporalSplitter(traj).split(mode="year"):
                line = QgsGeometry.fromWkt(split.to_linestringm_wkt())
                f = QgsFeature()
                f.setGeometry(line)
                f.setAttributes([split.id])
                sink.addFeature(f, QgsFeatureSink.FastInsert)
        
        # default return type for function
        return {self.OUTPUT: dest_id}
