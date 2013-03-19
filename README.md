Project-Manager
===============

Python application to create, manage and deploy projects.

This is a simple applicaton that uses an .ini config file to define software projects.
A project can come from a remote host with or without a repository.

A project can be instantiated in different folders as desired. The default is to create a
project folder named after the project in the Project root. ctags is run automatically.

    PM new dotfiles

Will create an instance of the dotfiles project in the project root by cloning the repository.

    PM new dotfiles foo

Will create another instance of the dotfiles project in a directory named Project_root/foo.

    PM new some_utils

Will create an instance of the some_utils project by rsyncing the code from the host.

    PM deploy 

Will rsync the project with it's destination host and path.

    PM deploy somefile

Will rsync only that file.

    PM download 

Will rsync the project back down again.


Currently only Git repositories are understood.

The innards.
-------------

There is an Application package which wraps up logging, argparse, configparse and execution of 
system calls. There is another class which wraps rsync. It also has the capability of creating
a local Git repository for projects that are not in a repository for whatever stupid reason that may be.

The Project Manager is a simple class that adds to the basic arguments and makes decisions based on the contents
of the config file and the arguments.

Project manager also detects when it is inside a project. Many commands simply find the root of the project, get the 
name from that instance's config file and go from there.

Currently this works for rsyncing up and down projects, and for cloning from a repository and rsyncing locally
or remotely. 

TO DO
=====

* deploy/test to remote host retrieve results.
* Separation of targets so there can be development and production hosts and/or target paths.
* Choose to create local repository based on setting.
* SVN support?
* CVS support?

Configuration file example:
============================

<pre>
[default]
  ProjectRoot = Projects
  LocalGit =  GIT
  ProjectBase = /Volumes/Macintosh HD/Users/eric
  GitBase =  /Volumes/Macintosh HD/Users/eric
  LogLevel = info
  excludes = '*.jpg, *.mov, *.git, *.PM*, *.pyc, __pycache__'

[some_utils]
  type=Project
  repository=local
  devHost = somehost
  devPath = /some/path/on/the/host/down/to/the/code/
  excludes = '*.bak*','*\ copy'

; this one is a github repository, with deployment to a local directory.
[dotfiles]
  type=Project
  repository=ssh://git@github.com/EricGebhart/dotfiles/
  devHost = localhost
  prodHost = localhost
  devPath = /Users/eric/
  prodPath = /Users/eric/
</pre>
 
That's it for now. It's working mostly, but has a ways to go. Application core could use a little more flexibility but
does work pretty well for any program that needs a config file, logging to stdio and a log file, and argument parsing.
Here's the help text from the application.

Help text from Project Manager
====================================
    PM --help

<pre>
usage: PM [-h] [-noex] [-v {info,debug,error,critical,warning}] [-quiet]
          [-log LOG] [-config CONFIG]
          {ctags,download,deploy,new,delete,open} ...

This is a set of classes to manage local and remote software projects, with
and without revision control. Supplementing a local git repository for
projects that have no revision control.

positional arguments:
  {ctags,download,deploy,new,delete,open}
                        sub-command help
    ctags               Run ctags on current project or specified directory
    download            Get project or file from server. defaults to an update
                        of the current project
    deploy              "Upload project or file to server. Defaults to an
                        upload of the current project
    new                 New Project, if project exists creates a working
                        instance of that project in the projects directory
                        using the project name or the directory name given
    delete              Delete Project instance. Tries to delete current
                        project, or project given by the -d option
    open                Open Project with external shell command - invoke vim, eclipse, whatever...

optional arguments:
  -h, --help            show this help message and exit
  -noex                 Do not execute
  -v {info,debug,error,critical,warning}, --verbose {info,debug,error,critical,warning}
                        Verbosity level
  -quiet                Silent running
  -log LOG              Log file, defaults to .PM.log
  -config CONFIG        Config file, defaults to /Users/eric/.PMrc

</pre>
