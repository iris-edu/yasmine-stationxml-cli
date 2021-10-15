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

from sys import exit
import argparse
import os
import sys
import yaml

from .. import installation_dir, yml_template_dir

import logging
logger = logging.getLogger()

from .libs_obs import read_yml_file, show_fields, check_field
from .libs_log import string_to_logLevel

list_fields = {'comments', 'equipments', 'identifiers', 'operators', 'types', 'external_references'}
root_fields = {'source', 'sender', 'module', 'module_uri'}

TEMPLATE_DIR = yml_template_dir()

def read_config(requireConfigFile=False):
    '''
    Read yaml configfil
    '''

    config = None

    # From highest to lowest priority location of config.yml:
    # 1. passed on cmd line --configFile=...
    # 2. os.getcwd() = Location script is called from
    # 3. INSTALL_DIR = Location of yasmine_cli directory
    # 4. None

    configfile = None
    # See if it was passed on cmd line:
    configfile = pick_off_configFile(sys.argv)

    if configfile is None:
        # Look for config.yml in dir where pdl-to-aqms is called from (changes)
        test_path = os.path.join(os.getcwd(), 'config.yml')
        if os.path.exists(test_path):
            configfile = test_path
    if configfile is None:
        # Look for config.yml in dir where pdl_to_aqms.py is located (it never changes)
        #SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        #test_path = os.path.join(SCRIPT_DIR, 'config.yml')
        INSTALL_DIR = installation_dir()
        test_path = os.path.join(INSTALL_DIR, 'config.yml')
        if os.path.exists(test_path):
            configfile = test_path

    if configfile:
        config = configure(configfile)
    else:
        if requireConfigFile:
            logger.ERROR("ConfigFile is required but none has been found --> Exit")
            exit(2)

    return config

def pick_off_configFile(argv):
    '''
    See if configFile was passed on cmd line
    '''
    configFile= None
    for word in argv:
        if '--configFile' in word:
            foo, configFile = word.split('--configFile=')
    return configFile

def processCmdLine(fname):

    epilog='''
Examples:
>python yasmine-cli.py --level_network=II --field=description --value='Network description' --infiles=...
>python yasmine-cli.py --level_station=II.* --field=latitude --value=34.97 --infiles=...
>python yasmine-cli.py --level_channel=II.ANMO.00.* --field=comments[0] --value=yml:/path/comment.yml --infiles=...
>python yasmine-cli.py --level_network=* --action=add --from_yml=path/to/station.yml --infiles=...
    '''

    parser = argparse.ArgumentParser(
        description='',
        #usage='use "%(prog)s --help" for more information',
        epilog=''
    )

    agroup = parser.add_argument_group('level options: [default=root is implied if no level set]')
    group = agroup.add_mutually_exclusive_group()
    group.add_argument("--level_network", type=str, metavar='II')
    group.add_argument("--level_station", type=str, metavar='II.*')
    group.add_argument("--level_channel", type=str, metavar='II.ANMO.00.*')

    bgroup = parser.add_argument_group('action options: [default=update if no action set]')
    bgroup.add_argument("--action", type=str, choices=['add','delete','update','select'],
                          metavar='[add/delete/update basenode]')

    cgroup = parser.add_argument_group('epoch options: Use to filter down to epoch level')
    cgroup.add_argument("--epoch_station", type=int, metavar='int', help="station epoch index to filter on, eg, --epoch_station=1")
    cgroup.add_argument("--epoch_channel", type=int, metavar='int', help="channel epoch index to filter on, eg, --epoch_channel=0")

    dgroup = parser.add_argument_group('build options')
    dgroup.add_argument("--field", type=str, help='field, key or attribute to update. eg, --field=Latitude or --field=comments[1]')
    group = dgroup.add_mutually_exclusive_group()
    group.add_argument("--value", type=str, help='value of field, key or attribute to update. Ex. --value=34.97 or --value=yml:/path/comment.yml')
    group.add_argument("--from_yml", type=str, metavar='fname.yml', help='Used to add new basenode object created from fname.yml. eg, --from_yml=/some/path/network.yml')

    optional = parser.add_argument_group('other optional arguments')
    optional.add_argument("--infiles", type=list_str, required=False, metavar='', help='comma separated list of input xml files [default=stdin]')
    optional.add_argument('-o', '--output', type=str, metavar='', help='Name of output xml file [default=stdout]. eg, --output=foo.xml')
    optional.add_argument('-p', '--print-epochs', help='Print out sorted Station/Channel epochs', action="store_true")

    optional.add_argument('--print_all', help='Print out sorted Station/Channel epochs + operator/comment lists', action="store_true")
    optional.add_argument('--dont_validate', help='Turn OFF StationXML validation on all inputs/outputs', action="store_true")
    optional.add_argument("--schema_version", type=str, choices=['1.0', '1.1'], metavar='ver', help='{1.0, 1.1}')
    optional.add_argument('--show_fields', help='Print out allowable --field, + --value combinations', action="store_true")
    optional.add_argument('--show-fields', help='Print out allowable --field, + --value combinations', action="store_true")
    #optional.add_argument('-s', '--select', help='Select only --level_station stations', action="store_true")
    optional.add_argument('--plot_resp', help='Plot all channel responses', action="store_true")
    optional.add_argument('--plot_dir', type=str, metavar='path', help='Path to dir to save plot responses')
    optional.add_argument('--loglevel', type=str, metavar='log level', help='loglevel in {DEBUG, INFO, WARN, etc}')

    # Intercept the help msg so we can also print examples after
    if len(sys.argv) == 1 or \
       (len(sys.argv) == 2 and (sys.argv[1] == '-h' or sys.argv[1] == '--help')):
        parser.print_help()
        print(epilog)
        exit()

    args, unknown = parser.parse_known_args()

    if unknown:
        logger.error("The following cmd line params are unknown:%s" %(" ".join(unknown)))
        parser.print_usage()
        exit(2)


    if args.show_fields or getattr(args, 'show-fields', None):
        show_fields()
        exit()

    if args.loglevel:
        logger.setLevel(string_to_logLevel(args.loglevel))

