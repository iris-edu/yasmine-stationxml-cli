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
import sys
from sys import exit

import tempfile

from obspy import read_inventory
from obspy.core.inventory.inventory import Inventory
from obspy.core.inventory.channel import Channel
from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station

import logging
logger = logging.getLogger()

from .. import fdsn_schema_dir, installation_dir

#from libs.libs_xml import valid_xmlfiles, get_schema_version, check_files
from .libs_xml import validate_stationxml, get_schema_version, check_files
from .libs_obs import _write_stationxml
from .plot_poly_resp import plot_polynomial_resp

import threading

def edit_xml_to_inv(args, scnl_filter):
    """
    Read in xml file(s), determine schema version, validate against schema version
        Perform desired modifications (update/delete/add) to metadata
        Return modified metadata in Inventory format

    :param args: Determines what modifications to make to input metadata
    :type args: class argparse.Namespace

    :param scnl_filter: Filter that determines level (network, station, channel) at which to
                        apply modifications
    :type scnl_filter: Simple python struct for holding attributes

    :returns: Modified metadata in obspy inventory format
    :rtype: obspy.core.inventory.inventory

    :returns: Schema_version
    :rtype: string
    """

    fname = 'edit_xml_to_inv'

    cleanup_files = []
    # Verify all input xml file(s) exist
    if args.infiles:
        valid = check_files(args.infiles) # Make sure files exist, are readable, etc.
        if not valid:
            logger.error("One or more xmlfiles could not be read --> STOP EXECUTION")
            exit(2)
    else:
        read_stdin = True
        tf = tempfile.NamedTemporaryFile(delete=False)
        infile = tf.name
        logger.info("Read from stdin infile=[%s] thread=[%s]" % (infile, threading.get_ident()))

        # How to get version direct from stdin either as file or buffer:
        #   If you haven't exhausted sys.stdin, you could do:
        #   schema_version = get_schema_version(sys.stdin)   // read xmlfile to get version
        #   or, you could parse it and do:
        #   buf = ""
        #   for line in sys.stdin:
               #buf += line
        #   schema_version = get_schema_version(buf)         // read from xml_string
        #   schema_version = get_schema_version(infile)      // read from infile

        with open(infile, 'w') as f:
            for line in sys.stdin:
                f.write(line)
        args.infiles = [infile]
        cleanup_files.append(infile)


    # Verify all file(s) have same stationxml schema version:
    versions = []
    for xmlfile in args.infiles:
        versions.append(get_schema_version(xmlfile))
    if len(set(versions)) > 1:
        logger.error("Input files have different schema versions --> Exit")
        exit(2)

    # Validate input xml files against schema
    #          where schema version = --args.schema_version (if set)  *or* schema version of input files
    schema_version = None
    if not args.dont_validate:           # Check for valid StationXML
        valid = True
        for xmlfile in args.infiles:
            schema_version = get_schema_version(xmlfile)
            logger.info("Input schema_version=%s" % schema_version)
            if args.schema_version:
                logger.info("Input files version:[%s] --> Request output version:[%s]" % \
                            (schema_version, args.schema_version))
                schema_version = args.schema_version

            schema_file = os.path.join(fdsn_schema_dir(), 'fdsn-station-%s.xsd' % schema_version)
            logger.info("Check file:%s against schema_file:%s" % (xmlfile, schema_file))
            valid, errors = validate_stationxml(xmlfile, schema_file)

            if not valid:
                for error in errors:
                    logger.error(error)
                logger.error("File:%s does not validate against schema version:[%s]" % \
                            (xmlfile, schema_version))

        if not valid:
            logger.error("One or more xmlfiles are NOT valid StationXML --> STOP EXECUTION")
            exit(2)

    # Read all input xml
    xml_list = load_xmlfiles(args.infiles)

    '''
    for tmpfile in cleanup_files:
        try:
            os.remove(tmpfile)
        except:
            raise
    '''

    if not xml_list:
        logger.error("No xml files loaded --> exit")
        exit(2)

    if args.print_epochs:
        print_all(xml_list, args)
        exit(2)

    # Perform the action
    if args.action == 'delete':
        delete_base_node(xml_list, args.level, scnl_filter)
    elif args.action == 'add':
        add_base_node(xml_list, scnl_filter, args.level, args.value)
    elif args.action == 'update':
        if args.use_index:
            logger.info("Call update_field: field %s[%d] = value=%s" % (args.field, args.field_index, args.value))
        else:
            logger.info("Call update_field: field %s = value=%s" % (args.field, args.value))
        if args.update_root:
            update_root_field(xml_list, args)
        else:
            update_field(xml_list, scnl_filter, args)
    elif args.action == 'select':
        #filter_xml(xml_list, args.level, scnl_filter)
        filter_xml(xml_list, scnl_filter)

    # Output the modified inventory/stationxml
    inv_new = pack_xml_list_to_inv(xml_list)

    return inv_new, schema_version

