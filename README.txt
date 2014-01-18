script.skinshortcuts was written with the intention of making user customizable shortcuts on the home page easier for skins to handle.

Version Information
-------------------

This version of the script has many changes to the previous version. These are highlighted throughout the readme with

*VERSION INFORMATION*

	
Usage
-----

There are two ways to use this script. You can either (1) provide your own main menu items, and use the script to provide items for a sub-menu, or (2) use the script to provide both the main menu and sub-menu


Using the script to provide sub-menus
-------------------------------------

1. Recommended [groupname]'s
 
The script uses group=[groupname] property in order to determine which set of shortcuts to show. In order to share users customized shortcuts across different skins using this script, there are a few recommended [groupname]'s to use for your sub-menus
	videos
	movies
	tvshows
	livetv
	music
	musicvideos
	pictures
	weather
	programs
	dvd
	settings

	
2. Let users manage their shortcuts
 
In your overrides.xml file, you need to create a button for each [groupname] that you want to support, with the following in the <onclick> tag
 
	RunScript(script.skinshortcuts?type=manage&amp;group=[groupname])
 
 
3. Display user shortcuts
 
Uses new method of filling the contents of a list in Gotham. In the list where you want the submenu to appear, put the following in the <content> tag:
 
	plugin://script.skinshortcuts?type=list&amp;group=[groupname]
   
This will fill the list with items with the following properties:

	Label		Label of the item (localized where possible)
	Label2		Type of shortcut
	Icon		Icon image
	Thumbnail	Thumbnail image
	Property(labelID)	Unlocalized string primarily used when displaying both main menu and sub-menus
	Property(action)	The action that will be run when the shortcut is selected
	Property(group)		The [groupname] that this shortcut is listed from


Using the script to provide both main menu and sub-menus
--------------------------------------------------------

1. Information
 
This is a work in progress - it may not fully work as you expect and may require some creative skinning to get it looking right!
 
 
2. Let users manage their main menu and sub-menu shortcuts
 
The script can provide a list of controls for your overrides.xml to let the user manage both main menu and sub-menu.
  
Uses new method of filling the contents of a list in Gotham. In the list where you want these controls to appear, put the following in the <content> tag:
  
	plugin://script.skinshortcuts?type=settings&amp;property=$INFO[Window(10000).Property("skinshortcuts")]
 
 
3. Display main menu and shortcuts
 
This details the simplest method of displaying main menu and sub-menus, using two lists. When the user focuses on an item in the main menu list, the sub-menu list will update with the shortcuts for that item.
  
In the list where you want the main menu to appear, put the following in the <content> tag:
 
	plugin://script.skinshortcuts?type=list&amp;group=mainmenu
   
This will fill the list with items with the following properties:

	Label		Label of the item (localized where possible)
	Label2		Type of shortcut
	Icon		Icon image
	Thumbnail	Thumbnail image
	Property(labelID)	Unlocalized string used for sub-menu and for displaying more controls depending on the main menu item
	Property(action)	The action that will be run when the shortcut is selected
	Property(group)		The [groupname] that this shortcut is listed from
	Property(widget)	If your skin uses Skin Shortcuts to manage widgets, the [widgetID] will appear here (mainmenu only)
	Property(background)If your skin uses Skin Shortcuts to manage background, the [backgroundID] will appear here (mainmenu only)

In the list where you want the sub-menu to appear, put the following in the <content> tag:
 
	plugin://script.skinshortcuts?type=submenu&amp;mainmenuID=9000
   
Remember to replace 9000 with the id of the list you are using for the main menu.

*VERSION INFORMATION* - The method type=submenu is new in version 0.1.1, which is not currently on the repo. It also allows you to have multiple sub-menus should you wish. See section on "Multiple sub menus" for more information. For older versions, continue to use:

	plugin://script.skinshortcuts?type=list&amp;group=$INFO[Container(9000).ListItem.Property("labelID")]
	
 
4. Display more controls depending on the mainmenu item
 
