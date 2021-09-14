# ****************************************************************************
  #
  # This file is part of the yasmine editing tool.
  #
  # yasmine (Yet Another Station Metadata INformation Editor), a tool to
  # create and edit station metadata information in FDSN stationXML format,
  # is a common development of IRIS and RESIF.
  # Development and addition of new features is shared and agreed between * IRIS and RESIF.
  #
  #
  # Version 1.0 of the software was funded by SAGE, a major facility fully
  # funded by the National Science Foundation (EAR-1261681-SAGE),
  # development done by ISTI and led by IRIS Data Services.
  # Version 2.0 of the software was funded by CNRS and development led by * RESIF.
  #
  # This program is free software; you can redistribute it
  # and/or modify it under the terms of the GNU Lesser General Public
  # License as published by the Free Software Foundation; either
  # version 3 of the License, or (at your option) any later version. *
  # This program is distributed in the hope that it will be
  # useful, but WITHOUT ANY WARRANTY; without even the implied warranty
  # of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  # GNU Lesser General Public License (GNU-LGPL) for more details. *
  # You should have received a copy of the GNU Lesser General Public
  # License along with this software. If not, see
  # <https://www.gnu.org/licenses/>
  #
  #
  # 2019/10/07 : version 2.0.0 initial commit
  #
  # ****************************************************************************/

import copy
import os
import yaml

from obspy.core.inventory.util import *
from obspy.core.inventory.channel import Channel
from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station

import logging
logger = logging.getLogger()

def main():
    show_fields()

    return


inventory_fields = {'source':'IRIS-DMC', 'sender':'IRIS-DMC',
                    'module':'IRIS WEB SERVICE: fdsnws-station | version: 1.1.41',
                    'module_uri' : 'https://seiscode.iris.washington.edu/projects/stationxml-converter/wiki',
                    }

network_fields = {'code':'IU', 'alternate_code':'XX', 'historical_code':'YY',
                  'description':"'This is a network'",
                  'restricted_status':'open',
                  'start_date':'2010-09-01T00:00:00', 'end_date':'2015-03-01T00:00:00',
                  'selected_number_of_stations':162,
                  'total_number_of_stations':195,
                  'source_id':"'example schema:path'",
                  'identifiers':"['id_1 schema:path', 'id_2 schema:path', ...]",
                  'operators':'yml:yml/operators.yml', 'comments':'yml:yml/comments.yml',
                  'data_availability':'yml:yml/data_availability.yml',
                 }

station_fields = {'code':'ANMO', 'alternate_code':'AAAA', 'historical_code':'BBBB',
                  'description':"'this is a station'",
                  'restricted_status':'open',
                  'start_date':'2010-09-01T00:00:00', 'end_date':'2015-03-01T00:00:00',
                  'creation_date':'2010-09-01T00:00:00', 'termination_date':'2010-09-01T00:00:00',
                  'latitude':34.9459, 'longitude':-106.4572, 'elevation':1850.0,
                  'selected_number_of_channels':27,'total_number_of_channels':42,
                  'vault':"'This is a vault string'", 'geology':"'This is a geology string'",
                  'source_id':"'example schema:path'",
                  'identifiers':"['id_1 schema:path', 'id_2 schema:path', ...]",
                  'operators':'yml:yml/operators.yml', 'comments':'yml:yml/comments.yml',
                  'data_availability':'yml:yml/data_availability.yml',
                  'equipments':'yml:yml/equipments.yml',
                  'site':'yml:yml/site.yml', 'external_references':'yml:yml/references.yml'
                 }

channel_fields = {'code':'BHZ', 'location_code':'00', 'location_code':'XXX', 'historical_code':'YYY',
                  'description':"'this is a channel'",
                  'restricted_status':'open',
                  'start_date':'2010-09-01T00:00:00', 'end_date':'2015-03-01T00:00:00',
                  'latitude':34.9459, 'longitude':-106.4572, 'elevation':1850.0, 'depth':100.0,
                  'azimuth':0.0, 'dip':90.0,
                  'water_level':120.0,
                  'types':"['CONTINUOUS', 'GEOPHYSICAL', ...]",

                  'sample_rate':40.0,
                  'sample_rate_ratio_number_samples':40,
                  'sample_rate_ratio_number_seconds':40,
                  'clock_drift_in_seconds_per_sample':0.01,
                  'calibration_units':"'M/S'",
                  'calibration_units_description':"'Velocity in meters per second'",

                  'source_id':"'example schema:path'",
                  'identifiers':"['id_1 schema:path', 'id_2 schema:path', ...]",
                  'operators':'yml:yml/operators.yml', 'comments':'yml:yml/comments.yml',
                  'data_availability':'yml:yml/data_availability.yml',

                  'sensor':'yml:yml/sensor.yml',
                  'data_logger':'yml:yml/data_logger.yml',
                  'pre_amplifier':'yml:yml/pre_amplifier.yml',
                  'equipments':'yml:yml/equipments.yml',

                  'external_references':'yml:yml/references.yml'
                 }
