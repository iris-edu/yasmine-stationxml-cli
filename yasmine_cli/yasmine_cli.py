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

import os
import sys

import logging
logger = logging.getLogger()

from . import installation_dir

from .libs.libs_log import configure_logger
from .libs.libs_obs import _write_stationxml
from .libs.libs_util import processCmdLine, read_config
from .libs.edit_xml_to_inv import edit_xml_to_inv, plot_responses

def main():
    '''
    usage: yasmine-cli [-h]
                   [--level_network II | --level_station II.* | --level_channel II.ANMO.00.*]
                   [--action [add/delete/update basenode]]
                   [--epoch_station int] [--epoch_channel int] [--field FIELD]
                   [--value VALUE | --from_yml fname.yml] [--infiles] [-o]
                   [-p] [--print_all] [--dont_validate] [--schema_version ver]
                   [--show_fields] [--plot_resp] [--plot_dir path]
                   [--loglevel log level]

    See ../README.md or https://gitlab.isti.com/mhagerty/yasmine-cli
    for full docs

    '''

    fname = 'yasmine-cli'
    config = read_config()
    configure_logger(config, logfile="%s.log" % fname)

    args, scnl_filter = processCmdLine(fname)

    logger.info("[cmd: >%s]" % " ".join(arg for arg in sys.argv))
    logger.info("NET:%s STA:%s LOC:%s CHA:%s" % (scnl_filter.NET, scnl_filter.STA, scnl_filter.LOC, scnl_filter.CHA))
    logger.info("level=[%s] action=[%s]" % (args.level, args.action))

    inv_new, schema_version = edit_xml_to_inv(args, scnl_filter)

    if args.plot_resp:
        plot_responses(inv_new, args.plot_dir)

    else:
        outfile = args.output if args.output else sys.stdout.buffer
        validate = False if args.dont_validate else True

        try:
            #inv_new.write(outfile, format='stationxml', validate=validate)
            # This is a hack to set the output stationxml version to the requested and/or input versions:
            _write_stationxml(inv_new, outfile, validate=validate, schema_version=schema_version)

        except:
            raise

    logger.info("%s: Finished Processing\n" % fname)

    return
