Issue Switcher
==============

Script which takes a Rally or Jira issue ID as an argument, and provides
various types of output related to the issue on stdout.

Currently it provides:
- The issue, and (if it has one) its parent's ID as "`###: <summary>`" and as "`###`"

This script is mostly intended for my personal use along with CopyQ by doing the following:
- Add a command to CopyQ named "Collect Issue data"
- Set the "Content" to: "`^[ \t\n]*([A-Z]{2,}-?[0-9]{2,9})[ \t\n]*$`"
- Type of Action "Automatic" and "In Menu"
- Command: "`/path/to/issueswitch %2`"
- Output: "`text/plain`"
- Separator: "`\n`"
- Output tab: "`&issues`"

The result of the above is that when an issue ID is copied, CopyQ will run this
script and put it's output into a separate tab.

I recommend creating a single-file binary using pyinstaller by running:

    pyinstaller issueswitch.spec
