# coding=utf-8
import os, sys, datetime, unicodedata
import xbmc, xbmcgui, xbmcvfs, urllib
import xml.etree.ElementTree as xmltree
import thread
from xml.dom.minidom import parse
from xml.sax.saxutils import escape as escapeXML
from traceback import print_exc
from unidecode import unidecode
import datafunctions, nodefunctions, common
DATA = datafunctions.DataFunctions()
NODE = nodefunctions.NodeFunctions()

import json

ADDON        = sys.modules[ "__main__" ].ADDON
ADDONID      = sys.modules[ "__main__" ].ADDONID
CWD          = sys.modules[ "__main__" ].CWD
DATAPATH     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), ADDONID )
LANGUAGE     = sys.modules[ "__main__" ].LANGUAGE

def kodiwalk(path, stringForce = False):
    json_query = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"files"},"id":1}' % str(path))
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)
    files = []
    if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files'] is not None:
        for item in json_response['result']['files']:
            if item.has_key('file') and item.has_key('filetype') and item.has_key('label'):
                if item['filetype'] == 'directory' and not item['file'].endswith(('.xsp', '.m3u', '.xml/', '.xml' )):
                    if stringForce and item['file'].startswith(stringForce):
                        files = files + kodiwalk( xbmc.translatePath( item['file'] ), stringForce )
                    else:
                        files = files + kodiwalk( item['file'], stringForce )
                else:
                    if stringForce and item['file'].startswith(stringForce):
                        files.append({'path':xbmc.translatePath(item['file']), 'label':item['label']})
                    else:
                        files.append({'path':item['file'], 'label':item['label']})
    return files