#import matplotlib
#matplotlib.use('TkAgg')
#matplotlib.use('agg')
import matplotlib.pyplot as plt

def plot_responses(inventory, plot_dir):
    """
        Loop over channels in inventory, create response plot for each
            channel and save to file in plot_dir
        Response may be 'normal' (= use obspy response.plot()) or
            polynomial (= use plot_polynomial_response() to generate fig)


    """
    if plot_dir is None:
        plot_dir = "."

    else:
        if not os.path.exists(plot_dir):
            try:
                os.makedirs(plot_dir)
            except OSError as e:
                logger.error("Can't create plot_dir: %s --> Check permissions" % (plot_dir))
                exit(2)

    level=logger.level
    logger.setLevel(30)

    min_freq = .001

    logger.info("plot_responses: plot_dir=[%s]" % plot_dir)

    for network in inventory.networks:
        for station in network.stations:
            for channel in station.channels:
                sampling_rate = channel.sample_rate if channel.sample_rate > 0 else 100.

                if channel.start_date is not None:
                    start = channel.start_date.datetime.strftime('%Y-%m-%dT%H:%M:%S')
                    end = channel.end_date.datetime.strftime('%Y-%m-%dT%H:%M:%S') if channel.end_date else None
                    label = "%s.%s.%s.%s.%s-%s" % (network.code, station.code, channel.code,
                                                      channel.location_code, start, end)
                else:
                    label = "%s.%s.%s.%s" % (network.code, station.code, channel.code,
                                                   channel.location_code)
                outfile = label + ".png"
                outfile = os.path.join(plot_dir, outfile)

                if channel.response.instrument_polynomial:
                    #logger.warning("%s.%s.%s.%s has instrument_polynomial: "
                                #"Polynomial response plot not yet supported" %
                                #(network.code, station.code, channel.code, channel.location_code))
                    label = "%s.%s.%s.%s polynomial response" % \
                            (network.code, station.code, channel.code, channel.location_code)
                    fig = plot_polynomial_resp(channel.response, label=label,
                                               axes=None, outfile=outfile)

                else:
                    print("MTH: label=%s" % label)
                    fig = channel.response.plot(min_freq, output="VEL", unwrap_phase=False,
                                                sampling_rate=sampling_rate, label=label,
                                                outfile=outfile)
                    plt.close(fig)

    logger.setLevel(level)

    return

