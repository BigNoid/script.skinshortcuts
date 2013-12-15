import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib
import xml.etree.ElementTree as xmltree
from xml.dom.minidom import parse
from time import gmtime, strftime
from traceback import print_exc

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
    
class SkinShortcuts:
    def __init__(self):
        #log( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) )
            
        self.WINDOW = xbmcgui.Window( 10000 )

        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
            self.TYPE = params.get( "type", "" )
        except:
            try:
                params = dict( arg.split( "=" ) for arg in sys.argv[ 2 ].split( "&" ) )
                self.TYPE = params.get( "?type", "" )
            except:
                params = {}
        
        self.GROUP = params.get( "group", "" )
        self.PATH = params.get( "path", "" )
        log( self.PATH )
        
        # Perform action specified by user
        if not self.TYPE:
            line1 = "This addon is for skin developers, and requires skin support"
            xbmcgui.Dialog().ok(__addonname__, line1)
        elif self.TYPE=="manage":
            import gui
            ui= gui.GUI( "script-skinshortcuts.xml", __cwd__, "default", group=self.GROUP )
            ui.doModal()
            del ui
            # Update home window property (used to automatically refresh type=settings)
            xbmcgui.Window( 10000 ).setProperty( "skinshortcuts",strftime( "%Y%m%d%H%M%S",gmtime() ) )
            
            # Check for settings
            self.checkForSettings()
            
        elif self.TYPE=="list":
            if not self.GROUP == "":
                log( "### Listing shortcuts ..." )
                # Set path based on existance of user defined shortcuts, then skin-provided, then script-provided
                if os.path.isfile( os.path.join( __datapath__ , self.GROUP + ".shortcuts" ) ):
                    # User defined shortcuts
                    path = os.path.join( __datapath__ , self.GROUP + ".shortcuts" )
                elif os.path.isfile( os.path.join( __skinpath__ , self.GROUP + ".shortcuts" ) ):
                    # Skin-provided defaults
                    path = os.path.join( __skinpath__ , self.GROUP + ".shortcuts" )
                elif os.path.isfile( os.path.join( __defaultpath__ , self.GROUP + ".shortcuts" ) ):
                    # Script-provided defaults
                    path = os.path.join( __defaultpath__ , self.GROUP + ".shortcuts" )
                else:
                    # No custom shortcuts or defaults available
                    path = ""
                    
                if not path == "":
                    try:
                        # Try loading shortcuts
                        loaditems = eval( file( path, "r" ).read() )
                        
                        listitems = []
                        loadedOverrides = False
                        hasOverrides = True
                        
                        for item in loaditems:
                            # Generate a listitem
                            path = sys.argv[0] + "?type=launch&path=" + item[4]
                            
                            listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                            listitem.setProperty('isPlayable', 'False')
                            listitem.setProperty( "labelID", item[0].replace(" ", "").lower() )
                            
                            # Localize strings
                            if not listitem.getLabel().find( "::SCRIPT::" ) == -1:
                                listitem.setProperty( "labelID", self.createNiceName( listitem.getLabel()[10:] ) )
                                listitem.setLabel( __language__(int( listitem.getLabel()[10:] ) ) )
                            elif not listitem.getLabel().find( "::LOCAL::" ) == -1:
                                listitem.setProperty( "labelID", self.createNiceName( listitem.getLabel()[9:] ) )
                                listitem.setLabel( xbmc.getLocalizedString(int( listitem.getLabel()[9:] ) ) )
                            
                            if not listitem.getLabel2().find( "::SCRIPT::" ) == -1:
                                listitem.setLabel2( __language__( int( listitem.getLabel2()[10:] ) ) )
                                                                
                            # If the icon and thumbnail are the same, check for an override
                            log( "Checking for thumbnail overrides" )
                            if not len(item) == 6 or (len(item) == 6 and item[5] == "True"):
                                # Check if we need to load overrides file
                                if loadedOverrides == False and hasOverrides == True:
                                    overridepath = os.path.join( __skinpath__ , "overrides.xml" )
                                    log( " - " + overridepath )
                                    if os.path.isfile(overridepath):
                                        try:
                                            log( " - Trying to load overrides" )
                                            tree = xmltree.parse( overridepath )
                                            log( " - Loaded overrides" )
                                            loadedOverrides = True
                                        except:
                                            log( " - Failed to load overrides" )
                                            hasOverrides = False
                                            print_exc()
                                            log( "### ERROR could not load file %s" % overridepath )
                                    else:
                                        hasOverrides = False
                                
                                # If we've loaded override file, search for an override
                                if loadedOverrides == True and hasOverrides == True:
                                    log( " - Checking for an override" )
                                    log( " - " + item[3] )
                                    for elem in tree.iterfind('thumbnail[@image="' + item[2] + '"]'):
                                        listitem.setIconImage( elem.text )
                                        log( " - New icon for " + item[2] + ": " + elem.text )
                                        break
                                        
                                    for elem in tree.iterfind('thumbnail[@image="' + item[3] + '"]'):
                                        listitem.setThumbnailImage( elem.text )
                                        log( " - New thumbnail for " + item[3] + ": " + elem.text )
                                        break
                                        
                                    for elem in tree.iterfind('thumbnail[@labelID="' + listitem.getProperty( "labelID" ) + '"]'):
                                        listitem.setThumbnailImage( elem.text )
                                        log( " - New thumbnail for " + listitem.getProperty( "labelID" ) + ": " + elem.text )
                                        break
                                    
                            # If this is the main menu, check whether we should actually display this item (e.g.
                            #  don't display PVR if PVR isn't enabled)
                            if self.GROUP == "mainmenu":
                                if self.checkVisibility( listitem.getProperty( "labelID" ) ):
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
                            else:
                                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)

                            
                        # If we've loaded anything, save them to the list
                        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
                                    
                    except:
                        print_exc()
                        log( "### ERROR could not load file %s" % path )
                else:   
                    log( " - No shortcuts found")
                    
            # Set window property if no settings shortcut
            file_path = os.path.join( __datapath__, "nosettings.info")
            if os.path.isfile( file_path ):
                xbmcgui.Window( 10000 ).setProperty( "SettingsShortcut","False" )
            else:
                xbmcgui.Window( 10000 ).setProperty( "SettingsShortcut","True" )
                
        elif self.TYPE=="settings":
            log( "### Generating list for skin settings" )
            
            # Create link to manage main menu
            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=mainmenu)" )
            listitem = xbmcgui.ListItem(label=__language__(32035), label2="", iconImage="DefaultShortcut.png", thumbnailImage="DefaultShortcut.png")
            listitem.setProperty('isPlayable', 'False')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
            
            # Set path based on user defined mainmenu, then skin-provided, then script-provided
            if os.path.isfile( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
                # User defined shortcuts
                path = os.path.join( __datapath__ , "mainmenu.shortcuts" )
            elif os.path.isfile( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
                # Skin-provided defaults
                path = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
            elif os.path.isfile( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
                # Script-provided defaults
                path = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
            else:
                # No custom shortcuts or defaults available
                path = ""
                
            if not path == "":
                try:
                    # Try loading shortcuts
                    loaditems = eval( file( path, "r" ).read() )
                    
                    listitems = []
                    
                    for item in loaditems:
                        path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + item[0].replace(" ", "").lower() + ")" )
                        
                        listitem = xbmcgui.ListItem(label=__language__(32036) + item[0], label2="", iconImage="", thumbnailImage="")
                        listitem.setProperty('isPlayable', 'False')
                        
                        # Localize strings
                        if not item[0].find( "::SCRIPT::" ) == -1:
                            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][10:] ) + ")" )
                            listitem.setLabel( __language__(32036) + __language__(int( item[0][10:] ) ) )
                        elif not item[0].find( "::LOCAL::" ) == -1:
                            path = sys.argv[0] + "?type=launch&path=" + urllib.quote( "RunScript(script.skinshortcuts,type=manage&group=" + self.createNiceName( item[0][9:] ) + ")" )
                            listitem.setLabel( __language__(32036) + xbmc.getLocalizedString(int( item[0][9:] ) ) )
                            
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)

                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )
            
            # Add a link to reset all shortcuts
            path = sys.argv[0] + "?type=resetall"
            listitem = xbmcgui.ListItem(label=__language__(32037), label2="", iconImage="DefaultShortcut.png", thumbnailImage="DefaultShortcut.png")
            listitem.setProperty('isPlayable', 'False')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
            
            # Save the list
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            
        elif self.TYPE=="resetall":
            log( "### Resetting all shortcuts" )
            dialog = xbmcgui.Dialog()
            if dialog.yesno(__language__(32037), __language__(32038)):
                for files in os.listdir( __datapath__ ):
                    try:
                        log( "File found - " + files )
                        file_path = os.path.join( __datapath__, files)
                        if os.path.isfile( file_path ):
                            log( "Deleting file" )
                            os.unlink( file_path )
                    except:
                        print_exc()
                        log( "### ERROR could not delete file %s" % path )
            
            # Update home window property (used to automatically refresh type=settings)
            xbmcgui.Window( 10000 ).setProperty( "skinshortcuts",strftime( "%Y%m%d%H%M%S",gmtime() ) )
            
            # Check for settings
            self.checkForSettings()
            
        elif self.TYPE=="launch":
            log( "### Launching shortcut" )
            log( " - " + urllib.unquote( self.PATH ) )
            
            runDefaultCommand = True
            
            # Check if the skin has overridden this command
            paths = [os.path.join( __profilepath__ , "overrides.xml" ),os.path.join( __skinpath__ , "overrides.xml" )]
            for path in paths:
                if os.path.isfile( path ) and runDefaultCommand:    
                    try:
                        tree = xmltree.parse( path )
                        # Search for any overrides
                        for elem in tree.iterfind('override[@action="' + urllib.unquote(self.PATH) + '"]'):
                            runCustomCommand = True
                            # Check for any window settings we should check
                            for condition in elem.iterfind('condition'):
                                if xbmc.getCondVisibility(condition.text) == False:
                                    runCustomCommand = False
                            
                            if runCustomCommand == True:
                                for action in elem.iterfind('action'):
                                    log ( action.text )
                                    runDefaultCommand = False
                                    xbmc.executebuiltin( action.text )
                                break
                    except:
                        print_exc()
                        log( "### ERROR could not load file %s" % path )
                        
            
            
            # If we haven't overridden the command, run the original
            if runDefaultCommand == True:
                xbmc.executebuiltin( urllib.unquote(self.PATH) )
            
            
    def checkVisibility ( self, item ):
        # Return whether mainmenu items should be displayed
        if item == "movies":
            return xbmc.getCondVisibility("Library.HasContent(Movies)")
        elif item == "tvshows":
            return xbmc.getCondVisibility("Library.HasContent(TVShows)")
        elif item == "livetv":
            return xbmc.getCondVisibility("System.GetBool(pvrmanager.enabled)")
        elif item == "musicvideos":
            return xbmc.getCondVisibility("Library.HasContent(MusicVideos)")
        elif item == "music":
            return xbmc.getCondVisibility("Library.HasContent(Music)")
        elif item == "weather":
            return xbmc.getCondVisibility("!IsEmpty(Weather.Plugin)")
        elif item == "dvd":
            return xbmc.getCondVisibility("System.HasMediaDVD")
        else:
            return True
    
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
        if item == "32023":
            return "programs"
        if item == "32032":
            return "dvd"
        if item == "10004":
            return "settings"
        else:
            return item
            
    def checkForSettings( self ):
        # Iterate through main menu, searching for a link to settings
        hasSettingsLink = False
        
        if os.path.isfile( os.path.join( __datapath__ , "mainmenu.shortcuts" ) ):
            # User defined shortcuts
            mainmenuPath = os.path.join( __datapath__ , "mainmenu.shortcuts" )
        elif os.path.isfile( os.path.join( __skinpath__ , "mainmenu.shortcuts" ) ):
            # Skin-provided defaults
            mainmenuPath = os.path.join( __skinpath__ , "mainmenu.shortcuts" )
        elif os.path.isfile( os.path.join( __defaultpath__ , "mainmenu.shortcuts" ) ):
            # Script-provided defaults
            mainmenuPath = os.path.join( __defaultpath__ , "mainmenu.shortcuts" )
        else:
            # No custom shortcuts or defaults available
            mainmenuPath = ""
            
        if not mainmenuPath == "":
            try:
                # Try loading shortcuts
                loaditems = eval( file( mainmenuPath, "r" ).read() )
                
                for item in loaditems:
                    # Check if the path (item 4) is for settings
                    if urllib.unquote(item[4]) == "ActivateWindow(Settings)":
                        hasSettingsLink = True
                        break
                    
                    # Get labelID so we can check shortcuts for this menu item
                    groupName = item[0].replace(" ", "").lower()
                    
                    # Localize strings
                    if not item[0].find( "::SCRIPT::" ) == -1:
                        groupName = self.createNiceName( item[0][10:] )
                    elif not item[0].find( "::LOCAL::" ) == -1:
                        groupName = self.createNiceName( item[0][9:] )
                    
                    # Get path of submenu shortcuts
                    if os.path.isfile( os.path.join( __datapath__ , groupName + ".shortcuts" ) ):
                        # User defined shortcuts
                        submenuPath = os.path.join( __datapath__ , groupName + ".shortcuts" )
                    elif os.path.isfile( os.path.join( __skinpath__ , groupName + ".shortcuts" ) ):
                        # Skin-provided defaults
                        submenuPath = os.path.join( __skinpath__ , groupName + ".shortcuts" )
                    elif os.path.isfile( os.path.join( __defaultpath__ , groupName + ".shortcuts" ) ):
                        # Script-provided defaults
                        submenuPath = os.path.join( __defaultpath__ , groupName + ".shortcuts" )
                    else:
                        # No custom shortcuts or defaults available
                        submenuPath = ""
                        
                    if not submenuPath == "":
                        try:
                            # Try loading shortcuts
                            submenuitems = eval( file( submenuPath, "r" ).read() )
                            
                            for item in submenuitems:
                                if urllib.unquote(item[4]) == "ActivateWindow(Settings)":
                                    hasSettingsLink = True
                                    break
                                
                        except:
                            print_exc()
                            log( "### ERROR could not load file %s" % submenuPath )
                            
                    if hasSettingsLink == True:
                        break
            except:
                print_exc()
                log( "### ERROR could not load file %s" % mainmenuPath )
                
        log ("- Finished checking")
        if hasSettingsLink:
            # There's a settings link, delete our info file
            file_path = os.path.join( __datapath__, "nosettings.info")
            if os.path.isfile( file_path ):
                log( "Deleting file" )
                os.unlink( file_path )
            xbmcgui.Window( 10000 ).setProperty( "SettingsShortcut","True" )
        else:
            # There's no settings link, create an info file
            file_path = os.path.join( __datapath__, "nosettings.info")
            if not os.path.isfile( file_path ):
               open( file_path, 'a' ).close()
            xbmcgui.Window( 10000 ).setProperty( "SettingsShortcut","False" )
                
if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    
    SkinShortcuts()
            
    log('script stopped')