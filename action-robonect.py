#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# complete Robonect API ist at https://forum.robonect.de/viewtopic.php?f=10&t=37

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
from robonect.robonect_client import SnipsRobonect


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(ConfigParser.SafeConfigParser):
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
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, intentname, conf)


def action_wrapper(hermes, intentMessage, intentname, conf):
    """ Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    #- conf : a dictionary that holds the skills parameters you defined 

    Refer to the documentation for further details. 
    """

    robonect = SnipsRobonect(
	conf["secret"]["ipaddress"],
	conf["secret"]["username"],
	conf["secret"]["password"])

    if intentname == "GetStatusMower":
	mower = robonect.getStatus()
	mower_status_codes = {
	    0: u'der Status wird ermittelt',
	    1: u'parkt',
	    2: u'mäht',
	    3: u'sucht die Ladestation',
	    4: u'lädt',
	    5: u'sucht (wartet auf das Umsetzen im manuellen Modus)',
	    7: u'ist im Fehlerstatus',
	    8: u'hat das Schleifensignal verloren',
	    16: u'ist abgeschaltet',
	    17: u'schläft'}
	mower_mode_codes = {
	    0: 'Auto',
	    1: 'manuell',
	    2: 'zu Hause',
	    3: 'Demo'}

	result_sentence = u'Die Batterie von %s ist %s%% geladen. Der Rasenmäher ist im Modus %s und %s'% (
	    mower["name"],
	    mower["status"]["battery"],
	    mower_mode_codes[mower["status"]["mode"]],
	    mower_status_codes[mower["status"]["status"]])
	hermes.publish_end_session(intentMessage.session_id, result_sentence.encode('utf-8'))


    if intentname == "StopMower":
	mower = robonect.getStatus()
	if mower["status"]["stopped"] is True:
	    result_sentence = u'%s is bereits gestoppt'% (mower["name"])
	else:
	    robonect.stop()
	    mower = robonect.getStatus()
	    if mower["status"]["stopped"] is True:
		result_sentence = u'%s wurde erfolgreich gestoppt'% (mower["name"])
	    else:
		result_sentence = u'%s konnte nicht erfolgreich gestoppt werden'% (mower["name"])
	hermes.publish_end_session(intentMessage.session_id, result_sentence.encode('utf-8'))

    if intentname == "StartMower":
	mower = robonect.getStatus()
	if mower["status"]["stopped"] is False:
	    result_sentence = u'%s is bereits gestartet'% (mower["name"])
	else:
	    robonect.start()
	    mower = robonect.getStatus()
	    if mower["status"]["stopped"] is False:
		result_sentence = u'%s wurde erfolgreich gestartet'% (mower["name"])
	    else:
		result_sentence = u'%s konnte nicht erfolgreich gestartet werden'% (mower["name"])
	hermes.publish_end_session(intentMessage.session_id, result_sentence.encode('utf-8'))

    if intentname == "SetModeMower":
	for (slot_value, slot) in intentMessage.slots.items():
	    print('Slot {} -> \n\tRaw: {} \tValue: {}'.format(slot_value, slot[0].raw_value, slot[0].slot_value.value.value))
	mower = robonect.getStatus()
	if slot[0].slot_value.value.value == 'auto':
	    if mower["status"]["mode"] == 0:
		result_sentence = u'%s ist bereits im Auto-Modus'% (mower["name"])
	    else:
		robonect.setMode("auto") # man | eod | home
		result_sentence = u'%s ist jetzt im Auto-Modus'% (mower["name"])
	elif slot[0].slot_value.value.value == 'manuell':
	    if mower["status"]["mode"] == 1:
		result_sentence = u'%s ist bereits im manuellen Modus'% (mower["name"])
	    else:
		robonect.setMode('man') # man | eod | home
		result_sentence = u'%s ist jetzt im manuellen Modus'% (mower["name"])
	elif slot[0].slot_value.value.value == 'home':
	    if mower["status"]["mode"] == 2:
		result_sentence = u'%s ist bereits im Modus hohm'% (mower["name"])
	    else:
		robonect.setMode('home') # man | eod | home
		result_sentence = u'%s ist jetzt im Modus hohm'% (mower["name"])
	hermes.publish_end_session(intentMessage.session_id, result_sentence.encode('utf-8'))
    else:
	result_sentence = u'Irgendwas hat nicht hingehauen'
	hermes.publish_end_session(intentMessage.session_id, result_sentence.encode('utf-8')) 


if __name__ == "__main__":
    """
    conf = read_configuration_file("config.ini")

    if conf.get("secret").get("hostname") is None:
        print "No ipaddress in config.ini, you must setup the ipaddress of your mower for this skill to work"
    elif len(conf.get("secret").get("username")) == 0:
        print "No username in config.ini, you must set the username to access your mower for this skill to work"
    elif len(conf.get("secret").get("password")) == 0:
        print "No password in config.ini, you must set the password to access your  mower for this skill to work"

    skill_locale = config["global"].get("locale", "de_DE")

    skill = SnipsRobonect(conf["secret"]["ipaddress"],
                     conf["secret"]["username"],conf["secret"]["password"],locale=skill_locale)
    lang = "DE"
"""
    with Hermes("localhost:1883") as h:
#        h.skill = skill
        h.subscribe_intents(subscribe_intent_callback).start()