def filter_xml(xml_list, scnl_filter):
    """
    Filter (remove) elements defined in scnl_filter from xml_list

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :param scnl_filter: Filter that determines level (network, station, channel) at which to
                        apply modifications
    :type scnl_filter: Simple python struct for holding attributes

    """

    if scnl_filter.NET:
        for xml_dict in xml_list:
            for net_code in xml_dict['net_codes']:
                if net_code != scnl_filter.NET:
                    try:
                        logger.info("Ignore network=%s" % net_code)
                        xml_dict['net_codes'].pop(net_code)
                    except KeyError:
                        logger.error("Key not found:%s" % net_code)
                else:
                    logger.info("Net:%s passed filter" % net_code)

    if scnl_filter.STA:
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                for sta_code in list(net_dict['sta_codes'].keys()):
                    if sta_code != scnl_filter.STA:
                        try:
                            logger.info("Ignore station=%s" % sta_code)
                            net_dict['sta_codes'].pop(sta_code)
                        except KeyError:
                            logger.error("Key not found:%s" % sta_code)
                    else:
                        logger.info("Sta:%s passed filter" % sta_code)

    return


def update_root_field(xml_list, args):
    """
    Update a root field of FDSN StationXML within xml_list

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :param args: Determines what modifications to make to input metadata
    :type args: class argparse.Namespace
    """
    update_pair = args.update_pair
    field = update_pair[0]
    value = update_pair[1]
    for xml in xml_list:
        if field in xml.keys():
            xml[field] = value
            logger.info("Update_root field:%s to value=[%s]" % (field, value))
    return

def update_field(xml_list, scnl_filter, args):
    """
    Update a non-root field of FDSN StationXML within xml_list

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :param scnl_filter: Filter that determines level (network, station, channel) at which to
                        apply modifications
    :type scnl_filter: Simple python struct for holding attributes

    :param args: Determines what modifications to make to input metadata
    :type args: class argparse.Namespace
    """
    update_pair = args.update_pair

    level = args.level

    update_pair = args.update_pair
    field = update_pair[0]
    value = update_pair[1]

    '''
    if basenodetype.attrib is a list and we:
        1. pass in value = list ==> replace old list with new list, even if new list = Empty
            network.operators = value  * This is the same if both attrib and field are scalars!
        2. pass in value = scalar
           if:
               i) --index is not used: append this value to end of old list
                    network.operators.append(value)
              ii) --index is used: replace element at old_list[index] with value
                    network.operators[INDEX] = value
    '''

    def _set_field(basenodeobj, field):

        if hasattr(basenodeobj, field):
            if args.update in {'list_modify', 'list_append'}:
                current_list = getattr(basenodeobj, field, None)
                if args.update == 'list_append':
                    logger.info("Append to end of list of len:%d" % (len(current_list)))
                    current_list.append(value)
                else: # Modify list (if value=None --> remove item)
                    if len(current_list) <= scnl_filter.INDEX:
                        logger.error("Current_list is of len=%d <= index=%d" % \
                                    (len(current_list), scnl_filter.INDEX))
                        return False
                    if value is None:
                        item = current_list.pop(scnl_filter.INDEX)
                        logger.info("Remove item at INDEX=%d :%s" % (scnl_filter.INDEX, item))

                    else:
                        logger.info("Modify current list index=%d of len:%d" % 
                                   (scnl_filter.INDEX, len(current_list)))
                        current_list[scnl_filter.INDEX] = value
            else:
                logger.info("Simply set field=value. field=%s value=%s" % (field, value))
                try:
                    setattr(basenodeobj, field, value)
                except (TypeError, ValueError) as e:
                    logger.error("Unable to set field:%s to value:%s Caught=[%s]" % \
                                (field, value, repr(e)))
                    return False
        else:
            logger.warning("basenodeobj has no attr=[%s]" % (field))
            return False

        return True

    success = False

    logger.info("update_field: level:%s field:%s value:%s" % (level, field, value))

    if level == 'network':
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                if not scnl_filter.NET or scnl_filter.NET == net_code:
                    network = net_dict['network']
                    logger.info("Update: net:%s ==> field:%s" % (network.code, field))
                    success = _set_field(network, field)

    elif level == 'station':
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                if not scnl_filter.NET or scnl_filter.NET == net_code:
                    for sta_code in list(net_dict['sta_codes'].keys()):
                        if not scnl_filter.STA or scnl_filter.STA == sta_code:
                            for i, station in enumerate(net_dict['sta_codes'][sta_code]):
                                if scnl_filter.STN_EPOCH is None or scnl_filter.STN_EPOCH == i:
                                    logger.info("Update net:%s stn:%s [%d] field:%s" % \
                                                (net_code, sta_code, i, field))
                                    success = _set_field(station, field)
    else:
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                if not scnl_filter.NET or scnl_filter.NET == net_code:
                    for sta_code, station_epochs in net_dict['sta_codes'].items():
                        if not scnl_filter.STA or scnl_filter.STA == sta_code:
                            for istn, station in enumerate(station_epochs):
                                for ichn, channel in enumerate(station.channels):
                                    keycode = "%s.%s" % (channel.code, channel.location_code)
                                    if not scnl_filter.LOC or scnl_filter.LOC == channel.location_code:
                                      if not scnl_filter.CHA or scnl_filter.CHA == channel.code:

                                        if (scnl_filter.STN_EPOCH is None or scnl_filter.STN_EPOCH == istn) and \
                                           (scnl_filter.CHN_EPOCH is None or scnl_filter.CHN_EPOCH == ichn):
                                            logger.info("Update net:%s stn:%s [%d] chn:%s [%d] field:%s" % \
                                                        (net_code, sta_code, istn, keycode, ichn, field))
                                            success = _set_field(channel, field)
    if not success:
        logger.error("Update failed, either because no matching basenodes found or because of error setting attrib")
    return



