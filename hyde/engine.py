# -*- coding: utf-8 -*-
"""
Implements the hyde entry point commands
"""
from commando import *
from hyde.exceptions import HydeException
from hyde.fs import File, Folder
from hyde.layout import Layout, HYDE_DATA
from hyde.model import Config
from hyde.site import Site
from hyde.version import __version__
from hyde.util import getLoggerWithConsoleHandler

import codecs
import os
import yaml

HYDE_LAYOUTS = "HYDE_LAYOUTS"

logger = getLoggerWithConsoleHandler('hyde')

class Engine(Application):
    """
    The Hyde Application
    """

    @command(description='hyde - a python static website generator',
        epilog='Use %(prog)s {command} -h to get help on individual commands')
    @true('-v', '--verbose', help="Show detailed information in console")
    @version('--version', version='%(prog)s ' + __version__)
    @store('-s', '--sitepath', default='.', help="Location of the hyde site")
    def main(self, args):
        """
        Will not be executed. A sub command is required. This function exists
        to provide common parameters for the subcommands and some generic stuff
        like version and metadata
        """
        if args.verbose:
            import logging
            logger.setLevel(logging.DEBUG)

    @subcommand('create', help='Create a new hyde site')
    @store('-l', '--layout', default='basic', help='Layout for the new site')
    @true('-f', '--force', default=False, dest='overwrite',
                            help='Overwrite the current site if it exists')
    def create(self, args):
        """
        The create command. Creates a new site from the template at the given
        sitepath.
        """
        self.main(args)
        sitepath = Folder(Folder(args.sitepath).fully_expanded_path)
        if sitepath.exists and not args.overwrite:
            raise HydeException(
                    "The given site path[%s] is not empty" % sitepath)
        layout = Layout.find_layout(args.layout)
        logger.info(
            "Creating site at [%s] with layout [%s]" % (sitepath, layout))
        if not layout or not layout.exists:
            raise HydeException(
            "The given layout is invalid. Please check if you have the"
            " `layout` in the right place and the environment variable(%s)"
            " has been setup properly if you are using custom path for"
            " layouts" % HYDE_DATA)
        layout.copy_contents_to(args.sitepath)
        logger.info("Site creation complete")

    @subcommand('gen', help='Generate the site')
    @store('-c', '--config-path', default='site.yaml', dest='config',
            help='The configuration used to generate the site')
    @store('-d', '--deploy-path', dest='deploy', default=None,
                        help='Where should the site be generated?')
    def gen(self, args):
        """
        The generate command. Generates the site at the given
        deployment directory.
        """
        self.main(args)
        site = self.make_site(args.sitepath, args.config, args.deploy)
        from hyde.generator import Generator
        gen = Generator(site)
        gen.generate_all()

    @subcommand('serve', help='Serve the website')
    @store('-a', '--address', default='localhost', dest='address',
            help='The address where the website must be served from.')
    @store('-p', '--port', type=int, default=8080, dest='port',
            help='The port where the website must be served from.')
    @store('-c', '--config-path', default='site.yaml', dest='config',
            help='The configuration used to generate the site')
    @store('-d', '--deploy-path', dest='deploy', default=None,
                    help='Where should the site be generated?')
    def serve(self, args):
        """
        The serve command. Serves the site at the given
        deployment directory, address and port. Regenerates
        the entire site or specific files based on ths request.
        """
        self.main(args)
        sitepath = Folder(Folder(args.sitepath).fully_expanded_path)
        config_file = sitepath.child(args.config)
        site = self.make_site(args.sitepath, args.config, args.deploy)
        from hyde.server import HydeWebServer
        server = HydeWebServer(site, args.address, args.port)
        logger.info("Starting webserver at [%s]:[%d]", args.address, args.port)
        try:
            server.serve_forever()
        except KeyboardInterrupt, SystemExit:
            logger.info("Received shutdown request. Shutting down...")
            server.shutdown()
            logger.info("Server successfully stopped")
            exit()

    def make_site(self, sitepath, config, deploy):
        """
        Creates a site object from the given sitepath and the config file.
        """
        sitepath = Folder(Folder(sitepath).fully_expanded_path)
        config = Config(sitepath, config_file=config)
        if deploy:
            config.deploy_root = deploy
        return Site(sitepath, config)