class LibraryFunctions():
    def __init__( self, *args, **kwargs ):
        
        # Dictionary to make checking whether things are loaded easier
        self.loaded = { "static": [False, "static shortcuts"],
                "videolibrary": [False, "video library"],
                "musiclibrary": [False, "music library"],
                "librarysources": [False, "library sources"],
                "playlists": [False, "playlists"],
                "addons": [False, "add-ons"],
                "favourites": [False, "favourites"],
                "upnp": [False, "upnp sources"],
                "widgets": [False, "widgets"] }
        
        self.widgetPlaylistsList = []
        
        # Empty dictionary for different shortcut types
        self.dictionaryGroupings = {"common":None,
                "commands":None,
                "video":None, "movie":None,
                "tvshow":None,
                "musicvideo":None,
                "customvideonode":None,
                "videosources":None,
                "pvr":None,
                "radio":None,
                "pvr-tv":None,
                "pvr-radio":None,
                "music":None,
                "musicsources":None,
                "picturesources":None,
                "gamesources":None,
                "playlist-video":None,
                "playlist-audio":None,
                "addon-program":None,
                "addon-program-plugin":None,
                "addon-video":None,
                "addon-audio":None,
                "addon-image":None,
                "addon-game":None,
                "addon-game-plugin":None,
                "favourite":None,
                "settings":None,
                "widgets":None }
        self.folders = {}
        self.foldersCount = 0

        # Widget providers, for auto-installing
        self.widgetProviders = [ [ "service.library.data.provider", None, "Library Data Provider" ], 
                [ "script.extendedinfo", None, "ExtendedInfo Script" ], 
                [ "service.smartish.widgets", "Skin.HasSetting(enable.smartish.widgets)", "Smart(ish) Widgets" ] ]
        self.allowWidgetInstall = False
        self.skinhelperWidgetInstall = True
        
        self.useDefaultThumbAsIcon = None

    def loadLibrary( self, library ):
        # Common entry point for loading available shortcuts

        # INTROSPECT
        #json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "JSONRPC.Introspect" }')
        #json_query = unicode(json_query, 'utf-8', errors='ignore')
        #json_response = json.loads(json_query)

        #with open( os.path.join( os.path.expanduser('~'), "kodi.txt" ), 'w') as outfile:
        #    json.dump(json_response, outfile, indent=4, sort_keys=True)

        # Handle whether the shortcuts are already loaded/loading
        if self.loaded[ library ][ 0 ] is True:
            return True
        elif self.loaded[ library ][ 0 ] == "Loading":
            # The list is currently being populated, wait and then return it
            for i in range( 0, 50 ):
                if xbmc.Monitor().waitForAbort(0.1) or self.loaded[ library ][ 0 ] is True:
                    return True
        else:
            # We're going to populate the list
            self.loaded[ library ][ 0 ] = "Loading"

        # Call the function responsible for loading the library type we've been passed
        common.log( "Listing %s..." %( self.loaded[ library ][ 1 ] ) )
        try:
            if library == "static":
                self.staticShortcuts()
            elif library == "videolibrary":
                self.libraryNodes( "video" )
            elif library == "musiclibrary":
                self.libraryNodes( "music" )
            elif library == "librarysources":
                self.librarysources()
            elif library == "playlists":
                self.playlists()
            elif library == "addons":
                self.addons()
            elif library == "favourites":
                self.favourites()
            elif library == "widgets":
                self.widgets()
            elif library == "upnp":
                json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "directory": "upnp://", "media": "files" } }')

        except:
            common.log( "Failed to load %s" %( self.loaded[ library ][ 1 ] ) )
            print_exc()

        # Mark library type as loaded
        self.loaded[ library ][ 0 ] = True
        return True
        
    def loadAllLibrary( self ):
        # Load all library data, for use with threading
        self.loadLibrary( "static" )
        self.loadLibrary( "videolibrary" )
        self.loadLibrary( "musiclibrary" )
        self.loadLibrary( "librarysources" )
        self.loadLibrary( "playlists" )
        self.loadLibrary( "addons" )
        self.loadLibrary( "favourites" )
        self.loadLibrary( "widgets" )
        self.loadLibrary( "upnp" )

    # ==============================================
    # === BUILD/DISPLAY AVAILABLE SHORTCUT NODES ===
    # ==============================================
    
    def retrieveGroup( self, group, grouping = None ):
        trees = [ DATA._get_overrides( "skin" ), DATA._get_overrides( "script" ) ]
        nodes = None
        for tree in trees:
            if grouping is None:
                nodes = tree.find( "groupings" )
            else:
                nodes = tree.find( "%s-groupings" %( grouping ) )
                
            if nodes is not None:
                break                
                
        if nodes is None:
            return [ "Error", [] ]
            
        returnList = []
        
        if group == "":
            # We're going to get the root nodes
            self.installWidget = False
            windowTitle = LANGUAGE(32048)
            if grouping == "widget":
                windowTitle = LANGUAGE(32044)
            return [ windowTitle, self.buildNodeListing( nodes ) ]
        else:
            groups = group.split( "," )
            
            nodes = [ "", nodes ]
            for groupNum in groups:
                nodes = self.getNode( nodes[1], int( groupNum ) )
                
            return [ nodes[0], self.buildNodeListing( nodes[1] ) ]
                        
    def getNode( self, tree, number ):
        count = 0
        for subnode in tree:
            count += 1
            # If not visible, skip it
            if "condition" in subnode.attrib:
                if not xbmc.getCondVisibility( subnode.attrib.get( "condition" ) ):
                    number += 1
                    continue
            if "installWidget" in subnode.attrib and subnode.attrib.get( "installWidget" ).lower() == "true":
                self.installWidget = True
            else:
                self.installWidget = False

            if count == number:
                label = DATA.local( subnode.attrib.get( "label" ) )[2]
                return [ label, subnode ]
                
    def buildNodeListing( self, nodes ):
        returnList = []
        count = 0
        for node in nodes:
            if "condition" in node.attrib:
                if not xbmc.getCondVisibility( node.attrib.get( "condition" ) ):
                    continue
            count += 1
            if node.tag == "content":
                returnList = returnList + self.retrieveContent( node.text )
            if node.tag == "shortcut":
                shortcutItem = self._create( [node.text, node.attrib.get( "label" ), node.attrib.get( "type" ), {"icon": node.attrib.get( "icon" )}] )
                if "widget" in node.attrib:
                    # This is a widget shortcut, so add the relevant widget information
                    shortcutItem.setProperty( "widget", node.attrib.get( "widget" ) )
                    if "widgetName" in node.attrib:
                        shortcutItem.setProperty( "widgetName", node.attrib.get( "widgetName" ) )
                    else:
                        shortcutItem.setProperty( "widgetName", node.attrib.get( "label" ) )
                    shortcutItem.setProperty( "widgetPath", node.text )
                    if "widgetType" in node.attrib:
                        shortcutItem.setProperty( "widgetType", node.attrib.get( "widgetType" ) )
                    else:
                        shortcutItem.setProperty( "widgetType", "" )
                    if "widgetTarget" in node.attrib:
                        shortcutItem.setProperty( "widgetTarget", node.attrib.get( "widgetTarget" ) )
                    else:
                        shortcutItem.setProperty( "widgetTarget", "" )
                returnList.append( shortcutItem )
            if node.tag == "node":
                returnList.append( self._create( ["||NODE||" + str( count ), node.attrib.get( "label" ), "", {"icon": "DefaultFolder.png"}] ) )
                
        # Override icons
        tree = DATA._get_overrides( "skin" )
        for item in returnList:
            item = self._get_icon_overrides( tree, item, None )

        return returnList
                
    def retrieveContent( self, content ):
        if content == "upnp-video":
            items = [ self._create(["||UPNP||", "32070", "32069", {"icon": "DefaultFolder.png"}]) ]
        elif content == "upnp-music":
            items = [ self._create(["||UPNP||", "32070", "32073", {"icon": "DefaultFolder.png"}]) ]
            
        elif self.dictionaryGroupings[ content ] is None:
            # The data hasn't been loaded yet
            items = self.loadGrouping( content )
        else:
            items = self.dictionaryGroupings[ content ]

        if items is not None:
            items = self.checkForFolder( items )
        else:
            items = []

        # Add widget information for video/audio nodes
        if content in [ "video", "music" ]:
            # Video nodes - add widget information
            for listitem in items:
                path = listitem.getProperty( "path" )
                if path.lower().startswith( "activatewindow" ):
                    path = DATA.getListProperty( path )
                    listitem.setProperty( "widget", "Library" )
                    if content == "video":
                        listitem.setProperty( "widgetType", "video" )
                        listitem.setProperty( "widgetTarget", "videos" )
                    else:
                        listitem.setProperty( "widgetType", "audio" )
                        listitem.setProperty( "widgetTarget", "music" )
                    listitem.setProperty( "widgetName", listitem.getLabel() )
                    listitem.setProperty( "widgetPath", path )

                    widgetType = NODE.get_mediaType( path )
                    if widgetType != "unknown":
                        listitem.setProperty( "widgetType", widgetType )
            
        # Check for any icon overrides for these items
        tree = DATA._get_overrides( "skin" )
            
        for item in items:
            item = self._get_icon_overrides( tree, item, content )
            
        return items
            
    def checkForFolder( self, items ):
        # This function will check for any folders in the listings that are being returned
        # and, if found, move their sub-items into a property
        returnItems = []
        for item in items:
            if isinstance( item, list ):
                self.foldersCount += 1
                self.folders[ str( self.foldersCount ) ] = item[1]
                newItem = item[0]
                newItem.setProperty( "folder", str( self.foldersCount ) )
                returnItems.append( newItem )
            else:
                returnItems.append( item )
            
        return( returnItems )
        
    def loadGrouping( self, content ):
        # Display a busy dialog
        dialog = xbmcgui.DialogProgress()
        dialog.create( "Skin Shortcuts", LANGUAGE( 32063 ) )

        # We'll be called if the data for a wanted group hasn't been loaded yet
        if content in [ "common", "commands", "settings", "pvr", "pvr-tv", "pvr-radio", "radio" ]:
            self.loadLibrary( "static" )
        if content == "video":
            self.loadLibrary( "videolibrary" )
        if content == "videosources" or content == "musicsources" or content == "picturesources" or content == "gamesources":
            self.loadLibrary( "librarysources" )
        if content == "music":
            self.loadLibrary( "musiclibrary" )
        if content == "playlist-video" or content == "playlist-audio":
            self.loadLibrary( "playlists" )
        if content == "addon-program" or content == "addon-video" or content == "addon-audio" or content == "addon-image" or content == "addon-game":
            self.loadLibrary( "addons" )
        if content == "favourite":
            self.loadLibrary( "favourites" )
        if content == "widgets":
            self.loadLibrary( "widgets" )
            
        # The data has now been loaded, return it
        dialog.close()
        return self.dictionaryGroupings[ content ]
        
    
    def addToDictionary( self, group, content ):
        # This function adds content to the dictionaryGroupings - including
        # adding any skin-provided shortcuts to the group
        tree = DATA._get_overrides( "skin" )
            
        # Search for skin-provided shortcuts for this group
        originalGroup = group
            
        if group not in [ "movie", "tvshow", "musicvideo" ]:
            for elem in tree.findall( "shortcut" ):
                if "grouping" in elem.attrib:
                    if group == elem.attrib.get( "grouping" ):
                        # We want to add this shortcut
                        label = elem.attrib.get( "label" )
                        type = elem.attrib.get( "type" )
                        thumb = elem.attrib.get( "thumbnail" )
                        icon = elem.attrib.get( "icon" )
                        
                        action = elem.text
                        
                        #if label.isdigit():
                        #    label = "::LOCAL::" + label
                            
                        if type is None:
                            type = "32024"
                        #elif type.isdigit():
                        #    type = "::LOCAL::" + type
                        
                        if icon is None:
                            icon = ""
                        if thumb is None:
                            thumb = ""

                        listitem = self._create( [action, label, type, {"icon": icon, "thumb": thumb}] )
                        
                        if "condition" in elem.attrib:
                            if xbmc.getCondVisibility( elem.attrib.get( "condition" ) ):
                                content.insert( 0, listitem )
                        else:
                            content.insert( 0, listitem )

                elif group == "common":
                    # We want to add this shortcut
                    label = elem.attrib.get( "label" )
                    type = elem.attrib.get( "type" )
                    thumb = elem.attrib.get( "thumbnail" )
                    icon = elem.attrib.get( "icon" )
                    
                    action = elem.text
                    
                    #if label.isdigit():
                    #    label = "::LOCAL::" + label
                        
                    if type is None:
                        type = "32024"
                    #elif type.isdigit():
                    #    type = "::LOCAL::" + type
                        
                    if type is None or type == "":
                        type = "Skin Provided"
                        
                    if icon is None:
                        icon = ""
                        
                    if thumb is None:
                        thumb = ""

                    listitem = self._create( [action, label, type, {"icon": icon, "thumb":thumb}] )
                    
                    if "condition" in elem.attrib:
                        if xbmc.getCondVisibility( elem.attrib.get( "condition" ) ):
                            content.append( listitem )
                    else:
                        content.append( listitem )
                    
        self.dictionaryGroupings[ originalGroup ] = content
        
    # ================================
    # === BUILD AVAILABLE SHORTCUT ===
    # ================================
    
    def _create ( self, item, allowOverrideLabel = True ):
        # Retrieve label
        localLabel = DATA.local( item[1] )[0]
        
        # Create localised label2
        displayLabel2 = DATA.local( item[2] )[2]
        shortcutType = DATA.local( item[2] )[0]
        
        if allowOverrideLabel:
            # Check for a replaced label
            replacementLabel = DATA.checkShortcutLabelOverride( item[0] )
            if replacementLabel is not None:
                
                localLabel = DATA.local( replacementLabel[0] )[0]
                    
                if len( replacementLabel ) == 2:
                    # We're also overriding the type
                    displayLabel2 = DATA.local( replacementLabel[1] )[2]
                    shortcutType = DATA.local( replacementLabel[1] )[0]
                    
        # Try localising it
        displayLabel = DATA.local( localLabel )[2]
        
        if displayLabel.startswith( "$NUMBER[" ):
            displayLabel = displayLabel[8:-1]
        
        # Create localised label2
        displayLabel2 = DATA.local( displayLabel2 )[2]
        shortcutType = DATA.local( shortcutType )[0]
        
        # If either displayLabel starts with a $, ask Kodi to parse it for us
        if displayLabel.startswith( "$" ):
            displayLabel = xbmc.getInfoLabel( displayLabel )
        if displayLabel2.startswith( "$" ):
            displayLabel2 = xbmc.getInfoLabel( displayLabel2 )
            
        # If this launches our explorer, append a notation to the displayLabel
        noNonLocalized = False
        if item[0].startswith( "||" ):
            displayLabel = displayLabel + "  >"
            # We'll also mark that we don't want to use a non-localised labelID, as this
            # causes issues with some folders picking up overriden icons incorrectly
            noNonLocalized = True

        # Get the items labelID
        DATA._clear_labelID()
        labelID = DATA._get_labelID( DATA.createNiceName( DATA.local( localLabel )[0], noNonLocalized = noNonLocalized ), item[0], noNonLocalized = noNonLocalized )
            
        # Retrieve icon and thumbnail
        if item[3]:
            if "icon" in item[3].keys() and item[ 3 ][ "icon" ] is not None:
                icon = item[3]["icon"]
            else:
                icon = "DefaultShortcut.png"
            if "thumb" in item[3].keys():
                thumbnail = item[3]["thumb"]
            else:
                thumbnail = None
        else:
            icon = "DefaultShortcut.png"
            thumbnail = None
                        
        # Check if the option to use the thumb as the icon is enabled
        if self.useDefaultThumbAsIcon is None:
            # Retrieve the choice from the overrides.xml
            tree = DATA._get_overrides( "skin" )
            node = tree.getroot().find( "useDefaultThumbAsIcon" )
            if node is None:
                self.useDefaultThumbAsIcon = False
            else:
                if node.text.lower() == "true":
                    self.useDefaultThumbAsIcon = True
                else:
                    self.useDefaultThumbAsIcon = False
            
        usedDefaultThumbAsIcon = False
        if self.useDefaultThumbAsIcon == True and thumbnail is not None:            
            icon = thumbnail
            thumbnail = None
            usedDefaultThumbAsIcon = True
            
        oldicon = None
        
        # If the icon starts with a $, ask Kodi to parse it for us
        displayIcon = icon
        iconIsVar = False
        if icon.startswith( "$" ):
            displayIcon = xbmc.getInfoLabel( icon )
            iconIsVar = True
                        
        # If the skin doesn't have the icon, replace it with DefaultShortcut.png
        if ( not displayIcon or not xbmc.skinHasImage( displayIcon ) ) and not iconIsVar:
            if not usedDefaultThumbAsIcon:
                displayIcon = "DefaultShortcut.png"
                            
        # Build listitem
        if thumbnail is not None:
            listitem = xbmcgui.ListItem(label=displayLabel, label2=displayLabel2, iconImage=displayIcon, thumbnailImage=thumbnail)
            listitem.setProperty( "thumbnail", thumbnail)
        else:
            listitem = xbmcgui.ListItem(label=displayLabel, label2=displayLabel2, iconImage=thumbnail)
        listitem.setProperty( "path", item[0] )
        listitem.setProperty( "localizedString", localLabel )
        listitem.setProperty( "shortcutType", shortcutType )
        listitem.setProperty( "icon", displayIcon )
        listitem.setProperty( "tempLabelID", labelID )
        listitem.setProperty( "defaultLabel", labelID )
        
        if displayIcon != icon:
            listitem.setProperty( "untranslatedIcon", icon )
        
        return( listitem )
                
    def _get_icon_overrides( self, tree, item, content, setToDefault = True ):
        if tree is None:
            return item
            
        oldicon = None
        newicon = item.getProperty( "icon" )
        for elem in tree.findall( "icon" ):
            if oldicon is None:
                if ("labelID" in elem.attrib and elem.attrib.get( "labelID" ) == item.getProperty( "tempLabelID" )) or ("image" in elem.attrib and elem.attrib.get( "image" ) == item.getProperty( "icon" )):
                    # LabelID matched
                    if "grouping" in elem.attrib:
                        if elem.attrib.get( "grouping" ) == content:
                            # Group also matches - change icon
                            oldicon = item.getProperty( "icon" )
                            newicon = elem.text
                    elif "group" not in elem.attrib:
                        # No group - change icon
                        oldicon = item.getProperty( "icon" )
                        newicon = elem.text
                        
        # If the icon doesn't exist, set icon to default
        setDefault = False
        if not xbmc.skinHasImage( newicon ) and setToDefault == True:
            oldicon = item.getProperty( "icon" )
            icon = "DefaultShortcut.png"
            setDefault = True

        if oldicon is not None:
            # we found an icon override
            item.setProperty( "icon", newicon )
            item.setIconImage( newicon )
            
        if setDefault == True:
            item = self._get_icon_overrides( tree, item, content, False )
            
        return item

    # ==========================
    # === LOAD LIBRARY NODES ===
    # ==========================

    def libraryNodes( self, library ):
        # Try loading custom nodes first
        try:
            if self._parse_libraryNodes( library, "custom" ) == False:
                common.log( "Failed to load custom %s nodes" %( library ) )
                self._parse_libraryNodes( library, "default" )
        except:
            common.log( "Failed to load custom %s nodes" %( library ) )
            print_exc()
            try:
                # Try loading default nodes
                self._parse_libraryNodes( library, "default" )
            except:
                # Empty library
                common.log( "Failed to load default %s nodes" %( library ) )
                print_exc()

        self.loadLibrary( "upnp" )

    def _parse_libraryNodes( self, library, type ):
        #items = {"video":[], "movies":[], "tvshows":[], "musicvideos":[], "custom":{}}
        items = {}

        if library == "video":
            windowID = "Videos"
            prefix = "library://video"
            action = "||VIDEO||"
        elif library == "music":
            windowID = "music"
            prefix = "library://music"
            action = "||AUDIO||"

        rootdir = os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", library )
        if type == "custom":
            common.log( "Listing custom %s nodes..." %( library ) )
        else:
            rootdir = os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", library )
            common.log( "Listing default %s nodes..." %( library ) )
            
        nodes = NODE.get_nodes( rootdir, prefix )
        if nodes == False or len( nodes ) == 0:
            return False
        
        items = []
        
        for key in nodes:
            # 0 = Label
            # 1 = Icon
            # 2 = Path
            # 3 = Type
            # 4 = Order
            # 5 = Media type (not folders...?)
            
            #make sure the path ends with a trailing slash te prevent weird kodi behaviour
            if "/" in nodes[key][2] and not nodes[key][2].endswith("/"):
                nodes[key][2] += "/"
            
            if nodes[ key ][ 3 ] == "folder":
                item = self._create( [ "%s%s" % ( action, nodes[ key ][ 2 ] ), nodes[ key ][ 0 ], nodes[ key ][ 3 ], { "icon": nodes[ key ][ 1 ] } ] )
            elif nodes[ key ][ 3 ] == "grouped":
                item = self._create( [ "%s%s" % ( action, nodes[ key ][ 2 ] ), nodes[ key ][ 0 ], nodes[ key ][ 3 ], { "icon": nodes[ key ][ 1 ] } ] )
            else:
                item = self._create( [ "ActivateWindow(%s,%s,return)" %( windowID, nodes[ key ][ 2 ] ), nodes[ key ][ 0 ], nodes[ key ][ 3 ], { "icon": nodes[ key ][ 1 ] } ] )
            if nodes[ key ][ 5 ] is not None:
                item.setProperty( "widgetType", nodes[ key ][ 5 ] )
                item.setProperty( "widgetTarget", library )
            items.append( item )
            
        self.addToDictionary( library, items )
    

    # ============================
    # === LOAD OTHER LIBRARIES ===
    # ============================

    def staticShortcuts( self ):
        # List all static shortcuts from overrides

        # Define static groups
        staticGroups = [ ( "common", "32034" ), ( "commands", "32054" ), ( "settings", "10004" ), ( "pvr-tv", "32017" ), ( "pvr-radio", "32087" ) ]

        # Pull out static shortcuts
        trees = [ DATA._get_overrides( "skin" ).find( "static" ), DATA._get_overrides( "script" ).find( "static" ) ]

        for staticGroup in staticGroups:
            common.log( repr( staticGroup ) )
            listitems = []
            for tree in trees:
                if tree is None:
                    continue

                staticItems = tree.find( staticGroup[ 0 ] )
                if staticItems is None:
                    continue

                for staticItem in staticItems.findall( "item" ):
                    if "condition" in staticItem.attrib and not xbmc.getCondVisibility( staticItem.attrib.get( "condition" ) ):
                        # Condition specified doesn't match
                        continue

                    # Pull out properties of static item
                    path = staticItem.text
                    label = staticItem.attrib.get( "label" )
                    icon = staticItem.attrib.get( "icon" )

                    # Build static item
                    listitems.append( self._create( [ staticItem.text, staticItem.attrib.get( "label" ), staticGroup[ 1 ], { "icon": staticItem.attrib.get( "icon" ) } ] ) )

                break

            self.addToDictionary( staticGroup[ 0 ], listitems )
    
    def librarysources( self ):
        for mediaType in [ ( "video", "videosources" ), ( "music", "musicsources" ), ( "pictures", "picturesources" ), ( "games", "gamesources" ) ]:
            listitems = []
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetSources", "params": { "media": "%s" } }' %( mediaType[ 0 ] ) )
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = json.loads(json_query)

            # Add all directories returned by the json query
            if json_response.has_key('result') and json_response['result'].has_key('sources') and json_response['result']['sources'] is not None:
                for item in json_response['result']['sources']:
                    listitems.append( self._create(["||SOURCE||" + item['file'], item['label'], "32069", {"icon": "DefaultFolder.png"} ]) )
                self.addToDictionary( mediaType[ 1 ], listitems )

                common.log( " - %i %s sources" %( len( listitems), mediaType[ 0 ] ) )
            else:
                common.log( " - Unable to load %s sources" %( mediaType[ 0 ] ) )
            
    def playlists( self ):
        audiolist = []
        videolist = []
        paths = [['special://videoplaylists/','32004','Videos'], ['special://musicplaylists/','32005','Music'], ["special://skin/playlists/",'32059',None], ["special://skin/extras/",'32059',None]]
        for path in paths:
            count = 0
            if not xbmcvfs.exists(path[0]): continue
            for file in kodiwalk( path[0] ):
                try:
                    playlist = file['path']
                    label = file['label']
                    playlistfile = xbmc.translatePath( playlist ).decode('utf-8')
                    mediaLibrary = path[2]
                    
                    if playlist.endswith( '.xsp' ):
                        contents = xbmcvfs.File(playlistfile, 'r')
                        contents_data = contents.read().decode('utf-8')
                        xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                        mediaType = "unknown"
                        for line in xmldata.getiterator():
                            if line.tag == "smartplaylist":
                                mediaType = line.attrib['type']
                                if mediaType == "movies" or mediaType == "tvshows" or mediaType == "seasons" or mediaType == "episodes" or mediaType == "musicvideos" or mediaType == "sets":
                                    mediaLibrary = "Videos"
                                    mediaContent = "video"
                                elif mediaType == "albums" or mediaType == "artists" or mediaType == "songs":
                                    mediaLibrary = "Music"
                                    mediaContent = "music"
                                
                            if line.tag == "name" and mediaLibrary is not None:
                                name = line.text
                                if not name:
                                    name = label
                                # Create a list item
                                listitem = self._create(["::PLAYLIST>%s::" %( mediaLibrary ), name, path[1], {"icon": "DefaultPlaylist.png"} ])
                                listitem.setProperty( "action-play", "PlayMedia(" + playlist + ")" )
                                listitem.setProperty( "action-show", "ActivateWindow(" + mediaLibrary + "," + playlist + ",return)".encode( 'utf-8' ) )
                                listitem.setProperty( "action-party", "PlayerControl(PartyMode(%s))" %( playlist ) )

                                # Add widget information
                                listitem.setProperty( "widget", "Playlist" )
                                listitem.setProperty( "widgetType", mediaType )
                                listitem.setProperty( "widgetTarget", mediaContent )
                                listitem.setProperty( "widgetName", name )
                                listitem.setProperty( "widgetPath", playlist )
                                
                                if mediaLibrary == "Videos":
                                    videolist.append( listitem )
                                else:
                                    audiolist.append( listitem )
                                # Save it for the widgets list
                                self.widgetPlaylistsList.append( [playlist, "(" + LANGUAGE( int( path[1] ) ) + ") " + name, name] )
                                
                                count += 1
                                break

                    elif playlist.endswith( '.m3u' ) and path[2] is not None:
                        name = label
                        listitem = self._create( ["::PLAYLIST>%s::" %( path[2] ), name, path[1], {"icon": "DefaultPlaylist.png"} ] )
                        listitem.setProperty( "action-play", "PlayMedia(" + playlist + ")" )
                        listitem.setProperty( "action-show", "ActivateWindow(%s,%s,return)".encode( 'utf-8' ) %( path[2], playlist ) )
                        listitem.setProperty( "action-party", "PlayerControl(PartyMode(%s))" %( playlist ) )

                        # Add widget information
                        listitem.setProperty( "widget", "Playlist" )
                        listitem.setProperty( "widgetName", name )
                        listitem.setProperty( "widgetPath", playlist )
                        if path[2] == "Videos":
                            listitem.setProperty( "widgetType", "videos" )
                            listitem.setProperty( "widgetTarget", "videos" )
                            videolist.append( listitem )
                        else:
                            listitem.setProperty( "widgetType", "songs" )
                            listitem.setProperty( "widgetTarget", "music" )
                            audiolist.append( listitem )
                        
                        count += 1
                except:
                    common.log( "Failed to load playlist: %s" %( file ) )
                    print_exc()
                        
            common.log( " - [" + path[0] + "] " + str( count ) + " playlists found" )
        
        self.addToDictionary( "playlist-video", videolist )
        self.addToDictionary( "playlist-audio", audiolist )
                
    def favourites( self ):
        listitems = []
        listing = None
        
        fav_file = xbmc.translatePath( 'special://profile/favourites.xml' ).decode("utf-8")
        if xbmcvfs.exists( fav_file ):
            doc = parse( fav_file )
            listing = doc.documentElement.getElementsByTagName( 'favourite' )
        else:
            # No favourites file found
            self.addToDictionary( "favourite", [] )
            self.loadedFavourites = True
            return True
            
        for count, favourite in enumerate(listing):
            name = favourite.attributes[ 'name' ].nodeValue
            path = favourite.childNodes [ 0 ].nodeValue
            if ('RunScript' not in path) and ('StartAndroidActivity' not in path) and not (path.endswith(',return)') ):
                path = path.rstrip(')')
                path = path + ',return)'

            try:
                thumb = favourite.attributes[ 'thumb' ].nodeValue
                
            except:
                thumb = None
            
            listitems.append( self._create( [ path, name, "32006", { "icon": "DefaultFolder.png", "thumb": thumb} ] ) )
        
        common.log( " - " + str( len( listitems ) ) + " favourites found" )
        
        self.addToDictionary( "favourite", listitems )
        
    def addons( self ):
        executableItems = {}
        videoItems = {}
        audioItems = {}
        imageItems = {}
        gameItems = {}
        gameEngineItems = {}
        contenttypes = [ ( "executable", executableItems, "xbmc.addon.executable" ),  ( "video", videoItems, "xbmc.addon.video" ), ( "audio", audioItems, "xbmc.addon.audio" ), ( "image", imageItems, "xbmc.addon.image" ), ( "gameEngine", gameItems, "kodi.gameclient" ), ( "game", gameItems, "kodi.addon.game" ) ]
        for contenttype, listitems, addonType in contenttypes:
            plugins = {}
            if contenttype == "executable":
                contentlabel = LANGUAGE(32009)
                shortcutType = "::SCRIPT::32009"
            elif contenttype == "video":
                contentlabel = LANGUAGE(32010)
                shortcutType = "::SCRIPT::32010"
            elif contenttype == "audio":
                contentlabel = LANGUAGE(32011)
                shortcutType = "::SCRIPT::32011"
            elif contenttype == "image":
                contentlabel = LANGUAGE(32012)
                shortcutType = "::SCRIPT::32012"
            elif contenttype == "game":
                contentlabel = LANGUAGE(35049)
                shortcutType = "::SCRIPT::35049"
                
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Addons.Getaddons", "params": { "type": "%s", "properties": ["name", "path", "thumbnail", "enabled"] } }' % addonType)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = json.loads(json_query)

            #log( repr( json_response ) )
            
            if json_response.has_key('result') and json_response['result'].has_key('addons') and json_response['result']['addons'] is not None:
                for item in json_response['result']['addons']:
                    if item['enabled'] == True:                            
                        path = "RunAddOn(" + item['addonid'].encode('utf-8') + ")"
                        action = None
                        thumb = "DefaultAddon.png"
                        if item['thumbnail'] != "":
                            thumb = item[ 'thumbnail' ]
                        else:   
                            thumb = None  
                        listitem = self._create([path, item['name'], shortcutType, {"icon": "DefaultAddon.png", "thumb": thumb} ])

                        # If this is a plugin, mark that we can browse it
                        if item[ "type" ] == "xbmc.python.pluginsource":
                            path = "||BROWSE||" + item['addonid'].encode('utf-8')
                            action = "RunAddOn(" + item['addonid'].encode('utf-8') + ")"

                            listitem.setProperty( "path", path )
                            listitem.setProperty( "action", action )
                            listitem.setLabel( listitem.getLabel() + "  >" )

                            # If its executable or a game, save it to our program plugin widget list
                            if contenttype in ("executable", "game"):
                                plugins[ item[ "name" ] ] = listitem

                        elif contenttype == "executable":
                            # Check if it's a program that can be run as an exectuble
                            provides = self.parseAddonXML( item[ "path" ], "plugin" )
                            for content in provides:
                                # For each content that it provides, add it to the add-ons for that type
                                contentData = { "video": [ "::SCRIPT::32010", videoItems ], "audio": [ "::SCRIPT::32011", audioItems ], "image": [ "::SCRIPT::32012", imageItems ], "executable": [ "::SCRIPT::32009", executableItems ] }
                                if content in contentData:
                                    # Add it as a plugin in the relevant category
                                    otherItem = self._create([path, item['name'] + "  >", contentData[ content ][ 0 ], {"icon": "DefaultAddon.png", "thumb": thumb} ])
                                    otherItem.setProperty( "path", "||BROWSE||" + item['addonid'].encode('utf-8') )
                                    otherItem.setProperty( "action", "RunAddOn(" + item['addonid'].encode('utf-8') + ")" )
                                    contentData[ content ][ 1 ][ item[ "name" ] ] = otherItem
                                    # If it's executable, add it to our seperate program plugins for widgets
                                    if content == "executable":
                                        executablePluginItems[ item[ "name" ] ] = otherItem

                        elif contenttype == "gameEngine":
                            if not self.parseAddonXML( item[ "path" ], "game" ):
                                # Not standalone, so we're not interested
                                continue

                        # Save the listitem
                        listitems[ item[ "name" ] ] = listitem
                        
            if contenttype == "executable":
                self.addToDictionary( "addon-program", self.sortDictionary( listitems ) )
                self.addToDictionary( "addon-program-plugin", self.sortDictionary( plugins ) )
                common.log( " - %i programs found (of which %i are plugins)" %( len( listitems ), len( plugins ) ) )
            elif contenttype == "video":
                self.addToDictionary( "addon-video", self.sortDictionary( listitems ) )
                common.log( " - " + str( len( listitems ) ) + " video add-ons found" )
            elif contenttype == "audio":
                self.addToDictionary( "addon-audio", self.sortDictionary( listitems ) )
                common.log( " - " + str( len( listitems ) ) + " audio add-ons found" )
            elif contenttype == "image":
                self.addToDictionary( "addon-image", self.sortDictionary( listitems ) )
                common.log( " - " + str( len( listitems ) ) + " image add-ons found" )
            elif contenttype == "game":
                self.addToDictionary( "addon-game", self.sortDictionary( listitems ) )
                self.addToDictionary( "addon-game-plugin", self.sortDictionary( plugins ) )
                common.log( " - %i game add-ons found (of which %i are plugins)" %( len( listitems ), len( plugins ) ) )


    def parseAddonXML( self, path, type ):
        # Get information about an addon by parsing its addon.xml file
        info = { "plugin": ( "xbmc.python.pluginsource", "provides", [] ), "game": ( "kodi.gameclient", "supports_standalone", False ) }
        try:
            tree = xmltree.parse( os.path.join( path, "addon.xml" ) ).getroot()
            for extension in tree.findall( "extension" ):
                if "point" in extension.attrib and extension.attrib.get( "point" ) == info[ type ][ 0 ]:
                    # Find out what content type it provides
                    details = extension.find( info[ type ][ 1 ] )
                    if details is None:
                        return []
                    if type == "plugin":
                        return details.text.split( " " )
                    elif type == "game":
                        if details.text == "false":
                            return False
                        return True

        except:
            print_exc()
        return info[ type ][ 2 ]    
    
    def detectPluginContent(self, item):
        #based on the properties in the listitem we try to detect the content
        
        if not item.has_key("showtitle") and not item.has_key("artist"):
            #these properties are only returned in the json response if we're looking at actual file content...
            # if it's missing it means this is a main directory listing and no need to scan the underlying listitems.
            return None

        if not item.has_key("showtitle") and not item.has_key("artist"):
            #these properties are only returned in the json response if we're looking at actual file content...
            # if it's missing it means this is a main directory listing and no need to scan the underlying listitems.
            return "files"
        if not item.has_key("showtitle") and item.has_key("artist"):
            ##### AUDIO ITEMS ####
            if len( item["artist"] ) != 0:
                artist = item["artist"][0]
            else:
                artist = item["artist"]
            if item["type"] == "artist" or artist == item["title"]:
                return "artists"
            elif item["type"] == "album" or item["album"] == item["title"]:
                return "albums"
            elif (item["type"] == "song" and not "play_album" in item["file"]) or (item["artist"] and item["album"]):
                return "songs"
        else:    
            ##### VIDEO ITEMS ####
            if (item["showtitle"] and not item["artist"]):
                #this is a tvshow, episode or season...
                if item["type"] == "season" or (item["season"] > -1 and item["episode"] == -1):
                    return "seasons"
                elif item["type"] == "episode" or item["season"] > -1 and item["episode"] > -1:
                    return "episodes"
                else:
                    return "tvshows"
            elif (item["artist"]):
                #this is a musicvideo
                return "musicvideos"
            elif item["type"] == "movie" or item["imdbnumber"] or item["mpaa"] or item["trailer"] or item["studio"]:
                return "movies"

        return None

    def widgets( self ):
        # Get widgets
        listitems = []
        
        # Load skin overrides
        tree = DATA._get_overrides( "skin" )
        elems = tree.getroot().findall( "widget" )
        for elem in elems:
            widgetType = None
            widgetPath = None
            widgetTarget = None
            widgetIcon = ""
            widgetName = None
            if "type" in elem.attrib:
                widgetType = elem.attrib.get( "type" )
            if "condition" in elem.attrib:
                if not xbmc.getCondVisibility( elem.attrib.get( "condition" ) ):
                    continue
            if "path" in elem.attrib:
                widgetPath = elem.attrib.get( "path" )
            if "target" in elem.attrib:
                widgetTarget = elem.attrib.get( "target" )
            if "icon" in elem.attrib:
                widgetIcon = elem.attrib.get( "icon" )
            if "name" in elem.attrib:
                widgetName = DATA.local( elem.attrib.get( 'name' ) )[2]

            # Save widgets for button 312
            listitem = self._create( [ elem.text, DATA.local( elem.attrib.get( 'label' ) )[2], "::SCRIPT::32099", {"icon": widgetIcon } ] )
            listitem.setProperty( "widget", elem.text )
            if widgetName is not None:
                listitem.setProperty( "widgetName", widgetName )
            else:
                listitem.setProperty( "widgetName", DATA.local( elem.attrib.get( 'label' ) )[2] )
            if widgetType is not None:
                listitem.setProperty( "widgetType", widgetType )
            if widgetPath is not None:
                listitem.setProperty( "widgetPath", widgetPath )
            if widgetTarget is not None:
                listitem.setProperty( "widgetTarget", widgetTarget )
            listitems.append( listitem )

        self.addToDictionary( "widgets", listitems )
        
    def sortDictionary( self, dictionary ):
        listitems = []
        for key in sorted( dictionary.keys() ): #, reverse = True):
            listitems.append( dictionary[ key ] )
        return listitems
            
    # =============================
    # === ADDON/SOURCE EXPLORER ===
    # =============================
    
    def explorer( self, history, location, label, thumbnail, itemType, isWidget = False ):
        isLibrary = False
        widgetType = None
        addonType = None

        dialogLabel = common.try_decode( label[0] ).replace( "  >", "" )
        if len( label ) != 1:
            dialogLabel = common.try_decode( label[0] ).replace( "  >", "" ) + " - " + common.try_decode( label[ -1 ] ).replace( "  >", "" )

        listings = []
        
        tree = DATA._get_overrides( "skin" )

        # Shortcut to go 'up'
        if len( label ) == 1:
            # This is the root, create a link to go back to selectShortcut
            listitem = self._create( [ "::UP::", "..", "", {} ] )
        else:
            # This isn't the root, create a link to go up the heirachy
            listitem = self._create( [ "::BACK::", "..", "", {} ] )
        listings.append( listitem )
            
        
        # Default action - create shortcut (do not show when we're looking at the special entries from skinhelper service)
        if not "script.skin.helper.service" in location:
            createLabel = "32058"
            if isWidget:
                createLabel = "32100"
            listings.append( self._get_icon_overrides( tree, self._create( ["::CREATE::", createLabel, "", {}] ), "" ) )
                
        common.log( "Getting %s - %s" %( dialogLabel, common.try_decode( location ) ) )
            
        # Show a waiting dialog, then get the listings for the directory
        dialog = xbmcgui.DialogProgress()
        dialog.create( dialogLabel, LANGUAGE( 32063 ) )
        
        #we retrieve a whole bunch of properties, needed to guess the content type properly
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album", "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"], "directory": "' + location + '", "media": "files" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files']:
            json_result = json_response['result']['files']
            
            for item in json_result:
                # Handle numeric labels
                altLabel = item[ "label" ]
                if item[ "label" ].isnumeric():
                    altLabel = "$NUMBER[" + item[ "label" ] + "]"
                if location.startswith( "library://" ):
                    # Process this as a library node
                    isLibrary = True
                    if widgetType is None:
                        widgetType = NODE.get_mediaType( location )

                    if itemType == "32014":
                        # Video node
                        windowID = "Videos"
                        if widgetType == "unknown":
                            widgetType = "video"
                        widgetTarget = "videos"
                    else:
                        # Audio node
                        windowID = "Music"
                        if widgetType == "unknown":
                            widgetType = "audio"
                        widgetTarget = "music"

                    if item[ "filetype" ] == "directory":
                        thumb = None
                        if item[ "thumbnail" ] is not "":
                            thumb = item[ "thumbnail" ]
                            
                        listitem = self._create( [ "ActivateWindow(%s,%s,return)" %( windowID, item[ "file" ] ), altLabel, "", {"icon": "DefaultFolder.png", "thumb": thumb} ] )

                        if item[ "file" ].endswith( ".xml/" ) and NODE.isGrouped( item[ "file" ] ):
                            listitem = self._create( [ item[ "file" ], "%s  >" %( item[ "label" ] ), "", {"icon": "DefaultFolder.png", "thumb": thumb} ] )

                        # Add widget properties
                        widgetName = common.try_decode(label[0]).replace( "  >", "" ) + " - " + item[ "label" ]
                        listitem.setProperty( "widget", "Library" )
                        listitem.setProperty( "widgetName", widgetName )
                        listitem.setProperty( "widgetType", widgetType )
                        listitem.setProperty( "widgetTarget", widgetTarget )
                        listitem.setProperty( "widgetPath", item[ "file" ] )

                        listings.append( self._get_icon_overrides( tree, listitem, "" ) )
                
                #some special code for smart shortcuts in script.skin.helper.service
                elif item.get("title",None) == "smartshortcut":

                    smartShortCutsData = eval(item.get("mpaa"))                  
                    thumb = smartShortCutsData["background"]
                    
                    listitem = self._create( [ item[ "file" ], altLabel, "", {"icon": item.get("icon"), "thumb": thumb} ] )
                    # add all passed properties to the gui to set default background, widget etc.
                    properties = []
                    for key, value in smartShortCutsData.iteritems():
                        properties.append( [key, value ] )
                    listitem.setProperty( "smartShortcutProperties", repr( properties ) )
                    listitem.setProperty( "untranslatedIcon", thumb )
                    listitem.setProperty( "widget", smartShortCutsData.get("widget","Addon") )
                    listitem.setProperty( "widgetName", item["label"] )
                    listitem.setProperty( "widgetType", smartShortCutsData["type"] )
                    if smartShortCutsData["type"] == "music" or smartShortCutsData["type"] == "artists" or smartShortCutsData["type"] == "albums" or smartShortCutsData["type"] == "songs":
                        listitem.setProperty( "widgetTarget", "music" )
                    else:
                        listitem.setProperty( "widgetTarget", "videos" )
                    listitem.setProperty( "widgetPath", smartShortCutsData["list"] )
                    listings.append( self._get_icon_overrides( tree, listitem, "" ) )
                    
                else:
                    # Process this as a plugin
                    if item["filetype"] == "directory":
                        thumb = None
                        if item[ "thumbnail" ] is not "":
                            thumb = item[ "thumbnail" ]
                        listitem = self._create( [item[ "file" ], item[ "label" ] + "  >", "", {"icon": "DefaultFolder.png", "thumb": thumb} ] )
                        listings.append( self._get_icon_overrides( tree, listitem, "" ) )
                    else:
                        contentType = self.detectPluginContent( item )
                        if contentType is not None:
                            if addonType is not None:
                                addonType = contentType
                            else:
                                if addonType != contentType and addonType != "mixed":
                                    addonType = "mixed"
            
        # Close progress dialog
        dialog.close()

        # Show select dialog
        getMore = self._allow_install_widget_provider( location, isWidget )
        w = ShowDialog( "DialogSelect.xml", CWD, listing=listings, windowtitle=dialogLabel, getmore=getMore )
        w.doModal()
        selectedItem = w.result
        del w

        if selectedItem == -2:
            # Get more button
            common.log( "Selected get more button" )
            return self._explorer_install_widget_provider( history, history[ len( history ) -1 ], label, thumbnail, itemType, isWidget )
        
        elif selectedItem != -1:
            selectedAction = listings[ selectedItem ].getProperty( "path" )
            if selectedAction == "::UP::":
                # User wants to go out of explorer, back to selectShortcut
                listitem = xbmcgui.ListItem( label="back" )
                listitem.setProperty( "path", "::UP::" )

                return listitem
            if selectedAction == "::CREATE::":
                # User has chosen the shortcut they want

                # Localize strings
                localItemType = DATA.local( itemType )[2]
                
                # Create a listitem
                listitem = xbmcgui.ListItem(label=label[ len( label ) - 1 ].replace( "  >", "" ), label2=localItemType, iconImage="DefaultShortcut.png", thumbnailImage=thumbnail[ len( thumbnail ) - 1 ])
                
                # Build the action
                if itemType in [ "32010", "32014", "32069" ]:
                    action = 'ActivateWindow(Videos,"' + location + '",return)'
                    listitem.setProperty( "windowID", "Videos" )
                    listitem.setProperty( "widgetType", "videos" )

                    # Add widget details
                    if isLibrary:
                        listitem.setProperty( "widget", "Library" )
                        widgetType = NODE.get_mediaType( location )
                        if widgetType != "unknown":
                            listitem.setProperty( "widgetType", widgetType )
                    else:
                        listitem.setProperty( "widget", "Addon" )

                    if addonType is not None:
                        listitem.setProperty( "widgetType", addonType)

                    listitem.setProperty( "widgetTarget", "videos" )
                    listitem.setProperty( "widgetName", dialogLabel )
                    listitem.setProperty( "widgetPath", location )

                elif itemType in [ "32011", "32019", "32073" ]:
                    action = 'ActivateWindow(Music,"' + location + '",return)'
                    listitem.setProperty( "windowID", "Music" )

                    # Add widget details
                    listitem.setProperty( "widgetType", "audio" )
                    if isLibrary:
                        listitem.setProperty( "widget", "Library" )
                        widgetType = NODE.get_mediaType( location )
                        if widgetType != "unknown":
                            listitem.setProperty( "widgetType", widgetType )
                    else:
                        listitem.setProperty( "widget", "Addon" )
                    if addonType is not None:
                        listitem.setProperty( "widgetType", addonType)
                    
                    listitem.setProperty( "widgetTarget", "music" )
                    listitem.setProperty( "widgetName", dialogLabel )
                    listitem.setProperty( "widgetPath", location )

                elif itemType in [ "32012", "32089" ]:
                    action = 'ActivateWindow(Pictures,"' + location + '",return)'
                    listitem.setProperty( "windowID", "Pictures" )

                    # Add widget details
                    listitem.setProperty( "widget", "Addon" )
                    listitem.setProperty( "widgetType", "picture" )
                    listitem.setProperty( "widgetTarget", "pictures" )
                    listitem.setProperty( "widgetName", dialogLabel )
                    listitem.setProperty( "widgetPath", location )
                    
                elif itemType == "32009":
                    action = 'ActivateWindow(Programs,"' + location + '",return)'
                    listitem.setProperty( "windowID", "Programs" )

                    # Add widget details
                    listitem.setProperty( "widget", "Addon" )
                    listitem.setProperty( "widgetType", "program" )
                    listitem.setProperty( "widgetTarget", "programs" )
                    listitem.setProperty( "widgetName", dialogLabel )
                    listitem.setProperty( "widgetPath", location )

                elif itemType == "15016":
                    action = 'ActivateWindow(Games,"' + location + '",return)'
                    listitem.setProperty( "windowID", "Games" )

                    # Add widget details
                    listitem.setProperty( "widget", "Addon" )
                    listitem.setProperty( "widgetType", "games" )
                    listitem.setProperty( "widgetTarget", "games" )
                    listitem.setProperty( "widgetName", dialogLabel )
                    listitem.setProperty( "widgetPath", location )

                else:
                    action = "RunAddon(" + location + ")"

                listitem.setProperty( "path", action )
                listitem.setProperty( "displayPath", action )
                listitem.setProperty( "shortcutType", itemType )
                listitem.setProperty( "icon", "DefaultShortcut.png" )
                if thumbnail[ len( thumbnail ) -1 ] == "":
                    listitem.setProperty( "thumbnail", thumbnail[ 0 ] )
                else:
                    listitem.setProperty( "thumbnail", thumbnail[ len( thumbnail ) - 1 ] )
                listitem.setProperty( "location", location )
                
                return listitem
                
            elif selectedAction == "::BACK::":
                # User is going up the heirarchy, remove current level and re-call this function
                history.pop()
                label.pop()
                thumbnail.pop()
                return self.explorer( history, history[ len( history ) -1 ], label, thumbnail, itemType, isWidget = isWidget )
                
            elif selectedAction.startswith( "ActivateWindow(" ) or selectedAction.startswith( "$INFO" ):
                # The user wants to create a shortcut to a specific shortcut listed
                listitem = listings[ selectedItem ]

                # Add widget details
                if isLibrary:
                    widgetType = NODE.get_mediaType( listitem.getProperty( "widgetPath" ) )
                    if widgetType != "unknown":
                        listitem.setProperty( "widgetType", widgetType )

                return listitem
                
            else:
                # User has chosen a sub-level to display, add details and re-call this function
                history.append( selectedAction )
                label.append( listings[ selectedItem ].getLabel() )
                thumbnail.append( listings[ selectedItem ].getProperty( "thumbnail" ) )
                return self.explorer( history, selectedAction, label, thumbnail, itemType, isWidget = isWidget )


    # ================================
    # === INSTALL WIDGET PROVIDERS ===
    # ================================

    def _explorer_install_widget_provider( self, history, location, label, thumbnail, itemType, isWidget ):
        # CALLED FROM EXPLORER FUNCTION
        # The user has clicked the 'Get More...' button to install additional widget providers
        providerList = []
        providerLabel = []

        # Get widget providers available for install
        for widgetProvider in self.widgetProviders:
            if widgetProvider[ 1 ] is None or xbmc.getCondVisibility( widgetProvider[ 1 ] ):
                if not xbmc.getCondVisibility( "System.HasAddon(%s)" %( widgetProvider[ 0 ] ) ):
                    providerList.append( widgetProvider[ 0 ] )
                    providerLabel.append( widgetProvider[ 2 ] )

        # Ask user to select widget provider to install
        selectedProvider = xbmcgui.Dialog().select( LANGUAGE(32106), providerLabel )

        if selectedProvider != -1:
            # User has selected a widget provider for us to install
            self._install_widget_provider( providerList[ selectedProvider ] )

        # Return to where we were
        return self.explorer( history, history[ len( history ) -1 ], label, thumbnail, itemType, isWidget = isWidget )

    def _select_install_widget_provider( self, group, grouping, custom, showNone, currentAction ):
        # CALLED FROM SELECT FUNCTION
        # The user has clicked the 'Get More...' button to install additional widget providers
        providerList = []
        providerLabel = []

        # Get widget providers available for install
        for widgetProvider in self.widgetProviders:
            if widgetProvider[ 1 ] is None or xbmc.getCondVisibility( widgetProvider[ 1 ] ):
                if not xbmc.getCondVisibility( "System.HasAddon(%s)" %( widgetProvider[ 0 ] ) ):
                    providerList.append( widgetProvider[ 0 ] )
                    providerLabel.append( widgetProvider[ 2 ] )

        # Ask user to select widget provider to install
        selectedProvider = xbmcgui.Dialog().select( LANGUAGE(32106), providerLabel )

        if selectedProvider != -1:
            # User has selected a widget provider for us to install
            self._install_widget_provider( providerList[ selectedProvider ] )

        # Return to where we were
        return self.selectShortcut( group = group, grouping = grouping, custom = custom, showNone = showNone, currentAction = currentAction )

    def _allow_install_widget_provider( self, location, isWidget, nodeAllows = None ):
        # This function checks whether the 'Get More...' button should be enabled to install
        # additional widget providers

        # Check we're browsing widgets
        if not isWidget:
            return False

        # Check whether we're in skin.helper.service's widgets
        if location is not None and ("script.skin.helper.service" not in location or self.skinhelperWidgetInstall == False):
            return False

        # OR check whether node has enabled widget browsing
        if nodeAllows is not None and nodeAllows == False:
            return False

        # Check whether the user has the various widget providers installed
        for widgetProvider in self.widgetProviders:
            if widgetProvider[ 1 ] is None or xbmc.getCondVisibility( widgetProvider[ 1 ] ):
                if not xbmc.getCondVisibility( "System.HasAddon(%s)" %( widgetProvider[ 0 ] ) ):
                    # The user doesn't have this widget provider installed
                    return True

        # User has all widget providers installed
        return False

    def _install_widget_provider( self, provider ):
        # Prepare
        executeAndObserve = ("InstallAddon(%s)", "DialogConfirm.xml", "DialogConfirm.xml" )

        # Begin install
        xbmc.executebuiltin( executeAndObserve[ 0 ] %( provider ) )

        # Stage 1 - Wait for user to agree to installation
        if xbmc.Monitor().waitForAbort(0.5):
            return
        while xbmc.getCondVisibility( "Window.IsActive(%s)" %( executeAndObserve[ 1 ] ) ):
            if xbmc.Monitor().waitForAbort(0.5):
                return

        # Stage 2 - progress dialog
        if xbmc.Monitor().waitForAbort(0.5):
            return
        while xbmc.getCondVisibility( "Window.IsActive(%s)" %( executeAndObserve[ 2 ] ) ):
            if xbmc.Monitor().waitForAbort(0.5):
                return

    def getImagesFromVfsPath(self, path):
        #this gets images from a vfs path to be used as backgrounds or icons
        images = []
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "art", "file", "fanart"], "directory": "' + path + '", "media": "files" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files']:
            json_result = json_response['result']['files']
            for item in json_result:
                label = item["label"]
                image = None
                if item.has_key("art"):
                    if item["art"].has_key("fanart"):
                        image = item["art"]["fanart"]
                if item.get("file",None).lower().endswith(".jpg") or item.get("file",None).lower().endswith(".png"):
                    image = item["file"]
                    label = label.replace(".jpg","").replace(".png","")
                if image:
                    image = urllib.unquote(image).decode('utf8')
                    if "$INFO" in image:
                        image = image.replace("image://","")
                        if image.endswith("/"):
                            image = image[:-1]
                    images.append( [image, label ] )
        return images