If you want to display more controls onscreen when the user focuses on a main menu item (for instance, to display a list of recently added movies when a "Movies" main menu item is focused) you can set the visibility of your additional controls using listitem.property(labelID). For common main menu items, it will contain one of the following strings:
	videos
	movies
	tvshows
	livetv
	music
	musicvideos
	pictures
	weather
	programs
	dvd
	settings
  
So, for example, you could set visibility for your list of recently added movies like so
  
	<visible>StringCompare(Container(50).ListItem.Property(labelID), movies)</visible>
   
For more information on what labelID may contain, see section on localization. A full list of labelID's can be found in the Resources folder.

*VERSION INFORMATION* - Version 0.1.1, which is not currently on the repo, provides an alternative way to provide a list of widgets, and let the user select which one should be used for each menu item. See section on "Widgets" for more information.


5. Providing alternative access to settings

One of the side effects of using skinshortcuts to provide the whole main menu is that users have the ability to delete any shortcut, including those that they will later turn out to actually want. Generally, this isn't a problem as they can add them back at any time. However if they delete all links to settings, they will have no way to add it back unless your skin offers an alternative access.

Therefore, it is recommended to have an alternative link to settings. One possible location is in your shutdown menu.


Skinning the management dialog
------------------------------

To customize the look of the dialog displayed to allow the user to customize shortcuts, your skin needs to provide script-overrides.xml. It requires the following controls:

ID	Type	Description
101	Label	Current type of shortcut being viewed
102	Button	Change type of shortcut being viewed (down)
103	Button	Change type of shortcut being viewed (up)
111	List	Available shortcuts for the current type being viewed
211	List	Shortcuts the user has chosen for the [groupname]
301	Button	Add a new shortcut
302	Button	Delete shortcut
303	Button	Move shortcut up
304	Button	Move shortcut down
305	Button	Change shortcut label
306	Button	Change shortcut thumbnail
307	Button	Change shortcut action
308	Button	Reset shortcuts


Multiple Sub Menus
------------------

*VERSION INFORMATION* - This section only applies to version 0.1.1, which is not currently on the repo.

When using Skin Shortcuts to provide the whole main menu system, you may wish to provide more than one sub menu. For example, you could ape Confluence's favourites - which are displayed below the main and sub-menu's - with an additional sub menu.

In the list where you want an additional sub-menu to appear, put the following in the <content> tag:
 
	plugin://script.skinshortcuts?type=submenu&amp;level=1&amp;mainmenuID=9000
   
Remember to replace 9000 with the id of the list you are using for the main menu. To provide more sub-menus for a main menu item, increase the value of the 'level' parameter.

The script can provide a list of controls for your overrides.xml to let the user manage the additional sub-menu items.
  
In the list where you want these controls to appear, put the following in the <content> tag:
  
	plugin://script.skinshortcuts?type=settings&amp;level=1&amp;property=$INFO[Window(10000).Property("skinshortcuts")]
	
You MUST provide a string for the settings list. See 'overrides.xml' (section 4) for details.
	
	
Widgets
-------

*VERSION INFORMATION* - This section only applies to version 0.1.1, which is not currently on the repo.

When using Skin Shortcuts to provide the whole main menu, you may wish to provide a series of widgets - such as PVR information, weather conditions, recently added movies, and so forth - that the user can choose from for each main menu item.

Skin Shortcuts can provide a list of controls for your overrides.xml to let the user choose a widget for their main menu items.

In the list where you want these controls to appear, put the following in the <content> tag:
  
	plugin://script.skinshortcuts?type=widgets&amp;property=$INFO[Window(10000).Property("skinshortcuts")]
	
Then use the following in the visibility condition for each widget:

	<visible>StringCompare(Container(9000).ListItem.Property(Widget),[WidgetID])</visible>
	
You can define your widgets - along with their WidgetID, and default labelID's they should appear against - in an overrides.xml file. See "overrides.xml" sections 3 and 4 for more details.

Widgets are saved on a skin-by-skin basis.


