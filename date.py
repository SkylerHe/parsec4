# -*- coding: utf-8 -*-
import typing
from   typing import *

###
# Standard imports, starting with os and sys
###
min_py = (3, 11)
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
from   collections.abc import *
import contextlib
import getpass
import logging

###
# Installed libraries like numpy, pandas, paramiko
###

###
# From hpclib
###
import linuxutils
from   urdecorators import trap
from   urlogger import URLogger

###
# imports and objects that were written for this project.
###

from calendar import monthrange
from datetime import datetime
import parsec as p 
###
# Global objects
###
mynetid = getpass.getuser()
logger = None

###
# Credits
###
__author__ = 'Skyler He'
__copyright__ = 'Copyright 2025, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Skyler He'
__email__ = 'skyler.he@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'

###
# Step 1: Initialize Constants
###

# Strings
star = p.string("*").lexeme()
LAST = p.string("LAST").lexeme()
slash = p.string("/").lexeme()
SLASH = slash.parse()

# Arithmetic
op = p.one_of("+-").lexeme()
offset = p.regex(r"0?[1-9]+").parsecmap(int).lexeme()
LD = last_day_of_month(year, month)


###
# Step 2: Helper functions
###
def adjust_date(year: int, month: int, day: int) -> tuple:
    """
    Function to adjust month and day to ensure they are within valid ranges
    Modify year if necessary
    """
    # Adjust Month
    year, month = [year + (month - 1) // 12 if month > 12 else year - ((abs(month) // 12) + 1) if month < 1 else year,
                   (month - 1) % 12 + 1 if month > 12 else 12 - (abs(month) % 12) if month< 1 else month]
    
    # Underflow
    while day < 1 or day > LD:
        year, month, day = [year - 1 if day < 1 and month == 1 else year + 1 if day > LD and month == 12 else year,
                            month - 1 if day < 1 else month + 1 if day > LD else month.
                            day + LD if day < 1 else day - LD if day > LD else day]
    return year, month, day 
def last_day_of_month(year: int, month: int) -> int:
    """
    Function to find the last day of the month in the year
    """
    return calendar.monthrange(year, month)[1]

def star_offset() -> tuple:
    """
    Function returns default ("*",0), + -> ("*",+offset), - -> ("*", -offset)
    """
    return (star + (op + str(offset)).optional()).map(lambda x: ("*", int(x[1][1]) if x[1] and x[1][0] == "+"
                                                            else -int(x[1][1]) if x[1]
                                                            else 0))

###
# Step 3: Date Parser
###
@p.generate
def date_parser():
    """
    Main parser for date expression
    Return could be tuple, int, or string
    """
    first = (star_offsert() | offset) << SLASH
    second = (star_offsert() | offset) << SLASH
    third = (star_offsert | offset | LAST)
    return first, second, third

###
# Step 4: Date Evaluation
###   
def eval_date(exp:str) -> str:
    # Current date
    yy, mm, dd = datetime.today().year, datetime.today().month, datetime.today().day
    # Prase the input
    year, month, day = date_parser().parse(exp)
    # Year, Month, Day
    year, month, day = [yy + year[1] if isinstance(year, tuple) else year,
                        mm + month[1] if isinstance(month, tuple) else month,
                        dd + day[1] if isinstance(day,tuple) else LD if day == "LAST" else day]
    
    # Ensure month/day validity
    year, month, day = adjust_date(year, month, day)
    
    return year, month, day
@trap
def date_main(myargs:argparse.Namespace) -> int:
    try:
        result = eval_date(myargs.exp)
        print(f"Computed Date: {result}")
        return os.EX_OK
    except Exception as e:
        return e

if __name__ == '__main__':

    here       = os.getcwd()
    progname   = os.path.basename(__file__)[:-3]
    configfile = f"{here}/{progname}.toml"
    logfile    = f"{here}/{progname}.log"
    lockfile   = f"{here}/{progname}.lock"
    
    parser = argparse.ArgumentParser(prog="date", 
        description="What date does, date does best.")

    parser.add_argument('--loglevel', type=int, 
        choices=range(logging.FATAL, logging.NOTSET, -10),
        default=logging.DEBUG,
        help=f"Logging level, defaults to {logging.DEBUG}")

    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    
    parser.add_argument('-z', '--zap', action='store_true', 
        help="Remove old log file and create a new one.")

    parser.add_argument("exp", type=str, 
        help="Enter a date expression (e.g. '2025/2/16' or '*/*/*')")
    myargs = parser.parse_args()
    logger = URLogger(logfile=logfile, level=myargs.loglevel)

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{progname}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