def add_base_node(xml_list, scnl_filter, level, obj):
    """
    Locate the appropriate position in xml_list and insert a new 
        base node (Network, Station or Channel object).

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :param level: Level at which to apply changes, must be in {'network', 'station', 'channel'}
    :type level: string

    :param scnl_filter: simple python object holding NET, STA, CHA, LOC attributes that mods apply to
    :type scnl_filter: python class used as container

    :param obj: Obspy base_node object (Network, Station, Channel)
    :type obj: obspy.core.inventory.network.Network, obspy.core.inventory.station.Station or obspy.core.inventory.channel.Channel
    """

    if isinstance(obj, Network):
        logger.info("Add Network: Note that level is ignored since Network can only go in root")
        for xml_dict in xml_list:
            if obj.code in xml_dict['net_codes']:
                logger.warning("Warning: Network code:[%s] already exists!" % obj.code)
            else:
                logger.info("Add Network code:[%s] to xml_dict" % obj.code)

                xml_dict['net_codes'][obj.code] = {}
                xml_dict['net_codes'][obj.code]['network'] = obj
                xml_dict['net_codes'][obj.code]['sta_codes'] = {}

# MTH: if obj = Station, then it can go in 1...N networks specified by filter
# Right now the new Station is added to end of each network stations list
# This could be changed to (re)filter the network dicts by alphabet/time before writing xml

    elif isinstance(obj, Station):
        if level != 'network':
            logger.error("Add Station: You *must* use level_network=.. to specify which network(s) get the new station")
            return None
        else:
            for xml_dict in xml_list:
                for net_code, net_dict in xml_dict['net_codes'].items():
                    if not scnl_filter.NET or scnl_filter.NET == net_code:
                    # If this station code already present append a new epoch to its list of Station (epochs)
                        if obj.code in net_dict['sta_codes']:
                            net_dict['sta_codes'][obj.code].append(obj)
                        else:
                            net_dict['sta_codes'][obj.code] = [obj]

# MTH: To add a Channel we need to know which Station(s) will get it
    elif isinstance(obj, Channel):
        if level != 'station':
            logger.error("Add Channel: You *must* use level_station=.. to specify which station(s) get the new channel")
            return None
        else:
            for xml_dict in xml_list:
                for net_code, net_dict in xml_dict['net_codes'].items():
                    if not scnl_filter.NET or scnl_filter.NET == net_code:
                        for sta_code, station_epochs in net_dict['sta_codes'].items():
                            if not scnl_filter.STA or scnl_filter.STA == sta_code:
                                #for station in station_epochs:
                                    #for channel in station.channels:

                                # Inside matching sta_code - which epoch gets it ?
                                station_epochs[-1].channels.append(obj)

    else:
        logger.error("ERROR: Unknown combination: obj type:%s + level" % (type(obj)))

