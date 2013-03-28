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

no_execute = None   # so we can run and not do anything.

import os
import configparser
import argparse
from collections import OrderedDict
from application.applogger import applicationlogger


class applicationCore():

    def __init__(self, prefix_chars='-', epilog=''):

        self.applogger = applicationlogger()
        self.logger = self.applogger.get_logger()
        self.cmd = syscall(self.logger)

        self.prefix_chars = prefix_chars
        if  self.__doc__:
            self.description = self.__doc__
        else:
            self.description = __doc__

        self.epilog = epilog   # put closing help paragraph here.
        self.formatter_class = argparse.RawDescriptionHelpFormatter

        self.last_group = None
        self.stdio_hdlr = None
        self.config_sections = []

        self.config_file = os.path.join(os.getenv('HOME'), self.default_config)

        # 2 layer ordered lists of argument objects. - for creating parse groups and screen panels.
        self.config_groups = OrderedDict()
        self.arg_groups = OrderedDict()

        self.args = None
        # single layer list of same argument objects for easy lookup.
        self.ARGS = {}

        # An ordered list of args with callbacks.  determined by execute_order or by order added.
        self.callbacks = []

        self.conf_parser = argparse.ArgumentParser(add_help=False, prefix_chars=self.prefix_chars)

        conf_p_group = self.conf_parser.add_argument_group('Configuration files')
        conf_p_group.add_argument('-cf', '--config_file',
                                  help=('Config file, defaults to %s' %
                                  self.config_file),
                                  default=self.config_file)

    def create_parser(self):
        # create the top-level parser
        #  parents=[self.conf_parser],
        self.main_parser = argparse.ArgumentParser(prog=self.application,
                                                   description=self.description,
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
                                      self.default_log,
                                      default=self.default_log)

        # These are args for the first parse of the command line,
        # add them to the main parser as well, so they will show up in help.
        # I have a better way of doing this, but this will do for now.
        conf_m_group = self.main_parser.add_argument_group('Configuration files')

        conf_m_group.add_argument('-cf', '--config_file',
                                  help='Config file, defaults to %s' %
                                  self.config_file,
                                  default=self.config_file)

        conf_m_group.add_argument('-cs', '--config_section',
                                  choices=self.config_sections,
                                  help="Specify section name in configuration file",
                                  default='default')

        conf_m_group.add_argument('-ss', '--save_settings', action='store',
                                  help="Save settings to configuration file in this section")

        conf_m_group.add_argument('-ps', '--print_settings', action='store',
                                  help="Print section configuration settings.")

        self.argument_setup()

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

        self.logger_setup()
        self.parse_for_configuration()

        #print (vars(self.config_args))

        # load configuration.
        self.load_settings()

        # This is delayed so we know what our section choices are.
        self.create_parser()

        # parse the rest of the command line.
        self.parse_for_rest()

        # this is a global that anyone can check.
        self.cmd.no_execute = self.args.noex

        self.setup_log_file()

        # combine named section and parsed arguments, save as new section.
        self.save_settings()

        # section settings if asked.
        self.print_settings()

        # put all the arguments and default settings into one place.
        self.merge_args()

        # if we are given a section, go ahead and merge it's settings in.
        if 'config_section' in self.config_args:
            self.merge_section(self.config_args.config_section)

    def merge_args(self):
        """Create a master list of default and commandline arguments."""
        self.applogger.info(self.config['default'])
        args_dict = dict(self.config.items('default'))
        for k in args_dict:
            self.ARGS[k] = args_dict[k]
        args_dict = self.args.__dict__
        for k in args_dict:
            self.ARGS[k] = args_dict[k]

    def merge_section(self, section):
        """ layer a section's settings on top of the defaults, and under
        the commandline arguments"""
        args_dict = dict(self.config.items(section))
        for k in args_dict:
            self.ARGS[k] = args_dict[k]
        args_dict = self.args.__dict__
        for k in args_dict:
            self.ARGS[k] = args_dict[k]

    def parse_for_configuration(self):
        """ get the default configuration file name or if someone passed it in"""
        self.config_args, self.remaining_argv = self.conf_parser.parse_known_args()

    def parse_for_rest(self):
        """ parse the rest of the command line"""
        self.args = self.main_parser.parse_args(self.remaining_argv)

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
        for section in self.config.sections():
            self.print_config_section(section)
        return

    def print_settings(self):
        if self.args.print_settings:
            self.print_config_section(self.args.print_settings)

    def print_config_section(self, section):
            for key in self.config[section]:
                self.applogger.info("%s: %s" % (key, self.config[section][key]))

    def load_settings(self):
        """Load all the sections of the config file."""
        # these will be here as defaults from the inital parse.
        config_file = self.config_args.config_file

        # if we have them in args, use those instead.
        if self.args:
            if self.args.config_file:
                config_file = self.args.config_file

        # If we have a config file, load up the section indicated and set
        # defaults to it's result.
        if config_file:
            self.config = configparser.SafeConfigParser()
            if  os.path.isfile(config_file):
                self.config.read([config_file])

                self.applogger.debug("Reading configuration file: %s" %
                                     (config_file))

                self.config_sections = ['default']
                for name in self.config.sections():
                    if name == 'default':
                        continue
                    self.config_sections.append(name)

            else:
                # don't die if the default config file is missing.
                if config_file != self.default_config:
                    self.applogger.error("Could not read configuration file %s" %
                                         config_file)

    def save_settings(self):
        """Save a section in the config file. Based on the arguments and section
        already chosen."""
        # Save the settings to a configuration file and section.
        if self.args.save_settings and self.config_args.config_file:
            config = configparser.SafeConfigParser()

            config_file = self.config_args.config_file
            save_section = self.args.save_settings

            if os.path.isfile(config_file):
                config.read([config_file])

            self.applogger.info("Saving settings to the '%s' section in configuration file: %s" %
                                (save_section,
                                 config_file))

            # create a section in the config_parser and save to config file.
            #config = configparser.RawConfigParser()
            if config.has_section(save_section):
                self.applogger.warning("Section '%s' already exists in configuration file '%s'" %
                                       (save_section, config_file))

                # Should have a continue/abort dialog here.
                #if self.args.gui_type and self.args.gui_type != 'none':
                #    return
                #
                # exit() this is a bit harsh I think...

                # remove the current section so we can replace it.
                config.remove_section(save_section)

            config.add_section(save_section)

            # build a dictionary from the named section and the args.
            all_args = {}
            if self.args.config_section is not None:
                args_dict = dict(self.config.items(self.args.config_section))
                for k in args_dict:
                    all_args[k] = args_dict[k]

            # Get the command line arguments.
            args_dict = self.args.__dict__
            for k in args_dict:
                all_args[k] = args_dict[k]

            # add them to the new section.
            for arg in all_args:
                # we don't need to save the file or section we are saving into.
                if (arg == 'save_settings' or
                        arg == 'config_file' or
                        arg == 'config_section'):
                    continue

                if all_args[arg] is not None:
                    self.applogger.debug("%s:%s:%s" % (arg, type(all_args[arg]), all_args[arg]))
                    config.set(save_section, arg, str(all_args[arg]))

            # Writing our configuration file to args.config_file
            with open(config_file, 'w') as fconfig_file:
                config.write(fconfig_file)

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
