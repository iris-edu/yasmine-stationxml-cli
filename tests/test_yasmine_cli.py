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

import yasmine_cli

from yasmine_cli import installation_dir, fdsn_schema_dir
from yasmine_cli.libs.libs_xml import validate_stationxml, get_schema_version
from yasmine_cli.libs.edit_xml_to_inv import load_xmlfiles, pack_xml_list_to_inv
from yasmine_cli.libs.libs_obs import _write_stationxml
from yasmine_cli.libs.libs_util import configure, processCmdLine
from yasmine_cli.libs.libs_log import configure_logger
from yasmine_cli.libs.edit_xml_to_inv import update_root_field, update_field
import logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

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
        sys.argv = ['/Users/mth/mth/miniconda3/envs/yas/bin/yasmine-cli',
                    '--field=code', '--value=MIKE',
                    '--level_station=*.ANMO', '--epoch_station=1', '--epoch_channel=3',
                    '--schema_version', '1.1',
                    '-o', '1.xml']
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
        outfile = '1.xml'
        xml_list = load_xmlfiles([xmlfile])
        inv = pack_xml_list_to_inv(xml_list)
        schema_version = get_schema_version(xmlfile)
        self.assertIsNotNone(inv)
        _write_stationxml(inv, outfile, validate=True, schema_version=schema_version)
        assert(os.path.isfile(outfile))

    def test_delete_base_node(self):
        #pass
        self.assertIs(1,1)
    def test_add_base_node(self):
        pass
    def test_update_field(self):
        pass

    def tearDown(self):
        files = glob.glob('?.xml')
        for f in files:
            os.remove(f)

if __name__ == "__main__":
    unittest.main()