def delete_base_node(xml_list, level, scnl_filter):
    """
    Find the base_node specified via level + scnl_filter and delete from xml_list

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :param level: Level at which to apply changes, must be in {'network', 'station', 'channel'}
    :type level: string

    :param scnl_filter: simple python object holding NET, STA, CHA, LOC attributes that mods apply to
    :type scnl_filter: python class used as container
    """

    if level == 'network':
        for xml_dict in xml_list:
            if scnl_filter.NET in xml_dict['net_codes']:
                try:
                    logger.info("Delete network=%s" % scnl_filter.NET)
                    xml_dict['net_codes'].pop(scnl_filter.NET)
                except KeyError:
                    logger.error("Key not found:%s" % scnl_filter.NET)

    elif level == 'station':
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                if not scnl_filter.NET or scnl_filter.NET == net_code:

                    for sta_code in list(net_dict['sta_codes'].keys()):
                        if not scnl_filter.STA or scnl_filter.STA == sta_code:

                            if scnl_filter.STN_EPOCH is None: # Could have scnl_filter.STN_EPOCH = 0
                                try:
                                    logger.info("Delete net:%s stn:%s all epochs" % (net_code, sta_code))
                                    net_dict['sta_codes'].pop(sta_code)
                                except KeyError:
                                    logger.error("Key not found:%s" % sta_code)
                            else:
                                epochs = net_dict['sta_codes'][sta_code]
                                cleaned_epochs = []
                                for i, epoch in enumerate(epochs):
                                    if i == scnl_filter.STN_EPOCH:
                                        logger.info("Delete net:%s stn:%s epoch:%d" % (net_code, sta_code, i))
                                    else:
                                        cleaned_epochs.append(epoch)

                                net_dict['sta_codes'][sta_code] = cleaned_epochs

    else:
        for xml_dict in xml_list:
            for net_code, net_dict in xml_dict['net_codes'].items():
                if not scnl_filter.NET or scnl_filter.NET == net_code:
                    for sta_code, station_epochs in net_dict['sta_codes'].items():
                        if not scnl_filter.STA or scnl_filter.STA == sta_code:
                            for istn, station in enumerate(station_epochs):
                                cleaned_channels = copy.deepcopy(station.channels)
                                modified = False
                                for ichn, channel in enumerate(station.channels):
                                    if not scnl_filter.LOC or scnl_filter.LOC == channel.location_code:
                                      if not scnl_filter.CHA or scnl_filter.CHA == channel.code:

                                        if (scnl_filter.STN_EPOCH is None or scnl_filter.STN_EPOCH == istn) and \
                                           (scnl_filter.CHN_EPOCH is None or scnl_filter.CHN_EPOCH == ichn):

                                            keycode = "%s.%s" % (channel.code, channel.location_code)
                                            logger.info("Remove net:%s stn:%s [%d] chn:%s [%d] epoch" % \
                                                       (net_code, sta_code, istn, keycode, ichn))
                                            cleaned_channels.remove(channel)
                                            modified = True

                                if modified:
                                    station.channels = cleaned_channels


    return




def pack_xml_list_to_inv(xml_list):
    """
    Convert xml_list of dictionaries containing network(s) metadata to obspy inventory object

    :param xml_list: List of python dicts containing metadata
    :type xml_list: list

    :returns: Inventory object created from xml_list
    :rtype: obspy.core.inventory.inventory
    """

    source = xml_list[0]['source']
    sender = xml_list[0]['sender']
    module = xml_list[0]['module']
    module_uri = xml_list[0]['module_uri']

    inv = Inventory(source=source, sender=sender, module=module, module_uri=module_uri)

    networks = []
    for xml_dict in xml_list:
        for net_code in xml_dict['net_codes']:
            network = xml_dict['net_codes'][net_code]['network']
            stations = []
            for sta_code in xml_dict['net_codes'][net_code]['sta_codes']:
                stations.extend(xml_dict['net_codes'][net_code]['sta_codes'][sta_code])
            network.stations = stations
            networks.append(network)

    inv.networks = networks

    return inv

