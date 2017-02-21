# Easy SVN 2 GIT wrapper

I wrote this script since I found myself always taking the same actions when
performing SVN 2 GIT migrations for customers. It is a very simple wrapper
around other tools so no real innovation to be found here, just automation.

## Dependencies

* A Linux system
* Python3 (tested with Python 3.5)
* SVN (including svnsync)
* svn2git (from https://github.com/svn-all-fast-export/svn2git/ at least v1.0.11 is advised)
* git

*All dependencies should be installed in $PATH!*

## Usage

### Clone this repository
```
git clone https://github.com/MathyV/svn-migration.git
```

### Create a sync project
```
python3 svnmigrate.py create --authormap AUTHORMAP name source target
```

* Note that this will create a working directory called *name* in $CWD
* If you have no idea yet about the users to map just use an empty file,
the process will inform you about unmapped users after upstream synchronization
or you can look in the $CWD/name/users.txt
* There is a sample-authors.txt in the repository to view the file format

#### Arguments
```
usage: svnmigrate.py create [-h] --authormap AUTHORMAP [--nofetch]
                            name source 

positional arguments:
  name                  Name of the project
  source                Source repository (URL)

optional arguments:
  -h, --help            show this help message and exit
  --authormap AUTHORMAP
                        Username mapping file
  --nofetch             Do not perform the initial data fetch
```

### Configure the ruleset

A default rules file is installed in $CWD/name/ruleset.txt, it is pretty barren
so you should add some rules to it. For more information see the svn2git
documentation or https://techbase.kde.org/Projects/MoveToGit/UsingSvn2Git

### Perform a sync
```
python3 svnmigrate.py sync name
```

#### Arguments
```
usage: svnmigrate.py sync [-h] [--nofetch] [--push] [--force] name

positional arguments:
  name        Migration project to operate on

optional arguments:
  -h, --help  show this help message and exit
  --nofetch   Do not fetch data from the remote SVN repository
```

### Check results

The new git repositories are in $CWD/name/repos/. Check the contents and if
happy push downstream. If you need to change some rules just remove the
offending repository from the repos directory and start the sync again.

## Inner workings

* create
  * Create a working directory
  * Save the configuration in a pickle
  * Mirror the source repository locally
  * Synchronize the local mirror with upstream (optional)
  * Install a default ruleset
* sync
  * Synchronize the local mirror with upstream (optional)
  * Execute svn2git with options --identity-map, --rules and --add-metadata
  * Repack the git repositories

Note that the configuration is saved very crudely in a pickle file, which
means that it will probably won't withstand an update of this wrapper script.

