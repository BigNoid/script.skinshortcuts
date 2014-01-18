import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib, xbmcvfs
import xml.etree.ElementTree as xmltree
from time import gmtime, strftime
from datetime import datetime
from traceback import print_exc

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__     = __addon__.getLocalizedString
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__addonname__    = __addon__.getAddonInfo('name').decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
__profilepath__  = xbmc.translatePath( "special://profile/" ).decode('utf-8')
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')
__defaultpath__  = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'shortcuts').encode("utf-8") ).decode("utf-8")

sys.path.append(__resource__)

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
        
class Main:
    # MAIN ENTRY POINT
    def __init__(self):
        self._parse_argv()
        self.WINDOW = xbmcgui.Window(10000)
        
        # Check if the user has changed skin
        if self.WINDOW.getProperty("skinsettings-currentSkin-Path"):
            if self.WINDOW.getProperty("skinsettings-currentSkin-Path") != xbmc.getSkinDir():
                self.reset_window_properties()
                self.WINDOW.setProperty("skinsettings-currentSkin-Path", xbmc.getSkinDir() )
        else:
            self.WINDOW.setProperty("skinsettings-currentSkin-Path", xbmc.getSkinDir() )
                
        
        # Create datapath if not exists
        if not xbmcvfs.exists(__datapath__):
            xbmcvfs.mkdir(__datapath__)
        
        # Perform action specified by user
        if not self.TYPE:
            line1 = "This addon is for skin developers, and requires skin support"
            xbmcgui.Dialog().ok(__addonname__, line1)
            
        if self.TYPE=="launch":
            self._launch_shortcut( self.PATH )
        if self.TYPE=="manage":
            self._manage_shortcuts( self.GROUP )
        if self.TYPE=="list":
            self._list_shortcuts( self.GROUP )
        if self.TYPE=="submenu":
            self._list_submenu( self.MENUID, self.LEVEL )
        if self.TYPE=="settings":
            self._manage_shortcut_links() 
        if self.TYPE=="customsettings":
            self._manage_custom_links()
        if self.TYPE=="widgets":
            self._manage_widgets()
        if self.TYPE=="setWidget":
            self._set_widget()
        if self.TYPE=="backgrounds":
            self._manage_backgrounds()
        if self.TYPE=="setBackgrounds":
            self._set_background()
        if self.TYPE=="resetall":
            self._reset_all_shortcuts()

    def _parse_argv( self ):
        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
            self.TYPE = params.get( "type", "" )
        except:
            print_exc()
            try:
                params = dict( arg.split( "=" ) for arg in sys.argv[ 2 ].split( "&" ) )
                self.TYPE = params.get( "?type", "" )
            except:
                params = {}
        
        self.GROUP = params.get( "group", "" )
        self.PATH = params.get( "path", "" )
        self.MENUID = params.get( "mainmenuID", "0" )
        self.LEVEL = params.get( "level", "" )
        self.CUSTOMID = params.get( "customid", "" )
    
    
    # -----------------
    # PRIMARY FUNCTIONS
    # -----------------

    def _launch_shortcut( self, path ):
        log( "### Launching shortcut" )
        
        runDefaultCommand = True
        paths = [os.path.join( __profilepath__ , "overrides.xml" ),os.path.join( __skinpath__ , "overrides.xml" )]
        action = urllib.unquote( self.PATH )
        for path in paths:
            if xbmcvfs.exists( path ) and runDefaultCommand:    
                trees = [self._load_overrides_skin(), self._load_overrides_user()]
                log( trees )
                for tree in trees:
                    if tree is not None:
                        tree = xmltree.parse( path )
                        # Search for any overrides
                        elems = tree.findall( 'override' )
                        for elem in elems:
                            if elem.attrib.get( 'action' ) == action:
                                runCustomCommand = True
                                
                                # Check any conditions
                                conditions = elem.findall('condition')
                                for condition in conditions:
                                    if xbmc.getCondVisibility( condition.text ) == False:
                                        runCustomCommand = False
                                        break
                                
                                # If any and all conditions have been met, run actions
                                if runCustomCommand == True:
                                    actions = elem.findall( 'action' )
                                    for action in actions:
                                        log( "Override action: " + action.text )
                                        runDefaultCommand = False
                                        xbmc.executebuiltin( action.text )
                                    break
        
        # If we haven't overridden the command, run the original
        if runDefaultCommand == True:
            xbmc.executebuiltin( urllib.unquote(self.PATH) )
            
        # Tell XBMC not to try playing any media
        xbmcplugin.setResolvedUrl( handle=int( sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem() )
        
    
    def _manage_shortcuts( self, group ):
        import gui
        ui= gui.GUI( "script-skinshortcuts.xml", __cwd__, "default", group=group )
        ui.doModal()
        del ui
        # Update home window property (used to automatically refresh type=settings)
        xbmcgui.Window( 10000 ).setProperty( "skinshortcuts",strftime( "%Y%m%d%H%M%S",gmtime() ) )
        
        # Clear window properties for this group
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-" + group )
        

    def _list_shortcuts( self, group ):
        log( "### Listing shortcuts ..." )
        if group == "":
            log( "### - NO GROUP PASSED")
            # Return an empty list
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            return None
            
        # Load shortcuts and overrides
        listitems = self._get_shortcuts( group )
        
        for item in listitems:
            # Generate a listitem
            path = sys.argv[0] + "?type=launch&path=" + item[4] + "&group=" + self.GROUP
            
            listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
            
            listitem.setProperty( 'IsPlayable', 'True')
            listitem.setProperty( "labelID", item[5] )
            listitem.setProperty( "action", urllib.unquote( item[4] ) )
            listitem.setProperty( "group", group )
            listitem.setProperty( "path", path )
            
            # Localize label2 (type of shortcut)
            if not listitem.getLabel2().find( "::SCRIPT::" ) == -1:
                listitem.setLabel2( __language__( int( listitem.getLabel2()[10:] ) ) )
                            
            # Add item
            if group == "mainmenu":
                visibilityCheck = self.checkVisibility( listitem.getProperty( 'labelID' ) )
                if visibilityCheck != "":
                    listitem.setProperty( "node.visible", visibilityCheck )
                widgetCheck = self.checkWidget( listitem.getProperty( 'labelID' ) )
                if widgetCheck != "":
                    listitem.setProperty( "widget", widgetCheck )
                backgroundCheck = self.checkBackground( listitem.getProperty( 'labelID' ) )
                if backgroundCheck != "":
                    listitem.setProperty( "background", backgroundCheck )
                    
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)
            
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
        
                
    def _list_submenu( self, mainmenuID, levelInt ):
        log( "### Listing submenu ..." )
        if mainmenuID == "0":
            log( "### - NO MAIN MENU ID PASSED")
            # Return an empty list
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            return None
            
        # Load shortcuts for the main menu
        mainmenuListItems = self._get_shortcuts( "mainmenu" )
        
        for mainmenuItem in mainmenuListItems:
            # Load menu for each labelID
            mainmenuLabelID = mainmenuItem[5]
            # log( "unencoded: " + mainmenuLabelID )
            # mainmenuLabelID = mainmenuLabelID.encode('ascii', 'xmlcharrefreplace' )
            # log( "encoded: " + mainmenuLabelID )
            if levelInt == "":
                listitems = self._get_shortcuts( mainmenuLabelID )
            else:
                listitems = self._get_shortcuts( mainmenuLabelID + "." + levelInt )
            for item in listitems:
                path = sys.argv[0] + "?type=launch&path=" + item[4] + "&group=" + mainmenuLabelID
                
                listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                
                listitem.setProperty('IsPlayable', 'True')
                listitem.setProperty( "labelID", item[5] )
                listitem.setProperty( "action", urllib.unquote( item[4] ) )
                listitem.setProperty( "group", mainmenuLabelID )
                listitem.setProperty( "path", path )
                
                listitem.setProperty( "node.visible", "StringCompare(Container(" + mainmenuID + ").ListItem.Property(labelID)," + mainmenuLabelID + ")" )
                
                # Localize label2 (type of shortcut)
                if not listitem.getLabel2().find( "::SCRIPT::" ) == -1:
                    listitem.setLabel2( __language__( int( listitem.getLabel2()[10:] ) ) )
                                
                # Add item
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)
            
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    

    def _reset_all_shortcuts( self ):
        log( "### Resetting all shortcuts" )
        dialog = xbmcgui.Dialog()
        
        # Ask the user if they're sure they want to do this
        if dialog.yesno(__language__(32037), __language__(32038)):
            # List all shortcuts
            files = xbmcvfs.listdir( __datapath__ )
            for file in files:
                try:
                    # Try deleting all shortcuts
                    if file:
                        file_path = os.path.join( __datapath__, file[0])
                        if xbmcvfs.exists( file_path ):
                            xbmcvfs.delete( file_path )
                except:
                    print_exc()
                    log( "### ERROR could not delete file %s" % file_path )
        
            # Update home window property (used to automatically refresh type=settings)
            xbmcgui.Window( 10000 ).setProperty( "skinshortcuts",strftime( "%Y%m%d%H%M%S",gmtime() ) )   
            
            # Reset all window properties (so menus will be reloaded)
            self.reset_window_properties()
                
        # Tell XBMC not to try playing any media
        xbmcplugin.setResolvedUrl( handle=int( sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem() )
    
    
    # ---------
    # LOAD DATA
    # ---------
    
    def _get_shortcuts( self, group ):
        # This will load the shortcut file, and save it as a window property
        # Additionally, if the override files haven't been loaded, we'll load them too
        
        # If we've not loaded this shortcut group...
        log( "We're working with " + group )
        if not xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-" + group ):
            log( "### LOADING SHORTCUTS FROM FILE ###" )
            
            # Set path based on existance of user defined shortcuts, then skin-provided, then script-provided
            if xbmcvfs.exists( os.path.join( __datapath__ , group + ".shortcuts" ) ):
                # User defined shortcuts
                path = os.path.join( __datapath__ , group + ".shortcuts" )
            elif xbmcvfs.exists( os.path.join( __skinpath__ , group + ".shortcuts" ) ):
                # Skin-provided defaults
                path = os.path.join( __skinpath__ , group + ".shortcuts" )
            elif xbmcvfs.exists( os.path.join( __defaultpath__ , group + ".shortcuts" ) ):
                # Script-provided defaults
                path = os.path.join( __defaultpath__ , group + ".shortcuts" )
            else:
                # No custom shortcuts or defaults available
                path = ""
                
            # If no path was found ... (this means there are no shortcuts for this group)
            if path == "":
                log( "### - NO SHORTCUTS FOUND" )
                # Save an empty array to the global property
                xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-" + group, simplejson.dumps( [] ) )
            else:
                log( "### FILE CONTAINING SHORTCUTS FOUND ###" )
                # We've found a file containing shortcuts
                try:
                    # Try loading shortcuts
                    log ("### LOADING SHORTCUTS FILE ###" )
                    file = xbmcvfs.File( path )
                    log( "### PROCESSING SHORTCUTS FILE ###" )
                    unprocessedList = eval( file.read() )
                    file.close
                    processedList = self._process_shortcuts( unprocessedList, group )
                    log ( processedList )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-" + group, simplejson.dumps( processedList ) )
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-" + group, simplejson.dumps( [] ) )
                    
        else:
            log( "### SHORTCUTS ALREADY LOADED ###" )

        # Return this shortcut group
        return simplejson.loads( xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-" + group ) )
    
    
    def _load_overrides_skin( self ):
        # If we haven't already loaded skin overrides, or if the skin has changed, load the overrides file
        if not xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-overrides-skin" ) or not xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-overrides-skin" ) == __skinpath__:
            xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-skin", __skinpath__ )
            overridepath = os.path.join( __skinpath__ , "overrides.xml" )
            if xbmcvfs.exists(overridepath):
                try:
                    file = xbmcvfs.File( overridepath )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-skin-data", simplejson.dumps( file.read().encode( 'utf-8' ) ) )
                    file.close
                except:
                    print_exc()
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-skin-data", "No overrides" )
            else:
                xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-skin-data", "No overrides" )
        else:
            log( "### SKIN OVERRIDES ALREADY LOADED ###" )
                
        # Return the overrides
        returnData = xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-overrides-skin-data" )
        if returnData == "No overrides":
            return None
        else:
            return xmltree.fromstring( simplejson.loads( returnData ) )
            
            
    def _process_shortcuts( self, listitems, group ):
        # This function will process any graphics overrides provided by the skin, and return a set of listitems ready to be stored
        tree = self._load_overrides_skin()
        returnitems = []
        
        for item in listitems:
            # Generate the labelID
            label = item[0]
            labelID = item[0].replace(" ", "").lower()
            
            # Localize label & labelID
            if not label.find( "::SCRIPT::" ) == -1:
                labelID = self.createNiceName( label[10:] )
                label = __language__(int( label[10:] ) )
            elif not label.find( "::LOCAL::" ) == -1:
                labelID = self.createNiceName( label[9:] )
                label = xbmc.getLocalizedString(int( label[9:] ) )
            
            # If the user hasn't overridden the thumbnail, check for skin override
            if not len(item) == 6 or (len(item) == 6 and item[5] == "True"):
                if tree is not None:
                    elems = tree.findall('thumbnail')
                    for elem in elems:
                        if elem is not None and elem.attrib.get( 'labelID' ) == labelID:
                            item[3] = elem.text
                        if elem is not None and elem.attrib.get( 'image' ) == item[3]:
                            item[3] = elem.text
                        if elem is not None and elem.attrib.get( 'image' ) == item[2]:
                            item[2] = elem.text
            
            # Add item
            returnitems.append( [label, item[1], item[2], item[3], item[4], labelID] )
            #returnitems.append( item )
                
        return returnitems            
            
    
    def _load_overrides_user( self ):
        # If we haven't already loaded user overrides
        if not xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-overrides-user" ):
            log( "### LOADING USER OVERRIDES FROM FILE ###" )
            xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-user", __profilepath__ )
            overridepath = os.path.join( __profilepath__ , "overrides.xml" )
            if xbmcvfs.exists(overridepath):
                try:
                    file = xbmcvfs.File( overridepath )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-user-data", simplejson.dumps( file.read().encode( 'utf-8' ) ) )
                    file.close
                except:
                    print_exc()
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-user-data", "No overrides" )
            else:
                xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-overrides-user-data", "No overrides" )
        else:
            log( "### USER OVERRIDES ALREADY LOADED ###" )
                
        # Return the overrides
        returnData = xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-overrides-user-data" )
        if returnData == "No overrides":
            return None
        else:
            return xmltree.fromstring( simplejson.loads( returnData ) )
    
    
    # ----------------
    # SKINSETTINGS.XML
    # ----------------
    
    def _manage_shortcut_links ( self ):
        log( "### Generating list for skin settings" )
        pathAddition = ""
        
        # Create link to manage main menu
        if self.LEVEL == "":
            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=mainmenu)" )
            displayLabel = self._get_customised_settings_string("main")
            listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="DefaultShortcut.png", thumbnailImage="DefaultShortcut.png")
            listitem.setProperty('isPlayable', 'False')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
        else:
            pathAddition = "." + self.LEVEL
        
        # Set path based on user defined mainmenu, then skin-provided, then script-provided
        if xbmcvfs.exists( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
            # User defined shortcuts
            path = os.path.join( __datapath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
            # Skin-provided defaults
            path = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
            # Script-provided defaults
            path = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
        else:
            # No custom shortcuts or defaults available
            path = ""
            
        if not path == "":
            try:
                # Try loading shortcuts
                file = xbmcvfs.File( path )
                loaditems = eval( file.read() )
                file.close()
                
                listitems = []
                
                for item in loaditems:
                    log( "### Original item: " + item[0] )
                    itemEncoded = repr( item[0] )
                    log( itemEncoded )
                    log( eval( itemEncoded ).encode( 'utf-8' ) )
                    # path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + itemEncoded.replace(" ", "").lower() + pathAddition + ")" )
                    path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + itemEncoded + pathAddition + ")" )
                    
                    # Get localised label
                    if not item[0].find( "::SCRIPT::" ) == -1:
                        localLabel = __language__(int( item[0][10:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][10:] ).encode("ascii", "xmlcharrefreplace") + pathAddition + ")" )
                    elif not item[0].find( "::LOCAL::" ) == -1:
                        localLabel = xbmc.getLocalizedString(int( item[0][9:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][9:] ).encode("ascii", "xmlcharrefreplace") + pathAddition + ")" )
                    else:
                        localLabel = item[0]
                        
                    log( path )
                        
                    # Get display label
                    displayLabel = self._get_customised_settings_string("submenu").replace("::MENUNAME::", localLabel)
                    
                    #listitem = xbmcgui.ListItem(label=__language__(32036) + item[0], label2="", iconImage="", thumbnailImage="")
                    listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="", thumbnailImage="")
                    listitem.setProperty('isPlayable', 'True')
                    
                    # Localize strings
                    #if not item[0].find( "::SCRIPT::" ) == -1:
                    #    path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][10:] ) + pathAddition + ")" )
                    #    listitem.setLabel( __language__(32036) + __language__(int( item[0][10:] ) ) )
                    #elif not item[0].find( "::LOCAL::" ) == -1:
                    #    path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][9:] ) + pathAddition + ")" )
                    #    listitem.setLabel( __language__(32036) + xbmc.getLocalizedString(int( item[0][9:] ) ) )
                        
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)

            except:
                print_exc()
                log( "### ERROR could not load file %s" % path )
        
        # Add a link to reset all shortcuts
        if self.LEVEL == "":
            path = sys.argv[0] + "?type=resetall"
            displayLabel = self._get_customised_settings_string("reset")
            listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="DefaultShortcut.png", thumbnailImage="DefaultShortcut.png")
            listitem.setProperty('isPlayable', 'True')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)
        
        # Save the list
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

    
    def _manage_custom_links ( self ):
        log( "### Generating custom list for skin settings" )
        # Set path based on user defined mainmenu, then skin-provided, then script-provided
        if xbmcvfs.exists( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
            # User defined shortcuts
            path = os.path.join( __datapath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
            # Skin-provided defaults
            path = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
            # Script-provided defaults
            path = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
        else:
            # No custom shortcuts or defaults available
            path = ""
            
        if not path == "":
            try:
                # Try loading shortcuts
                file = xbmcvfs.File( path )
                loaditems = eval( file.read() )
                file.close()
                
                # Load skin overrides, and get the specified override
                tree = self._load_overrides_skin()
                settingsMenuElem = None
                
                log( "### Finding custom list in overrides.xml" )
                log( "### (looking for " + self.CUSTOMID + ")" )
                if tree is not None:
                    elems = tree.findall('settingsmenu')
                    for elem in elems:
                        log( elem.attrib.get( 'id' ) )
                        if elem.attrib.get( 'id' ) == self.CUSTOMID:
                            log( "### Found custom list" )
                            settingsMenuElem = elem
                            break

                
                listitems = []
                
                if settingsMenuElem is not None:
                    for item in loaditems:                        
                        # Get localised label and labelID
                        localLabel = item[0]
                        labelID = item[0].replace(" ", "").lower()
                        if not item[0].find( "::SCRIPT::" ) == -1:
                            localLabel = __language__(int( item[0][10:] ) )
                            labelID = self.createNiceName( item[0][10:] )
                            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setWidget&group=" + self.createNiceName( item[0][10:] ) + ")" )
                        elif not item[0].find( "::LOCAL::" ) == -1:
                            localLabel = xbmc.getLocalizedString(int( item[0][9:] ) )
                            labelID = self.createNiceName( item[0][9:] )
                            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setWidget&group=" + self.createNiceName( item[0][9:] ) + ")" )
                        
                        # Get custom action
                        customAction = settingsMenuElem.find('action').text.replace("::LABELID::", labelID)
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( customAction )

                        # Get display label
                        displayLabel = settingsMenuElem.find('label').text
                        if displayLabel.isdigit():
                            displayLabel = xbmc.getLocalisedString( displayLabel )
                        displayLabel = displayLabel.replace("::MENUNAME::", localLabel)
                        
                        #listitem = xbmcgui.ListItem(label=__language__(32036) + item[0], label2="", iconImage="", thumbnailImage="")
                        listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="", thumbnailImage="")
                        listitem.setProperty('isPlayable', 'True')
                                                
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)

            except:
                print_exc()
                log( "### ERROR could not load file %s" % path )
        
        # Save the list
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    
    def _get_customised_settings_string( self, group ):
        # This function will return the customised settings string for the given group
        tree = self._load_overrides_skin()
        if tree is not None:
            elems = tree.findall('settingslabel')
            for elem in elems:
                if elem is not None and elem.attrib.get( 'type' ) == group:
                    if self.LEVEL != "":
                        if elem.attrib.get( 'level' ) == self.LEVEL:
                            if elem.text.isdigit():
                                return xbmc.getLocalizedString( int( elem.text ) )
                            else:
                                return elem.text
                    else:
                        if 'level' not in elem.attrib:
                            if elem.text.isdigit():
                                return xbmc.getLocalizedString( int( elem.text ) )
                            else:
                                return elem.text
                                
        # If we get here, no string has been specified in overrides.xml
        if group == "main":
            return __language__(32035)
        elif group == "submenu" and self.LEVEL == "":
            return __language__(32036)
        elif group == "submenu" and self.LEVEL != "":
            return "::MENUNAME::"
        elif group == "reset":
            return __language__(32037)
        elif group == "widget":
            return __language__(32039)
        return "::MENUNAME::"
    
    
    # ----------------
    # WIDGET FUNCTIONS
    # ----------------
    
    def _set_widget( self ):
        # Load the widgets the skin has defined
        tree = self._load_overrides_skin()
        widgetLabel = ["None"]
        widget = [""]
        
        if tree is not None:
            elems = tree.findall('widget')
            for elem in elems:
                if elem.attrib.get( 'label' ).isdigit():
                    widgetLabel.append( xbmc.getLocalizedString( int( elem.attrib.get( 'label' ) ) ) )
                else:
                    widgetLabel.append( elem.attrib.get( 'label' ) )
                widget.append( elem.text )
        
        dialog = xbmcgui.Dialog()
        selectedWidget = dialog.select( "Choose a widget", widgetLabel )
        
        # Load the current widgets
        currentWidgets = ( self._get_widgets() )
        saveWidgets = []
        foundWidget = False
        
        # Loop through current widgets, looking for the current self.GROUP
        for currentWidget in currentWidgets:
            if currentWidget[0] == self.GROUP:
                saveWidgets.append( [ self.GROUP, widget[selectedWidget] ] )
                foundWidget = True
            else:
                saveWidgets.append( [ currentWidget[0], currentWidget[1] ] )
                
        # If we didn't find an existing widget for the group, add a new one
        if foundWidget == False:
            saveWidgets.append( [ self.GROUP, widget[selectedWidget] ] )
            
        # Clear the window property
        self.reset_window_properties()
        
        # Save the widgets
        path = os.path.join( __datapath__ , xbmc.getSkinDir() + ".widgets" )
        
        try:
            f = xbmcvfs.File( path, 'w' )
            f.write( repr( saveWidgets ) )
            f.close()
        except:
            print_exc()
            log( "### ERROR could not save file %s" % __datapath__ )
    
    
    def _manage_widgets ( self ):
        log( "### Generating widget list for skin settings" )
        
        # Set path based on user defined mainmenu, then skin-provided, then script-provided
        if xbmcvfs.exists( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
            # User defined shortcuts
            path = os.path.join( __datapath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
            # Skin-provided defaults
            path = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
            # Script-provided defaults
            path = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
        else:
            # No custom shortcuts or defaults available
            path = ""
            
        if not path == "":
            try:
                # Try loading shortcuts
                file = xbmcvfs.File( path )
                loaditems = eval( file.read() )
                file.close()
                
                listitems = []
                
                for item in loaditems:
                    path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setWidget&group=" + item[0].replace(" ", "").lower() + ")" )
                    
                    # Get localised label
                    if not item[0].find( "::SCRIPT::" ) == -1:
                        localLabel = __language__(int( item[0][10:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setWidget&group=" + self.createNiceName( item[0][10:] ) + ")" )
                    elif not item[0].find( "::LOCAL::" ) == -1:
                        localLabel = xbmc.getLocalizedString(int( item[0][9:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setWidget&group=" + self.createNiceName( item[0][9:] ) + ")" )
                    else:
                        localLabel = item[0]
                        
                    # Get display label
                    displayLabel = self._get_customised_settings_string("widget").replace("::MENUNAME::", localLabel)
                    
                    #listitem = xbmcgui.ListItem(label=__language__(32036) + item[0], label2="", iconImage="", thumbnailImage="")
                    listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="", thumbnailImage="")
                    listitem.setProperty('isPlayable', 'True')
                                            
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)

            except:
                print_exc()
                log( "### ERROR could not load file %s" % path )
        
        # Save the list
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    
    def _get_widgets( self ):
        # This will load the shortcut file, and save it as a window property
        # Additionally, if the override files haven't been loaded, we'll load them too
        
        # If we've not loaded widgets...
        if not xbmcgui.Window( 10000 ).getProperty( "skinshortcutsWidgets" ):
            log( "### LOADING WIDGETS FROM FILE ###" )
            
            # Try to load user-defined widgets
            if xbmcvfs.exists( os.path.join( __datapath__ , xbmc.getSkinDir() + ".widgets" ) ):
                path = os.path.join( __datapath__ , xbmc.getSkinDir() + ".widgets" )
                try:
                    # Try loading widgets
                    log ("### LOADING WIDGETS FILE ###" )
                    file = xbmcvfs.File( path )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcutsWidgets", simplejson.dumps( eval( file.read() ) ) )
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcutsWidgets", simplejson.dumps( [] ) )

            else:
                # User hasn't set any widgets, so we'll load them from the
                # skins overrides.xml instead
                tree = self._load_overrides_skin()
                widgets = []
                
                if tree is not None:
                    elems = tree.findall('widgetdefault')
                    for elem in elems:
                        widgets.append( [ elem.attrib.get( 'labelID' ), elem.text ] )
                
                # Save the widgets to a window property               
                xbmcgui.Window( 10000 ).setProperty( "skinshortcutsWidgets", simplejson.dumps( widgets ) )
                log( "### Default widgets loaded:" )
                log( xbmcgui.Window( 10000 ).getProperty( "skinshortcutsWidgets" ) )
        else:
            log( "### WIDGETS ALREADY LOADED ###" )

        # Return the widgets
        return simplejson.loads( xbmcgui.Window( 10000 ).getProperty( "skinshortcutsWidgets" ) )
    
    
    # --------------------
    # BACKGROUND FUNCTIONS
    # --------------------
    
    def _set_background( self ):
        # Load the widgets the skin has defined
        tree = self._load_overrides_skin()
        backgroundLabel = ["None"]
        background = [""]
        
        if tree is not None:
            elems = tree.findall('background')
            for elem in elems:
                if elem.attrib.get( 'label' ).isdigit():
                    backgroundLabel.append( xbmc.getLocalizedString( int( elem.attrib.get( 'label' ) ) ) )
                else:
                    backgroundLabel.append( elem.attrib.get( 'label' ) )
                background.append( elem.text )
        
        dialog = xbmcgui.Dialog()
        selectedBackground = dialog.select( "Choose a background", backgroundLabel )
        
        # Load the current widgets
        currentBackgrounds = ( self._get_background() )
        saveBackgrounds = []
        foundBackgrounds = False
        
        # Loop through current widgets, looking for the current self.GROUP
        for currentBackground in currentBackgrounds:
            if currentBackground[0] == self.GROUP:
                saveBackgrounds.append( [ self.GROUP, background[selectedBackground] ] )
                foundBackground = True
            else:
                saveBackgrounds.append( [ currentBackground[0], currentBackground[1] ] )
                
        # If we didn't find an existing widget for the group, add a new one
        if foundBackground == False:
            saveBackgrounds.append( [ self.GROUP, background[selectedBackground] ] )
            
        # Clear the window property
        self.reset_window_properties()
        
        # Save the widgets
        path = os.path.join( __datapath__ , xbmc.getSkinDir() + ".backgrounds" )
        
        try:
            f = xbmcvfs.File( path, 'w' )
            f.write( repr( saveBackgrounds ) )
            f.close()
        except:
            print_exc()
            log( "### ERROR could not save file %s" % __datapath__ )
    
    
    def _manage_background ( self ):
        log( "### Generating background list for skin settings" )
        
        # Set path based on user defined mainmenu, then skin-provided, then script-provided
        if xbmcvfs.exists( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
            # User defined shortcuts
            path = os.path.join( __datapath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
            # Skin-provided defaults
            path = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
        elif xbmcvfs.exists( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
            # Script-provided defaults
            path = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
        else:
            # No custom shortcuts or defaults available
            path = ""
            
        if not path == "":
            try:
                # Try loading shortcuts
                file = xbmcvfs.File( path )
                loaditems = eval( file.read() )
                file.close()
                
                listitems = []
                
                for item in loaditems:
                    path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setBackground&group=" + item[0].replace(" ", "").lower() + ")" )
                    
                    # Get localised label
                    if not item[0].find( "::SCRIPT::" ) == -1:
                        localLabel = __language__(int( item[0][10:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setBackground&group=" + self.createNiceName( item[0][10:] ) + ")" )
                    elif not item[0].find( "::LOCAL::" ) == -1:
                        localLabel = xbmc.getLocalizedString(int( item[0][9:] ) )
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=setBackground&group=" + self.createNiceName( item[0][9:] ) + ")" )
                    else:
                        localLabel = item[0]
                        
                    # Get display label
                    displayLabel = self._get_customised_settings_string("background").replace("::MENUNAME::", localLabel)
                    
                    #listitem = xbmcgui.ListItem(label=__language__(32036) + item[0], label2="", iconImage="", thumbnailImage="")
                    listitem = xbmcgui.ListItem(label=displayLabel, label2="", iconImage="", thumbnailImage="")
                    listitem.setProperty('isPlayable', 'True')
                                            
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem)

            except:
                print_exc()
                log( "### ERROR could not load file %s" % path )
        
        # Save the list
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    
    def _get_backgrounds( self ):
        # This function will load users backgrounds settings
        if not xbmcgui.Window( 10000 ).getProperty( "skinshortcutsBackgrounds" ):
            log( "### LOADING BACKGROUNDS FROM FILE" )
            # Try to load user-defined widgets
            if xbmcvfs.exists( os.path.join( __datapath__ , xbmc.getSkinDir() + ".backgrounds" ) ):
                path = os.path.join( __datapath__ , xbmc.getSkinDir() + ".backgrounds" )
                try:
                    # Try loading widgets
                    log ("### LOADING WIDGETS FILE ###" )
                    file = xbmcvfs.File( path )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcutsBackgrounds", simplejson.dumps( eval( file.read() ) ) )
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )
                    xbmcgui.Window( 10000 ).setProperty( "skinshortcutsBackgrounds", simplejson.dumps( [] ) )

            else:
                # User hasn't set any widgets, so we'll load them from the
                # skins overrides.xml instead
                tree = self._load_overrides_skin()
                widgets = []
                
                if tree is not None:
                    elems = tree.findall('backgrounddefault')
                    for elem in elems:
                        widgets.append( [ elem.attrib.get( 'labelID' ), elem.text ] )
                
                # Save the widgets to a window property               
                xbmcgui.Window( 10000 ).setProperty( "skinshortcutsBackgrounds", simplejson.dumps( widgets ) )
                log( "### Default widgets loaded:" )
                log( xbmcgui.Window( 10000 ).getProperty( "skinshortcutsBackgrounds" ) )
        else:
            log( "### WIDGETS ALREADY LOADED ###" )

        # Return the widgets
        return simplejson.loads( xbmcgui.Window( 10000 ).getProperty( "skinshortcutsBackgrounds" ) )
    
    
    # ----------------
    # HELPER FUNCTIONS
    # ----------------
    
    def checkVisibility ( self, item ):
        # Return whether mainmenu items should be displayed
        if item == "movies":
            return "Library.HasContent(Movies)"
        elif item == "tvshows":
            return "Library.HasContent(TVShows)"
        if item == "livetv":
            return "System.GetBool(pvrmanager.enabled)"
        elif item == "musicvideos":
            return "Library.HasContent(MusicVideos)"
        elif item == "music":
            return "Library.HasContent(Music)"
        elif item == "weather":
            return "!IsEmpty(Weather.Plugin)"
        elif item == "dvd":
            return "System.HasMediaDVD"
        else:
            return ""
            
    
    def checkWidget( self, item ):
        # Return any widget for mainmenu items
        currentWidgets = ( self._get_widgets() )
        
        # Loop through current widgets, looking for the current item
        for currentWidget in currentWidgets:
            if currentWidget[0] == item:
                return currentWidget[1]
                
        return ""
        
    
    def checkBackground( self, item ):
        # Return any widget for mainmenu items
        currentBackgrounds = ( self._get_widgets() )
        
        # Loop through current widgets, looking for the current item
        for currentBackground in currentBackgrounds:
            if currentBackground[0] == item:
                return currentBackground[1]
                
        return ""

     
    def createNiceName ( self, item ):
        # Translate certain localized strings into non-localized form for labelID
        if item == "10006":
            return "videos"
        if item == "342":
            return "movies"
        if item == "20343":
            return "tvshows"
        if item == "32022":
            return "livetv"
        if item == "10005":
            return "music"
        if item == "20389":
            return "musicvideos"
        if item == "10002":
            return "pictures"
        if item == "12600":
            return "weather"
        if item == "10001":
            return "programs"
        if item == "32032":
            return "dvd"
        if item == "10004":
            return "settings"
        else:
            return item
                        
    
    def reset_window_properties( self ):
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-overrides-skin" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcutsWidgets" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcutsBackgrounds" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-mainmenu" )
        listitems = self._get_shortcuts( "mainmenu" )
        for item in listitems:
            # Get labelID so we can check shortcuts for this menu item
            groupName = item[0].replace(" ", "").lower()
            
            # Localize strings
            if not item[0].find( "::SCRIPT::" ) == -1:
                groupName = self.createNiceName( item[0][10:] )
            elif not item[0].find( "::LOCAL::" ) == -1:
                groupName = self.createNiceName( item[0][9:] )        
                
            # Clear the property
            xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-" + groupName )
            
            # Clear any additional submenus
            i = 0
            finished = False
            while finished == False:
                i = i + 1
                log( "Current level: " + str( i ) )
                if xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-" + groupName + "." + str( i ) ):
                    log( xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-" + groupName + "." + str( i ) ) )
                    xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-" + groupName + "." + str( i ) )
                else:
                    finished = True

                    
if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    
    Main()
            
    log('script stopped')