Additional Settings Menus
-------------------------

*VERSION INFORMATION* - This section only applies to version 0.1.1, which is not currently on the repo.

When using Skin Shortcuts to provide the whole main menu, you have the option of providing one or more custom lists for your skin settings file. These lists could, for example, be used to launch your skins method for choosing a backgound image or setting a description.

Skin Shortcuts will provide a list of controls for your overrides.xml, with one control for each main menu item.

In the list where you want these controls to appear, put the following in the <content> tag:

	plugin://script.skinshortcuts?type=customsettings&amp;customID=[Custom ID]&amp;property=$INFO[Window(10000).Property("skinshortcuts")]
	
You can set the [Custom ID], along with the action(s) to be performed when the user selects the control and the control label in an overrides.xml file. See "overrides.xml" section 5 for more details.


Custom Backgrounds
------------------

*VERSION INFORMATION* - This section only applies to version 0.1.1, which is not currently on the repo.

Many skin allow users to select custom backgrounds for various areas of the skin. If using Skin Shortcuts to provide the whole main menu, there are a few ways to extend these to the main menu items the user has selected, for example you could use the labelID or a custom settings menu.

However, the recommended method is as follows:

Continue to provide a method of setting the background for each area where you want the user to be able to specify a custom background.

Tell Skin Shortcuts about each of these areas, including a custom ID for each one and the defaults for labelID's, in the overrides.xml file. (See "overrides.xml", section 6)

Use Skin Shortcuts to provide a list of controls in your skinsettings.xml file for the user to choose which areas background they want to associate with each menu item. In the list where you want these controls to appear, include the following in the content tag:

	plugin://script.skinshortcuts?type=background&amp;property=$INFO[Window(10000).Property("skinshortcuts")]

When populating main menu items, Skin Shortcuts will then add a 'background' property to each item, containing the custom ID of the background chosen, which you can test against for visibility.

Custom backgrounds are saved on a skin-by-skin basis.


Providing default shortcuts
---------------------------

If the user has not already selected any shortcuts or if the user resets shortcuts, the script will first attempt to load defaults from a file provided by the skin before trying to load its own.

To provide this optional file, create a new sub-directory in your skin called 'shortcuts', and drop the relevant [groupname].shortcuts file into it.

The easiest way to create this file is to use the script to build a list of shortcuts, then copy it from your userdata folder. See recommended groupname's for ideas of some of the default files you may wish to provide, along with mainmenu.shortcuts if you are using the script to manage the main menu.

The script provides defaults equivalent to Confluence's main menu and sub-menus.

*VERSION INFORMATION* The following applies to 0.1.1 only, which is not currently in the repo. To provide defaults for additional sub-menus, the filename will be [groupname].[level].shortcuts


overrides.xml
----------------

Your skin can include an optional file called 'overrides.xml' in a sub-directory of your skin called 'shortcuts'. This file allows you to provide various defaults for Skin Shortcuts, as well as overriding various things including actions and icons, allowing you to create a customised experience for your skin.


1. Overriding an action

You may wish to override an action in order to provide additional functionality. For example, you could override the default action for Movies (to go to the Movie Title view) to run Cinema Experience instead.

	<override action="[command]">
		<condition>[Boolean condition]</condition>
		<action>[XBMC function]</action>
	<override>
	
[command] - Replace with the action you are overriding
[Boolean condition] - [Optional] Replace with a string that must evaluate to True for the custom action to be run
[XBMC function] - Replace with the action that should be run instead. You may include multiple <action> tags.

A complete example would look like:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<override action="ActivateWindow(Videos,MovieTitles,return)">
		<condition>Skin.HasSetting(CinemaExperience) + System.HasAddon(script.cinema.experience)</condition>
		<action>RunScript(script.cinema.experience,movietitles)</action>
	</override>
</overrides>

Users can also provide an overrides.xml file to override actions in special://profile/ - overrides in this file will take precedent over overrides provided by the skin.


2. Overriding thumbnails

