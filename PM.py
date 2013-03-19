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

import os
import re
import datetime
import configparser


from application import applicationCore
from application import apperror
from rsync import rsync


class Project_config ():
    """Class for managing the project config file which resides at the top
       of each project directory tree """

    def __init__(self, path, name=None, configfile=__project_config_file__,
                 logger=None):

        if logger is not None:
            self.logger = logger
        else:
            import logging
            logger = logging.getLogger(__application__).addHandler(logging.NullHandler())

        # load up the project config file. get the name.
        self.config = configparser.SafeConfigParser()
        self.configfile = os.path.join(path, configfile)
        if  os.path.isfile(self.configfile):
            self.config.read([self.configfile])

            self.name = self.config['default']['name']

        else:
            #if we have a name we can make one. Otherwise we are done.
            if not name:
                logger.error("Could not read configuration file %s" % self.configfile)
            else:
                self.make(name)

        # These are potential values for the project file. Only name is there
        # so far.
        self.values = {
            'name':      '',
            'cvsroot':   '',
            'cvsbranch': '',
            'bugtrack':  '',
            'title':     '',
            'patchfile': ''
        }

    def make(self, name):
        """write out the default configuration file"""
        self.config['default'] = {}
        self.config['default']['name'] = name
        self.write()

    def write(self):
        try:
            config = open(self.configfile, 'w')
            self.config.write(config)
            config.close()
        except (IOError, OSError):
            self.logger.error('Could not create %s file' % self.configfile)
            raise Exception