def load_xmlfiles(xmlfiles):
    """
    Read list of xmlfile(s) into a list of python dicts, one for each xml file,
          where the python dict holds the obspy inventory network objects
          read from the file

    :param xmlfiles: List of xmlfiles with common FDSN schema version
    :type xmlfiles: list

    :returns: list of python dicts
    :rtype: list
    """

    xml_list = []

    for xmlfile in xmlfiles:

        #logger.info("Read_inventory from file:[%s] thread:[%s]" % (xmlfile, threading.get_ident()))

        try:
            inv = read_inventory(xmlfile)
        except ValueError as e:
            logger.error("Problem reading xml file:%s" % repr(e))
            return None

        xml_dict = {}
        xml_list.append(xml_dict)

        xml_dict['xmlfile'] = xmlfile
        xml_dict['source']  = inv.source
        xml_dict['sender']  = inv.sender
        xml_dict['module']  = inv.module
        xml_dict['module_uri'] = inv.module_uri
        xml_dict['net_codes'] = {}

        for network in inv.networks:
            net_dict = network_to_dict(network)
            xml_dict['net_codes'][network.code] = net_dict
            xml_dict['net_codes'][network.code]['network'] = network

    return xml_list


def print_all(xml_list, args):

    for xml_dict in xml_list:
        print("[File:%s]" % xml_dict['xmlfile'])
        for net_code, net_dict in xml_dict['net_codes'].items():
            print("  [Net:%s]" % net_code)
            print_net(net_dict, args)


def print_net(net_dict, args):
    """
    Checks a list of epochs for overlap
        If overlap found, returns 1 + list of overlap messages
        If overlap not found, returns 0 + empty list

    :param epoch_list: List of any like objects with start_date + end_date,
                       Pre-sorted by start_date
    :type epoch_list: list

    :returns: True/False if overlap found
    :rtype: bool

    :returns: List of overlap messages
    :rtype: list
    """

    for stn_code, stn_epochs in net_dict['sta_codes'].items():

        for istn, station in enumerate(stn_epochs):
            #print("stn:%s epoch:%s - %s [nchan=%d]" % \
                  #(station.code, station.start_date, station.end_date, len(station.channels)))
            print("    [Stn:%4s] epoch[%d]:%s - %s" % \
                 (station.code, istn, station.start_date, station.end_date))

            if args.print_all:
                for ic, comment in enumerate(station.comments):
                    print("      [Cmt: %d] %s" % (ic, comment))
                for io, operator in enumerate(station.operators):
                    all_names = []
                    for person in operator.contacts:
                        all_names.extend(person.names)
                    names = " ".join(all_names)
                    all_agency = []
                    for person in operator.contacts:
                        all_agency.extend(person.agencies)
                    agencies = " ".join(all_agency)

                    print("      [ Op: %d] names:%s agencies:%s" % (io, names, agencies))

            for ichan, channel in enumerate(station.channels):
                loc_code = channel.location_code if channel.location_code else '--'
                key_code = "%s.%s" % (channel.code, loc_code)
                #print(key_code)
                print("      [Chn:%s] epoch[%d]:%s - %s" % \
                     (key_code, ichan, channel.start_date, channel.end_date))
                if args.print_all:
                    for ic, comment in enumerate(channel.comments):
                        print("          [Cmt: %d] %s" % (ic, comment))


