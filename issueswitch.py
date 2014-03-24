#!/usr/bin/env python
# encoding: utf-8

import os
import os.path
import sys
import getpass
import ConfigParser
import itertools

import keyring
import pyral
import jira

def guiLogin(title, default_username="", default_password=""):
    from Tkinter import Tk, N, S, W, E, StringVar
    import ttk

    root = Tk()

    root.title(title)

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    username = StringVar()
    username.set(default_username)
    password = StringVar()
    password.set(default_password)

    def done(*args):
        root.destroy()

    ttk.Label(mainframe, text="Username:").grid(column=1, row=1, sticky=(W, E))
    username_entry = ttk.Entry(mainframe, width=7, textvariable=username)
    username_entry.grid(column=2, row=1, sticky=(W, E))

    ttk.Label(mainframe, text="Password:").grid(column=1, row=2, sticky=(W, E))
    pass_entry = ttk.Entry(mainframe, width=7, textvariable=password, show="*")
    pass_entry.grid(column=2, row=2, sticky=(W, E))

    ttk.Button(mainframe, text="Login", command=done).grid(column=2, row=3, sticky=W)

    for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=2)

    username_entry.focus()
    root.bind('<Return>', done)
    root.bind('<Escape>', lambda event: root.destroy())

    root.lift()
    root.call('wm', 'attributes', '.', '-topmost', True)
    root.after_idle(root.call, 'wm', 'attributes', '.', '-topmost', False)

    root.mainloop()

    return username.get(), password.get()

JIRA_CONFIG_FILE = os.path.expanduser("~/.jiraswtich.conf")

class JiraSwitcher:
    def __init__(self):
        self._jira = None
        self.config = ConfigParser.ConfigParser()
        self.config.read(JIRA_CONFIG_FILE)
        self.username = self.getConf("username", "")

        self.server = self.getConf("server", "")
        if not self.server:
            if not self.server and sys.stdin.isatty():
                self.server = raw_input("Jira server: ")
            if not self.server:
                self.server = "https://jira.atlassian.com"
            self.setConf("server", self.server)

    def getConf(self, key, default=None):
        if self.config.has_option("DEFAULT", key):
            return self.config.get("DEFAULT", key)
        else:
            return default

    def setConf(self, key, value):
        self.config.set("DEFAULT", key, value)
        with open(JIRA_CONFIG_FILE, "wb") as outf:
            self.config.write(outf)

    def getCred(self, username="", password="", force=False):
        if username and not force:
            password = keyring.get_password("jira", username)
        if not password or force:
            if sys.stdin.isatty():
                username = raw_input("Jira username: ")
                password = getpass.getpass("Jira password: ")
            else:
                username, password = guiLogin("Jira login", default_username=username, default_password=password)
        return username, password

    def storeCred(self, username, passw):
        self.setConf("username", username)

        if not passw:
            if keyring.get_password("jira", username):
                keyring.delete_password("jira", username)
        else:
            keyring.set_password("jira", username, passw)

    def getPass(self):
        password = keyring.get_password("jira", self.username)
        if not password:
            if sys.stdin.isatty():
                password = getpass.getpass("Jira password: ")
            else:
                password = getGuiPass()
        return password

    def storePass(self, value):
        if not value:
            if keyring.get_password("jira", self.username):
                keyring.delete_password("jira", self.username)
        else:
            keyring.set_password("jira", self.username, value)

    @property
    def jira(self):
        tries = 0
        while not self._jira:
            tries += 1
            if tries > 3:
                raise Exception("Too many tries")

            try:
                self.username, password = self.getCred(self.username)
                if not self.username or not password:
                    raise Exception("Missing username or password")

                # This causes an exception if the credentials are wrong
                options = {
                        'server': self.server,
                        'verify': False,
                        }
                self._jira = jira.client.JIRA(options, basic_auth=(self.username, password))

                self.storeCred(self.username, password)
                break
            except jira.exceptions.JIRAError, e:
                if e.status_code == 401:
                    self._jira = None
                    self.storeCred(self.username, None)
                else:
                    raise

        return self._jira

    def getItemAndParents(self, id):
        issue = self.jira.issue(id)
        while issue:
            yield {
                    "id": issue.key,
                    "name": issue.fields.summary,
                    }

            if issue.fields.issuetype.subtask and issue.fields.parent:
                issue = self.jira.issue(issue.fields.parent.key)
            else:
                issue = None


