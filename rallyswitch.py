#!/usr/bin/env python
# encoding: utf-8

import os
import os.path
import sys
import getpass
import ConfigParser

import keyring
import pyral

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


CONFIG_FILE = os.path.expanduser("~/.rallyswtich.conf")

class RallySwitcher:
    def __init__(self):
        self._rally = None
        self.config = ConfigParser.ConfigParser()
        self.config.read(CONFIG_FILE)
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
        with open(CONFIG_FILE, "wb") as outf:
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
        artifacts = self.rally.get("Artifact", query='(FormattedId = "%s")' % id, fetch="FormattedID,Parent,WorkProduct")
        artifact = None
        for a in artifacts:
            if a.FormattedID == id:
                artifact = a
                break
        return artifact

    def getItemAndParents(self, id):
        issue = self.getItem(id)
        while issue:
            yield issue
            if "Parent" in issue.attributes() and issue.Parent:
                issue = issue.Parent
            elif "WorkProduct" in issue.attributes() and issue.WorkProduct:
                issue = issue.WorkProduct
            else:
                issue = None

def main(args):
    switcher = RallySwitcher()
    for id in args:
        for issue in switcher.getItemAndParents(id):
            print "%s: %s\n%s" % (issue.FormattedID, issue.Name, issue.FormattedID)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