def network_to_dict(network):
    """
    Convert obspy Network object to compound dict of sorted Station/Channel
        objects (epochs).
        Check for overlapping epochs at both Station + Channel level

    :param network: Network
    :type network: obspy.core.inventory.network.Network

    :returns: Nested dict of sorted epochs
    :rtype: dict
    """

    net_dict = {}
    net_dict['sta_codes'] = {}

    # Sort all station epochs by code + start_date
    sorted_stations = []

    for station in network.stations:
        sorted_stations.append(station)
    sorted_stations.sort(key=lambda x: (x.code, x.start_date), reverse=False)

    # Load up dict by station code
    stn_dict = {}
    for station in sorted_stations:
        if station.code in stn_dict:
            l = stn_dict[station.code]
        else:
            l = []
            stn_dict[station.code] = l
        l.append(station)

    # Store list of station_epochs in net_dict under stn_code
    for stn_code, station_epochs in stn_dict.items():
        net_dict['sta_codes'][stn_code] = station_epochs

        # Check for overlapping station epochs:
        (overlap, msgs) = overlapping_epochs(station_epochs)
        if overlap:
            logger.warning("Stn:%s has overlapping station epochs!" % (station.code))
            for msg in msgs:
                logger.warning(msg)

        # For each station_epoch, sort its channel epochs by keycode + start_date:
        for station in station_epochs:
            sorted_channels = []
            for channel in station.channels:
                sorted_channels.append(channel)
            sorted_channels.sort(key=lambda x: (x.location_code, x.code, x.start_date), reverse=False)

            station.channels = sorted_channels

        # Check for overlapping channel epochs:
            chn_dict = {}
            for channel in sorted_channels:
                keycode = "%s.%s" % (channel.code, channel.location_code)
                if keycode in chn_dict:
                    l = chn_dict[keycode]
                else:
                    l = []
                    chn_dict[keycode] = l
                l.append(channel)

            for keycode, channel_epochs in chn_dict.items():
                (overlap, msgs) = overlapping_epochs(channel_epochs)
                if overlap:
                    logger.error("Stn:%s Chn:%s has overlapping channel epochs!" % (station.code, keycode))
                    for msg in msgs:
                        logger.warning(msg)


    return net_dict


def overlapping_epochs(epoch_list):

    """
    Checks a list of epochs for overlap
        If overlap found, returns 1 + list of overlap messages
        If overlap not found, returns 0 + empty list

    :param epoch_list: List of any like objects with start_date + end_date,
                       Pre-sorted by start_date
    :type epoch_list: list

    :returns: 1 if overlap found else 0
    :rtype: int

    :returns: List of overlap messages
    :rtype: list
    """

    overlap = False

    msgs = []
    #print("overlapping_epochs: list_len=%d" % len(epoch_list))
    for i in range(len(epoch_list)-1):

        epoch1 = epoch_list[i]
        epoch2 = epoch_list[i+1]
        #print("Compare: i=%d" % i)
        #print("  epoch1: %s - %s" % (epoch1.start_date, epoch1.end_date))
        #print("  epoch2: %s - %s" % (epoch2.start_date, epoch2.end_date))

        if epoch1.start_date == epoch2.start_date:
            msgs.append("Epochs have same start_date")
            overlap = True
        # epoch1 better be closed
        elif epoch1.end_date is None:
            msgs.append("Earlier epoch not closed!")
            overlap = True
        # epoch1 close must precede epoch2 start
        elif epoch1.end_date > epoch2.start_date:
            msgs.append("epoch1 end > epoch2 start")
            overlap = True

        if overlap:
            #print("Epoch:%s overlaps with epoch:%s" % (epoch1, epoch2))
            #print("Epoch:%s overlaps with epoch:%s" % (epoch1.start, epoch2))
            msgs.append("These epochs overlap:")
            msgs.append("  epoch1: %s - %s" % (epoch1.start_date, epoch1.end_date))
            msgs.append("  epoch2: %s - %s" % (epoch2.start_date, epoch2.end_date))
            return 1, msgs

    return 0, []



if __name__ == "__main__":
    main()
