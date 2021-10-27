#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_yasmine_cli
----------------------------------

Tests for `yasmine_cli` module.
"""

import glob
import os
import sys
import unittest

from obspy.core.inventory.network import Network
from obspy.core.inventory.station import Station
from obspy.core.inventory.channel import Channel
from obspy import read_inventory

import yasmine_cli

from yasmine_cli import installation_dir, fdsn_schema_dir, yml_template_dir
from yasmine_cli.libs.libs_xml import validate_stationxml, get_schema_version
from yasmine_cli.libs.edit_xml_to_inv import load_xmlfiles, pack_xml_list_to_inv
from yasmine_cli.libs.libs_obs import _write_stationxml, read_yml_file
from yasmine_cli.libs.libs_util import configure, processCmdLine
from yasmine_cli.libs.libs_log import configure_logger
from yasmine_cli.libs.edit_xml_to_inv import update_root_field, update_field, edit_xml_to_inv

import logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

TEMPLATE_DIR = yml_template_dir()

class TestYasmine_cli(unittest.TestCase):

    def setUp(self):

        self.install_dir = installation_dir()
        self.assertEqual(os.path.isdir(self.install_dir), 1)
        self.schema_dir  = fdsn_schema_dir()
        self.assertEqual(os.path.isdir(self.schema_dir), 1)

    def test_version(self):
        assert(yasmine_cli.__version__)

    def test_read_config(self):
        config = configure('./config.yml')
        self.assertEqual(config['LOG_LEVEL'], 'DEBUG')

    def test_process_command_line(self):
        #sys.argv = ['/Users/mth/mth/miniconda3/envs/yas/bin/yasmine-cli',
        sys.argv = ['yasmine-cli',
                    '--field=code', '--value=MIKE',
                    '--level_station=*.ANMO', '--epoch_station=1', '--epoch_channel=3',
                    '--schema_version', '1.1',
                    '-o', 'a.xml']
        args, scnl_filter = processCmdLine('yasmine-cli')
        self.assertEqual(args.level, 'station')
        self.assertEqual(args.field, 'code')
        self.assertEqual(args.value, 'MIKE')
        self.assertEqual(scnl_filter.STA, 'ANMO')
        self.assertEqual(scnl_filter.STN_EPOCH, 1)
        self.assertEqual(scnl_filter.CHN_EPOCH, 3)
        pass

    def test_read_xml_version(self):
        xmlfile = 'test_data/Test.xml'
        schema_version = get_schema_version(xmlfile)
        self.assertEqual(schema_version, '1.0')
        schema_file = os.path.join(self.schema_dir, 'fdsn-station-%s.xsd' % schema_version)
        assert(os.path.isfile(schema_file))
        valid, errors = validate_stationxml(xmlfile, schema_file)
        self.assertTrue(valid)

    def test_load_xml_file(self):
        xmlfile = 'test_data/Test.xml'
        xml_list = load_xmlfiles([xmlfile])
        self.assertIsInstance(xml_list, list)

    def test_convert_xml_list_to_inv(self):
        xmlfile = 'test_data/Test.xml'
        outfile = 'b.xml'
        xml_list = load_xmlfiles([xmlfile])
        inv = pack_xml_list_to_inv(xml_list)
        schema_version = get_schema_version(xmlfile)
        self.assertIsNotNone(inv)
        _write_stationxml(inv, outfile, validate=True, schema_version=schema_version)
        assert(os.path.isfile(outfile))

    def test_read_base_nodes(self):
        for basenode in [Network, Station, Channel]:
            node = test_read_base_node(basenode.__name__)
            self.assertIsInstance(node, basenode)

    def test_update_source(self):
        sys.argv = ['yasmine-cli', '--infiles=test_data/station.xml', '-o', 'a.xml',
                    '--field=source', '--value=RESIF-RAP',
                    ]
        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=True, schema_version=schema_version)

    def test_add_channel(self):
        sys.argv = ['yasmine-cli', '--infiles=test_data/Test.xml', '-o', '1.xml',
                    '--action=add', '--from_yml=yml:yml/channel.yml',
                    '--level_station=*.ANMO',
                    ]
        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=True, schema_version=schema_version)

    def test_add_station(self):
        sys.argv = ['yasmine-cli', '--infiles=test_data/NE.xml', '-o', '2.xml',
                    '--action=add', '--from_yml=yml:yml/station.yml',
                    '--level_network=NE',
                    '--schema_version=1.1',
                    ]
        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=True, schema_version=schema_version)

    def test_add_site(self):
        sys.argv = ['yasmine-cli', '--infiles=test_data/Test.xml', '-o', '3.xml',
                    #'--action=update',
                    '--field=site', '--value=yml:yml/site.yml',
                    '--level_station=*.ANMO',
                    '--schema_version=1.1',
                    ]
        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=True, schema_version=schema_version)
        inv = read_inventory('3.xml')
        tmp = inv.select(station="ANMO")
        self.assertEqual(tmp.networks[0].stations[0].site.town, 'Isleta Pueblo')
        self.assertEqual(tmp.networks[0].stations[0].site.county, 'Bernalillo')

    def test_pipe_0(self):
        """Piping example:
            1) Change all ANMO station codes to 'MIKE',
            2) Change the latitude of all CCM stations to 33.77,
            3) Add list of operators to all MIKE stations, and
            4) Replace the 2nd operator in the list with a new operator from yml file:
        """

        cmd = ("cat test_data/Test.xml | yasmine-cli --field=code --value=MIKE --level_station=*.ANMO --dont_validate "
               "| yasmine-cli --field=latitude --value=33.77 --level_station=*.CCM "
               "| yasmine-cli --field=operators --value=yml:yml/operators.yml --level_station=*.MIKE "
               "| yasmine-cli --field=operators[1] --value=yml:yml/operator.yml --level_station=*.MIKE -o y.xml "
               )
        os.system(cmd)

    def test_pipe_1(self):

        inv = read_inventory('y.xml')
        tmp = inv.select(station="CCM")
        self.assertEqual(tmp.networks[0].stations[0].latitude, 33.77)

        tmp = inv.select(station="MIKE")
        for station in tmp.networks[0].stations:
            self.assertEqual(station.operators[0].agency, 'United States Geological Survey, USGS')
            self.assertEqual(station.operators[0].contacts[0].names[0], 'Adam Ringler')
            self.assertEqual(station.operators[0].contacts[0].agencies[0], 'Albuquerque Seismic Lab')
            self.assertEqual(station.operators[1].agency, 'UCSC')
            self.assertEqual(station.operators[1].contacts[0].names[0], 'Dan Sampson')
            self.assertEqual(station.operators[1].contacts[0].emails[0], 'd.sampson@ucsc.edu')


    def test_update_0(self):
        sys.argv = ['yasmine-cli', '--infiles=test_data/station.xml', '-o', '4.xml',
                    '--action=update', '--level_station=*.*',
                    '--field=comments', '--value=yml:yml/comment.yml',
                    ]
        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=True, schema_version=schema_version)
        inv = read_inventory('4.xml')
        #print(inv.networks[0].stations[0].comments[0].authors[0].names[0])
        #print(inv.networks[0].stations[0].comments[0].authors[0].agencies[0])
        self.assertEqual(inv.networks[0].stations[0].comments[0].authors[0].names[0], 'Jean-Marie Saurel')
        self.assertEqual(inv.networks[0].stations[0].comments[0].authors[0].agencies[0], 'Institut de Physique du Globe de Paris')


    def test_update_1(self):
        """Replace the 7th comment of the 128th channel epoch of the
            5th station epoch with a comment from yaml file
        """
        sys.argv = ['yasmine-cli', '--infiles=test_data/ANMO.xml', '-o', '5.xml',
                    '--action=update', '--level_channel=*.ANMO.10.VHZ',
                    '--epoch_channel=128', '--epoch_station=5',
                    '--field=comments[6]', '--value=yml:yml/comment.yml',
                    '--dont_validate'
                    ]

        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=False, schema_version=schema_version)
        inv = read_inventory('5.xml')

        self.assertEqual(inv.networks[0].stations[5].channels[128].comments[6].authors[0].names[0],
                         'Jean-Marie Saurel')
        self.assertEqual(inv.networks[0].stations[5].channels[128].comments[6].authors[1].names[0],
                         'Sid Hellman')

    def test_update_3(self):
        """Remove the 0th comment from the 128th channel epoch of the
            5th station epoch, then read it back in and make sure
            what was the comment at channel.coments[6] is now at channel.comments[5]
        """
        #sys.argv = ['yasmine-cli', '--infiles=test_data/ANMO.xml', '-o', '6.xml',
        sys.argv = ['yasmine-cli', '--infiles=5.xml', '-o', '6.xml',
                    '--action=update', '--level_channel=*.ANMO.10.VHZ',
                    '--epoch_channel=128', '--epoch_station=5',
                    '--field=comments[0]', '--value=None',
                    '--dont_validate'
                    ]

        args, scnl_filter = processCmdLine('yasmine-cli')
        inv, schema_version = edit_xml_to_inv(args, scnl_filter)
        _write_stationxml(inv, args.output, validate=False, schema_version=schema_version)
        inv = read_inventory('6.xml')
        self.assertEqual(len(inv.networks[0].stations[5].channels[128].comments), 6)
        #for comment in inv.networks[0].stations[5].channels[128].comments:
            #print(comment.value)
        self.assertEqual(inv.networks[0].stations[5].channels[128].comments[5].authors[0].names[0],
                         'Jean-Marie Saurel')
        self.assertEqual(inv.networks[0].stations[5].channels[128].comments[5].authors[1].names[0],
                         'Sid Hellman')


    @classmethod
    def tearDownClass(cls):
        print("Call teardownclass")
        files = glob.glob('?.xml')
        for f in files:
            os.remove(f)


def test_read_base_node(basenode):
        yml_path = 'yml:yml/%s.yml' % basenode.lower()
        file_1 = os.path.join(os.getcwd(), yml_path[4:])
        # Else look for file in TEMPLATE_DIR
        file_2 = os.path.join(TEMPLATE_DIR, os.path.basename(yml_path[4:]))

        if os.path.exists(file_1):
            ymlfile = file_1
        elif os.path.exists(file_2):
            ymlfile = file_2
        else:
            print("Unable to find yml_file=[%s] file in either: cwd=%s -or: TEMPLATE_DIR=%s" %
                  (yml_path[4:], os.getcwd(), TEMPLATE_DIR))

        return read_yml_file(ymlfile)


if __name__ == "__main__":
    unittest.main()