# =====================================
# === COMMON SELECT SHORTCUT METHOD ===
# =====================================

    def selectShortcut( self, group = "", custom = False, availableShortcuts = None, windowTitle = None, showNone = False, currentAction = "", grouping = None ):
        # This function allows the user to select a shortcut

        isWidget = False
        if grouping == "widget":
            isWidget = True
        
        if availableShortcuts is None:
            nodes = self.retrieveGroup( group, grouping = grouping )
            availableShortcuts = nodes[1]
            windowTitle = nodes[0]
        else:
            availableShortcuts = self.checkForFolder( availableShortcuts )
            
        if showNone is not False and group == "":
            availableShortcuts.insert( 0, self._create(["::NONE::", LANGUAGE(32053), "", {"icon":"DefaultAddonNone.png"}] ) )
            
        if custom is not False and group == "":
            availableShortcuts.append( self._create(["||CUSTOM||", LANGUAGE(32024), "", {}] ) )

        if group != "":
            # Add a link to go 'up'
            availableShortcuts.insert( 0, self._create( ["::BACK::", "..", "", {}] ) )

        # Show select dialog
        getMore = self._allow_install_widget_provider( None, isWidget, self.allowWidgetInstall )
        w = ShowDialog( "DialogSelect.xml", CWD, listing=availableShortcuts, windowtitle=windowTitle )
        w.doModal()
        number = w.result
        del w
        
        if number == -2:
            # Get more button
            common.log( "Selected get more button" )
            return self._select_install_widget_provider( group, grouping, custom, showNone, currentAction )

        if number != -1:
            selectedShortcut = availableShortcuts[ number ]
            path = selectedShortcut.getProperty( "Path" )
            if path.startswith( "::BACK::" ):
                # Go back up
                if "," in group:
                    # Remove last level from group
                    newGroup = group.rsplit( ",", 1 )[ 0 ]
                else:
                    # We're only one level in, so we'll just clear the group
                    newGroup = ""
                # Recall this function
                return self.selectShortcut( group = newGroup, grouping = grouping, custom = custom, showNone = showNone, currentAction = currentAction )
            if path.startswith( "||NODE||" ):
                if group == "":
                    group = path.replace( "||NODE||", "" )
                else:
                    group = group + "," + path.replace( "||NODE||", "" )
                return self.selectShortcut( group = group, grouping = grouping, custom = custom, showNone = showNone, currentAction = currentAction )
            elif path.startswith( "||BROWSE||" ):
                selectedShortcut = self.explorer( ["plugin://" + path.replace( "||BROWSE||", "" )], "plugin://" + path.replace( "||BROWSE||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], selectedShortcut.getProperty("shortcutType"), isWidget = isWidget )
                # Convert backslashes to double-backslashes (windows fix)
                if selectedShortcut is not None:
                    newAction = selectedShortcut.getProperty( "Path" )
                    newAction = newAction.replace( "\\", "\\\\" )
                    selectedShortcut.setProperty( "Path", newAction )
                    selectedShortcut.setProperty( "displayPath", newAction )
            elif path.startswith( "||VIDEO||" ):
                # Video node
                selectedShortcut = self.explorer( [ path.replace( "||VIDEO||", "" )], path.replace( "||VIDEO||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], "32014", isWidget = isWidget )
                # Convert backslashes to double-backslashes (windows fix)
                if selectedShortcut is not None:
                    newAction = selectedShortcut.getProperty( "Path" )
                    newAction = newAction.replace( "\\", "\\\\" )
                    selectedShortcut.setProperty( "Path", newAction )
                    selectedShortcut.setProperty( "displayPath", newAction )
            elif path.startswith( "||AUDIO||" ):
                # Audio node
                selectedShortcut = self.explorer( [ path.replace( "||AUDIO||", "" )], path.replace( "||AUDIO||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], "32019", isWidget = isWidget )
                # Convert backslashes to double-backslashes (windows fix)
                if selectedShortcut is not None:
                    newAction = selectedShortcut.getProperty( "Path" )
                    newAction = newAction.replace( "\\", "\\\\" )
                    selectedShortcut.setProperty( "Path", newAction )
                    selectedShortcut.setProperty( "displayPath", newAction )
            elif path == "||UPNP||":
                selectedShortcut = self.explorer( ["upnp://"], "upnp://", [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], selectedShortcut.getProperty("shortcutType"), isWidget = isWidget )
                path = selectedShortcut.getProperty( "Path" )
            elif path.startswith( "||SOURCE||" ):
                selectedShortcut = self.explorer( [path.replace( "||SOURCE||", "" )], path.replace( "||SOURCE||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], selectedShortcut.getProperty("shortcutType"), isWidget = isWidget )
                if selectedShortcut is None or "upnp://" in selectedShortcut.getProperty( "Path" ):
                    return selectedShortcut
                if isWidget:
                    # Set widget to 'source'
                    selectedShortcut.setProperty( "widget", "source" )
                else:
                    # Displaying source - escape all backslashes for Windows
                    selectedShortcut.setProperty( "Path", selectedShortcut.getProperty( "Path" ).replace( "\\", "\\\\" ) )
                    selectedShortcut.setProperty( "displayPath", selectedShortcut.getProperty( "Path" ).replace( "\\", "\\\\" ) )
            elif path.startswith( "::PLAYLIST" ):
                common.log( "Selected playlist" )
                if isWidget:
                    # Return actionShow as chosenPath
                    selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-show" ) )
                elif not ">" in path or "Videos" in path:
                    # Give the user the choice of playing or displaying the playlist
                    dialog = xbmcgui.Dialog()
                    userchoice = dialog.yesno( LANGUAGE( 32040 ), LANGUAGE( 32060 ), "", "", LANGUAGE( 32061 ), LANGUAGE( 32062 ) )
                    # False: Display
                    # True: Play
                    if not userchoice:
                        selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-show" ) )
                    else:
                        selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-play" ) )
                elif ">" in path:
                    # Give the user the choice of playing, displaying or party more for the playlist
                    dialog = xbmcgui.Dialog()
                    userchoice = dialog.select( LANGUAGE( 32060 ), [ LANGUAGE( 32061 ), LANGUAGE( 32062 ), xbmc.getLocalizedString( 589 ) ] )
                    # 0 - Display
                    # 1 - Play
                    # 2 - Party mode
                    if not userchoice or userchoice == 0:
                        selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-show" ) )
                    elif userchoice == 1:
                        selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-play" ) )
                    else:
                        selectedShortcut.setProperty( "chosenPath", selectedShortcut.getProperty( "action-party" ) )

            elif path.startswith ( "::INSTALL::" ):
                # Try to automatically install an addon
                self._install_widget_provider( path.replace( "::INSTALL::", "" ) )

                # Re-call this function
                return self.selectShortcut( group = group, grouping = grouping, custom = custom, showNone = showNone, currentAction = currentAction )

                   
            elif path == "||CUSTOM||":
                # Let the user type a command
                keyboard = xbmc.Keyboard( currentAction, LANGUAGE(32027), False )
                keyboard.doModal()
                
                if ( keyboard.isConfirmed() ):
                    action = keyboard.getText()
                    if action != "":
                        # Create a really simple listitem to return
                        selectedShortcut = xbmcgui.ListItem( None, LANGUAGE(32024) )
                        selectedShortcut.setProperty( "Path", action )
                        selectedShortcut.setProperty( "custom", "true" )
                    else:
                        selectedShortcut = None
                            
                else:
                    selectedShortcut = None
                    
            elif path == "::NONE::":
                # Create a really simple listitem to return
                selectedShortcut = xbmcgui.ListItem( "::NONE::" )

            # Check that explorer hasn't sent us back here
            if selectedShortcut is not None and selectedShortcut.getProperty( "path" ) == "::UP::":
                return self.selectShortcut( group = group, custom = custom, availableShortcuts = None, windowTitle = windowTitle, showNone = showNone, grouping = grouping, currentAction = currentAction )

            return selectedShortcut
        else:
            return None

# ==============================
# === WIDGET RELOAD FUNCTION ===
# ==============================

    # With gui 312, we're finding a number of plugins aren't returning updated content after media is played. This function adds
    # a widgetReload property - managed by Skin Helper Service - to plugins to help display updated content

    def addWidgetReload( self, widgetPath ):
        if "plugin://" not in widgetPath or "reload=" in widgetPath.lower() or "script.extendedinfo" in widgetPath.lower():
            # Not a plugin, or already has a reload parameter
            # Also return on Extended Info, as it doesn't like its parameters to be altered
            return widgetPath

        # Depending whether it already has additional components or not, we may need to use a ? or a & to extend the path
        # with the new reload parameter
        reloadParameter = "?"
        if "?" in widgetPath:
            reloadParameter = "&"

        # And return it all
        return "%s%sreload=$INFO[Window(Home).Property(widgetreload)]" %( widgetPath, reloadParameter )

# ============================
# === PRETTY SELECT DIALOG ===
# ============================
            
class ShowDialog( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.listing = kwargs.get( "listing" )
        self.windowtitle = kwargs.get( "windowtitle" )
        self.getmore = kwargs.get( "getmore" )
        self.result = -1

    def onInit(self):
        try:
            self.fav_list = self.getControl(6)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.fav_list = self.getControl(3)

        if self.getmore == True:
            self.getControl(5).setLabel(xbmc.getLocalizedString(21452))
        else:
            self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)

        try:
            self.getControl(7).setLabel(xbmc.getLocalizedString(222))
        except:
            common.log( "Unable to set label for control 7" )

        for item in self.listing :
            listitem = xbmcgui.ListItem(label=item.getLabel(), label2=item.getLabel2(), iconImage=item.getProperty( "icon" ), thumbnailImage=item.getProperty( "thumbnail" ))
            listitem.setProperty( "Addon.Summary", item.getLabel2() )
            self.fav_list.addItem( listitem )

        self.setFocus(self.fav_list)

    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, controlID):
        if controlID == 5:
            self.result = -2
        elif controlID == 6 or controlID == 3:
            num = self.fav_list.getSelectedPosition()
            self.result = num
        else:
            self.result = -1

        self.close()

    def onFocus(self, controlID):
        pass
