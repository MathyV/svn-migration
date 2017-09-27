import argparse
import os
import pickle
import shutil
import subprocess
import sys

scriptdir = os.path.dirname(os.path.realpath(__file__))
hook = os.path.join(scriptdir, "pre-revprop-change")

class Configuration:
    pass

    @property
    def projectdir(self):
        return os.path.join(self.workdir, self.name)

    @property
    def configfile(self):
        return os.path.join(self.projectdir, "config.pickle")

    @property
    def mirror(self):
        return os.path.join(self.projectdir, "mirror")

    @property
    def mirrorurl(self):
        return "file://{}".format(self.mirror)

    @property
    def userfile(self):
        return os.path.join(self.projectdir, "users.txt")

    @property
    def repo(self):
        return self.name

    @property
    def rules(self):
        return os.path.join(self.projectdir, "ruleset.txt")

    @property
    def repopath(self):
        return os.path.join(self.projectdir, "repos")

    @property
    def svn2gitlog(self):
        return os.path.join(self.repopath, "svn2git.log")

    def save(self):
        self.authormap = os.path.realpath(self.authormap)

        with open(self.configfile, 'wb') as f:
            pickle.dump(self, f)

    def load(self):
        with open(self.configfile, 'rb') as f:
            return pickle.load(f)

ruletemplate = """# For more info, see https://techbase.kde.org/Projects/MoveToGit/UsingSvn2Git

create repository {repo}
end repository

match /trunk/
    repository {repo}
    branch master
end match

# Any non-matched path gets a no-op
match /
end match"""

def svnsync(url):
    print("Pulling upstream changes")
    subprocess.run(["svnsync", "sync", config.mirrorurl], check=True)

def fetchusers(url, f):
    print("Writing usernames to {}".format(f))
    subprocess.run("svn log -q " + url + " | grep -e '^r' | awk 'BEGIN { FS = \"|\" } ; { print $2 }' | sort | uniq > " + f, shell=True, check=True)

def checkusers(users, mapping):
    m = []

    with open(mapping, 'r') as f:
        for line in f:
            if len(line) > 0 and line[0] != '#':
                m.append(line.split(' ')[0])

    with open(users, 'r') as f:
        for line in f:
            u = line.strip(' \n')
            if not u in m:
                print("Unmapped user: {}".format(u))

def fetch(config):
    if config.nofetch:
        print("Not fetching data")
    else:
        svnsync(config.mirrorurl)
        fetchusers(config.mirrorurl, config.userfile)
        checkusers(config.userfile, config.authormap)

def create(config):
    if not os.path.isdir(config.workdir):
        print("Working directory does not exist")
        sys.exit(1)
    
    os.mkdir(config.projectdir)
    os.mkdir(config.repopath)
    config.save()

    print("Creating a mirror repository")
    subprocess.run(["svnadmin", "create", config.mirror], check=True)
    
    # Copy the hook that allows changing properties
    shutil.copy(hook, os.path.join(config.mirror, "hooks"))

    print("Initializing the sync")
    subprocess.run(["svnsync", "init", config.mirrorurl, config.source], check=True)

    print("Installing a default ruleset in {}".format(config.rules))
    with open(config.rules, 'w') as f:
        f.write(ruletemplate.format(**{ 'repo' : config.repo }))

    fetch(config)

def sync(config):
    fetch(config)

    print("Performing svn2git")
    with open(config.svn2gitlog, "w") as f:
        subprocess.run(["svn2git",
            "--identity-map", config.authormap,
            "--rules", config.rules,
            "--add-metadata",
            config.mirror],
            check=True, cwd=config.repopath, stdout=f, stderr=subprocess.STDOUT)

    print("Packing git repositories")
    for item in os.listdir(config.repopath):
        path = os.path.join(config.repopath, item)

        if os.path.isdir(path) and os.path.exists(os.path.join(path, "HEAD")):
            print("  {}".format(path))
            subprocess.run(["git", "repack", "-a", "-d", "-f"], check=True, cwd=path)


parser = argparse.ArgumentParser(description='Perform an SVN to Git migration')
parser.add_argument('--workdir', default=os.getcwd(), help='Working directory, make sure you have enough free space! (default: $CWD)')
actions = parser.add_subparsers(metavar='action', help='Action to perform')

create_parser = actions.add_parser('create', help='Create a new migration project')
create_parser.add_argument('name', help='Name of the project')
create_parser.add_argument('source', help='Source repository (URL)')
create_parser.add_argument('target', help='Target repository (URL)')
create_parser.add_argument('--authormap', help='Username mapping file', required=True)
create_parser.add_argument('--nofetch', action='store_true', help='Do not perform the initial data fetch')
create_parser.set_defaults(func=create)

sync_parser = actions.add_parser('sync', help='Sync a migration')
sync_parser.add_argument('name', help='Migration project to operate on')
sync_parser.add_argument('--nofetch', action='store_true', help='Do not fetch data from the remote SVN repository')
sync_parser.add_argument('--push', action='store_true', help='Push the data to the remote Git repository')
sync_parser.add_argument('--force', action='store_true', help='Force push to the remote repository')
sync_parser.set_defaults(func=sync)

config = Configuration()

parser.parse_args(namespace=config)

# If a config file exists, load it and apply the arguments again
if os.path.isfile(config.configfile):
    config = config.load()
    parser.parse_args(namespace=config)

config.func(config)

