# -*- coding: utf-8 -*-
from __future__ import print_function
#from ._version import get_versions

__author__ = 'Mike Hagerty'
__email__ = 'mhagerty@isti.com'
__version__ = '0.0.5'
#__version__ = get_versions()['version']
#del get_versions

import os
def installation_dir():
  return os.path.dirname(os.path.realpath(__file__))

def fdsn_schema_dir():
  return os.path.join(installation_dir(), 'fdsn-schema')

def yml_template_dir():
  return os.path.join(installation_dir(), 'yml')