# If no action set and we're not simpling printing out,
#  the action is either 'update' or 'select':
    if not args.action and not args.print_epochs and not args.print_all:
        args.action = 'update'
        if not args.field and not args.value:
            args.action = 'select'

    if args.action == 'select' and args.field:
        msg = ("You're using --action=select with --field: If you want to update the field, "
               "don't use --action (default action=update). If you want to select (=filter on a station), "
               "don't use --field.")
        logger.warning(msg)
        exit(2)

    update_pair = None
    args.use_index = False

    args.update_root = False
    if args.field in root_fields:
        args.update_root = True

    if args.action == 'update':
        args.update = 'set' # default

        if args.field and args.value:
            if not args.level_network and not args.level_station and \
               not args.level_channel and not args.update_root:
                logger.error("--field=%s is *not* a recognized root field and no --level was specified" % args.field)
                logger.error("Use yasmine-cli.py --show_fields to see all known fields -or-")
                logger.error("    yasmine-cli.py -h to see all options")
                logger.error("You must specify level where this (field,value) should be updated!")
                logger.error("Example: --level_network=II")
                logger.error("Example: --level_channel=II.*.00.*")
                #parser.print_help()
                exit(2)

            field = args.field
            # Replace --field=comments[16] --> field='comments', index=16
            use_index = False
            field_index = None
            if '[' in field and field[-1] == ']':
                try:
                    i = field.index('[') + 1
                    field_index = int(field[i:-1])
                    field = field[0:i-1]
                    use_index = True
                    args.field_index = field_index
                    args.use_index = use_index
                except ValueError as err:
                    raise
                    #logger.info("Keep it a string!")
            #logger.info("field:%s value:%s type(%s)" % (args.field, value, type(value)))


            # --value='some_string'
            # --value=['a','list','of','strings']
            # --value=[]  // empty list
            # --value=None  // remove attribute
            # --value=71.12
            # --value=[72.5, 32.7] // list of floats
            # --value=from_yml --from_yml=some_path_to_yml   // yml file specifies value
            value = args.value
            #if value == 'from_yml':
            if value[0:4] == 'yml:':  # Read/build value from yaml file
                yml_file = value[4:]
                logger.info("Read value(s) from yml file:%s" % yml_file)

                # First look for file in dir we're calling this script *from*
                file_1 = os.path.join(os.getcwd(), yml_file)
                # Else look for file in TEMPLATE_DIR
                file_2 = os.path.join(TEMPLATE_DIR, os.path.basename(yml_file))

                logger.debug("Try to read from file_1=[%s]" % file_1)
                logger.debug("Try to read from file_2=[%s]" % file_2)
                if os.path.exists(file_1):
                    ymlfile = file_1
                    logger.info("Found yml_file=[%s]" % ymlfile)
                elif os.path.exists(file_2):
                    ymlfile = file_2
                    logger.info("Found yml_file=[%s]" % ymlfile)
                else:
                    logger.error("%s: Unable to find yml_file=[%s] file in either: cwd=%s -or: TEMPLATE_DIR=%s" %
                                 (fname, yml_file, os.getcwd(), TEMPLATE_DIR))
                    exit(2)

                value = read_yml_file(ymlfile)

            elif value[0] == '[' and value[-1] == ']': # value is a list of some sort
                    if len(value) <= 3: # --value=[] or --value=[ ]  // Set to empty list (to nullify list attribs)
                        value = []
                    else:
                        new_value = []
                        strings = value[1:-1].split(',')
                        logger.info("ProcessCmdLine: --value=%s = list.  Process as list:%s" % (value, strings))
                        try:
                            val = int(strings[0])
                            logger.info("ProcessCmdLine: --value=%s = list.  Appears to be list of ints" % value)
                            for string in strings:
                                new_value.append(int(string))
                        except ValueError as err:
                            try:
                                val = float(strings[0])
                                logger.info("ProcessCmdLine: --value=%s = list.  Appears to be list of floats" % value)
                                for string in strings:
                                    new_value.append(float(string))
                            except ValueError as err:
                                try:
                                    val = str(strings[0])
                                    logger.info("ProcessCmdLine: --value=%s = list.  Appears to be list of strings" % value)
                                    for string in strings:
                                        new_value.append(str(string))
                                except ValueError as err:
                                    logger.error("I give up: Unable to determine type of list elements in --value")
                                    exit(2)
            else: # value is scalar:
                try:
                    value = int(args.value)
                    logger.debug("ProcessCmdLine: --value=%s type=int" % value)
                except ValueError as err:
                    try:
                        value = float(args.value)
                        logger.debug("ProcessCmdLine: --value=%s type=float" % value)
                    except ValueError as err:
                        logger.debug("ProcessCmdLine: --value=%s type=str" % value)
                        if value == 'None':
                            value = None
                            logger.debug("ProcessCmdLine: convert --value=None --> remove attribute")

            args.field = field
            args.value = value
            args.update_pair = (field, value)

        else:
            logger.error("--action=update requires --field=... and --value=.. (or --value=from_yml + --from_yml=path..yml")
            logger.error("Example: --action=update --field=latitude --value=71.34 --level_station=II.ANMO   // set lat on II.ANMO")
            parser.print_help()
            exit(2)

        if field in list_fields:
            if isinstance(value, list):
                if use_index:
                    logger.error("%s[%d] cannot be set to *list* value=%s (type:%s)" % \
                                (field, field_index, value, type(value)))
                    exit(2)
                else:
                    if not value:
                        logger.info("field:%s set list to emtpy list" % field)
                    else:
                        logger.info("field:%s set list --> list" % field)
            else:
                if use_index:
                    logger.info("%s is list --> set %s[%d]=value (type:%s)" % \
                                (field, field, field_index, type(value)))
                    args.update = 'list_modify'
                else:
                    logger.info("%s is list --> append value (type:%s)" % \
                                (field, type(value)))
                    args.update = 'list_append'

        level = None
        if not args.update_root:
            if args.level_network:
                level = 'network'
            elif args.level_station:
                level = 'station'
            elif args.level_channel:
                level = 'channel'
            else:
                logger.error("Unknown state: No level set for action=update!")
                exit(2)

            if not check_field(field, value, level):
                #logger.error("field=[%s] or value=[%s] does not exist for level=[%s]" % \
                            #(field, value, level))
                logger.error("Element [%s] has no field/attrib=[%s]" % \
                            (level.capitalize(), field))
                logger.info("To see what fields are allowable do: >python yasmine-cli.py --show_fields")
                exit(2)

    elif args.action == 'add':
        if not args.from_yml:
            parser.print_help()
            logger.error("--action=add is used only to insert a BaseNodeType (Network/Station/Channel)")
            logger.error("Example: --action=add --from_yml=yml/network.yml")
            logger.error("Example: --action=add --from_yml=yml/station.yml --level_network=II")
            logger.error("Example: --action=add --from_yml=yml/channel.yml --level_network=II.ANMO")
            exit(2)
        else:
            if args.from_yml[0:4] == 'yml:':  # Read/build value from yaml file
                yml_file = args.from_yml[4:]
                logger.info("Read value(s) from yml file:%s" % yml_file)

                # First look for file in dir we're calling this script *from*
                file_1 = os.path.join(os.getcwd(), yml_file)
                # Else look for file in TEMPLATE_DIR
                file_2 = os.path.join(TEMPLATE_DIR, os.path.basename(yml_file))

                logger.debug("Try to read from file_1=[%s]" % file_1)
                logger.debug("Try to read from file_2=[%s]" % file_2)
                if os.path.exists(file_1):
                    ymlfile = file_1
                    logger.info("Found yml_file=[%s]" % ymlfile)
                elif os.path.exists(file_2):
                    ymlfile = file_2
                    logger.info("Found yml_file=[%s]" % ymlfile)
                else:
                    logger.error("%s: Unable to find yml_file=[%s] file in either: cwd=%s -or: TEMPLATE_DIR=%s" %
                                 (fname, yml_file, os.getcwd(), TEMPLATE_DIR))
            else:
                ymlfile = args.from_yml

            value = read_yml_file(ymlfile)
            field = value.__class__.__name__
            args.field = field
            args.value = value
            args.update_pair = (field, value)
    elif args.action == 'delete':
        logger.info("Use delete to delete a basenode")


    scnl_filter = struct(NET=None, STA=None, CHA=None, LOC=None, STN_EPOCH=None, CHN_EPOCH=None, INDEX=None)

    if args.use_index:
        scnl_filter.INDEX = args.field_index

    level = None

    if args.level_network:
        level = 'network'
        if args.level_network == '*':
            net = None
        elif args.level_network.isalnum() and len(args.level_network) > 0 :
            net = args.level_network
        else:
            parser.print_usage()
            logger.info("Example: --level_network=IU")
            exit(2)
        scnl_filter.NET = net
    elif args.level_station:
        level = 'station'
        fail = False
        if args.level_station.isalnum():
            sta = args.level_station
            net = None
        else:
            try:
                (tmp_net, tmp_sta) = args.level_station.split(".")

                if tmp_net.isalnum():
                    net = tmp_net
                elif tmp_net == '*':
                    net = None
                else:
                    fail = True

                if tmp_sta.isalnum():
                    sta = tmp_sta
                elif tmp_sta == '*':
                    sta = None
                else:
                    fail = True
            except:
                logger.error("Unable to split net.sta")
                logger.info("Example: --level_station=ANMO    // Act on station(s)=ANMO of net=*")
                logger.info("Example: --level_station=*.ANMO  // Act on station(s)=ANMO of net=*")
                logger.info("Example: --level_station=IU.ANMO // Act on station(s)=ANMO of net=IU")
                logger.info("Example: --level_station=IU.*    // Act on station(s)=*    of net=IU")
                parser.print_usage()
                exit(2)

        scnl_filter.NET = net
        scnl_filter.STA = sta

    elif args.level_channel:
        level = 'channel'
        fail = False
        try:
            (fields) = args.level_channel.split(".")
        except:
            #print("Unable to split net.sta")
            fail = True

        if len(fields) != 4:
            fail = True
        else:
            for field in fields:
                if not field.isalnum() and field != '*':

                    logger.info("Example: --level_channel=IU.ANMO.00.BHZ // Act on channel(s)=BHZ of loc=00 of sta=ANMO of net=IU")
                    logger.info("Example: --level_channel=IU.ANMO.00.*   // Act on channel(s)=*   of loc=00 of sta=ANMO of net=IU")
                    logger.info("Example: --level_channel=IU.ANMO.*.*    // Act on channel(s)=*   of loc=*  of sta=ANMO of net=IU")
                    logger.info("Example: --level_channel=IU.*.*.*       // Act on channel(s)=*   of loc=*  of sta=*    of net=IU")
                    logger.info("Example: --level_channel=*.*.*.BHZ      // Act on channel(s)=BHZ of loc=*  of sta=*    of net=*")
                    parser.print_usage()
                    exit(2)

        (net, sta, loc, cha) = tuple(fields)

        if net == '*': net = None
        if sta == '*': sta = None
        if cha == '*': cha = None
        if loc == '*': loc = None

        scnl_filter.NET = net
        scnl_filter.STA = sta
        scnl_filter.CHA = cha
        scnl_filter.LOC = loc

    args.level = level

    if args.epoch_channel is not None:
        scnl_filter.CHN_EPOCH = args.epoch_channel
    if args.epoch_station is not None:
        scnl_filter.STN_EPOCH = args.epoch_station

    return args, scnl_filter

def list_str(values):
    return values.split(',')

class struct:
     def __init__(self, **kwds):
         self.__dict__.update(kwds)

def configure(filename=None):
    """
        Read in config from yaml filename
    """
    configuration = {}
    with open(filename, 'r') as ymlfile:
        configuration = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return configuration



if __name__ == "__main__":
    main()
