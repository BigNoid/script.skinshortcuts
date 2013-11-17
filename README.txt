INFO FOR SKINNERS - How to use this addon in your skin:

1. Let users manage their shortcuts (e.g. from skinsettings.xml)

RunScript(script.skinshortcuts?type=manage&group=[groupname])

This will display a dialog where the users can select and manage shortcuts for the given group name.

2. Display user shortcuts

Uses new method of filling the contents of a list in Gotham

<content>plugin://script.skinshortcuts?type=list&group=[groupname]</content>

This will return items with the following information
	Label - The name of the shortcut
	Label2 - The type of shortcut
	Icon - The shortcuts icon
	Thumbnail - The shortcuts thumbnail

3. Customize shortcut management dialog

script-skinsettings.xml

id		Description
101		Label which script will fill with the current type of shortcut being viewed
102		Button to change type of shortcut being viewed (down)
103		Button to change type of shortcut being viewed (up)
111		List of Video Playlist shortcuts
121		List of Music Playlist shortcuts
131		List of Favourite shortcuts
141		List of Add-on shortcuts
211		List of Shortcuts the user has chosen for the [groupname]
301		Button to add a new shortcut
302		Button to delete shortcut
303		Button to move shortcut up
304		Button to move shortcut down
