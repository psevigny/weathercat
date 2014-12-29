#! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo
import time
import geo
from appscript import *

################################################################################
# Globals
################################################################################
weathercat = None
kWeatherCatUnavailableMessage = u"WeatherCat doesn't appear to be installed on your system"

indigoChannelVariableNames = {
1: "external_temperature",
2: "dewpoint",
3: "windchill",
4: "pressure",
5: "windspeed_instantaneous",
6: "windspeed_average_10mins",
7: "winddirection_instantaneous",
8: "winddirection_average",
9: "precipitation_per_hour",
10: "precipitation_daily",
11: "precipitation_raw",
12: "external_rh",
13: "internal_rh",
14: "internal_temperature",
15: "windgust_1mins",
16: "windgust_5mins",
17: "windgust_10mins",
18: "windgust_15mins",
19: "windgust_dir_1mins",
20: "windgust_dir_5mins",
21: "windgust_dir_10mins",
22: "windgust_dir_15mins",
23: "solar_radiation_WM2",
24: "uv_index",
25: "aux_temperature_1",
26: "aux_temperature_2",
27: "aux_temperature_3",
28: "aux_temperature_4",
29: "aux_temperature_5",
30: "aux_temperature_6",
31: "aux_temperature_7",
32: "aux_temperature_8",
33: "aux_rh1",
34: "aux_rh2",
35: "aux_rh3",
36: "aux_rh4",
37: "aux_rh5",
38: "aux_rh6",
39: "aux_rh7",
40: "aux_rh8",
41: "leaf_wetness1",
42: "leaf_wetness2",
43: "leaf_wetness3",
44: "leaf_wetness4",
45: "soil_moisture1",
46: "soil_moisture2",
47: "soil_moisture3",
48: "soil_moisture4",
49: "leaf_temperature1",
50: "leaf_temperature2",
51: "leaf_temperature3",
52: "leaf_temperature4",
53: "soil_temperature1",
54: "soil_temperature2",
55: "soil_temperature3",
56: "soil_temperature4",
57: "monthly_rain",
58: "yearly_rain",
59: "daily_et",
60: "monthly_et",
61: "yearly_et"
}

indigoOtherVariableNames = {
"ExternalTempDelta1": "external_temperature_delta1",
"DewPointDelta1": "dewpoint_delta1",
"PressureDelta1": "pressure_delta1",
"PressureDelta3": "pressure_delta3",
"WindSpeedDelta1": "windspeed_delta1",
"AverageWindSpeedDelta1": "windspeed_average_delta1",
"WindGustDelta1": "windgust_delta1",
"WindDirectionDelta1": "winddirection_delta1",
"PrecipitationPerHourDelta1": "precipitation_per_hour_delta1",
"PrecipitationDelta1": "precipitation_delta1",
"WindChillDelta1": "windchill_delta1",
"ExternalRHDelta1": "external_rh_delta1",
"InternalTempDelta1": "internal_temperature_delta1",
"SolarRadiationDelta1": "solar_radiation_delta1",
"UVIndexDelta1": "uv_index_delta1"
}

################################################################################
class Plugin(indigo.PluginBase):

    availableChannels = []

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.debug = pluginPrefs.get("showDebugInfo", False)
        self.folderName = pluginPrefs.get("varsFolder", None)

        self.weathercat = None
        try:
            self.weathercat = app("WeatherCat")

            # Probe for available working channels
            self.debugLog("Available WeatherCat channels:")
            for channelNum in range(1, self.weathercat.NumberOfChannels.get()):
                self.weathercat.WorkingChannel.set(channelNum)
                chanVar = self.getIndigoChannelVariableName(channelNum)

                if self.weathercat.WorkingChannelStatus.get():
                    chanName = self.weathercat.WorkingChannelName.get()
                    chanValue = "%s" % round(self.weathercat.WorkingChannelValue.get(), 1)

                    self.debugLog(" Channel %d (%s - %s): %s" % (channelNum, chanVar, chanName, chanValue))
                    self.availableChannels.append(channelNum)

                #else:
                #    self.debugLog(" Channel %d (%s): not available" % (channelNum, chanVar))

        except Exception, e:
            self.debugLog("Error talking to WeatherCat:\n%s" % str(e))
            self.errorLog(kWeatherCatUnavailableMessage)

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    def runConcurrentThreadz(self):
        try:
            while True:
                if (self.weathercat != None):  # and (self.airfoil.isrunning()):
                    self.debugLog("Polling WeatherCat")
                    updateWeatherCatVariables()

                else:
                    if self.weathercat:
                        self.debugLog("WeatherCat is not running or not available")

            self.sleep(60)

        except self.StopThread:
            pass


    ########################################
    def getIndigoChannelVariableName(self, channelNumber):
        varname = indigoChannelVariableNames[channelNumber];
        if varname:
            varname = "WCT_" + varname
        else:
            varname = "WCT_channel%d" % channelNumber
        return varname

    ########################################
    def getIndigoOtherVariableName(self, wcVarName):
        varname = indigoOtherVariableNames[wcVarName];
        if varname:
            varname = "WCT_" + varname
        else:
            varname = "WCT_%s" % wcVarName
        return varname

    ########################################
    def updateIndigoVar(self, name, value, folder):
        svalue = "%s" % value
        if name not in indigo.variables:
            indigo.variable.create(name, value=svalue, folder=folder)
        else:
            indigo.variable.updateValue(name, svalue)

    ########################################
    def updateWeatherCatVariables(self, action):
        if self.weathercat:

            # Get variables folder (and create it, if necessary)
            folderId = 0
            if self.folderName != None:
                if self.folderName not in indigo.variables.folders:
                    folder = indigo.variables.folder.create(self.folderName)
                else:
                    folder = indigo.variables.folders[self.folderName]
                folderId = folder.id

            # Update channel-based variables
            for channelNum in self.availableChannels:
                self.weathercat.WorkingChannel.set(channelNum)
                chanVar = self.getIndigoChannelVariableName(channelNum)
                chanName = self.weathercat.WorkingChannelName.get()
                chanValue = "%s" % round(self.weathercat.WorkingChannelValue.get(), 1)

                self.debugLog("Channel %d (%s - %s): %s" % (channelNum, chanVar, chanName, chanValue))

                self.updateIndigoVar(chanVar, chanValue, folderId)

            # Update other variables
            self.updateIndigoVar("WCT_current_conditions", self.weathercat.CurrentConditions.get(), folderId)
            self.updateIndigoVar("WCT_station_status", self.weathercat.StationDriverStatus.get(), folderId)

            windCard = geo.direction_name(self.weathercat.WindDirection.get())
            self.updateIndigoVar("WCT_winddirection_cardinal", windCard, folderId)

            lastUpdateTime = time.strftime("%Y-%m-%d %H:%M:%S")
            self.updateIndigoVar("WCT_last_update", lastUpdateTime, folderId)

    ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo", False)
            if self.debug:
                indigo.server.log("Debug logging enabled")
            else:
                indigo.server.log("Debug logging disabled")

    ########################################
    # Menu Methods
    ########################################
    def toggleDebugging(self):
        if self.debug:
            indigo.server.log("Turning off debug logging")
            self.pluginPrefs["showDebugInfo"] = False
        else:
            indigo.server.log("Turning on debug logging")
            self.pluginPrefs["showDebugInfo"] = True
        self.debug = not self.debug

