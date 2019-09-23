#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# complete Robonect API is at https://forum.robonect.de/viewtopic.php?f=10&t=37

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import json
from robonect.robonect_client import SnipsRobonect

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

# each intent has a language associated with it
# extract language of first intent of assistant since there should only be one language per assistant
lang = json.load(open('/usr/share/snips/assistant/assistant.json'))['intents'][0]['language']

class SnipsConfigParser(configparser.SafeConfigParser):
	def to_dict(self):
		return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
	try:
		with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
			conf_parser = SnipsConfigParser()
			conf_parser.readfp(f)
			return conf_parser.to_dict()
	except (IOError, ConfigParser.Error) as e:
		return dict()


def subscribe_intent_callback(hermes, intentMessage):
	user,intentname = intentMessage.intent.intent_name.split(':')  # the user can fork the intent with this method
	if intentname in ["GetStatusMower","StopMower","StartMower","SetModeMower"]:
		conf = read_configuration_file(CONFIG_INI)
		action_wrapper(hermes, intentMessage, conf)
	else:
		pass

def action_wrapper(hermes, intentMessage, conf):
	""" Write the body of the function that will be executed once the intent is recognized.
	In your scope, you have the following objects :
	- intentMessage : an object that represents the recognized intent
	- hermes : an object with methods to communicate with the MQTT bus following the hermes protocol.
	- conf : a dictionary that holds the skills parameters you defined

	Refer to the documentation for further details.
	"""
	intentname = intentMessage.intent.intent_name.split(':')[1]
	robonect = SnipsRobonect(
	conf["secret"]["ipaddress"],
	conf["secret"]["username"],
	conf["secret"]["password"])

	if intentname == "GetStatusMower":
		mower = robonect.getStatus()
		name = mower["name"]
		battery = mower["status"]["battery"]

		if lang == 'de':
			scode = {
			0: u'der Status wird ermittelt',1: u'parkt',2: u'mäht',
			3: u'sucht die Ladestation',4: u'lädt',5: u'sucht (wartet auf das Umsetzen im manuellen Modus)',
			7: u'ist im Fehlerstatus',8: u'hat das Schleifensignal verloren',16: u'ist abgeschaltet',17: u'schläft'}[mower["status"]["status"]]
			mcode = {0: 'Auto',1: 'manuell',2: 'zu Hause',3: 'Demo'}[mower["status"]["mode"]]
			result_sentence = u'Die Batterie von %s ist %s%% geladen. Der Rasenmäher ist im Modus %s und %s'% (name,battery,mcode,scode)

		elif lang == 'en':
			scode = {
			0: u'status check in progress',1: u'parking',2: u'mowing',
			3: u'searching for charging station',4: u'charging',5: u'searching (wating for change to manual mode)',
			7: u'is in error state',8: u'has lost the loop signal',16: u'is powered down',17: u'sleeping'}[mower["status"]["status"]]
			mcode = {0: 'Auto',1: 'manual',2: 'home',3: 'Demo'}[mower["status"]["mode"]]
			result_sentence = u'Charge level of the battery for %s is %s%%. The moweris in %s mode and %s'% (name,battery,mcode,scode)

	if intentname == "StopMower":
		mower = robonect.getStatus()
		if mower["status"]["stopped"] is True:
			if lang == 'de':
				result_sentence = u'%s is bereits gestoppt'% (mower["name"])
			elif lang == 'en':
				result_sentence = u'%s has stopped already'% (mower["name"])

		else:
			robonect.stop()
			mower = robonect.getStatus()
			if mower["status"]["stopped"] is True:
				if lang == 'de':
					result_sentence = u'%s wurde erfolgreich gestoppt'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s has been stopped'% (mower["name"])
			else:
				if lang == 'de':
					result_sentence = u'%s konnte nicht erfolgreich gestoppt werden'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s could not be stopped successfully'% (mower["name"])

	if intentname == "StartMower":
		mower = robonect.getStatus()
		if mower["status"]["stopped"] is False:
			if lang == 'de':
				result_sentence = u'%s is bereits gestartet'% (mower["name"])
			elif lang == 'en':
				result_sentence = u'%s has been started already'% (mower["name"])
		else:
			robonect.start()
			mower = robonect.getStatus()
			if mower["status"]["stopped"] is False:
				if lang == 'de':
					result_sentence = u'%s wurde erfolgreich gestartet'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s has been started successfully'% (mower["name"])
			else:
				if lang == 'de':
					result_sentence = u'%s konnte nicht erfolgreich gestartet werden'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s could not be started successfully'% (mower["name"])

	if intentname == "SetModeMower":
		for (slot_value, slot) in intentMessage.slots.items():
			print(slot[0].slot_value.value.value.encode('utf-8'))
			print('Slot {} -> \n\tRaw: {} \tValue: {}'.format(slot_value, slot[0].raw_value, slot[0].slot_value.value.value))
		mower = robonect.getStatus()
		if slot[0].slot_value.value.value == 'auto':
			if mower["status"]["mode"] == 0:
				if lang == 'de':
					result_sentence = u'%s ist bereits im Auto-Modus'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s is already in auto mode'% (mower["name"])
			else:
				robonect.setMode("auto")
				if lang == 'de':
					result_sentence = u'%s ist jetzt im Auto-Modus'% (mower["name"])
				elif lang == 'en':
					result_sentence = u'%s is now in auto mode'% (mower["name"])
		# elif slot[0].slot_value.value.value == 'manuell':
		# 	if mower["status"]["mode"] == 1:
		# 		if lang == 'de':
		# 			result_sentence = u'%s ist bereits im manuellen Modus'% (mower["name"])
		# 		elif lang == 'en':
		# 			result_sentence = u'%s is already in manual mode'% (mower["name"])
		# 	else:
		# 		robonect.setMode('man')
		# 		if lang == 'de':
		# 			result_sentence = u'%s ist jetzt im manuellen Modus'% (mower["name"])
		# 		elif lang == 'en':
		# 			result_sentence = u'%s is now in manual mode'% (mower["name"])
		# elif slot[0].slot_value.value.value == 'home':
		# 	if mower["status"]["mode"] == 2:
		# 		if lang == 'de':
		# 			result_sentence = u'%s ist bereits im Modus home'% (mower["name"])
		# 		elif lang == 'en':
		# 			result_sentence = u'%s is in home mode already'% (mower["name"])
		# 	else:
		# 		robonect.setMode('home')
		# 		if lang == 'de':
		# 			result_sentence = u'%s ist jetzt im Modus home'% (mower["name"])
		# 		elif lang == 'en':
		# 			result_sentence = u'%s is in mode home now'% (mower["name"])
		else:
			result_sentence = u'%s Fehler'% (mower["name"])

	print(result_sentence)

	hermes.publish_end_session(intentMessage.session_id, result_sentence)

if __name__ == "__main__":
	with Hermes("localhost:1883") as h:
		h.subscribe_intents(subscribe_intent_callback).start()