class PM(applicationCore):
    """Sync project to and from a remote host"""
    """This is Project Manager application, It syncs with remote hosts, and git.
        It uses a local git when the project has no real revision control which
        seems to be common for web applications"""

    def __init__(self):
        super().__init__()

        self.project = None         # project name
        self.directory = None       # project directory
        self.project_config = None  # project configuration.
        self.file = None            # individual file, send or get
        self.project_root = None    # Where all projects go.
        self.abs_project_path = None  # The absolute path to this project instance.
        self.name = None            # Name of the project
        self.pconfig = None         # This is the project directory's config.
        self.open_command = None    # what we do to open a project.
        self.excludes = None
        self.host = None
        self.repository = None
        self.host_path = None
        self.GitBase = None
        self.gitlocal = None
        project_base = self.config['default']['ProjectBase']
        project_root = self.config['default']['ProjectRoot']
        self.project_root = os.path.join(project_base, project_root)
        self.excludes = []

        if 'file' in self.args:
            current_directory = os.path.abspath('')
            self.file = self.args.file

        if 'p' in self.args:
            self.name = self.args.p

        if 'new' in self.args:
            self.name = self.args.new

        # Directory is the local location of the project.
        # The default is the name of the project.
        if 'directory' in self.args and self.args.directory is not None:
            self.directory = self.args.directory
        else:
            self.directory = self.name

        self.find_working_project()

        self.logger.debug('%s : %s' % (self.name, self.directory))

        # if a filename was given, get it's relative path in the project.
        if self.file:
            self.set_file(current_directory)

        # Try to load the Project manager's config file and get
        # the default settings and project definitions.
        self.set_project_config()

        # be ready to create or use a local git.
        self.set_local_git(project_base)

        #Get the open command if we have one.
        self.set_opencmd()

        #get the excludes for the rsync.
        self.setup_excludes()

        # set up the rsync connection
        self.rsync = rsync(self.cmd, self.logger,
                           self.host_path, self.host,
                           self.abs_project_path,
                           self.excludes)

        self.months = {
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dec': 12
        }

        self.files = ['*.xml',
                      '*.html',
                      '*.rtf',
                      '*.csv',
                      '*.xls',
                      '*.pdf',
                      '*.ps',
                      '*.gif',
                      '*.tpl',
                      '*.lua',
                      '*.sas',
                      '*.py',
                      '*.c',
                      '*.ini',
                      '*.map',
                      '*.gif',
                      '.newpp',
                      '*.sas7bdat'
                      ]

        self.sas_command = 'slt'
        #self.remote_setup = ". ~/.profile;. ~/.zshrc;"
        self.remote_setup = ". ~/.zshrc; sdsenv ;"

    def set_file(self, current_directory):
        """If a file name was given get it's relative path within the project"""
        if self.file is not None:
            self.file = os.path.relpath(
                os.path.join(current_directory, self.file),
                self.abs_project_path)

    def set_project_config(self):
        """get the config file from the root of the project so we can find the
        root and get the name"""
        try:
            self.pconfig = self.config[self.name]
        except:
            self.logger.error("Could not find project definition: %s" % self.project)
            raise Exception

        # make everything easier to get to.
        self.host = self.pconfig['devHost']
        self.host_path = self.pconfig['devPath']
        self.directories = self.pconfig['directories']
        self.repository = self.pconfig['repository'] or 'local'

    def set_local_git(self, project_base):
        """ setup the local git repository settings."""
        gitbase = self.config['default']['GitBase'] or None
        gitlocal = self.config['default']['localGit'] or None

        try:
            self.local_git = os.path.join(gitbase, gitlocal)
        except:
            self.local_git = os.path.join(project_base, 'GIT')

        self.local_repository = os.path.join(self.local_git, ('%s.git' % self.name))

    def setup_excludes(self):
        try:
            # Get it from the default section.
            self.excludes = self.config['default']['excludes']
            self.excludes.append = self.pconfig['excludes']
        except:
            try:
                self.excludes = self.pconfig['excludes'] or None
            except:
                self.excludes = None

    def set_opencmd(self):
        try:
            self.open_command = self.pconfig['OpenCmd']
        except:
            try:
                # Get it from the default section.
                self.open_command = self.config['default']['OpenCmd'] or None
            except:
                self.open_command = None

    def find_project_root(self):
        """Find the top of the project tree"""
        while (os.path.abspath(self.project_root) != os.path.abspath('')
               and os.path.abspath('') != os.path.abspath('/')):

            if os.path.isfile(__project_config_file__):
                self.abs_project_path = os.path.abspath('')
                return
            else:
                os.chdir('..')

        self.logger.error("This is not a valid PM project.")
        raise Exception

    def find_working_project(self):
        if self.name is None:
            if (self.directory):
                os.chdir(os.path.join(self.project_root, self.directory))
            #find the top of the current project and get the name from
            # the projects rc file.  Set the project abs path while we are at it.
            self.find_project_root()
            if self.abs_project_path is not None:
                self.logger.debug("Found root %s" % self.abs_project_path)
                self.project_config = Project_config(self.abs_project_path)
                self.name = self.project_config.name
            else:
                raise apperror("This is not a valid project directory")
        else:
            self.abs_project_path = os.path.join(self.project_root, self.directory)

    """ This is the beginning of the action methods. What we do with the commands
    given to us. Still some work to do. But create a project from a repository,
    or from a remote host. Upload, download, get results, run remote test, etc."""

    def delete(self):
        pass

    def new(self):
        """make project directory download or checkout source"""
        # clone it, or mkdir and rsync it down.
        # make sure there is a project config .PMrc.project file there.
        self.get()
        self.ctags()

    def make(self):
        """create the directory when we don't have a repo."""
        path = self.abs_project_path

        if os.path.isdir(path) or os.path.isfile(path):
            raise  apperror('Project directory exists: %s' % path)
        else:
            self.logger.info("making directory %s" % path)
            os.makedirs(path)
            # Create the config file for the project.

    def make_pconfig(self):
            self.project_config = Project_config(
                self.abs_project_path, self.name, logger=self.logger)

    def send(self, minimum=None):
        """Update to a remote host"""
        if self.file is not None:
            self.rsync.send_file(self.file)
        else:
            self.rsync.send_directories(self.directories)
            self.rsync.send_files(self.files)

    def get(self, minimum=None):
        """populate or update from a remote host"""
        # If we have a remote repository, check stuff out.
        if self.repository != 'local':
            self.clone()
        else:
            # Not a remote repository, unless we have one here.
            # if we have a local repository, check stuff out.
            if os.path.isdir(self.local_repository):
                self.logger.info("Local repository: %s" % self.local_repository)
                self.clone()
            else:
                # no repository, download everything, and create a local remote
                # git init --bare repository. After this we can just check stuff in and
                # out and upload our changes to the server.
                self.make()
                self.rsync.get_directories(self.directories)
                self.rsync.get_files(self.files)
                #self.setup_local_git()
        self.ctags()
        self.make_pconfig()

    def setup_local_git(self):
        """ create a local git repository."""
        if self.repository == 'local':
            if os.path.isdir(self.local_repository):
                # do we just do a clone here?
                self.clone()
            else:
                # create bare git repository to check stuff into.
                os.mkdir(self.local_repository)
                command = "git init --bare %s" % self.local_repository
                self.cmd.run(command)

                # initilize git in working project, push all to repository.
                os.chdir(self.directory)
                self.cmd.run('git init')   # .git in local dir.
                self.cmd.run('git remote add origin %s' % self.local_repository)  # connect to remote repo
                self.cmd.run('git add .')  # add everything
                self.cmd.run('git commit -m "Initial import"')  # commit
                self.cmd.run('git push')  # put it all into the remote repository.

    def clone(self):
        """ get the project from it's git repository."""
        # Going to need to check repository type if we want to support
        # something other than git.
        os.chdir(self.project_root)
        if self.repository == 'local':
            if os.path.isdir(self.local_repository):
                command = "git clone %s" % self.local_repository
            else:
                raise  apperror('Sorry, no repository for this project')
        else:
            command = "git clone %s" % self.repository

        command = ('%s %s' % (command, self.directory))
        self.cmd.run(command)

    def open(self):
        """ Open an IDE session on this project using the command given."""
        if self.open_command is not None:
            command = '%s %s' % (self.open_command,
                                 self.abs_project_path.replace(' ', '\ '))
            self.cmd.run(command)
        else:
            self.logger.info("""Sorry, no open command defined.
                        Add OpenCmd setting to config_file""")

    def ctags(self):
        """ run ctags on the current project"""
        os.chdir(self.abs_project_path)
        self.cmd.run("/usr/local/bin/ctags -R .")

    """These guys need some work. Mostly just stolen code from my SAS project
    manager which isn't really valid here. But similar. So these  are placeholders
    until I can get to them."""

    def get_results(self):
        """Get the most recent files from the the host"""
        self.logger.info("Getting Results")
        #ssh defender "ls -lt pp/s0265456"
        base_time = None
        files = []
        sas_files = re.compile('\.sas', re.S)
        for line in os.popen('ssh 10.16.2.246 "ls -lt %s"' % self.remote_directory):

            # if it's not a directory entry we don't want it.
            if len(line.split()) < 9:
                continue

            #print line.split()
            month_name, day, time, name = line.split()[5:]
            #print month_name, day, time, name
            hour, minutes = time.split(':')
            time_tuple = [datetime.datetime.now().year, self.months[month_name], int(day), int(hour), int(minutes), 0, 0, 1, 0]
            #print time_tuple
            epoch_time = datetime.datetime(time_tuple)

            # the first file.
            if not base_time:
                base_time = epoch_time
                files.append(name)
            else:
                # get all the files that have a date within a minute
                # of the first one.
                if base_time - epoch_time < 90:
                    if not sas_files.search(name):
                        files.append(name)
                else:
                    # bail once a file is too old
                    break

        self.get_files(files)

    def run_sas(self, program='test.sas'):
        """run batch sas with a program on a remote host"""
        # ". ~/.zlogin;. ~/.zshrc; cd ~/pp/s0265456; slt t11"
        remote_sas_command = "ssh %s '%s cd %s" % (self.remote_host, self.remote_setup, self.remote_directory)
        remote_sas_command += "; %s %s'" % (self.sas_command, program)
        os.system(remote_sas_command)

    def run_and_get(self, program='test.sas'):
        """run batch sas remotely and get the results back"""
        self.run_sas(program)
        self.get_results()

    def checkout_source(self):
        if self.directory:
            if not self.noex:
                os.system(("cvs -z2 co -r %s %s_src" %
                           (self.track_tls, self.directory)))
            else:
                print ("No execute: cvs -z2 co -r %s %s_src" %
                       (self.track_tls, self.directory))
        else:
            for directory in self.__class__.directories:
                if not self.noex:
                    os.system(("cvs -z2 co -r %s %s_src" %
                               (self.track_tls, directory)))
                else:
                    print ("No execute: cvs -z2 co -r %s %s_src" %
                           (self.track_tls, directory))
    """This is where we setup the commandline arguments for the ApplicationCore
    class. application core handles help, verbosity, config file, quiet,
    no execute. Maybe more. This class uses subparsers to create commands.
    Each subparser has a default function that is called automatically later on.
    """
    def argument_setup(self):

        #Create the sub parsers for each command
        #self.main_parser.add_argument('command', choices=['ctags', 'deploy', 'download'],
        #                              help='execute command on current project')
        subparsers = self.main_parser.add_subparsers(help='sub-command help')

        # create the parser for the "ctags" command
        parser = subparsers.add_parser('ctags',
                                       help="""Run ctags on current project or specified directory""")
        parser.add_argument('-d', '--directory',
                            help='Run ctags on this directory instead of project')
        parser.set_defaults(func=self.ctags)

        # create the parser for the "get" command
        parser = subparsers.add_parser('download', help="""Get project or file from server.
                                       defaults to an update of the current project""")
        parser.add_argument('-p', '--project', help='download project into current directory')
        parser.add_argument('-f', '--file', help='download file.')
        parser.set_defaults(func=self.get)

        # create the parser for the "put" command
        parser = subparsers.add_parser('deploy', help=""""Upload project or file
                                       to server. Defaults to an upload of the current project""")
        parser.add_argument('-f', '--file', help='download file.')
        parser.add_argument('-d', '--directory',
                            help="""Directory name of project to upload.
                            Must be a valid project directory.""")
        parser.set_defaults(func=self.send)

        # create the parser for the "new" command, this either creates a new
        # config section or creates the project directory and gets the source
        # code.
        parser = subparsers.add_parser('new', help="""New Project, if project exists creates
                                       a working instance of that project in the projects
                                       directory using the project name or the directory name
                                       given""")
        parser.add_argument('new', help='Name of Project to create')
        parser.add_argument('-d', '--directory', help="""Name of Directory to put project in.
                            Defaults to Project name.""")
        parser.set_defaults(func=self.new)

        # create the parser for the "Delete" command
        parser = subparsers.add_parser('delete', help="""Delete Project instance.
                                       Tries to delete current project, or project
                                       given by the -d option""")
        parser.add_argument('-d', '--directory',
                            help="""Name of Directory to delete. Defaults to
                            Project name if currently inside project.""")
        parser.set_defaults(func=self.delete)

        # create the parser for the "Open" command
        parser = subparsers.add_parser('open',
                                       help="""Open Project directory with shell
                                       command as specified by OpenCmd in
                                       the config file""")
        parser.add_argument('directory', help='Name of Project directory to open in IDE')
        #parser.add_argument('-t', '--type', help="""Type of project. Helps determine stuff""")
        parser.set_defaults(func=self.open)

    def process(self):
        """Process the arguments, distribute the work. """

        # Load the config file, setup logging and read the arguments.
        super().process()

        #ready to go.
        #This is where we do what we need based on the config file and arguments.

        # Need some debug for understanding???? Here it is.
        #self.logger.info(self.args)
        #self.logger.info(self.config)
        #self.print_config()

        # run our default functions for our subparsers.
        # It's either this, or process them all the hard way.
        # self.args.func() will farm out the arguments to each
        # subparser's default function.

        # surround it all with a try to handle errors nicely.
        #try:
        self.args.func()
        #    return 0
        #except Exception as e:
        #    self.logger.error(e)
        #    return 1

if __name__ == "__main__":
    PM().app_main()
