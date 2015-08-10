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

kPrefVarsFolder = "varsFolder"
kPrefRoundDigits = "roundDigits"
kPrefPollInterval = "pollInterval"
kPrefShowDebugInfo = "showDebugInfo"

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
    pollInterval = 0
    roundDigits = 1

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.updateConfiguration()

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
                    chanValue = "%s" % round(self.weathercat.WorkingChannelValue.get(), self.roundDigits)

                    self.debugLog(" Channel %d (%s - %s): %s" % (channelNum, chanVar, chanName, chanValue))
                    self.availableChannels.append(channelNum)

        except Exception, e:
            self.debugLog("Error talking to WeatherCat:\n%s" % str(e))
            self.errorLog("WeatherCat is not running or not available")

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    def runConcurrentThread(self):
        try:
            while True:
                if self.pollInterval > 0:
                    if (self.weathercat != None):
                        self.debugLog("Polling WeatherCat")
                        self.updateWeatherCatVariables()

                    else:
                        if self.weathercat:
                            self.errorLog("WeatherCat is not running or not available")

                    self.sleep(self.pollInterval)
                else:
                    # Check every 5 seconds if the poll interval has changed
                    self.sleep(5)

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
    def updateIndigoVar(self, name, label, value, folder):
        svalue = "%s" % value
        if name not in indigo.variables:
            indigo.variable.create(name, value=svalue, folder=folder)
        else:
            indigo.variable.updateValue(name, svalue)

        self.debugLog("%s [%s]: %s" % (label, name, value))

    ########################################
    def updateWeatherCatVariables(self):
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
            for chanNum in self.availableChannels:
                self.weathercat.WorkingChannel.set(chanNum)
                chanVar = self.getIndigoChannelVariableName(chanNum)
                chanName = self.weathercat.WorkingChannelName.get()
                chanValue = ("%." + str(self.roundDigits) + "f") % self.weathercat.WorkingChannelValue.get()
                #chanValue = "%s" % round(self.weathercat.WorkingChannelValue.get(), self.roundDigits)
                label = "%s - Channel %d" % (chanName, chanNum)

                self.updateIndigoVar(chanVar, label, chanValue, folderId)

            # Update other variables
            self.updateIndigoVar("WCT_current_conditions", "Current Conditions", self.weathercat.CurrentConditions.get(), folderId)
            self.updateIndigoVar("WCT_station_status", "Station Status", self.weathercat.StationDriverStatus.get(), folderId)

            windCard = geo.direction_name(self.weathercat.WindDirection.get())
            self.updateIndigoVar("WCT_winddirection_cardinal", "Wind Direction (cardinal)", windCard, folderId)

            lastUpdateTime = time.strftime("%Y-%m-%d %H:%M:%S")
            self.updateIndigoVar("WCT_last_update", "Last Update Time", lastUpdateTime, folderId)

    ########################################
    def updateWeatherCatVariablesAction(self, action):
        self.updateWeatherCatVariables()

    ########################################
    def updateWeatherCatVariablesMenuItem(self):
        self.updateWeatherCatVariables()

    ########################################
    def validatePrefsConfigUi(self, valuesDict):
        errorsDict = indigo.Dict()

        self.validatePositiveInteger(valuesDict, kPrefPollInterval, errorsDict)
        self.validatePositiveInteger(valuesDict, kPrefRoundDigits, errorsDict)

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        else:
            return True

    def validatePositiveInteger(self, valuesDict, prefKey, errorsDict):
        try:
            value = int(valuesDict.get(prefKey, 1))
            if(value < 0):
                errorsDict[prefKey] = "Value must be a positive integer"
        except ValueError:
            errorsDict[prefKey] = "Value must be an integer"

    def updateConfiguration(self):
            self.debug = self.pluginPrefs.get(kPrefShowDebugInfo, False)
            if self.debug:
                indigo.server.log("Debug logging enabled")
            else:
                indigo.server.log("Debug logging disabled")

            self.folderName = self.pluginPrefs.get(kPrefVarsFolder, None)
            self.debugLog("Variables folder set to %s" % self.folderName)

            self.roundDigits = int(self.pluginPrefs.get(kPrefRoundDigits, 1))
            self.debugLog("Rounding values to %d digits" % self.roundDigits)

            self.pollInterval = int(self.pluginPrefs.get(kPrefPollInterval, 0))
            if self.pollInterval == 0:
                self.debugLog("Automatic refresh disabled")
            else:
                self.debugLog("Refresh interval set to %i seconds" % self.pollInterval)



    ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.updateConfiguration()

    ########################################
    # Menu Methods
    ########################################
    def toggleDebugging(self):
        if self.debug:
            indigo.server.log("Turning off debug logging")
            self.pluginPrefs[kPrefShowDebugInfo] = False
        else:
            indigo.server.log("Turning on debug logging")
            self.pluginPrefs[kPrefShowDebugInfo] = True
        self.debug = not self.debug

