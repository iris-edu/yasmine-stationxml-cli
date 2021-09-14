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

import logging
logger = logging.getLogger()

def valid_xmlfiles(args):

    # Verify all input xml a) exist and b) validate
    #schemafile = './fdsn-schema/fdsn-station-1.0.xsd'
    #schemafile = './fdsn-schema/fdsn-station-1.1.xsd'

    if args.infiles:
        valid = validate_files(args.infiles) # Make sure files exist, are readable, etc.
        if not valid:
            logger.error("One or more xmlfiles could not be read --> STOP EXECUTION")
            return False

    if not args.dont_validate:           # Check for valid StationXML
        for xmlfile in args.infiles:
            schema_version = get_schema_version(xmlfile)
            schema_file = 'fdsn-schema/fdsn-station-%s.xsd' % schema_version
            logger.info("Check file:%s against schema_file:%s" % (xmlfile, schema_file))
            #valid, errors = validate_stationxml(BytesIO(contents), schemafile)
            #valid, errors = validate_stationxml(xmlfile, schemafile)
            valid, errors = validate_stationxml(xmlfile, schema_file)

            if not valid:
                for error in errors:
                    logger.error(error)
                logger.error("One or more xmlfiles are NOT valid StationXML --> STOP EXECUTION")
                return False
    return True


from lxml import etree

def validate_stationxml(path_or_object, schemafile):

    try:
      xmlschema = etree.XMLSchema(etree.parse(schemafile))

      if isinstance(path_or_object, etree._Element):
          xmldoc = path_or_object
      else:
          try:
              xmldoc = etree.parse(path_or_object)
          except etree.XMLSyntaxError:
              msg = "file=[%s] is NOT a XML file!" % path_or_object
              return (False, [msg])
    except:
        raise

    valid = xmlschema.validate(xmldoc)

    # Pretty error printing if the validation fails.
    if valid is not True:
        return (False, xmlschema.error_log)

    return (True, ())


import errno
#def validate_files(xmlfiles):
def check_files(xmlfiles):

    for xmlfile in xmlfiles:

        logger.info("Validate exists xml file:[%s]" % xmlfile)

        try:
            with open(xmlfile) as f:
                contents = f.read()
            #f = xmlfile
            #contents = f.read()
        except IOError as x:
            if x.errno == errno.ENOENT:
                logger.error('File:%s does not exist' % xmlfile)
            elif x.errno == errno.EACCES:
                logger.error('File:%s Not readable' % xmlfile)
            else:
                logger.error('File:%s Caught error:%s' % (xmlfile, repr(x)))
            return False

    return True


import xml.etree.ElementTree as ET
#from lxml import etree as ET
def get_schema_version(xmlfile_or_string):

    namespace = "http://www.fdsn.org/xml/station/1"

    root = None
    try:
        # parse an xmlfile
        tree = ET.parse(xmlfile_or_string)
        root = tree.getroot()
    except:
        # parse an xml string
        root = ET.fromstring(xmlfile_or_string)
    if root is not None:
        stationxml_version = root.attrib.get('schemaVersion')
        return stationxml_version
    else:
        logger.ERROR("Unable to parse xmlfile_or_string")
        return None


def set_schema_version(xmlfile, version):

    namespace = "http://www.fdsn.org/xml/station/1"

    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        root.attrib['schemaVersion'] = version
    except:
        raise

    return tree