RALLY_CONFIG_FILE = os.path.expanduser("~/.rallyswtich.conf")

class RallySwitcher:
    def __init__(self):
        self._rally = None
        self.config = ConfigParser.ConfigParser()
        self.config.read(RALLY_CONFIG_FILE)
        self.username = self.getConf("username", "")
        self.server = self.getConf("server", "rally1.rallydev.com")
        self.workspace = self.getConf("workspace", None)
        self.project = self.getConf("project", None)

    def getConf(self, key, default=None):
        if self.config.has_option("DEFAULT", key):
            return self.config.get("DEFAULT", key)
        else:
            return default

    def setConf(self, key, value):
        self.config.set("DEFAULT", key, value)
        with open(RALLY_CONFIG_FILE, "wb") as outf:
            self.config.write(outf)

    def getCred(self, username="", password="", force=False):
        if username and not force:
            password = keyring.get_password("rally", username)
        if not password or force:
            if sys.stdin.isatty():
                username = raw_input("Rally username: ")
                password = getpass.getpass("Rally password: ")
            else:
                username, password = guiLogin("Rally login", default_username=username, default_password=password)
        return username, password

    def storeCred(self, username, passw):
        self.setConf("username", username)

        if not passw:
            if keyring.get_password("rally", username):
                keyring.delete_password("rally", username)
        else:
            keyring.set_password("rally", username, passw)

    @property
    def rally(self):
        tries = 0
        while not self._rally:
            tries += 1
            if tries > 3:
                raise Exception("Too many tries")
            try:
                self.username, password = self.getCred(self.username)
                if not self.username or not password:
                    raise Exception("Missing username or password")

                # This causes an exception if the credentials are wrong
                extras = {}
                if self.workspace:
                    extras["workspace"] = self.workspace
                if self.project:
                    extras["project"] = self.project
                self._rally = pyral.Rally(self.server, self.username, password, **extras)
                if not self.workspace:
                    self.setConf("workspace", self._rally.getWorkspace().Name)
                if not self.project:
                    self.setConf("project", self._rally.getProject().Name)
                self.storeCred(self.username, password)
                break
            except pyral.RallyRESTAPIError, e:
                if e.message.startswith("401"):
                    self._rally = None
                    self.storeCred(self.username, None)
                else:
                    raise
        return self._rally

    def getItem(self, id):
        if self.server in id:
            id = id.split("/")[-1]
            query = '(ObjectID = "%s")' % id
        else:
            query = '(FormattedId = "%s")' % id
        artifacts = self.rally.get("Artifact", query=query, fetch="FormattedID,Parent,WorkProduct")
        artifact = None
        for a in artifacts:
            if a.FormattedID == id or a.oid == id:
                artifact = a
                break
        return artifact

    def getItemAndParents(self, id):
        issue = self.getItem(id)
        while issue:
            yield {
                    "id": issue.FormattedID,
                    "name": issue.Name,
                    }
            if "Parent" in issue.attributes() and issue.Parent:
                issue = issue.Parent
            elif "WorkProduct" in issue.attributes() and issue.WorkProduct:
                issue = issue.WorkProduct
            else:
                issue = None

def get_issues(ids):
    for switcher in [RallySwitcher(), JiraSwitcher()]:
        for id in ids:
            for issue in switcher.getItemAndParents(id):
                yield issue

def main(args):
    if not os.access(os.curdir, os.W_OK):
        os.chdir(os.path.expanduser("~"))
    issues = list(get_issues(args))
    for i, issue in enumerate(issues):
        if i > 0:
            print
        # Write without trailing newline (CopyQ is weird..)
        sys.stdout.write("%s: %s\n%s" % (issue["id"], issue["name"], issue["id"]))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
