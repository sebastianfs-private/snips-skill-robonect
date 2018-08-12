#!/usr/bin/env python2
# -*- coding: utf-8 -*-

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
    if intentname == "GetStatusMower":
        conf = read_configuration_file(CONFIG_INI)
        action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
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
    robonect_status = robonect.getStatus()
    result_sentence = "Batteriestatus fuer %s ist %s%%" % (
        robonect_status["name"],
        robonect_status["status"]["battery"])
    current_session_id = intentMessage.session_id
    hermes.publish_end_session(current_session_id, result_sentence)

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
