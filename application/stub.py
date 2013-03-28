#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   This is a stub program that uses the application class framework.
   Do what you want with it. It has logging, config files etc.
   Copy this as a starting point for any new commandline program.
"""

__author__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__support__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__version__ = '$Revision: 1 $'[11:-2]
__application__ = 'stub'    # we don't have a name yet...
__default_config__ = '.STUBrc'  # we don't have a name yet...
__default_log__ = '.STUB.log'   # we don't have a name yet...


from application import applicationCore
from application import apperror


class stub(applicationCore):
    """
    This is a stub class that uses the application Core framework.
    Do what you want with it. It has logging, config files etc.
    run this with python3 stub.py -h to see what it can do as is.
    """

    def __init__(self):

        self.doc = __doc__
        self.application = __application__
        self.default_config = __default_config__
        self.default_log = __default_log__

        super().__init__()

        """ Setup whatever else you need here."""

    def argument_setup(self):

        """Add arguments or add subparsers. Read up on argparse for more info.
        """
        # here's a subparser example.
        """
        subparsers = self.main_parser.add_subparsers(help='sub-command help')
        """

        # create the parser for the "ctags" command
        """
        parser = subparsers.add_parser('sub-command',
                                       help="Sub command help.")
        parser.add_argument('-d', '--directory',
                            help='Run sub-command on this directory')
        """
        # setting a default method will allow easy processing
        """
        parser.set_defaults(func=self.sub-command)
        """

    def process(self):
        """Process the arguments, distribute the work. """

        # Load the config file, setup logging and read the arguments.
        super().process()

        #ready to go.
        #This is where we do what we need based on the config file and arguments.

        # Everything we need should be in self.ARGS. Except for our project
        # section. We can ask our super to merge the config section in as
        # soon as we know it's name.

        # You can raise errors this way or with an exception...
        if __doc__ is None:
            raise apperror("This program has not doc comment.")

        # Need some debug for understanding???? Here it is.
        #self.logger.info(self.ARGS)
        #self.logger.info(self.config)   #  Probably don't need this.
        #self.print_config()             #  Or this.

        # run our default functions for our subparsers.
        # It's either this, or process them all the hard way.
        # self.args.func() will farm out the arguments to each
        # subparser's default function.

        # surround it all with a try to handle errors nicely.
        if 'func' in self.args:
            try:
                self.args.func()
                return 0
            except Exception as e:
                self.logger.error(e)
                return 1

if __name__ == "__main__":
    stub().app_main()
