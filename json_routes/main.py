#!/usr/bin/env python3
# *_* coding: utf-8 *_*

"""
Class to take raw output of routing tables from network devides and save them as newline delimted 
JSON to be used in elastic and kibana.

"""

__version__ = "1.0.0"
__author__ = "BestPath"
__email__ = "info@bestpath.io"
__license__ = "GPL"
__status__ = "Production"

supported_devices = [
    'nxos', # Cisco Nexus Switches
    'ios', # Cisco IOS
    'fortinet' # Fortinet Firewalls
]
# --------------------------------------------------------------------------------

import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
        print("This script requires Python version 3.6")
        sys.exit(1)

import logging
import argparse
from parser import RouteParser

def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='version', version=__version__)

    parser.add_argument('-f', '--file', required=True,
                        help='The location of the text file with routing output.')

    parser.add_argument('-d', '--device', required=True, choices=supported_devices,
                        help='The device type the routing output was taken from.')

    args = parser.parse_args()

    RouteParser(vars(args))

if '__main__' == __name__:
    main()