def show_fields():
    """
    yasmine-cli --show_fields  or
    yasmine-cli --show-fields

    For each level (Network, Station, etc), prints out the fields that can be 
        changed with this code
    """

    print("               root: [=default level] ")
    print("%40s    %s" % ('--field', '--value'))
    print("%40s    %s" % ('==========', '=========='))
    for k,v in inventory_fields.items():
        print("%40s    %s" % (k,v))


    print("    --level_network:")
    print("%40s    %s" % ('--field', '--value'))
    print("%40s    %s" % ('==========', '=========='))
    for k,v in network_fields.items():
        print("%40s    %s" % (k,v))

    print()
    print("    --level_station:")
    print("%40s    %s" % ('--field', '--value'))
    print("%40s    %s" % ('==========', '=========='))
    for k,v in station_fields.items():
        print("%40s    %s" % (k,v))

    print()
    print("    --level_channel:")
    print("%40s    %s" % ('--field', '--value'))
    print("%40s    %s" % ('==========', '=========='))
    for k,v in channel_fields.items():
        print("%40s    %s" % (k,v))

    return

def check_field(field, value, level):
    """
    Confirm that field is in obj_dict at level

    :param field:
    :type field:

    :param value:
    :type value:

    :param level: Level at which to apply changes, must be in {'network', 'station', 'channel'}
    :type level: string

    :returns: True if field in obj_dict at specified level
    :rtype: bool
    """

    obj_dict = "%s_fields" % level
    if field not in eval(obj_dict):
        return False
    return True

