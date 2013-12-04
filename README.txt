INFO FOR SKINNERS - How to use this addon in your skin:

1. Let users manage their shortcuts (e.g. from skinsettings.xml)

RunScript(script.skinshortcuts?type=manage&amp;group=[groupname])

This will display a dialog where the users can select and manage shortcuts for the given group name.

2. Display user shortcuts

Uses new method of filling the contents of a list in Gotham

<content>plugin://script.skinshortcuts?amp;type=list&amp;group=[groupname]</content>

This will return items with the following information
	Label - The name of the shortcut
	Label2 - The type of shortcut
	Icon - The shortcuts icon
	Thumbnail - The shortcuts thumbnail
	
3. Defaults

If the user hasn't already created custom shortcuts for the given [groupname], skinshortcuts will attempt to load defaults for the group from the skin, allowings skinners to provide default selections. To provide this optional file, create a new sub-directory in your skin called 'shortcuts', and drop the relevant [groupname].db file into it.

The easiest way to create the [groupname].db file is to use skinshortcuts to create the file, then copy it from your userdata folder.

If the skin default file isn't found, skinshortcuts will create defaults (the same defaults as Confluence has) for the following [groupname]'s:
	videos
	movies
	tvshows
	livetv
	music
	pictures

4. Customize shortcut management dialog

script-skinshortcuts.xml

id		Description
101		Label which script will fill with the current type of shortcut being viewed
102		Button to change type of shortcut being viewed (down)
103		Button to change type of shortcut being viewed (up)
111		List of available shortcuts for the current type being viewed
211		List of Shortcuts the user has chosen for the [groupname]
301		Button to add a new shortcut
302		Button to delete shortcut
303		Button to move shortcut up
304		Button to move shortcut down