The script tries to provide reasonable default images for all shortcuts, with a fallback on "DefaultShortcut.png", however you may wish to override images to specific ones provided by your skin.

This can be done by providing an optional file called 'overrides.xml' in a sub-directory of your skin called 'shortcuts'. It provides two ways to override images - either overriding the image for a specific labelID, or overriding all instances of a particular image - as follows:

	<thumbnail labelID="[labelID]">[New image]</thumbnail>
	<thumbnail image="[Old image]">[New image]</thumbnail>

[labelID] - The labelID whose thumbnail you want to override
[Old image] - The image you are overriding
[New image] - The replacement image

A complete example would look like:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<thumbnail labelID="movies">MyMovieImage.png</thumbnail>
	<thumbnail image="DefaultShortcut.png">MyShortcutImage.png</thumbnail>
</overrides>

Note, any thumbnail image the user has set will take precedence over skin-provided overrides.

A full list of labelID's and default thumbnail images can be found in the Resources folder.

*VERSION INFORMATION* - I'm testing using video nodes in version 0.1.1 - with nodes, the default thumbnail may not be the same as in the list in the resources folder for video library shortcuts.


3. Widgets

*VERSION INFORMATION* - This only applies to version 0.1.1, which is not currently in the repo.

If you want to use Skin Shortcuts to manage widgets that your skin provides (such as PVR information, current weather conditions, recently added movies) for main menu items, you need to tell the script about your widgets as follows:

	<widget label="[label]">[WidgetID]</widget>
	
[label] - The display name of the widget, to be shown when choosing widgets (can be a localised string)
[widgetID] - A string you use to identify this widget

So, for example:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<widget label="PVR Status">PVR</widget>
	<widget label="30222">RecentMovies</widget>
</overrides>

You can also specify the default widget for a given labelID:

	<widgetdefault labelID="[labelID]">[widgetID]</widgetdefault>
	
[labelID] - The labelID you are setting the default for
[widgetID] - The string you have used to identify the target widget

So, for example:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<widgetdefault labelID="movies">RecentMovies</widgetdefault>
	<widgetdefault labelID="livetv">PVR</widgetdefault>
</overrides>

A full list of labelID's and default thumbnail images can be found in the Resources folder.

You can then use the following in the visibility for your widgets:

	<visible>StringCompare(Container(9000).ListItem.Property("widget"),[widgetID])</visible>
	
Remember to replace 9000 with the ID of the list containing your main menu.


4. Overriding settings labels

When using Skin Shortcuts to provide the whole main menu, it will provide a list of controls for your overrides.xml to launch the management dialog. You can override the default labels for these controls.

If you are using more than one sub-menu, you MUST provide the label otherwise they will be left blank.

	<settingslabel type="[type]" level="[level]">[string]</settingslabel>
	
[type] - Either "main" (Main Menu), "submenu" (sub menu item), "widget" (Widgets menu), "background" (Background menu) or "reset" (Reset all shortcuts)
[level] - [OPTIONAL] Use this to indicate an additional sub-menu. See 'Multiple Sub-Menu's' for details. (Only works with type="submenu")
[string] - The label that should be displayed. Can be a localised string. Include ::MENUNAME:: where you want the name of the menu to appear (does not apply to 'Main' or 'Reset').

So, for example:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<settingslabel type="main">Choose what to display on the main menu</settingslabel>
	<settingslabel type="submenu">Pick submenu items for ::MENUNAME::</settingslabel>
	<settingslabel type="submenu" level="1">30015</settingslabel>
	<settingslabel type="widget">Choose widgets for menu item ::MENUNAME::</settingslabel>
	<settingslabel type="reset">Reset all shortcuts back to default</settingslabel>
</overrides>


5. Additional Settings Menus

If you are using Skin Shortcuts to provide additional settings menu, you must define these menus in your overrides.xml file.

	<settingsmenu id=[Custom ID]>
		<label>[label]</label>
		<action>[action]</action>
		<onchange>[skinstring]</onchange>
	</settingsmenu>
	