def read_yml_file(configFile):

    '''
    Read in configFile and use to create some sort of obspy object
    e.g., Network/Station/Channel/Operator/Comment
    return this
    '''

    # ObsPy object that contains another ObsPy object
    obspy_complex_types = ['Operator', 'Comment', 'DataAvailability']

    return_obj = None
    field = None

    with open(configFile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    first_key = list(cfg.keys())[0]

    process_list = False
    if isinstance(cfg[first_key], list):
        obj_key = list(cfg[first_key][0].keys())[0]
        process_list = True
    else:
        obj_key = first_key

    if not process_list:
        obj_dict = cfg[first_key]

        if obj_key in obspy_complex_types:
            func = 'obspy_%s' % obj_key.lower()
            obj, field  = eval(func)(obj_dict)
        else:
            obj, field  = obspy_simple_type(obj_dict, obj_key)

        return obj, field

    else:
        #for obj_dict in cfg[first_key][obj_key]:
        return_list = []
        for item in cfg[first_key]:
            obj_dict = item[obj_key]
            if obj_key in obspy_complex_types:
                func = 'obspy_%s' % obj_key.lower()
                obj, _unused  = eval(func)(obj_dict)
            else:
                obj, _unused  = obspy_simple_type(obj_dict, obj_key)

            return_list.append(obj)
        #field = obj_key.lower() + 's'
        field = first_key.lower()
        return return_list, field

    return


def obspy_person(person_dict):
    phonenumbers = []
    if 'phones' in person_dict and person_dict['phones']:
        for phone in person_dict['phones']:
            phonenumbers.append(PhoneNumber(phone[1:4], phone[5:], description=None))
        person_dict['phones'] = phonenumbers
    try:
        obj = Person(**person_dict)
    except TypeError as e:
        logger.error("Caught: %s" % repr(e))
        raise
    return obj

def obspy_operator(operator_dict):

    if 'agency' not in operator_dict or operator_dict['agency'] is None:
        logger.error("Operator agency field is required! Please set in yml file")
        exit(2)

    if 'contacts' in operator_dict:
        persons =[]
        for contact in operator_dict['contacts']:
            persons.append(obspy_person(contact['person']))
        operator_dict['contacts'] = persons
    try:
        obj = Operator(**operator_dict)
    except TypeError as e:
        logger.error("Caught: %s" % repr(e))
        raise
    return obj, 'operator'

def obspy_comment(comment_dict):

    persons =[]
    for contact in comment_dict['authors']:
        persons.append(obspy_person(contact['author']))

    comment_dict['authors'] = persons
    comment_text = comment_dict.pop('text')
    try:
        obj = Comment(comment_text, **comment_dict)
    except TypeError as e:
        logger.error("Caught: %s" % repr(e))
        raise
    return obj, 'comment'

def obspy_dataavailability(obj_dict):
    if 'spans' in obj_dict and obj_dict['spans']:
        spans = []
        for span in obj_dict['spans']:
            spans.append(DataAvailabilitySpan(**span))
        obj_dict['spans'] = spans
    try:
        obj = DataAvailability(**obj_dict)
    except TypeError as e:
        logger.error("Caught: %s" % repr(e))
        raise
    return obj, 'data_availability'

def obspy_simple_type(obj_dict, obj_key=None):
    '''
    For ObsPy objects that don't contain any other Obspy objects, only simple fields
    '''
    try:
        obj = eval(obj_key)(**obj_dict)
    except TypeError as e:
        logger.error("Caught: %s" % repr(e))
        raise
    return obj, obj_key.lower()


# MTH: Everything below here is a quick hack to override the hard-coded
#      schema version (SCHEMA_VERSION = '1.1') in ObsPy inventory module.
#      The only change is looking through kwargs for 'schema_version='

from lxml import etree

from obspy.io.stationxml.core import _write_network, _write_extra
from obspy.io.stationxml.core import validate_stationxml

import io

def _write_stationxml(inventory, file_or_file_object, validate=False,
                      nsmap=None, level="response", **kwargs):
    """
    Writes an inventory object to a buffer.
    :type inventory: :class:`~obspy.core.inventory.Inventory`
    :param inventory: The inventory instance to be written.
    :param file_or_file_object: The file or file-like object to be written to.
    :type validate: bool
    :param validate: If True, the created document will be validated with the
        StationXML schema before being written. Useful for debugging or if you
        don't trust ObsPy. Defaults to False.
    :type nsmap: dict
    :param nsmap: Additional custom namespace abbreviation mappings
        (e.g. `{"edb": "http://erdbeben-in-bayern.de/xmlns/0.1"}`).

    """

    SCHEMA_VERSION = '1.1'

    if 'schema_version' in kwargs and kwargs['schema_version'] is not None:
        SCHEMA_VERSION = kwargs['schema_version']
        logger.info("_write_stationxml: set output schema_version=[%s]" % SCHEMA_VERSION)

    if nsmap is None:
        nsmap = {}
    elif None in nsmap:
        msg = ("Custom namespace mappings do not allow redefinition of "
               "default StationXML namespace (key `None`). "
               "Use other namespace abbreviations for custom namespace tags.")
        raise ValueError(msg)

    nsmap[None] = "http://www.fdsn.org/xml/station/1"
    attrib = {"schemaVersion": SCHEMA_VERSION}

    root = etree.Element("FDSNStationXML", attrib=attrib, nsmap=nsmap)

    etree.SubElement(root, "Source").text = inventory.source
    if inventory.sender:
        etree.SubElement(root, "Sender").text = inventory.sender

    # Undocumented flag that does not write the module flags. Useful for
    # testing. It is undocumented because it should not be used publicly.
    if kwargs.get("_suppress_module_tags", False):
        pass
    else:
        etree.SubElement(root, "Module").text = inventory.module
        etree.SubElement(root, "ModuleURI").text = inventory.module_uri

    etree.SubElement(root, "Created").text = str(inventory.created)

    if level not in ["network", "station", "channel", "response"]:
        raise ValueError("Requested stationXML write level is unsupported.")

    for network in inventory.networks:
        _write_network(root, network, level)

    # Add custom namespace tags to root element
    _write_extra(root, inventory)

    tree = root.getroottree()

    # The validation has to be done after parsing once again so that the
    # namespaces are correctly assembled.
    if validate is True:
        buf = io.BytesIO()
        tree.write(buf)
        buf.seek(0)
        # This works since ObsPy validate_stationxml gets version from the xml
        validates, errors = validate_stationxml(buf)
        buf.close()
        if validates is False:
            msg = "The created file fails to validate.\n"
            for err in errors:
                msg += "\t%s\n" % err
            raise Exception(msg)

    # Register all namespaces with the tree. This allows for
    # additional namespaces to be added to an inventory that
    # was not created by reading a StationXML file.
    for prefix, ns in nsmap.items():
        if prefix and ns:
            etree.register_namespace(prefix, ns)

    tree.write(file_or_file_object, pretty_print=True, xml_declaration=True,
               encoding="UTF-8")


if __name__ == '__main__':
    main()
