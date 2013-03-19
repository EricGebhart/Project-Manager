#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   This is a set of classes to manage local and remote software projects, with and
   without revision control. Supplementing a local git repository for projects that
   have no revision control.
"""

__author__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__support__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__version__ = '$Revision: 1 $'[11:-2]
__application__ = 'PM'    # we don't have a name yet...
__default_config__ = '.PMrc'  # we don't have a name yet...
__default_log__ = '.PM.log'   # we don't have a name yet...
__project_config_file__ = '.PMrc.project'

no_execute = None   # so we can run and not do anything.

import os
import configparser
import argparse
from collections import OrderedDict
from application.applogger import applicationlogger


class applicationCore():

    def __init__(self, prefix_chars='-', prog=__application__, description=__doc__, epilog=''):

        self.applogger = applicationlogger()
        self.logger = self.applogger.get_logger()
        self.cmd = syscall(self.logger)

        self.prefix_chars = prefix_chars
        self.description = description
        self.epilog = epilog   # put closing help paragraph here.
        self.formatter_class = argparse.RawDescriptionHelpFormatter

        self.last_group = None
        self.stdio_hdlr = None
        self.config_sections = []

        self.config_file = os.path.join(os.getenv('HOME'), __default_config__)

        # 2 layer ordered lists of argument objects. - for creating parse groups and screen panels.
        self.config_groups = OrderedDict()
        self.arg_groups = OrderedDict()

        self.args = None
        # single layer list of same argument objects for easy lookup.
        self.ARGS = {}

        # An ordered list of args with callbacks.  determined by execute_order or by order added.
        self.callbacks = []

        # create the top-level parser
        self.main_parser = argparse.ArgumentParser(prog=__application__,
                                                   description=description,
                                                   epilog=self.epilog,
                                                   prefix_chars=self.prefix_chars)
        # create the top-level parser
        self.main_parser.add_argument('-noex', default=None, action='store_const',
                                      const=1, help='Do not execute')
        self.main_parser.add_argument('-v', '--verbose', help='Verbosity level',
                                      default='info',
                                      choices=self.applogger.get_choices())
        self.main_parser.add_argument('-quiet', action='store_const', const=1,
                                      help='Silent running', default=None)
        self.main_parser.add_argument('-log', help='Log file, defaults to %s' %
                                      __default_log__,
                                      default=__default_log__)
        self.main_parser.add_argument('-config',
                                      help='Config file, defaults to %s' %
                                      self.config_file,
                                      default=self.config_file)

        self.argument_setup()

        self.args = self.main_parser.parse_args()

        # this is a global that anyone can check.
        self.cmd.no_execute = self.args.noex

        self.logger_setup()

        #print (vars(self.config_args))

        # Load config file.
        self.load_settings()
        self.setup_log_file()

    # Set this up in the child class. This is where you add your arguments to
    # the argument parser.
    def argument_setup(self):
        pass

    def process(self):
        """this is where we do the work. Process is the core of it all.
        The child should define this method, and call it's super.__class__
        Then process it's config data and arguments as it wishes.
        Load the config file, read the arguments and setup logging.
        The child uses process to do the work, look at the config entries and
        arguments do the actual proecessing."""
        pass

    def create_defaults(self, args):
        self.defaults = {}
        for k, arg in args.items():
            if arg.default is not None:
                self.defaults[k] = arg.default

    def logger_setup(self):
        self.formatter = self.applogger.formatter(
            '%(asctime)s %(levelname)s %(message)s')
        self.applogger.setup(self.formatter)

    def setup_log_file(self):
        # set the log file if we need to.
        if self.args.quiet:
            self.applogger.quiet()
        if self.args.log:
            self.applogger.logfile(self.args.log, self.formatter)

        self.applogger.debug(vars(self.args))
        self.applogger.setLevel(self.args.verbose)

    def print_config(self):
        self.applogger.info(self.config.sections())
        for section in self.config.sections():
            self.print_config_section(section)
        return

    def print_config_section(self, section):
            for key in self.config[section]:
                self.applogger.info("%s: %s" % (key, self.config[section][key]))

    def load_settings(self):
        config_file = self.args.config
        # If we have a config file, load up the section indicated and set
        # defaults to it's result.
        if config_file:
            self.config = configparser.SafeConfigParser()
            if  os.path.isfile(config_file):
                self.config.read([config_file])

                self.applogger.debug("Reading configuration file: %s" %
                                    (config_file))
                """
                try:
                    items = self.config.items(config_section)
                    self.defaults = dict(items)
                except:
                    logger.error("Could not read %s" % config_file)
                    logging.shutdown()
                    exit()

                # add them to defaults so they will show up later - in the gui
                self.defaults['config_file'] = config_file
                self.defaults['config_section'] = config_section

                # setup the config sections combobox choices...
                self.config_sections = ['default']
                for name in self.config.sections():
                    self.config_sections.append(name)
                # totally cheating here.  But it works.  perhaps there should
                # be a way to bind a method to an action so that it can update
                # another fields choices.  but this is working for this.
                self.ARGS['config_section'].choices = self.config_sections
                """

            else:
                # don't die if the default config file is missing.
                if config_file != __default_config__:
                    self.applogger.error("Could not read configuration file %s" %
                                         config_file)

    def save_settings(self):
        # Save the settings to a configuration file and section.
        if self.arguments.save_settings and self.config_args.config_file:
            config = configparser.SafeConfigParser()

            if os.path.isfile(self.config_args.config_file):
                config.read([self.config_args.config_file])

            self.applogger.info("Saving settings to the '%s' section in configuration file: %s" %
                                (self.arguments.save_settings,
                                 self.config_args.config_file))

            # create a section in the config_parser and save to config file.
            #config = configparser.RawConfigParser()
            if config.has_section(self.args.save_settings):
                self.applogger.warning("Section '%s' already exists in configuration file '%s'" %
                                       (self.args.save_settings,
                                        self.config_args.config_file))

                # Should have a continue/abort dialog here.
                #if self.args.gui_type and self.args.gui_type != 'none':
                #    return
                #
                # exit() this is a bit harsh I think...

                # remove the current section so we can replace it.
                config.remove_section(self.args.save_settings)

            config.add_section(self.args.save_settings)

            # We have two sets of arguments to go through. -
            # verbosity is in the first list.
            args_dict = vars(self.args)
            for arg in args_dict:
                # we don't need to save the file or section we are saving into.
                if (arg == 'save_settings' or
                        arg == 'config_file' or
                        arg == 'config_section'):
                    continue

                if args_dict[arg] is not None:
                    self.applogger.debug("%s:%s:%s" % (arg, type(args_dict[arg]), args_dict[arg]))
                    config.set(self.args.save_settings, arg, str(args_dict[arg]))

            # Writing our configuration file to args.config_file
            with open(self.config_args.config_file, 'w') as config_file:
                config.write(config_file)

    def app_main(self):
        self.process()


class syscall():
    def __init__(self, logger):
        self.no_execute = True
        self.logger = logger

    def run(self, command, doitanyway=None):
        self.logger.info(command)
        if (self.no_execute is None or
                doitanyway is not None):
            os.system(command)


class apperror(RuntimeError):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == "__main__":
    applicationCore.main()
