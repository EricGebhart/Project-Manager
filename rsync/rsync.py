#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   This is just a helper class to do rsync. Nothing very special here,
   but it does use the app syscall class to execute commands.
"""

__author__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__support__ = 'Eric Gebhart <e.a.gebhart@gmail.com>'
__version__ = '$Revision: 1 $'[11:-2]
__application__ = '__rsync__'    # we don't have a name yet...

import sys
import os
import re
import glob
import logging
from application.application import syscall

#logger = logging.getLogger(__application__).addHandler(logging.NullHandler())

#logger = logging.getLogger()


class connection:
    """ A class to verify, establish and re-establish the vpn connection """

    def __init__(self, logger=None):
        self.ping_stats = re.compile('^([0-9]*) packets transmitted, ([0-9]*) packets received, ([0-9]*)\% packet loss', re.S)
        self.ping_unknown = re.compile('unknown host', re.S)

        if logger is None:
            self.logger = logging.getLogger(__application__).addHandler(logging.NullHandler())
        else:
            self.logger = logger

    def check_connection(self, destination_host):
        """ Check to make sure the remote host can be found"""
        # check to make sure the host can be connected to.
        if destination_host is None:
            return True

        for ping_output in os.popen("ping -c 2 %s 2>&1" % destination_host):

            if self.ping_unknown.search(ping_output):
                self.logger.info(ping_output)
                return False

            match = self.ping_stats.match(ping_output)
            if match:
                trans, received, loss = match.group(1), match.group(2), match.group(3)
                self.logger.error("%s transmitted, %s Received, %s %% loss" % (trans, received, loss))
                if loss == '100':
                    self.logger.error("Not connected")
                    return False

        return True


class rsync:

    def __init__(self, cmd=None, logger=None, remote_directory=None, remote_host=None,
                 local_dir=None, excludes=None):

        #self.current_directory = os.getcwd()
        self.current_directory = local_dir
        if not remote_directory:
            self.remote_directory = os.path.basename(self.current_directory)
        else:
            self.remote_directory = remote_directory

        if cmd is None:
            self.cmd = syscall()
        else:
            self.cmd = cmd

        if logger is None:
            self.logger = logging.getLogger(__application__).addHandler(logging.NullHandler())
        else:
            self.logger = logger

        # lead with a space so we get a --exclude after it with the join.
        self.excludes = ["'.git'", "'.CVS'", "'.com'", "'.obj'"]

        # Set up the rsync command variables.
        if excludes is not None:
            self.excludes.append(excludes)
        self.parent_dir = local_dir
        self.remote_host = remote_host
        if self.remote_host == 'localhost':
            self.remote_host = None
            self.remote_host_directory = self.remote_directory
        else:
            self.remote_host_directory = "%s:%s" % (self.remote_host, self.remote_directory)

        # take out the q's and put in v's for verbosity.
        self.logger.debug("Excludes: %s" % self.excludes)
        if self.excludes:
            exclude_string = " --exclude ".join(self.excludes)
        self.command = ("rsync -azvuK %s" % exclude_string)
        self.simple_command = 'rsync -uazvK '

        if connection(self.logger).check_connection(self.remote_host) is False:
            sys.exit()

    def get_directory(self, directory=None):
        """rsync a directory from the host."""
        #rsync -avz defender:pp/$1/sup ~/pp/$1
        try:
            remote_path = os.path.join(self.remote_host_directory, directory),
        except:
            remote_path = self.remote_host_directory
        command = "%s %s %s" % (self.command, remote_path,
                                self.current_directory.replace(' ', '\ '))
        self.cmd.run(command)

    def get_pattern(self, pattern):
        """rsync a file pattern from the host"""
        #rsync -avz defender:/pp/$1/*.sas  ~/pp/$1
        command = "%s %s %s" % (self.simple_command,
                                os.path.join(self.remote_host_directory, pattern),
                                self.current_directory)
        self.cmd.run(command)

    def send_directory(self, directory=None):
        """rsync a directory _to_ the host if it's here"""
        if not directory:
            directory = self.current_directory
        if os.path.isdir(directory):
            #rsync -avz --exclude com/ --exclude obj/ --exclude sio/ ods locutus:pp/$pp
            # Add a slash on the end if there isn't one so we don't create the
            # directory on the other end.
            if directory[-1] != '/':
                directory = "%s/" % directory
            command = "%s %s %s" % (self.command, directory.replace(' ', '\ '),
                                    self.remote_host_directory)
            self.cmd.run(command)

    def send_pattern(self, pattern):
        """rsync a file _to_ the host if it's here"""
        if glob.glob(pattern):
            #logger.info(pattern)
            #rsync -avz *.xml locutus:pp/$pp/
            command = "%s ./%s %s" % (self.simple_command, pattern, self.remote_host_directory)
            self.cmd.run(command)

    def send_directories(self, directories):
        """Send directories to the remote host"""
        #logger.info("Directories: %s" % directories)
        if len(directories):
            for directory in directories:
                self.send_directory(os.path.join(self.current_directory, directory))
        else:
            self.send_directory()

    def send_file(self, file):
        """Send files to the remote host"""
        self.logger.info("Send File %s" % file)
        if os.path.isfile(file):
            #rsync -avz --exclude com/ --exclude obj/ --exclude sio/ ods locutus:pp/$pp
            # Add a slash on the end if there isn't one so we don't create the
            # directory on the other end.
            extend_path = os.path.dirname(file)
            remote_path = os.path.join(self.remote_host_directory, extend_path)
            command = "%s %s %s" % (self.command, file, remote_path)
            self.cmd.run(command)

    def send_files(self, files):
        """Send files to the remote host"""
        self.logger.debug("Send Files %s" % files)
        for pattern in files:
            self.send_pattern(pattern)

    def get_directories(self, directories):
        """Get directories from the remote host"""
        self.logger.info("Get Directories")
        self.get_directory()
        try:
            for directory in directories:
                self.get_directory(directory)
        except:
            self.get_directory()

    def get_files(self, files):
        """Get files from the remote host"""
        self.logger.info("Get Files")
        for pattern in files:
            self.get_pattern(pattern)

if __name__ == "__main__":
    pass
