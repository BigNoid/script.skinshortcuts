# coding=utf-8
import os, sys, datetime, unicodedata
import xbmc, xbmcgui, xbmcvfs, urllib
import xml.etree.ElementTree as xmltree
import thread
from xml.dom.minidom import parse
from xml.sax.saxutils import escape as escapeXML
from traceback import print_exc
from unidecode import unidecode

import datafunctions
DATA = datafunctions.DataFunctions()

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = sys.modules[ "__main__" ].__addon__
__addonid__      = sys.modules[ "__main__" ].__addonid__
__addonversion__ = sys.modules[ "__main__" ].__addonversion__
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')
__defaultpath__  = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'shortcuts').encode("utf-8") ).decode("utf-8")
__language__     = sys.modules[ "__main__" ].__language__
__cwd__          = sys.modules[ "__main__" ].__cwd__

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

class LibraryFunctions():
    def __init__( self, *args, **kwargs ):
        
        # values to mark whether data from different areas of the library have been loaded
        self.loadedCommon = False
        self.loadedMoreCommands = False
        self.loadedVideoLibrary = False
        self.loadedMusicLibrary = False
        self.loadedLibrarySources = False
        self.loadedPVRLibrary = False
        self.loadedPlaylists = False
        self.loadedAddOns = False
        self.loadedFavourites = False
        self.loadedUPNP = False
        
        self.widgetPlaylistsList = []
        
        # Empty dictionary for different shortcut types
        self.dictionaryGroupings = {"common":None, "commands":None, "video":None, "movie":None, "tvshow":None, "musicvideo":None, "customvideonode":None, "videosources":None, "pvr":None, "music":None, "musicsources":None, "playlist-video":None, "playlist-audio":None, "addon-program":None, "addon-video":None, "addon-audio":None, "addon-image":None, "favourite":None }
        
        
        
    def loadLibrary( self ):
        # Load all library data, for use with threading
        self.common()
        self.more()
        self.videolibrary()
        self.musiclibrary()
        self.pvrlibrary()
        self.librarysources()
        self.playlists()
        self.addons()                
        self.favourites()
        
        # Do a JSON query for upnp sources (so that they'll show first time the user asks to see them)
        if self.loadedUPNP == False:
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "upnp://", "media": "files" } }')
            self.loadedUPNP = True

        
    def retrieveGroup( self, group, flat = True ):
        trees = [DATA._get_overrides_skin(), DATA._get_overrides_script()]
        nodes = None
        for tree in trees:
            if tree is not None:
                if flat:
                    nodes = tree.find( "flatgroupings" ).findall( "node" )
                else:
                    nodes = tree.find( "groupings" )
            if nodes is not None:
                break                
                
        if nodes is None:
            return [ "Error", [] ]
            
        returnList = []
        
        if flat:
            # Flat groupings
            #groupings = tree.find( "flatgroupings" )
            #nodes = groupings.findall( "node" )
            count = 0
            # Cycle through nodes till we find the one specified
            for node in nodes:
                count += 1
                if count == group:
                    # We found it :)
                    return( node.attrib.get( "label" ), self.buildNodeListing( node, True ) )
                    log( repr( node ) )
                    for subnode in node:
                        if subnode.tag == "content":
                            returnList = returnList + self.retrieveContent( subnode.text )
                        if subnode.tag == "shortcut":
                            returnList.append( self._create( [subnode.text, subnode.attrib.get( "label" ), subnode.attrib.get( "type" ), subnode.attrib.get( "icon" )] ) )

                    return [node.attrib.get( "label" ), returnList]
                    
            return ["Error", []]
            
        else:
            # Heirachical groupings
            #nodes = tree.find( "groupings" )
            if group == "":
                # We're going to get the root nodes
                return [ __language__(32048), self.buildNodeListing( nodes, False ) ]
            else:
                groups = group.split( "," )
                
                nodes = [ "", nodes ]
                for groupNum in groups:
                    nodes = self.getNode( nodes[1], int( groupNum ) )
                    
                return [ nodes[0], self.buildNodeListing( nodes[1], False ) ]
                        
                        
    def getNode( self, tree, number ):
        count = 0
        for subnode in tree:
            count += 1
            if count == number:
                return [subnode.attrib.get( "label" ), subnode]
                
    def buildNodeListing( self, nodes, flat ):
        returnList = []
        count = 0
        for node in nodes:
            count += 1
            if node.tag == "content":
                returnList = returnList + self.retrieveContent( node.text )
            if node.tag == "shortcut":
                returnList.append( self._create( [node.text, node.attrib.get( "label" ), node.attrib.get( "type" ), node.attrib.get( "icon" )] ) )
            if node.tag == "node" and flat == False:
                returnList.append( self._create( ["||NODE||" + str( count ), node.attrib.get( "label" ), "", "DefaultFolder.png"] ) )
                
        return returnList
                
    def retrieveContent( self, content ):
        if content == "upnp-video":
            return [ self._create(["||UPNP||", "::SCRIPT::32070", "::SCRIPT::32014", ""]) ]
        elif content == "upnp-music":
            return [ self._create(["||UPNP||", "::SCRIPT::32070", "::SCRIPT::32019", ""]) ]
            
        elif self.dictionaryGroupings[ content ] is None:
            # The data hasn't been loaded yet
            return self.loadGrouping( content )
        else:
            returnInfo = self.dictionaryGroupings[ content ]
            if returnInfo is not None:
                return returnInfo
            else:
                return []
                
    def addToDictionary( self, group, content ):
        # This function adds content to the dictionaryGroupings - including
        # adding any skin-provided shortcuts to the group
        tree = DATA._get_overrides_skin()
        if tree is None:
            # There are no overrides to check for extra shortcuts
            self.dictionaryGroupings[ group ] = content
            return
            
        for elem in tree.findall( "shortcut" ):
            if "grouping" in elem.attrib:
                if group == elem.attrib.get( "grouping" ):
                    # We want to add this shortcut
                    label = elem.attrib.get( "label" )
                    type = elem.attrib.get( "type" )
                    thumb = elem.attrib.get( "thumbnail" )
                    
                    action = elem.text
                    
                    if label.isdigit():
                        label = "::LOCAL::" + label
                        
                    if type is None:
                        type = "::SCRIPT::32024"
                    elif type.isdigit():
                        type = "::LOCAL::" + type
                        
                    if thumb is None:
                        thumb = ""

                    listitem = self._create( [action, label, type, thumb] )
                    
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
                
                action = elem.text
                
                if label.isdigit():
                    label = "::LOCAL::" + label
                    
                if type is None:
                    type = "::SCRIPT::32024"
                elif type.isdigit():
                    type = "::LOCAL::" + type
                    
                if type is None or type == "":
                    type = "Skin Provided"
                    
                if thumb is None:
                    thumb = ""

                listitem = self._create( [action, label, type, thumb] )
                
                if "condition" in elem.attrib:
                    if xbmc.getCondVisibility( elem.attrib.get( "condition" ) ):
                        content.append( listitem )
                else:
                    content.append( listitem )
                    
        self.dictionaryGroupings[ group ] = content

    def loadGrouping( self, content ):
        # We'll be called if the data for a wanted group hasn't been loaded yet
        if content == "common":
            self.common()
        if content  == "commands":
            self.more()
        if content == "video" or content == "movie" or content == "tvshow" or content == "musicvideo" or content == "customvideonode":
            self.videolibrary()
        if content == "videosources" or content == "musicsources":
            self.librarysources()
        if content == "music":
            self.musiclibrary()
        if content == "pvr":
            self.pvrlibrary()
        if content == "playlist-video" or content == "playlist-audio":
            self.playlists()
        if content == "addon-program" or content == "addon-video" or content == "addon-audio" or content == "addon-image":
            self.addons()
        if content == "favourite":
            self.favourites()
            
        # The data has now been loaded, return it
        return self.dictionaryGroupings[ content ]
        
    def flatGroupingsCount( self ):
        # Return how many nodes there are in the the flat grouping
        tree = DATA._get_overrides_script()
        if tree is None:
            return 1
        groupings = tree.find( "flatgroupings" )
        nodes = groupings.findall( "node" )
        count = 0
        for node in nodes:
            count += 1
        return count
        
        
    def selectShortcut( self, group = "", skinLabel = None, skinAction = None, skinType = None, skinThumbnail = None, custom = False ):
        # This function allows the user to select a shortcut, then passes it off to the skin to do with as it will
        
        # If group is empty, start background loading of shortcuts
        if group == "":
            thread.start_new_thread( self.loadLibrary, () )
        
        nodes = self.retrieveGroup( group, False )
        availableShortcuts = nodes[1]
        if custom == True:
            availableShortcuts.append( self._create(["||CUSTOM||", "Custom shortcut", "", ""] ) )
        
        # Check a shortcut is available
        if len( availableShortcuts ) == 0:
            log( "No available shortcuts found" )
            xbmcgui.Dialog().ok( __language__(32064), __language__(32065) )
            return
                                
        w = ShowDialog( "DialogSelect.xml", __cwd__, listing=availableShortcuts, windowtitle=nodes[0] )
        w.doModal()
        number = w.result
        del w
        
        if number != -1:
            selectedShortcut = availableShortcuts[ number ]
            path = urllib.unquote( selectedShortcut.getProperty( "Path" ) )
            if path.startswith( "||NODE||" ):
                if group == "":
                    group = path.replace( "||NODE||", "" )
                else:
                    group = group + "," + path.replace( "||NODE||", "" )
                return self.selectShortcut( group = group, skinLabel = skinLabel, skinAction = skinAction, skinType = skinType, skinThumbnail = skinThumbnail )
            if path.startswith( "||BROWSE||" ):
                selectedShortcut = self.explorer( ["plugin://" + path.replace( "||BROWSE||", "" )], "plugin://" + path.replace( "||BROWSE||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], [skinLabel, skinAction, skinType, skinThumbnail], selectedShortcut.getProperty("shortcutType") )
                path = urllib.unquote( selectedShortcut.getProperty( "Path" ) )
            elif path == "||UPNP||":
                selectedShortcut = self.explorer( ["upnp://"], "upnp://", [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], [skinLabel, skinAction, skinType, skinThumbnail], selectedShortcut.getProperty("shortcutType")  )
                path = urllib.unquote( selectedShortcut.getProperty( "Path" ) )
            elif path.startswith( "||SOURCE||" ):
                selectedShortcut = self.explorer( [path.replace( "||SOURCE||", "" )], path.replace( "||SOURCE||", "" ), [selectedShortcut.getLabel()], [selectedShortcut.getProperty("thumbnail")], [skinLabel, skinAction, skinType, skinThumbnail], selectedShortcut.getProperty("shortcutType")  )
                path = urllib.unquote( selectedShortcut.getProperty( "Path" ) )
            elif path == "::PLAYLIST::" :
                # Give the user the choice of playing or displaying the playlist
                dialog = xbmcgui.Dialog()
                userchoice = dialog.yesno( __language__( 32040 ), __language__( 32060 ), "", "", __language__( 32061 ), __language__( 32062 ) )
                # False: Display
                # True: Play
                if userchoice == False:
                    selectedShortcut.setProperty( "path", urllib.unquote( selectedShortcut.getProperty( "action-show" ) ) )
                else:
                    selectedShortcut.setProperty( "path", urllib.unquote( selectedShortcut.getProperty( "action-play" ) ) )
                   
            elif path == "||CUSTOM||":
                keyboard = xbmc.Keyboard( "", __language__(32027), False )
                keyboard.doModal()
                
                if ( keyboard.isConfirmed() ):
                    action = keyboard.getText()
                    if action != "":
                        # We're only going to update the action and type properties for this...
                        if skinAction is not None:
                            xbmc.executebuiltin( "Skin.SetString(" + skinAction + "," + action + " )" )
                        if skinType is not None:
                            xbmc.executebuiltin( "Skin.SetString(" + skinType + "," + __language__(32024) + ")" )
                            
                selectedShortcut = None

            if selectedShortcut is None:
                # Nothing was selected in the explorer
                return None
                
            # Set the skin.string properties we've been passed
            if skinLabel is not None:
                xbmc.executebuiltin( "Skin.SetString(" + skinLabel + "," + selectedShortcut.getLabel() + ")" )
            if skinAction is not None:
                xbmc.executebuiltin( "Skin.SetString(" + skinAction + "," + path + " )" )
            if skinType is not None:
                xbmc.executebuiltin( "Skin.SetString(" + skinType + "," + selectedShortcut.getLabel2() + ")" )
            if skinThumbnail is not None:
                xbmc.executebuiltin( "Skin.SetString(" + skinThumbnail + "," + selectedShortcut.getProperty( "thumbnail" ) + ")" )
                
            return selectedShortcut
        else:
            return None

                
    def common( self ):
        if self.loadedCommon == True:
            return True
        elif self.loadedCommon == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedCommon == True:
                    return True
        else:
            # We're going to populate the list
            self.loadedCommon = "Loading"
        
        listitems = []
        log('Listing xbmc common items...')
        
        # Videos, Movies, TV Shows, Live TV, Music, Music Videos, Pictures, Weather, Programs,
        # Play dvd, eject tray
        # Settings, File Manager, Profiles, System Info
        try:
            listitems.append( self._create(["ActivateWindow(Videos)", "::LOCAL::10006", "::SCRIPT::32034", "DefaultVideo.png"]) )
            listitems.append( self._create(["ActivateWindow(Videos,MovieTitles,return)", "::LOCAL::342", "::SCRIPT::32034", "DefaultMovies.png"]) )
            listitems.append( self._create(["ActivateWindow(Videos,TVShowTitles,return)", "::LOCAL::20343", "::SCRIPT::32034", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,34,0 ,13,0)", "::SCRIPT::32022", "::SCRIPT::32034", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindow(Music)", "::LOCAL::10005", "::SCRIPT::32034", "DefaultMusicAlbums.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,MusicVideos,return)", "::LOCAL::20389", "::SCRIPT::32034", "DefaultMusicVideos.png"]) )
            listitems.append( self._create(["ActivateWindow(Pictures)", "::LOCAL::10002", "::SCRIPT::32034", "DefaultPicture.png"]) )
            listitems.append( self._create(["ActivateWindow(Weather)", "::LOCAL::12600", "::SCRIPT::32034", ""]) )
            listitems.append( self._create(["ActivateWindow(Programs,Addons,return)", "::LOCAL::10001", "::SCRIPT::32034", "DefaultProgram.png"]) )

            listitems.append( self._create(["XBMC.PlayDVD()", "::SCRIPT::32032", "::SCRIPT::32034", "DefaultDVDFull.png"]) )
            listitems.append( self._create(["EjectTray()", "::SCRIPT::32033", "::SCRIPT::32034", "DefaultDVDFull.png"]) )
                    
            listitems.append( self._create(["ActivateWindow(Settings)", "::LOCAL::10004", "::SCRIPT::32034", ""]) )
            listitems.append( self._create(["ActivateWindow(FileManager)", "::LOCAL::7", "::SCRIPT::32034", "DefaultFolder.png"]) )
            listitems.append( self._create(["ActivateWindow(Profiles)", "::LOCAL::13200", "::SCRIPT::32034", "UnknownUser.png"]) )
            listitems.append( self._create(["ActivateWindow(SystemInfo)", "::LOCAL::10007", "::SCRIPT::32034", ""]) )
            
            listitems.append( self._create(["ActivateWindow(Favourites)", "::LOCAL::1036", "::SCRIPT::32034", ""]) )
        except:
            log( "Failed to load common XBMC shortcuts" )
            print_exc()
            listitems = []
            
        self.addToDictionary( "common", listitems )
        
        self.loadedCommon = True
        
        return self.loadedCommon
        
    def more( self ):
        if self.loadedMoreCommands == True:
            # The List has already been populated, return it
            return True
        elif self.loadedMoreCommands == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedMoreCommands == True:
                    return True
        else:
            # We're going to populate the list
            self.loadedMoreCommands = "Loading"

        try:
            listitems = []
            log( 'Listing more XBMC commands...' )
            
            listitems.append( self._create(["Reboot", "::LOCAL::13013", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["ShutDown", "::LOCAL::13005", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["PowerDown", "::LOCAL::13016", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["Quit", "::LOCAL::13009", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["Hibernate", "::LOCAL::13010", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["Suspend", "::LOCAL::13011", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["ActivateScreensaver", "::LOCAL::360", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["Minimize", "::LOCAL::13014", "::SCRIPT::32054", ""]) )

            listitems.append( self._create(["Mastermode", "::LOCAL::20045", "::SCRIPT::32054", ""]) )
            
            listitems.append( self._create(["RipCD", "::LOCAL::600", "::SCRIPT::32054", ""]) )
            
            listitems.append( self._create(["UpdateLibrary(video)", "::SCRIPT::32046", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["UpdateLibrary(audio)", "::SCRIPT::32047", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["CleanLibrary(video)", "::SCRIPT::32055", "::SCRIPT::32054", ""]) )
            listitems.append( self._create(["CleanLibrary(audio)", "::SCRIPT::32056", "::SCRIPT::32054", ""]) )
            
            self.addToDictionary( "commands", listitems )
        except:
            log( "Failed to load more XBMC commands" )
            print_exc()
            
        self.loadedMoreCommands = True
        return self.loadedMoreCommands
        
    def videolibrary( self ):
        if self.loadedVideoLibrary == True:
            # The List has already been populated, return it
            return self.loadedVideoLibrary
        elif self.loadedVideoLibrary == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedVideoLibrary == True:
                    return self.loadedVideoLibrary
        else:
            # We're going to populate the list
            self.loadedVideoLibrary = "Loading"
            
        # Try loading custom nodes first
        try:
            if self._parse_videolibrary( "custom" ) == False:
                self._parse_videolibrary( "default" )
        except:
            log( "Failed to load custom video nodes" )
            print_exc()
            try:
                # Try loading default nodes
                self._parse_videolibrary( "default" )
            except:
                # Empty library
                log( "Failed to load default video nodes" )
                print_exc()
                
        self.loadedVideoLibrary = True
        return self.loadedVideoLibrary
        
    def _parse_videolibrary( self, type ):
        videoListItems = []
        movieListItems = []
        tvListItems = []
        musicvideoListItems = []
        customListItems = []
        
        rootdir = os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video" )
        if type == "custom":
            log('Listing custom video nodes...')
        else:
            rootdir = os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", "video" )
            log( "Listing default video nodes..." )
        
        # Check the path exists
        if not os.path.exists( rootdir ):
            log( "No nodes found" )
            return False
            
        # Walk the path
        for root, subdirs, files in os.walk(rootdir):
            nodesVideo = {}
            nodesMovie = {}
            nodesTVShow = {}
            nodesMusicVideo = {}
            nodesCustom = {}
            
            unnumberedNode = 100
            label2 = "::SCRIPT::32014"
            if "index.xml" in files:
                # Parse the XML file to get the type of these nodes
                tree = xmltree.parse( os.path.join( root, "index.xml") )
                label = tree.find( 'label' )
                if label.text.isdigit():
                    label2 = "::LOCAL::" + label.text
                else:
                    label2 = label.text
            
            filesIndex = None
            filesItem = None
            for file in files:
                if not file == "index.xml":
                    # Load the file
                    tree = xmltree.parse( os.path.join( root, file) )
                    
                    # Check for a pretty library link
                    prettyLink = self._pretty_videonode( tree, file )
                    
                    # Create the action for this file
                    if prettyLink == False:
                        path = "ActivateWindow(Videos,library://video/" + os.path.relpath( os.path.join( root, file), rootdir ) + ",return)"
                        path.replace("\\", "/")
                    else:
                        path = "ActivateWindow(Videos," + prettyLink + ",return)"
                        
                    type = self._check_videonode_type( tree )
                    
                    listitem = [path]
                    
                    # Get the label
                    label = tree.find( 'label' )
                    if label is not None:
                        if label.text.isdigit():
                            listitem.append( "::LOCAL::" + label.text )
                        else:
                            listitem.append( label.text )
                    else:
                        listitem.append( "::SCRIPT::32042" )
                        
                    # Add the label2
                    listitem.append( label2 )
                    
                    # Get the icon
                    icon = tree.find( 'icon' )
                    if icon is not None:
                        listitem.append( icon.text )
                    else:
                        listitem.append( "defaultshortcut.png" )
                        
                    # Get the node 'order' value
                    order = tree.getroot()
                    try:
                        if type == "video":
                            nodesVideo[ order.attrib.get( 'order' ) ] = listitem
                        elif type == "Movie":
                            nodesMovie[ order.attrib.get( 'order' ) ] = listitem
                        elif type == "TvShow":
                            nodesTVShow[ order.attrib.get( 'order' ) ] = listitem
                        elif type == "MusicVideo":
                            nodesMusicVideo[ order.attrib.get( 'order' ) ] = listitem
                        else:
                            nodesCustom[ order.attrib.get( 'order' ) ] = listitem
                    except:
                        if type == "video":
                            nodesVideo[ str( unnumberedNode ) ] = listitem
                        elif type == "Movie":
                            nodesMovie[ str( unnumberedNode ) ] = listitem
                        elif type == "TvShow":
                            nodesTVShow[ str( unnumberedNode ) ] = listitem
                        elif type == "MusicVideo":
                            nodesMusicVideo[ str( unnumberedNode ) ] = listitem
                        else:
                            nodesCustom[ order.attrib.get( 'order' ) ] = listitem
                        unnumberedNode = unnumberedNode + 1
                
            filesIndex = None
            filesItem = None
            for key in sorted(nodesVideo.iterkeys()):
                if filesIndex is not None and int( key ) > int( filesIndex ):
                    videoListItems.append( filesItem )
                    filesIndex = None
                videoListItems.append( self._create( nodesVideo[ key ] ) )
            if filesIndex is not None:
                videoListItems.append( filesItem )
                filesIndex = None
                
            filesIndex = None
            filesItem = None    
            for key in sorted(nodesMovie.iterkeys()):
                if filesIndex is not None and int( key ) > int( filesIndex ):
                    movieListItems.append( filesItem )
                    filesIndex = None
                movieListItems.append( self._create( nodesMovie[ key ] ) )
            if filesIndex is not None:
                movieListItems.append( filesItem )
                filesIndex = None
                
            filesIndex = None
            filesItem = None
            for key in sorted(nodesTVShow.iterkeys()):
                if filesIndex is not None and int( key ) > int( filesIndex ):
                    tvListItems.append( filesItem )
                    filesIndex = None
                tvListItems.append( self._create( nodesTVShow[ key ] ) )
            if filesIndex is not None:
                tvListItems.append( filesItem )
                filesIndex = None
                
            filesIndex = None
            filesItem = None
            for key in sorted(nodesMusicVideo.iterkeys()):
                if filesIndex is not None and int( key ) > int( filesIndex ):
                    musicvideoListItems.append( filesItem )
                    filesIndex = None
                musicvideoListItems.append( self._create( nodesMusicVideo[ key ] ) )
            if filesIndex is not None:
                musicvideoListItems.append( filesItem )
                filesIndex = None
                
            filesIndex = None
            filesItem = None
            for key in sorted(nodesCustom.iterkeys()):
                if filesIndex is not None and int( key ) > int( filesIndex ):
                    customListItems.append( filesItem )
                    filesIndex = None
                customListItems.append( self._create( nodesCustom[ key ], False ) )
            if filesIndex is not None:
                customListItems.append( filesItem )
                filesIndex = None
                
        self.addToDictionary( "video", videoListItems )
        self.addToDictionary( "movie", movieListItems )
        self.addToDictionary( "tvshow", tvListItems )
        self.addToDictionary( "musicvideo", musicvideoListItems )
        self.addToDictionary( "customvideonode", customListItems )

        
    def _pretty_videonode( self, tree, filename ):
        # We're going to do lots of matching, to try to figure out the pretty library link
        
        # Root
        if filename == "addons.xml":
            if self._check_videonode( tree, False ):
                return "Addons"
        elif filename == "files.xml":
            if self._check_videonode( tree, False ):
                return "Files"
        # elif filename == "inprogressshows.xml": - Don't know a pretty library link for this...
        elif filename == "playlists.xml":
            if self._check_videonode( tree, False ):
                return "Playlists"
        elif filename == "recentlyaddedepisodes.xml":
            if self._check_videonode( tree, False ):
                return "RecentlyAddedEpisodes"
        elif filename == "recentlyaddedmovies.xml":
            if self._check_videonode( tree, False ):
                return "RecentlyAddedMovies"
        elif filename == "recentlyaddedmusicvideos.xml":
            if self._check_videonode( tree, False ):
                return "RecentlyAddedMusicVideos"
              
        # For the rest, they should all specify a type, so get that first
        shortcutType = self._check_videonode_type( tree )
        if shortcutType != "Custom Node":
            if filename == "actors.xml":    # Movies, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Actors"
            elif filename == "country.xml":   # Movies
                if self._check_videonode( tree, True ):
                    return shortcutType + "Countries"
            elif filename == "directors.xml": # Movies
                if self._check_videonode( tree, True ):
                    return shortcutType + "Directors"
            elif filename == "genres.xml":    # Movies, Music Videos, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Genres"
            elif filename == "sets.xml":      # Movies
                if self._check_videonode( tree, True ):
                    return shortcutType + "Sets"
            elif filename == "studios.xml":   # Movies, Music Videos, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Studios"
            elif filename == "tags.xml":      # Movies, Music Videos, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Tags"
            elif filename == "titles.xml":    # Movies, Music Videos, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Titles"
            elif filename == "years.xml":     # Movies, Music Videos, TV Shows
                if self._check_videonode( tree, True ):
                    return shortcutType + "Years"
            elif filename == "albums.xml":    # Music Videos
                if self._check_videonode( tree, True ):
                    return shortcutType + "Albums"
            elif filename == "artists.xml":   # Music Videos
                if self._check_videonode( tree, True ):
                    return shortcutType + "Artists"
            elif filename == "directors.xml": # Music Videos
                if self._check_videonode( tree, True ):
                    return shortcutType + "Directors"

        # If we get here, we couldn't find a pretty link
        return False
            
    def _check_videonode( self, tree, checkPath ):
        # Check a video node for custom entries
        if checkPath == False:
            if tree.find( 'match' ) is not None or tree.find( 'rule' ) is not None or tree.find( 'limit' ) is not None:
                return False
            else:
                return True
        else:
            if tree.find( 'match' ) is not None or tree.find( 'rule' ) is not None or tree.find( 'limit' ) is not None or tree.find( 'path' ) is not None:
                return False
            else:
                return True
                
    def _check_videonode_type( self, tree ):
        try:
            type = tree.find( 'content' ).text
            if type == "movies":
                return "Movie"
            elif type == "tvshows":
                return "TvShow"
            elif type == "musicvideos":
                return "MusicVideo"
            else:
                return "Custom Node"
        except:
            return "video"
                
    def pvrlibrary( self ):
        if self.loadedPVRLibrary == True:
            # The List has already been populated, return it
            return self.loadedPVRLibrary
        elif self.loadedPVRLibrary == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedPVRLibrary == True:
                    return self.loadedPVRLibrary
        else:
            # We're going to populate the list
            self.loadedPVRLibrary = "Loading"

        try:
            listitems = []
            log('Listing pvr library...')
            
            # PVR
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,32,0 ,11,0)", "::LOCAL::19023", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,33,0 ,12,0)", "::LOCAL::19024", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,31,0 ,10,0)", "::LOCAL::19069", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,34,0 ,13,0)", "::LOCAL::19163", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,35,0 ,14,0)", "::SCRIPT::32023", "::SCRIPT::32017", "DefaultTVShows.png"]) )

            # Test options
            listitems.append( self._create(["PlayPvrTV", "::SCRIPT::32066", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["PlayPvrRadio", "::SCRIPT::32067", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            listitems.append( self._create(["PlayPvr", "::SCRIPT::32068", "::SCRIPT::32017", "DefaultTVShows.png"]) )
            
            self.addToDictionary( "pvr", listitems )
        except:
            log( "Failed to load pvr library" )
            print_exc()

        self.loadedPVRLibrary = True
        return self.loadedPVRLibrary
        
    def musiclibrary( self ):
        if self.loadedMusicLibrary == True:
            # The List has already been populated, return it
            return self.loadedMusicLibrary
        elif self.loadedMusicLibrary == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if loadedMusicLibrary == True:
                    return self.loadedMusicLibrary
        else:
            # We're going to populate the list
            self.loadedMusicLibrary = "Loading"

        try:
            listitems = []
            log('Listing music library...')
                        
            # Music
            listitems.append( self._create(["ActivateWindow(MusicFiles)", "::LOCAL::744", "::SCRIPT::32019", "DefaultFolder.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,MusicLibrary,return)", "::LOCAL::15100", "::SCRIPT::32019", "DefaultFolder.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,MusicVideos,return)", "::LOCAL::20389", "::SCRIPT::32019", "DefaultMusicVideos.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Genres,return)", "::LOCAL::135", "::SCRIPT::32019", "DefaultMusicGenres.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Artists,return)", "::LOCAL::133", "::SCRIPT::32019", "DefaultMusicArtists.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Albums,return)", "::LOCAL::132", "::SCRIPT::32019", "DefaultMusicAlbums.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Songs,return)", "::LOCAL::134", "::SCRIPT::32019", "DefaultMusicSongs.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Years,return)", "::LOCAL::652", "::SCRIPT::32019", "DefaultMusicYears.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Top100,return)", "::LOCAL::271", "::SCRIPT::32019", "DefaultMusicTop100.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Top100Songs,return)", "::LOCAL::10504", "::SCRIPT::32019", "DefaultMusicTop100Songs.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Top100Albums,return)", "::LOCAL::10505", "::SCRIPT::32019", "DefaultMusicTop100Albums.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,RecentlyAddedAlbums,return)", "::LOCAL::359", "::SCRIPT::32019", "DefaultMusicRecentlyAdded.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,RecentlyPlayedAlbums,return)", "::LOCAL::517", "::SCRIPT::32019", "DefaultMusicRecentlyPlayed.png"]) )
            listitems.append( self._create(["ActivateWindow(MusicLibrary,Playlists,return)", "::LOCAL::136", "::SCRIPT::32019", "DefaultMusicPlaylists.png"]) )
            
            # Do a JSON query for upnp sources (so that they'll show first time the user asks to see them)
            if self.loadedUPNP == False:
                json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "upnp://", "media": "files" } }')
                self.loadedUPNP = True
                
            self.addToDictionary( "music", listitems )
        except:
            log( "Failed to load music library" )
            print_exc()

        self.loadedMusicLibrary = True
        return self.loadedMusicLibrary
        
    def _create ( self, item, allowOverrideLabel = True ):
        # Retrieve label
        localLabel = item[1]
        
        if allowOverrideLabel:
            # Check for a replaced label
            replacementLabel = DATA.checkShortcutLabelOverride( item[0] )
            if replacementLabel is not None:
                # Check if it's an integer
                if replacementLabel.isdigit():
                    localLabel = "::LOCAL::" + replacementLabel
                else:
                    localLabel = replacementLabel
        
        # Try localising it
        try:
            if not localLabel.find( "::SCRIPT::" ) == -1:
                displayLabel = __language__(int( localLabel[10:] ) )
            elif not localLabel.find( "::LOCAL::" ) == -1:
                displayLabel = xbmc.getLocalizedString(int( localLabel[9:] ) )
            else:
                displayLabel = localLabel
        except:
            displayLabel = localLabel
            print_exc()
        
        # Create localised label2
        displayLabel2 = item[2]
        try:
            if not item[2].find( "::SCRIPT::" ) == -1:
                displayLabel2 = __language__(int( item[2][10:] ) )
            elif not item[2].find( "::LOCAL::" ) == -1:
                displayLabel2 = xbmc.getLocalizedString(int( item[2][9:] ) )
        except:
            print_exc()
            
        # If this launches our explorer, append a notation to the displayLabel
        if item[0].startswith( "||" ):
            displayLabel = displayLabel + "  [B]>[/B]"
            
        thumbnail = item[3]
        oldthumbnail = None
        if thumbnail == "":
            thumbnail = None
            
        icon = "DefaultShortcut.png"
        oldicon = None
        
        # Check for any skin-provided thumbnail overrides
        tree = DATA._get_overrides_skin()
        if tree is not None:
            for elem in tree.findall( "thumbnail" ):
                if elem.attrib.get( "image" ) is not None:
                    if oldthumbnail is None:
                        if elem.attrib.get( "image" ) == thumbnail:
                            oldthumbnail = thumbnail
                            thumbnail = elem.text
                    if oldicon is None:
                        if elem.attrib.get( "image" ) == icon:
                            oldicon = icon
                            icon = elem.text
                    
            
        # Build listitem
        listitem = xbmcgui.ListItem(label=displayLabel, label2=displayLabel2, iconImage=icon, thumbnailImage=thumbnail)
        listitem.setProperty( "path", urllib.quote( item[0] ) )
        listitem.setProperty( "localizedString", localLabel )
        listitem.setProperty( "shortcutType", item[2] )
        listitem.setProperty( "icon", icon )
        listitem.setProperty( "thumbnail", thumbnail)
        
        if oldthumbnail is not None:
            listitem.setProperty( "original-thumbnail", oldthumbnail )
        if oldicon is not None:
            listitem.setProperty( "original-icon", oldicon )
        
        return( listitem )
        
    def librarysources( self ):
        if self.loadedLibrarySources == True:
            # The List has already been populated, return it
            return self.loadedLibrarySources
        elif self.loadedLibrarySources == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedLibrarySources == True:
                    return self.loadedLibrarySources
        else:
            # We're going to populate the list
            self.loadedLibrarySources = "Loading"
            
        # Add video sources
        listitems = []
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetSources", "params": { "media": "video" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('sources') and json_response['result']['sources'] is not None:
            for item in json_response['result']['sources']:
                log( "Added video source: " + item[ 'label' ] )
                listitems.append( self._create(["||SOURCE||" + item['file'], item['label'], "::SCRIPT::32069", "DefaultFolder.png" ]) )
        self.addToDictionary( "videosources", listitems )
                
        # Add audio sources
        listitems = []
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetSources", "params": { "media": "music" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('sources') and json_response['result']['sources'] is not None:
            for item in json_response['result']['sources']:
                log( "Added audio source: " + item[ 'label' ] )
                listitems.append( self._create(["||SOURCE||" + item['file'], item['label'], "::SCRIPT::32073", "DefaultFolder.png" ]) )
        self.addToDictionary( "musicsources", listitems )
        
        self.loadedLibrarySources = True
        return self.loadedLibrarySources
            
    def playlists( self ):
        if self.loadedPlaylists == True:
            # The List has already been populated, return it
            return self.loadedPlaylists
        elif self.loadedPlaylists == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedPlaylists == True:
                    return self.loadedPlaylists
        else:
            # We're going to populate the list
            self.loadedPlaylists = "Loading"
            
        try:
            audiolist = []
            videolist = []
            
            log('Loading playlists...')
            paths = [['special://profile/playlists/video/','32004','VideoLibrary'], ['special://profile/playlists/music/','32005','MusicLibrary'], ['special://profile/playlists/mixed/','32008','MusicLibrary'], [xbmc.translatePath( "special://skin/playlists/" ).decode('utf-8'),'32059',None], [xbmc.translatePath( "special://skin/extras/" ).decode('utf-8'),'32059',None]]
            for path in paths:
                count = 0
                rootpath = xbmc.translatePath( path[0] ).decode('utf-8')
                for root, subdirs, files in os.walk( rootpath ):
                    for file in files:
                        playlist = root.replace( rootpath, path[0] )
                        if not playlist.endswith( '/' ):
                            playlist = playlist + "/"
                        playlist = playlist + file
                        playlistfile = os.path.join( root, file ).decode( 'utf-8' )
                        mediaLibrary = path[2]
                        
                        if file.endswith( '.xsp' ):
                            contents = xbmcvfs.File(playlistfile, 'r')
                            contents_data = contents.read().decode('utf-8')
                            xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                            for line in xmldata.getiterator():
                                if line.tag == "smartplaylist":
                                    mediaType = line.attrib['type']
                                    if mediaType == "movies" or mediaType == "tvshows" or mediaType == "seasons" or mediaType == "episodes" or mediaType == "musicvideos" or mediaType == "sets":
                                        mediaLibrary = "VideoLibrary"
                                    elif mediaType == "albums" or mediaType == "artists" or mediaType == "songs":
                                        mediaLibrary = "MusicLibrary"                                
                                    
                                if line.tag == "name" and mediaLibrary is not None:
                                    name = line.text
                                    if not name:
                                        name = file[:-4]
                                    # Create a list item
                                    listitem = self._create(["::PLAYLIST::", name, "::SCRIPT::" + path[1], "DefaultPlaylist.png"])
                                    listitem.setProperty( "action-play", urllib.quote( "PlayMedia(" + playlist + ")" ) )
                                    listitem.setProperty( "action-show", urllib.quote( "ActivateWindow(" + mediaLibrary + "," + playlist + ", return)" ).encode( 'utf-8' ) )
                                    
                                    if mediaLibrary == "VideoLibrary":
                                        videolist.append( listitem )
                                    else:
                                        audiolist.append( listitem )
                                    # Save it for the widgets list
                                    self.widgetPlaylistsList.append( [playlist.decode( 'utf-8' ), "(" + __language__( int( path[1] ) ) + ") " + name] )
                                    
                                    count += 1
                                    break
                        elif file.endswith( '.m3u' ):
                            name = file[:-4]
                            listitem = self._create( ["::PLAYLIST::", name, "::SCRIPT::32005", "DefaultPlaylist.png"] )
                            listitem = xbmcgui.ListItem(label=name, label2= __language__(32005), iconImage='DefaultShortcut.png', thumbnailImage='DefaultPlaylist.png')
                            listitem.setProperty( "action-play", urllib.quote( "PlayMedia(" + playlist + ")" ) )
                            listitem.setProperty( "action-show", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ).encode( 'utf-8' ) )
                            
                            audiolist.append( listitem )
                            
                            count += 1
                            
                log( " - [" + path[0] + "] " + str( count ) + " playlists found" )
            
            self.addToDictionary( "playlist-video", videolist )
            self.addToDictionary( "playlist-audio", audiolist )
            
        except:
            log( "Failed to load playlists" )
            print_exc()
            
        self.loadedPlaylists = True
        return self.loadedPlaylists
                
    def favourites( self ):
        if self.loadedFavourites == True:
            # The List has already been populated, return it
            return self.loadedFavourites
        elif self.loadedFavourites == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedFavourites == True:
                    return self.loadedFavourites
        else:
            # We're going to populate the list
            self.loadedFavourites = "Loading"
            
        try:
            log('Loading favourites...')
            
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
                    thumb = "DefaultFolder.png"
                
                listitems.append( self._create( [ path.encode( 'utf-8' ), name, "::SCRIPT::32006", thumb] ) )
            
            log( " - " + str( len( listitems ) ) + " favourites found" )
            
            self.addToDictionary( "favourite", listitems )
            
        except:
            log( "Failed to load favourites" )
            print_exc()
            
        self.loadedFavourites = True            
        return self.loadedFavourites
        
    def addons( self ):
        if self.loadedAddOns == True:
            # The List has already been populated, return it
            return self.loadedAddOns
        elif self.loadedAddOns == "Loading":
            # The list is currently being populated, wait and then return it
            count = 0
            while False:
                xbmc.sleep( 100 )
                count += 1
                if count > 10:
                    # We've waited long enough, return an empty list
                    return []
                if self.loadedAddOns == True:
                    return self.loadedAddOns
        else:
            # We're going to populate the list
            self.loadedAddOns = "Loading"
            
        try:
            log( 'Loading add-ons' )
                        
            contenttypes = ["executable", "video", "audio", "image"]
            for contenttype in contenttypes:
                listitems = []
                if contenttype == "executable":
                    contentlabel = __language__(32009)
                    shortcutType = "32009"
                elif contenttype == "video":
                    contentlabel = __language__(32010)
                    shortcutType = "32010"
                elif contenttype == "audio":
                    contentlabel = __language__(32011)
                    shortcutType = "32011"
                elif contenttype == "image":
                    contentlabel = __language__(32012)
                    shortcutType = "32012"
                    
                json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Addons.Getaddons", "params": { "content": "%s", "properties": ["name", "path", "thumbnail", "enabled"] } }' % contenttype)
                json_query = unicode(json_query, 'utf-8', errors='ignore')
                json_response = simplejson.loads(json_query)
                
                if json_response.has_key('result') and json_response['result'].has_key('addons') and json_response['result']['addons'] is not None:
                    for item in json_response['result']['addons']:
                        if item['enabled'] == True:                            
                            path = "RunAddOn(" + item['addonid'].encode('utf-8') + ")"
                            action = None
                            
                            # If this is a plugin, mark that we can browse it
                            if item['addonid'].startswith( "plugin." ):
                                path = "||BROWSE||" + item['addonid'].encode('utf-8')
                                action = urllib.quote( "RunAddOn(" + item['addonid'].encode('utf-8') + ")" )

                            thumbnail = "DefaultAddon.png"
                            if item['thumbnail'] != "":
                                thumbnail = item[ 'thumbnail' ]
                                
                            listitem = self._create([path, item['name'], contentlabel, thumbnail])
                            if action is not None:
                                listitem.setProperty( "path", urllib.quote( path ) )
                                listitem.setProperty( "action", action )

                            listitems.append(listitem)
                            
                if contenttype == "executable":
                    self.addToDictionary( "addon-program", listitems )
                elif contenttype == "video":
                    self.addToDictionary( "addon-video", listitems )
                elif contenttype == "audio":
                    self.addToDictionary( "addon-audio", listitems )
                elif contenttype == "image":
                    self.addToDictionary( "addon-image", listitems )
            
            log( " - " + str( len( listitems ) ) + " add-ons found" )
            
        except:
            log( "Failed to load addons" )
            print_exc()
        
        self.loadedAddOns = True
        return self.loadedAddOns
            
    
    def explorer( self, history, location, label, thumbnail, skinStrings, itemType ):
        dialogLabel = label[0].replace( "  [B]>[/B]", "" )

        # Default action - create shortcut
        listings = []
        
        listitem = xbmcgui.ListItem( label=__language__(32058) )
        listitem.setProperty( "path", "||CREATE||" )
        listings.append( listitem )
                
        # If this isn't the root, create a link to go up the heirachy
        if len( label ) is not 1:
        #    listitem = xbmcgui.ListItem( label=".." )
        #    listitem.setProperty( "path", "||BACK||" )
        #    listings.append( listitem )
        #    
            dialogLabel = label[0].replace( "  [B]>[/B]", "" ) + " - " + label[ len( label ) - 1 ].replace( "  [B]>[/B]", "" )
            
        # Show a waiting dialog, then get the listings for the directory
        dialog = xbmcgui.DialogProgress()
        dialog.create( dialogLabel, __language__( 32063) )
    
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Files.GetDirectory", "params": { "properties": ["title", "file", "thumbnail"], "directory": "' + location + '", "media": "files" } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        
        dialog.close()
            
        # Add all directories returned by the json query
        if json_response.has_key('result') and json_response['result'].has_key('files') and json_response['result']['files'] is not None:
            for item in json_response['result']['files']:
                if item["filetype"] == "directory":
                    if item[ "thumbnail" ] is not "":
                        listitem = xbmcgui.ListItem( label=item['label'] + "  [B]>[/B]", iconImage="DefaultFolder.png", thumbnailImage=item[ 'thumbnail' ] )
                        log( repr( item[ 'thumbnail' ] ) )
                        listitem.setProperty( "thumbnail", item[ 'thumbnail' ] )
                    else:
                        listitem = xbmcgui.ListItem( label=item['label'] + "  [B]>[/B]", iconImage="DefaultFolder.png" )
                    listitem.setProperty( "path", item[ 'file' ] )
                    listitem.setProperty( "icon", "DefaultFolder.png" )
                    listings.append( listitem )
            
        # Show dialog
        w = ShowDialog( "DialogSelect.xml", __cwd__, listing=listings, windowtitle=dialogLabel )
        w.doModal()
        selectedItem = w.result
        del w
        
        if selectedItem != -1:
            if listings[ selectedItem ].getProperty( "path" ) == "||CREATE||":
                # User has chosen the shortcut they want
                
                # Build the action
                if itemType == "::SCRIPT::32010" or itemType == "::SCRIPT::32014" or itemType == "::SCRIPT::32069":
                    action = "ActivateWindow(10025," + location + ",Return)"
                elif itemType == "::SCRIPT::32011" or itemType == "::SCRIPT::32019" or itemType == "::SCRIPT::32073":
                    action = 'ActivateWindow(10501,&quot;' + location + '&quot;,Return)'
                elif itemType == "::SCRIPT::32012":
                    action = 'ActivateWindow(10002,&quot;' + location + '&quot;,Return)'
                else:
                    action = "RunAddon(" + location + ")"
                    
                if not itemType.find( "::SCRIPT::" ) == -1:
                    localItemType = __language__(int( itemType[10:] ) )
                elif not itemType.find( "::LOCAL::" ) == -1:
                    localItemType = xbmc.getLocalizedString(int( itemType[9:] ) )
                elif itemType.isdigit():
                    localItemType = xbmc.getLocalizedString( int( itemType ) )
                else:
                    localItemType = itemType

                listitem = xbmcgui.ListItem(label=label[ len( label ) - 1 ].replace( "  [B]>[/B]", "" ), label2=localItemType, iconImage="DefaultShortcut.png", thumbnailImage=thumbnail[ len( thumbnail ) - 1 ])
                listitem.setProperty( "path", urllib.quote( action ) )
                listitem.setProperty( "displayPath", action )
                listitem.setProperty( "shortcutType", itemType )
                listitem.setProperty( "icon", "DefaultShortcut.png" )
                listitem.setProperty( "thumbnail", thumbnail[ len( thumbnail ) - 1 ] )
                
                return listitem
                
            elif listings[ selectedItem ].getProperty( "path" ) == "||BACK||":
                # User is going up the heirarchy, remove current level and re-call this function
                history.pop()
                label.pop()
                thumbnail.pop()
                return self.explorer( history, history[ len( history ) -1 ], label, thumbnail, skinStrings, itemType )
                
            else:
                # User has chosen a sub-level to display, add details and re-call this function
                history.append( listings[ selectedItem ].getProperty( "path" ) )
                label.append( listings[ selectedItem ].getLabel() )
                thumbnail.append( listings[ selectedItem ].getProperty( "thumbnail" ) )
                return self.explorer( history, listings[ selectedItem ].getProperty( "path" ), label, thumbnail, skinStrings, itemType )
                

class ShowDialog( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.listing = kwargs.get( "listing" )
        self.windowtitle = kwargs.get( "windowtitle" )
        self.result = -1

    def onInit(self):
        try:
            self.fav_list = self.getControl(6)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.fav_list = self.getControl(3)

        self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)

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
        if controlID == 6 or controlID == 3:
            num = self.fav_list.getSelectedPosition()
            self.result = num
        else:
            self.result = -1

        self.close()

    def onFocus(self, controlID):
        pass