[Custom ID] - A string you use to identify this custom menu
[label] - The label that should be displayed. Can be a localised string. Include ::MENUNAME:: where you want the name of the menu to appear.
[action] - The action that should be run when the user selects the menu item. You can use ::LABELID:: if you want to use the labelID of the selected menu item in the action.
[skinstring] - [OPTIONAL] [FOR FUTURE USE] The skin.string that is set by your custom action. Include ::LABELID:: where the labelID of the menu item should appear. Will be used in future to update the string if the labelID changes.

Though [skinstring] is optional, if your custom menu sets a skin property it's recommended you include it as in future builds, this will be used to update the property if the labelID of the menu item changes.

So, if we wanted to browse for an image to use as the background image for the selected menu item, which will be stored in skin.string("background-::LABELID::"), your overrides.xml may look like this:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<settingsmenu id="background">
		<label>Set background image for ::MENUNAME::</label>
		<action>Skin.SetImage(Background_::LABELID::)</action>
		<onchange>Background_::LABELID::</onchange>
	</settingsmenu>
</overrides>


6. Custom background images

If you are using Skin Shortcuts to set background images for main menu items, you need to tell the script what backgrounds you have defined and provide default backgrounds.

	<background label="[Label]">[backgroundID]</background>
	<backgrounddefault labelID="[LabelID]">[backgroundID]</backgroundDefault>
	
[Label] - The display name of the background (can be a localised string)
[backgroundID] - A string you use to identify the background
[labelID] - The labelID you are providing a default for.


7. A complete example

A complete overrides.xml file may look as follows:

<?xml version="1.0" encoding="UTF-8"?>
<overrides>
	<!-- Override an action -->
	<override action="ActivateWindow(Videos,MovieTitles,return)">
		<condition>Skin.HasSetting(CinemaExperience) + System.HasAddon(script.cinema.experience)</condition>
		<action>RunScript(script.cinema.experience,movietitles)</action>
	</override>
	
	<!-- Override a thumbnail, first for a particular labelID and then all instances of a particular thumbnail -->
	<thumbnail image="[Old image]>[New image]</thumbnail>
	<thumbnail image="DefaultShortcut.png">My Shortcut Image.png</thumbnail>
	
	<!-- Create a widget the user can choose from -->
	<widget label="PVR" label2="Recording status of your PVR">PVR</widget>
	<widget label="30222" label2="30555">RecentMovies</widget>
	
	<!-- Set the default widget for the labelID movies -->
	<widgetdefault labelID="movies">RecentMovies</widgetdefault>
	<widgetdefault labelID="livetv">PVR</widgetdefault>
	
	<!-- Set labels for skinsettings lists -->
	<settingslabel type="main">Choose what to display on the main menu</settingslabel>
	<settingslabel type="submenu">Pick submenu items for ::MENUNAME::</settingslabel>
	<settingslabel type="submenu" level="1">30015</settingslabel>
	<settingslabel type="reset">Reset all shortcuts back to default</settingslabel>
</overrides>


Localization
------------

If you are providing default shortcuts and want to localize your label, you can do it using the format

  ::LOCAL::[id]
  
Where [id] is any string id provided by XBMC or your skin. However, you should generally avoid using strings provided by your skin as they won't carry over if the user switches to a different skin.

In order to make things easier for skinners using this script to provide the main menu, listitems returned by the script have the property labelID. This is a non-localized string that can be tested against (for visibility, for example).

For common main menu items, it will contain one of the following strings
	videos
	movies
	tvshows
	livetv
	music
	musicvideos
	pictures
	weather
	programs
	dvd
	settings
	
For other localized strings, it will contain the id of the string. For non-localized strings, it will contain the string in lowercase and without any spaces.

A full list of labelID's can be found in the Resources folder.


With Thanks
-----------

Huge thanks to Ronie, whose code for listing plugins is used in this script
Equally huge thanks to Ronie and `Black, for their favourites code used in this script
More huge thanks to BigNoid, for the ability to edit shortcuts
