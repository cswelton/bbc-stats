import logging
import re
import json
import argparse
import os
import warnings
import sys


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from golfgenius.parser import GGParser


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


def parse_args():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('ggid', type=str, metavar='<GGID-CODE>',
                        help="GGID Code to parse. This can be any GGID code from a bbc round_info.")
    parser.add_argument('--sync-all', action='store_true', help='If set, previously collected data will be re-synced.')
    parser.add_argument('--results-directory', default='./results', type=str, metavar='<PATH>',
                        help="The directory to output result JSON files.")
    parser.add_argument('--disable-screenshots', action='store_true',
                        help="Turn off screenshots")
    parser.add_argument("--screenshots-directory", type=str, metavar='<PATH>', default='screenshots',
                        help="Directory to store screenshots")
    parser.add_argument('--filter', default=".*", metavar='<REGEX>', type=re.compile,
                        help="A regular expression to filter round_info names to parse")
    parser.add_argument('--show-browser', action='store_true',
                        help="Show the browser as data is being scanned.")
    parser.add_argument('--quiet', action='store_true',
                        help="Do not print logs to the screen.")
    parser.add_argument("--logfile", type=str, metavar='<PATH>',
                        help="Send logs to a file.")
    parser.add_argument("--debug", action='store_true', help="Turn on debug logging.")
    return parser.parse_args()


def main():
    args = parse_args()
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging_formatter = logging.Formatter('%(asctime)s <%(name)s:%(module)s[%(lineno)d]> %(levelname)s: %(message)s',
                                          '%a %b %d %H:%M:%S')
    if not args.quiet:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging_level)
        stream_handler.setFormatter(logging_formatter)
        logger.addHandler(stream_handler)
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(logging_formatter)
        logger.addHandler(file_handler)

    if not args.disable_screenshots:
        os.makedirs(args.screenshots_directory, exist_ok=True)

    if not os.path.isdir(args.results_directory):
        os.mkdir(args.results_directory)

    logger.info("Refreshing BBC Results from GGID {} to {} using filter {}".format(
        args.ggid, args.results_directory, args.filter.pattern
    ))

    parser = GGParser(
        headless=False if args.show_browser else True,
        screenshots_enabled=True if not args.disable_screenshots else False,
        screenshot_directory=args.screenshots_directory,
        existing_results=args.results_directory if not args.sync_all else None)

    synced_rounds = 0
    try:
        for round_name, result in parser.iter_rounds(args.ggid, filter=args.filter):
            with open(os.path.join(args.results_directory, "{}.json".format(round_name)), "w") as fp:
                json.dump(result, fp, indent=4)
                synced_rounds += 1
        logger.info("Finished refreshing GGID {}. Results have been stored in {}".format(
            args.ggid, args.results_directory
        ))
        if synced_rounds == 0:
            sys.exit(1)
        else:
            sys.exit(0)
    finally:
        parser.close()
