# coding=utf-8
import os, sys, datetime, unicodedata
import xbmc, xbmcgui, xbmcvfs, urllib
import xml.etree.ElementTree as xmltree
from xml.dom.minidom import parse
from traceback import print_exc

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = sys.modules[ "__main__" ].__addon__
__addonid__      = sys.modules[ "__main__" ].__addonid__
__addonversion__ = sys.modules[ "__main__" ].__addonversion__
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).encode('utf-8'), __addonid__.encode( 'utf-8' ) ).decode( 'utf-8' )
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')
__defaultpath__  = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'shortcuts').encode("utf-8") ).decode("utf-8")
__language__     = sys.modules[ "__main__" ].__language__
__cwd__          = sys.modules[ "__main__" ].__cwd__

ACTION_CANCEL_DIALOG = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )

if not xbmcvfs.exists(__datapath__):
    xbmcvfs.mkdir(__datapath__)

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.group = kwargs[ "group" ]
        self.shortcutgroup = 1
        self.has402403 = True
        
        # Empty arrays for different shortcut types
        self.arrayXBMCCommon = []
        self.arrayVideoLibrary = []
        self.arrayMusicLibrary = []
        self.arrayPlaylists = []
        self.arrayFavourites = []
        self.arrayAddOns = []
        
        log('script version %s started - management module' % __addonversion__)

    def onInit( self ):
        if self.group == '':
            self._close()
        else:
            self.window_id = xbmcgui.getCurrentWindowDialogId()
            xbmcgui.Window(self.window_id).setProperty('SkinShortcuts.CurrentGroup', self.group)
            
            # Set button labels
            self.getControl( 301 ).setLabel( __language__(32000) )
            self.getControl( 302 ).setLabel( __language__(32001) )
            self.getControl( 303 ).setLabel( __language__(32002) )
            self.getControl( 304 ).setLabel( __language__(32003) )
            try:
                self.getControl( 305 ).setLabel( __language__(32025) )
            except:
                log( "Not set label for edit label button" )
            self.getControl( 306 ).setLabel( __language__(32026) )
            try:
                self.getControl( 307 ).setLabel( __language__(32027) )
            except:
                log( "Not set label for edit action button" )
            self.getControl( 308 ).setLabel( __language__(32028) )
            
            # List XBMC common shortcuts (likely to be used on a main menu
            self._load_xbmccommon()
            
            # List video and music library shortcuts
            self._load_videolibrary()
            self._load_musiclibrary()
            
            # Load favourites, playlists, add-ons
            # self._fetch_videoplaylists()
            # self._fetch_musicplaylists()
            self._fetch_playlists()
            self._fetch_favourites()
            self._fetch_addons()
            
            self._display_shortcuts()
            
            # Load current shortcuts
            self.load_shortcuts()
            
            self.updateEditControls()
        
    def _load_xbmccommon( self ):
        listitems = []
        log('Listing xbmc common items...')
        
        # Videos, Movies, TV Shows, Live TV, Music, Music Videos, Pictures, Weather, Programs,
        # Play dvd, eject tray
        # Settings, File Manager, Profiles, System Info
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
        
        self.arrayXBMCCommon = listitems
        
    def _load_videolibrary( self ):
        listitems = []
        log('Listing video library...')
        
        # os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
        rootdir = os.path.join( xbmc.translatePath( "special://userdata".decode('utf-8') ), "library", "video" )
        log( "Trying " + rootdir )
        if not os.path.exists( rootdir ):
            log( "Custom user library nodes aren't in existance!" )
            rootdir = os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", "video" )
 
        
        for root, subdirs, files in os.walk(rootdir):
            videonodes = {}
            unnumberedNode = 100
            label2 = "::SCRIPT::32014"
            if "index.xml" in files:
                # Parse the XML file to get the type of these nodes
                tree = xmltree.parse( os.path.join( root, "index.xml") )
                label = tree.find( 'label' )
                if label.text.isdigit:
                    label2 = "::LOCAL::" + label.text
                else:
                    label2 = label.text
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
                        
                    listitem = [path]
                    
                    # Get the label
                    label = tree.find( 'label' )
                    if label is not None:
                        if label.text.isdigit:
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
                        videonodes[ order.attrib.get( 'order' ) ] = listitem
                    except:
                        videonodes[ str( unnumberedNode ) ] = listitem
                        unnumberedNode = unnumberedNode + 1
                        
            for key in sorted(videonodes.iterkeys()):
                listitems.append( self._create( videonodes[ key ] ) )
                        
                    
                        
                    
                #log( os.path.relpath( os.path.join( root, file ), rootdir ) )
            #for file in files:
            #    print subdir+'/'+file
        
        # Videos
        #listitems.append( self._create(["ActivateWindow(Videos,Movies,return)", "::LOCAL::342", "::SCRIPT::32014", "DefaultMovies.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShows,return)", "::LOCAL::20343", "::SCRIPT::32014", "DefaultTVShows.png"]) )
        #listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,34,0 ,13,0)", "::SCRIPT::32022", "::SCRIPT::32014", "DefaultTVShows.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideos,return)", "::LOCAL::20389", "::SCRIPT::32014", "DefaultMusicVideos.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,Files,return)", "::LOCAL::744", "::SCRIPT::32014", "DefaultFolder.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,Playlists,return)", "::LOCAL::136", "::SCRIPT::32014", "DefaultVideoPlaylists.png"]) )
        
        # Movies
        #listitems.append( self._create(["ActivateWindow(Videos,RecentlyAddedMovies,return)", "::LOCAL::20386", "::SCRIPT::32015", "DefaultRecentlyAddedMovies.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieActors,return)", "::LOCAL::344", "::SCRIPT::32015", "DefaultActor.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieCountries,return)", "::LOCAL::20451", "::SCRIPT::32015", "DefaultCountry.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieDirectors,return)", "::LOCAL::20348", "::SCRIPT::32015", "DefaultDirector.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieGenres,return)", "::LOCAL::135", "::SCRIPT::32015", "DefaultGenre.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieSets,return)", "::LOCAL::20434", "::SCRIPT::32015", "DefaultSets.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieStudios,return)", "::LOCAL::20388", "::SCRIPT::32015", "DefaultStudios.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieTags,return)", "::LOCAL::20459", "::SCRIPT::32015", "DefaultTags.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieTitles,return)", "::LOCAL::369", "::SCRIPT::32015", "DefaultMovieTitle.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MovieYears,return)", "::LOCAL::562", "::SCRIPT::32015", "DefaultYear.png"]) )

        # TV Shows
        #listitems.append( self._create(["ActivateWindow(Videos,RecentlyAddedEpisodes,return)", "::LOCAL::20387", "::SCRIPT::32016", "DefaultRecentlyAddedEpisodes.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowActors,return)", "::LOCAL::344", "::SCRIPT::32016", "DefaultActor.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowGenres,return)", "::LOCAL::135", "::SCRIPT::32016", "DefaultGenre.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowStudios,return)", "::LOCAL::20388", "::SCRIPT::32016", "DefaultStudios.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowTags,return)", "::LOCAL::20459", "::SCRIPT::32016", "DefaultTags.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowTitles,return)", "::LOCAL::369", "::SCRIPT::32016", "DefaultTVShowTitle.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,TVShowYears,return)", "::LOCAL::562", "::SCRIPT::32016", "DefaultYear.png"]) )

        # PVR
        listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,32,0 ,11,0)", "::LOCAL::19023", "::SCRIPT::32017", "DefaultTVShows.png"]) )
        listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,33,0 ,12,0)", "::LOCAL::19024", "::SCRIPT::32017", "DefaultTVShows.png"]) )
        listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,31,0 ,10,0)", "::LOCAL::19069", "::SCRIPT::32017", "DefaultTVShows.png"]) )
        listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,34,0 ,13,0)", "::LOCAL::19163", "::SCRIPT::32017", "DefaultTVShows.png"]) )
        listitems.append( self._create(["ActivateWindowAndFocus(MyPVR,35,0 ,14,0)", "::SCRIPT::32023", "::SCRIPT::32017", "DefaultTVShows.png"]) )
        
        # Music Videos
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoAlbums,return)", "::LOCAL::20389", "::SCRIPT::32018", "DefaultMusicVideos.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoArtists,return)", "::LOCAL::133", "::SCRIPT::32018", "DefaultMusicArtists.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoDirectors,return)", "::LOCAL::20348", "::SCRIPT::32018", "DefaultDirector.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoGenres,return)", "::LOCAL::135", "::SCRIPT::32018", "DefaultMusicGenres.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoStudios,return)", "::LOCAL::20388", "::SCRIPT::32018", "DefaultStudios.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoTags,return)", "::LOCAL::20459", "::SCRIPT::32018", "DefaultTags.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoTitles,return)", "::LOCAL::369", "::SCRIPT::32018", "DefaultMusicVideoTitle.png"]) )
        #listitems.append( self._create(["ActivateWindow(Videos,MusicVideoYears,return)", "::LOCAL::562", "::SCRIPT::32018", "DefaultMusicYears.png"]) )
        
        self.arrayVideoLibrary = listitems
        
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
        type = tree.find( 'content' ).text
        if type == "movies":
            return "Movie"
        elif type == "tvshows":
            return "TvShow"
        elif type == "musicvideos":
            return "MusicVideo"
        else:
            return "Custom Node"
                
    def _load_musiclibrary( self ):
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
        
        self.arrayMusicLibrary = listitems
        
    def _create ( self, item ):
        # Create localised label
        displayLabel = item[1]
        if not item[1].find( "::SCRIPT::" ) == -1:
            displayLabel = __language__(int( item[1][10:] ) )
        elif not item[1].find( "::LOCAL::" ) == -1:
            displayLabel = xbmc.getLocalizedString(int( item[1][9:] ) )
        
        # Create localised label2
        displayLabel2 = item[2]
        if not item[2].find( "::SCRIPT::" ) == -1:
            displayLabel2 = __language__(int( item[2][10:] ) )
        elif not item[2].find( "::LOCAL::" ) == -1:
            displayLabel2 = xbmc.getLocalizedString(int( item[2][9:] ) )
            
        # Build listitem
        listitem = xbmcgui.ListItem(label=displayLabel, label2=displayLabel2, iconImage="DefaultShortcut.png", thumbnailImage=item[3])
        #if not item[1].find( "::SCRIPT::" ) == -1:
        #    listitem = xbmcgui.ListItem(label=__language__(int( item[1][10:] ) ), label2=__language__( int ( item[2][10:]) ), iconImage="DefaultShortcut.png", thumbnailImage=item[3])
        #elif not item[1].find( "::LOCAL::" ) == -1:
        #    log( __language__( int ( item[2][10:]) ) )
        #    listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(int( item[1][9:] ) ), label2=__language__( int ( item[2][10:]) ), iconImage="DefaultShortcut.png", thumbnailImage=item[3])
        #else:
        #    listitem = xbmcgui.ListItem(label=xbmc.item[1], label2=__language__( int ( item[2][10:]) ), iconImage="DefaultShortcut.png", thumbnailImage=item[3])
        listitem.setProperty( "path", urllib.quote( item[0] ) )
        listitem.setProperty( "localizedString", item[1] )
        listitem.setProperty( "shortcutType", item[2] )
        listitem.setProperty( "icon", "DefaultShortcut.png" )
        listitem.setProperty( "thumbnail", item[3] )
        
        return( listitem )
        
    def _fetch_playlists( self ):
        listitems = []
        # Music Playlists
        log('Loading music playlists...')
        paths = [['special://profile/playlists/video/','32004','VideoLibrary'], ['special://profile/playlists/music/','32005','MusicLibrary'], ['special://profile/playlists/mixed/','32008','MusicLibrary']]
        for path in paths:
            try:
                dirlist = os.listdir( xbmc.translatePath( path[0] ).decode('utf-8') )
            except:
                dirlist = []
            for item in dirlist:
                playlist = os.path.join( path[0].decode( 'utf-8' ), item).encode( 'utf-8' )
                playlistfile = xbmc.translatePath( playlist ).decode( 'utf-8' )
                if item.endswith('.xsp'):
                    contents = xbmcvfs.File(playlistfile, 'r')
                    contents_data = contents.read().decode('utf-8')
                    xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                    for line in xmldata.getiterator():
                        if line.tag == "name":
                            name = line.text
                            if not name:
                                name = item[:-4]
                            log('Playlist found %s' % name)
                            listitem = xbmcgui.ListItem(label=name, label2= __language__(int(path[1])), iconImage='DefaultShortcut.png', thumbnailImage='DefaultPlaylist.png')
                            listitem.setProperty( "path", urllib.quote( "ActivateWindow(" + path[2] + "," + playlist + ", return)" ).encode( 'utf-8' ) )
                            listitem.setProperty( "icon", "DefaultShortcut.png" )
                            listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                            listitem.setProperty( "shortcutType", "::SCRIPT::" + path[1] )
                            listitems.append(listitem)
                            break
                elif item.endswith('.m3u'):
                    name = item[:-4]
                    log('Music playlist found %s' % name)
                    listitem = xbmcgui.ListItem(label=name, label2= __language__(32005), iconImage='DefaultShortcut.png', thumbnailImage='DefaultPlaylist.png')
                    listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                    listitem.setProperty( "icon", "DefaultShortcut.png" )
                    listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                    listitem.setProperty( "shortcutType", "::SCRIPT::" +  "32005" )
                    listitems.append(listitem)
                        
        self.arrayPlaylists = listitems
                
    def _fetch_favourites( self ):
        log('Loading favourites...')
        
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Favourites.GetFavourites", "params": { "properties": ["path", "thumbnail", "window", "windowparameter"] } }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = simplejson.loads(json_query)
        
        listitems = []
        
        if json_response.has_key('result') and json_response['result'].has_key('favourites') and json_response['result']['favourites'] is not None:
            for item in json_response['result']['favourites']:
                listitem = xbmcgui.ListItem(label=item['title'], label2=__language__(32006), iconImage="DefaultShortcut.png", thumbnailImage=item['thumbnail'])
                
                # Build a path depending on the type of favourite returns
                if item['type'] == "window":
                    action = 'ActivateWindow(' + item['window'] + ', ' + item['windowparameter'] + ', return)'
                elif item['type'] == "media":
                    log( " - This is media" )
                    action = 'PlayMedia("' + item['path'] + '")'
                elif item['type'] == "script":
                    action = 'RunScript("' + item['path'] + '")'
                else:
                    action = item['path']
                
                log( action )
                listitem.setProperty( "path", urllib.quote( action.encode( 'utf-8' ) ) )
                
                if not item['thumbnail'] == "":
                    listitem.setProperty( "thumbnail", item['thumbnail'] )
                else:
                    listitem.setThumbnailImage( "DefaultShortcut.png" )
                    listitem.setProperty( "thumbnail", "DefaultShortcut.png" )
                
                listitem.setProperty( "icon", "DefaultShortcut.png" )
                listitem.setProperty( "shortcutType", "::SCRIPT::32006" )
                listitems.append(listitem)
        
        self.arrayFavourites = listitems
        
    def _fetch_addons( self ):
        listitems = []
        log( 'Loading add-ons' )
        
        # Add links to each add-on type in library
        listitems.append( self._create(["ActivateWindow(Videos,Addons,return)", "::LOCAL::1037", "::SCRIPT::32014", "DefaultAddonVideo.png"]) )
        listitems.append( self._create(["ActivateWindow(MusicLibrary,Addons,return)", "::LOCAL::1038", "::SCRIPT::32019", "DefaultAddonMusic.png"]) )
        listitems.append( self._create(["ActivateWindow(Pictures,Addons,return)", "::LOCAL::1039", "::SCRIPT::32020", "DefaultAddonPicture.png"]) )
        listitems.append( self._create(["ActivateWindow(Programs,Addons,return)", "::LOCAL::10001", "::SCRIPT::32021", "DefaultAddonProgram.png"]) )
        
        contenttypes = ["executable", "video", "audio", "image"]
        for contenttype in contenttypes:
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
                        listitem = xbmcgui.ListItem(label=item['name'], label2=contentlabel, iconImage="DefaultAddon.png", thumbnailImage=item['thumbnail'])
                        listitem.setProperty( "path", urllib.quote( "RunAddOn(" + item['addonid'].encode('utf-8') + ")" ) )
                        if item['thumbnail'] != "":
                            listitem.setProperty( "thumbnail", item['thumbnail'] )
                        else:
                            listitem.setProperty( "thumbnail", "DefaultAddon.png" )
                        
                        listitem.setProperty( "icon", "DefaultAddon.png" )
                        listitem.setProperty( "shortcutType", "::SCRIPT::" + shortcutType )
                        listitems.append(listitem)
        
        self.arrayAddOns = listitems
        
        
    def onClick(self, controlID):
        if controlID == 102:
            # Move to previous type of shortcuts
            self.shortcutgroup = self.shortcutgroup - 1
            if self.shortcutgroup == 0:
                self.shortcutgroup = 6
                
            self._display_shortcuts()

        if controlID == 103:
            # Move to next type of shortcuts
            self.shortcutgroup = self.shortcutgroup + 1
            if self.shortcutgroup == 7:
                self.shortcutgroup = 1
                
            self._display_shortcuts()
            
        if controlID == 111:
            # User has selected an available shortcut they want in their menu
            # Create a copy of the listitem
            listitemCopy = self._duplicate_listitem( self.getControl( 111 ).getSelectedItem() )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    log ( "### Found the item" )
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and add it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
        
        if controlID == 301:
            # Add a new item
            listitem = xbmcgui.ListItem( __language__(32013) )
            listitem.setProperty( "Path", 'noop' )
            
            self.getControl( 211 ).addItem( listitem )
            
            # Set focus
            self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
        
        if controlID == 302:
            # Delete an item
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            
            for x in range(0, self.getControl( 211 ).size()):
                if x != num:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    listitems.append(listitemShortcutCopy)
            
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            # If there are no items in the list, add an empty one...
            if self.getControl( 211 ).size() == 0:
                listitem = xbmcgui.ListItem( __language__(32013) )
                listitem.setProperty( "Path", 'noop' )
                
                self.getControl( 211 ).addItem( listitem )
                
                # Set focus
                self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
            
        if controlID == 303:
            # Move item up in list
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            if num != 0:
                # Copy the selected item and the one above it
                listitemSelected = self._duplicate_listitem( self.getControl( 211 ).getListItem(num) )
                listitemSwap = self._duplicate_listitem( self.getControl( 211 ).getListItem(num - 1) )
                
                for x in range(0, self.getControl( 211 ).size()):
                    if x == num:
                        listitems.append(listitemSwap)
                    elif x == num - 1:
                        listitems.append(listitemSelected)
                    else:
                        listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                        listitems.append(listitemCopy)
                
                self.getControl( 211 ).reset()
                self.getControl( 211 ).addItems(listitems)
                
                self.getControl( 211 ).selectItem( num - 1 )

        if controlID == 304:
            # Move item down in list
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            if num != self.getControl( 211 ).size() -1:
                # Copy the selected item and the one below it
                listitemSelected = self._duplicate_listitem( self.getControl( 211 ).getListItem(num) )
                listitemSwap = self._duplicate_listitem( self.getControl( 211 ).getListItem(num + 1) )
                
                for x in range(0, self.getControl( 211 ).size()):
                    if x == num:
                        listitems.append(listitemSwap)
                    elif x == num + 1:
                        listitems.append(listitemSelected)
                    else:
                        listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )

                        listitems.append(listitemCopy)
                
                self.getControl( 211 ).reset()
                self.getControl( 211 ).addItems(listitems)
                
                self.getControl( 211 ).selectItem( num + 1 )

        if controlID == 305:
            # Change label
            
            # Retrieve properties, copy item, etc (in case the user changes focus whilst we're running)
            custom_label = self.getControl( 211 ).getSelectedItem().getLabel()
            num = self.getControl( 211 ).getSelectedPosition()
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            
            if custom_label == __language__(32013):
                custom_label = ""
            keyboard = xbmc.Keyboard( custom_label, xbmc.getLocalizedString(528), False )
            keyboard.doModal()
            if ( keyboard.isConfirmed() ):
                custom_label = keyboard.getText()
                if custom_label == "":
                    custom_label = __language__(32013)
                
            # Set properties of the listitemCopy
            listitemCopy.setLabel(custom_label)
            listitemCopy.setProperty( "localizedString", "" )
            listitemCopy.setProperty( "labelID", self._get_labelID(custom_label) )
            
            # If there's no label2, set it to custom shortcut
            if not listitemCopy.getLabel2():
                listitemCopy.setLabel2( __language__(32024) )
                listitemCopy.setProperty( "shortcutType", "::SCRIPT::32024" )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

        if controlID == 306:
            # Change thumbnail
            
            # Retrieve properties, copy item, etc (in case the user changes focus)
            custom_thumbnail = self.getControl( 211 ).getSelectedItem().getProperty( "thumbnail" )
            num = self.getControl( 211 ).getSelectedPosition()
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )

            dialog = xbmcgui.Dialog()
            custom_thumbnail = dialog.browse( 2 , xbmc.getLocalizedString(1030), 'files')
            
            # Create a copy of the listitem
            if custom_thumbnail:
                listitemCopy.setThumbnailImage( custom_thumbnail )
                listitemCopy.setProperty( "Thumbnail", custom_thumbnail )
                listitemCopy.setProperty( "customThumbnail", "False" )
                
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered thumbnail
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

            
        if controlID == 307:
            # Change Action
            
            #Retrieve properties, copy item, etc (in case the user changes focus)
            custom_path = urllib.unquote( self.getControl( 211 ).getSelectedItem().getProperty( "path" ) )
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            num = self.getControl( 211 ).getSelectedPosition()

            if custom_path == "noop":
                custom_path = ""
            keyboard = xbmc.Keyboard( custom_path, xbmc.getLocalizedString(528), False )
            keyboard.doModal()
            if ( keyboard.isConfirmed() ):
                custom_path = keyboard.getText()
                if custom_path == "":
                    custom_path = "noop"
                    
            if not urllib.quote( custom_path ) == self.getControl( 211 ).getSelectedItem().getProperty( "path" ):
                listitemCopy.setProperty( "path", urllib.quote( custom_path ) )
                listitemCopy.setLabel2( __language__(32024) )
                listitemCopy.setProperty( "shortcutType", "::SCRIPT::32024" )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered path
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
            
        if controlID == 308:
            # Reset shortcuts
            self.getControl( 211 ).reset()
            
            # Set path based on existance of user defined shortcuts, then skin-provided, then script-provided
            if xbmcvfs.exists( os.path.join( __skinpath__ , self.group + ".shortcuts" ) ):
                # Skin-provided defaults
                path = os.path.join( __skinpath__ , self.group + ".shortcuts" )
            elif xbmcvfs.exists( os.path.join( __defaultpath__ , self.group + ".shortcuts" ) ):
                # Script-provided defaults
                path = os.path.join( __defaultpath__ , self.group + ".shortcuts" )
            else:
                # No custom shortcuts or defaults available
                path = ""
                
            if not path == "":
                # Try to load shortcuts
                try:
                    file = xbmcvfs.File( path )
                    loaditems = eval( file.read() )
                    file.close()
                    
                    listitems = []
                    
                    for item in loaditems:
                        listitems.append( self._parse_listitem( item ) )
                        
                    # If we've loaded anything, save them to the list
                    if len(listitems) != 0:
                        returnItems = self._load_properties( listitems )
                        self.getControl( 211 ).addItems(returnItems)   
                        
                    # If there are no items in the list, add an empty one...
                    if self.getControl( 211 ).size() == 0:
                        listitem = xbmcgui.ListItem( __language__(32013) )
                        listitem.setProperty( "Path", 'noop' )
                        
                        self.getControl( 211 ).addItem( listitem )
                        
                        # Set focus
                        self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
                except:
                    # We couldn't load the file
                    print_exc()
                    log( "### ERROR could not load file %s" % path )
                    return []
            else:
                # Add an empty item
                listitem = xbmcgui.ListItem( __language__(32013) )
                listitem.setProperty( "Path", 'noop' )
                
                self.getControl( 211 ).addItem( listitem )
                
                # Set focus
                self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
                
        if controlID == 309:
            # Choose widget
            
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            num = self.getControl( 211 ).getSelectedPosition()
            
            # Load skin overrides
            path = os.path.join( __skinpath__ , "overrides.xml" )
            if xbmcvfs.exists( path ):
                try:
                    tree = xmltree.fromstring( xbmcvfs.File( path ).read().encode( 'utf-8' ) )
                except:
                    print_exc()
            
            # Get widgets
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
            selectedWidget = dialog.select( __language__(32044), widgetLabel )
            
            if selectedWidget != -1:
                # Update the widget
                if selectedWidget == 0:
                    # No widget
                    if listitemCopy.getProperty( "additionalListItemProperties" ):
                        newAdditionalList = []
                        for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                            if listitemProperty[0] != "widget":
                                newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                                
                        listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )
                            
                    # Copy the item again - this will clear the widget property
                    listitemCopy = self._duplicate_listitem( listitemCopy )
                else:
                    listitemCopy.setProperty( "widget", widget[selectedWidget] )
                    newAdditionalList = [ ["widget", widget[selectedWidget]] ]
                    if listitemCopy.getProperty( "additionalListItemProperties" ):
                        for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                            if listitemProperty[0] != "widget":
                                newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                    listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )
                    
                # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
                listitems = []
                for x in range(0, self.getControl( 211 ).size()):
                    if x == num:
                        listitems.append(listitemCopy)
                    else:
                        # Duplicate the item and it to the listitems array
                        listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                        
                        listitems.append(listitemShortcutCopy)
                        
                self.getControl( 211 ).reset()
                self.getControl( 211 ).addItems(listitems)
                
                self.getControl( 211 ).selectItem( num )
                
        if controlID == 310:
            # Choose background
            
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            num = self.getControl( 211 ).getSelectedPosition()
            
            # Load skin overrides
            path = os.path.join( __skinpath__ , "overrides.xml" )
            if xbmcvfs.exists( path ):
                try:
                    tree = xmltree.fromstring( xbmcvfs.File( path ).read().encode( 'utf-8' ) )
                except:
                    print_exc()
            
            # Get backgrounds
            backgroundLabel = ["Default"]
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
            selectedBackground = dialog.select( __language__(32045), backgroundLabel )
            
            if selectedBackground != -1:
                # Update the Background
                if selectedBackground == 0:
                    # No background
                    if listitemCopy.getProperty( "additionalListItemProperties" ):
                        newAdditionalList = []
                        for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                            if listitemProperty[0] != "background":
                                newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                                
                        listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )
                            
                    # Copy the item again - this will clear the background property
                    listitemCopy = self._duplicate_listitem( listitemCopy )
                else:
                    listitemCopy.setProperty( "background", background[selectedBackground] )
                    newAdditionalList = [ ["background", background[selectedBackground]] ]
                    if listitemCopy.getProperty( "additionalListItemProperties" ):
                        for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                            if listitemProperty[0] != "background":
                                newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                    listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )
                    
                # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
                listitems = []
                for x in range(0, self.getControl( 211 ).size()):
                    if x == num:
                        listitems.append(listitemCopy)
                    else:
                        # Duplicate the item and it to the listitems array
                        listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                        
                        listitems.append(listitemShortcutCopy)
                        
                self.getControl( 211 ).reset()
                self.getControl( 211 ).addItems(listitems)
                
                self.getControl( 211 ).selectItem( num )
        
        if controlID == 401:
            # Choose shortcut (SELECT DIALOG)
            
            # Check for a window property designating category
            currentWindow = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
            shortcutCategory = -1
            if currentWindow.getProperty("category"):
                skinCategory = currentWindow.getProperty("category")
                if skinCategory == "common":
                    shortcutCategory = 0
                elif skinCategory == "video":
                    shortcutCategory = 1
                elif skinCategory == "music":
                    shortcutCategory = 2
                elif skinCategory == "playlists":
                    shortcutCategory = 3
                elif skinCategory == "favourites":
                    shortcutCategory = 4
                elif skinCategory == "addons":
                    shortcutCategory = 5
            else:
                # No window property passed, ask the user what category they want
                shortcutCategories = [__language__(32029), __language__(32030), __language__(32031), __language__(32040), __language__(32006), __language__(32007)]
                shortcutCategory = xbmcgui.Dialog().select( __language__(32043), shortcutCategories )
                
            # Clear the window property
            currentWindow.clearProperty("category")
            
            # Get the shortcuts for the group the user has selected
            displayLabel2 = False
            if shortcutCategory == 0: # Common
                availableShortcuts = self.arrayXBMCCommon
            elif shortcutCategory == 1: # Video Library
                availableShortcuts = self.arrayVideoLibrary
                displayLabel2 = True
            elif shortcutCategory == 2: # Music Library
                availableShortcuts = self.arrayMusicLibrary
                displayLabel2 = True
            elif shortcutCategory == 3: # Playlists
                availableShortcuts = self.arrayPlaylists
                displayLabel2 = True
            elif shortcutCategory == 4: # Favourites
                availableShortcuts = self.arrayFavourites
            elif shortcutCategory == 5: # Add-ons
                availableShortcuts = self.arrayAddOns
                displayLabel2 = True
                
                
            elif shortcutCategory != -1: # No category selected
                return
                
            log( "### Selected category: " + shortcutCategories[shortcutCategory] )
            log( availableShortcuts )
            
            # Now build an array of items to show to the user
            displayShortcuts = []
            for shortcut in availableShortcuts:
                if displayLabel2:
                    displayShortcuts.append( "(" + shortcut.getLabel2() + ") " + shortcut.getLabel() )
                else:
                    displayShortcuts.append( shortcut.getLabel() )

            log( displayShortcuts )
            
            selectedShortcut = xbmcgui.Dialog().select( shortcutCategories[shortcutCategory], displayShortcuts )
            
            if selectedShortcut != -1:
                # Create a copy of the listitem
                listitemCopy = self._duplicate_listitem( availableShortcuts[selectedShortcut] )
                
                # Loop through the original list, and replace the currently selected listitem with our new listitem
                listitems = []
                num = self.getControl( 211 ).getSelectedPosition()
                for x in range(0, self.getControl( 211 ).size()):
                    if x == num:
                        log ( "### Found the item" )
                        listitems.append(listitemCopy)
                    else:
                        # Duplicate the item and add it to the listitems array
                        listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                        listitems.append(listitemShortcutCopy)
                        
                self.getControl( 211 ).reset()
                self.getControl( 211 ).addItems(listitems)
                
                self.getControl( 211 ).selectItem( num )
        
        if controlID == 402:
            # Change label (EDIT CONTROL)
            
            # Retrieve properties, copy item, etc (in case the user changes focus whilst we're running)
            custom_label = self.getControl( 211 ).getSelectedItem().getLabel()
            num = self.getControl( 211 ).getSelectedPosition()
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            
            custom_label = self.getControl( 402 ).getText()
            if custom_label == "":
                custom_label = __language__(32013)
                
            # Set properties of the listitemCopy
            listitemCopy.setLabel(custom_label)
            listitemCopy.setProperty( "localizedString", "" )
            listitemCopy.setProperty( "labelID", self._get_labelID(custom_label) )
            
            # If there's no label2, set it to custom shortcut
            if not listitemCopy.getLabel2():
                listitemCopy.setLabel2( __language__(32024) )
                listitemCopy.setProperty( "shortcutType", "::SCRIPT::32024" )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
        
        
        if controlID == 403:
            # Change action (EDIT CONTROL)
             #Retrieve properties, copy item, etc (in case the user changes focus)
            custom_path = urllib.unquote( self.getControl( 211 ).getSelectedItem().getProperty( "path" ) )
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            num = self.getControl( 211 ).getSelectedPosition()

            custom_path = self.getControl( 403 ).getText()
            if custom_path == "":
                custom_path = "noop"
                    
            if not urllib.quote( custom_path ) == self.getControl( 211 ).getSelectedItem().getProperty( "path" ):
                listitemCopy.setProperty( "path", urllib.quote( custom_path ) )
                listitemCopy.setLabel2( __language__(32024) )
                listitemCopy.setProperty( "shortcutType", "::SCRIPT::32024" )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered path
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

            
        if controlID == 404:
            # Set custom property
            log( "### Setting custom property" )
            
            listitemCopy = self._duplicate_listitem( self.getControl( 211 ).getSelectedItem() )
            num = self.getControl( 211 ).getSelectedPosition()
            
            # Retrieve window properties
            currentWindow = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
            propertyName = ""
            propertyValue = ""
            if currentWindow.getProperty( "customProperty" ):
                propertyName = currentWindow.getProperty( "customProperty" )
                currentWindow.clearProperty( "customProperty" )
            else:
                # The customProperty value needs to be set, so return
                log( "### NO CUSTOM PROPERTY!")
                currentWindow.clearProperty( "customValue" )
                return
                
            if currentWindow.getProperty( "customValue" ):
                propertyValue = currentWindow.getProperty( "customValue" )
                currentWindow.clearProperty( "customValue" )
                
            log( "Property: " + propertyName )
            log( "Value: " + propertyValue )
                
            if propertyValue == "":
                # No value set, so remove it from additionalListItemProperties
                if listitemCopy.getProperty( "additionalListItemProperties" ):
                    newAdditionalList = []
                    for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                        if listitemProperty[0] != propertyName:
                            newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                            
                    listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )
                        
                # Copy the item again - this will clear the background property
                listitemCopy = self._duplicate_listitem( listitemCopy )
                
            else:
                # Set the property
                listitemCopy.setProperty( propertyName, propertyValue )
                newAdditionalList = [ [propertyName, propertyValue] ]
                if listitemCopy.getProperty( "additionalListItemProperties" ):
                    for listitemProperty in eval( listitemCopy.getProperty( "additionalListItemProperties" ) ):
                        log( listitemProperty )
                        if listitemProperty[0] != propertyName:
                            newAdditionalList.append( [listitemProperty[0], listitemProperty[1]] )
                listitemCopy.setProperty( "additionalListItemProperties", repr( newAdditionalList ) )

            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
            listitems = []
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

            
        if controlID == 405:
            # Launch management dialog for submenu
            log( "### Launching management dialog for submenu" )
            
            # Check if 'level' property has been set
            currentWindow = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
            launchGroup = self.getControl( 211 ).getSelectedItem().getProperty( "labelID" )
            if currentWindow.getProperty("level"):
                launchGroup = launchGroup + "." + currentWindow.getProperty("level")
                currentWindow.clearProperty("level")
            xbmc.executebuiltin( "RunScript(script.skinshortcuts,type=manage&group=" + launchGroup + ")" )

            
    def load_shortcuts( self ):
        log( "Loading shortcuts" )
        log( "Filename: " + self.group + ".shortcuts" )
        
        # Set path based on existance of user defined shortcuts, then skin-provided, then script-provided
        if xbmcvfs.exists( os.path.join( __datapath__ , self.group.decode( 'utf-8' ) + ".shortcuts" ) ):
            # User defined shortcuts
            path = os.path.join( __datapath__ , self.group.decode( 'utf-8' ) + ".shortcuts" )
        elif xbmcvfs.exists( os.path.join( __skinpath__ , self.group.decode( 'utf-8' ) + ".shortcuts" ) ):
            # Skin-provided defaults
            path = os.path.join( __skinpath__ , self.group.decode( 'utf-8' ) + ".shortcuts" )
        elif xbmcvfs.exists( os.path.join( __defaultpath__ , self.group.decode( 'utf-8' ) + ".shortcuts" ) ):
            # Script-provided defaults
            path = os.path.join( __defaultpath__ , self.group.decode( 'utf-8' ) + ".shortcuts" )
        else:
            # No custom shortcuts or defaults available
            path = ""
            
        if not path == "":
            # Try to load shortcuts
            try:
                file = xbmcvfs.File( path )
                loaditems = eval( file.read() )
                file.close()
                
                listitems = []
                
                for item in loaditems:
                    # Parse any localised labels
                    newItem = self._parse_listitem( item )
                    
                    # Load widgets, backgrounds and any skin-specific properties
                    # newItem = self._load_properties( newItem )
                    
                    # Add to list
                    listitems.append( newItem )
                    
                # If we've loaded anything, save them to the list
                if len(listitems) != 0:
                    # Load widgets, backgrounds and any skin-specific properties
                    returnItems = self._load_properties( listitems )
                    
                    self.getControl( 211 ).addItems(returnItems)
                
                # If there are no items in the list, add an empty one...
                if self.getControl( 211 ).size() == 0:
                    listitem = xbmcgui.ListItem( __language__(32013) )
                    listitem.setProperty( "Path", 'noop' )
                    
                    self.getControl( 211 ).addItem( listitem )
                    
                    # Set focus
                    self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
            except:
                # We couldn't load the file
                print_exc()
                log( "### ERROR could not load file %s" % path )
                return []
        else:
            # Add an empty item
            listitem = xbmcgui.ListItem( __language__(32013) )
            listitem.setProperty( "Path", 'noop' )
            
            self.getControl( 211 ).addItem( listitem )
            
            # Set focus
            self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
        
                
    def _parse_listitem( self, item ):
        # Parse a loaded listitem, replacing ::SCRIPT:: or ::LOCAL:: with localized strings
        loadLabel = item[0]
        loadLabel2 = item[1]
        saveLabel2 = item[1]

        if not loadLabel2.find( "::SCRIPT::" ) == -1:
            saveLabel2 = __language__( int ( loadLabel2[10:] ) )
        elif not loadLabel2.find( "::LOCAL::" ) == -1:
            saveLabel2 = xbmc.getLocalizedString(int( loadLabel2[9:] ) )
        
        if not loadLabel.find( "::SCRIPT::" ) == -1:
            # An item with a script-localized string
            listitem = xbmcgui.ListItem(label=__language__(int( loadLabel[10:] ) ), label2=saveLabel2, iconImage=item[2], thumbnailImage=item[3])
            listitem.setProperty( "path", item[4] )
            listitem.setProperty( "icon", item[2] )
            listitem.setProperty( "thumbnail", item[3] )
            listitem.setProperty( "localizedString", loadLabel )
            listitem.setProperty( "shortcutType", loadLabel2 )

        elif not loadLabel.find( "::LOCAL::" ) == -1:
            # An item with an XBMC-localized string
            listitem = xbmcgui.ListItem(label= xbmc.getLocalizedString(int( loadLabel[9:] ) ), label2=saveLabel2, iconImage=item[2], thumbnailImage=item[3])
            listitem.setProperty( "path", item[4] )
            listitem.setProperty( "icon", item[2] )
            listitem.setProperty( "thumbnail", item[3] )
            listitem.setProperty( "localizedString", loadLabel )
            listitem.setProperty( "shortcutType", loadLabel2 )
            
        else:
            # An item without a localized string
            listitem = xbmcgui.ListItem(label=item[0], label2=saveLabel2, iconImage=item[2], thumbnailImage=item[3])
            listitem.setProperty( "path", item[4] )
            listitem.setProperty( "icon", item[2] )
            listitem.setProperty( "thumbnail", item[3] )
            listitem.setProperty( "shortcutType", loadLabel2 )
            
        if len(item) == 6:
            listitem.setProperty( "customThumbnail", item[5] )
            
        listitem.setProperty( "labelID", self._get_labelID( loadLabel ) )
        return listitem
        
    def _get_labelID ( self, item ):
        # Translate certain localized strings into non-localized form for labelID
        item = item.replace("::SCRIPT::", "")
        item = item.replace("::LOCAL::", "")
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
            return item.replace(" ", "").lower()
        
    def _load_properties( self, listitems ):
        # Load widget, background and custom properties and add them as properties of the listitems
        
        # Load the files
        paths = [[os.path.join( __datapath__ , xbmc.getSkinDir() + ".widgets" ),"widget"], [os.path.join( __datapath__ , xbmc.getSkinDir() + ".backgrounds" ),"background"], [os.path.join( __datapath__ , xbmc.getSkinDir() + ".customproperties" ),"custom"]]
        overrides = False
        dataFiles = []
        for path in paths:
            if xbmcvfs.exists( path[0] ):
                log( path[0] )
                try:
                    # Try loading file
                    listProperties = eval( xbmcvfs.File( path[0] ).read() )
                    dataFiles.append( [listProperties, path[1]] )
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )   
            else:
                # Try to get defaults from skins overrides.xml
                if overrides == False:
                    # Load the overrides file
                    overridepath = os.path.join( __skinpath__ , "overrides.xml" )
                    if xbmcvfs.exists(overridepath):
                        try:
                            log( "### Loaded overrides" )
                            overrides = xmltree.fromstring( xbmcvfs.File( overridepath ).read() )
                        except:
                            print_exc()
                            overrides = "::NONE::"
                    else:
                        overrides = "::NONE::"
                        
                # If we have loaded an overrides file, get all defaults
                if overrides != "::NONE::":
                    elems = ""
                    if path[1] == "widget":
                        elems = overrides.findall('widgetdefault')
                    elif path[1] == "background":
                        elems = overrides.findall('backgrounddefault')
                    elif path[1] == "custom":
                        elems = overrides.findall('propertydefault')
                    
                    # Add each default to data array
                    data = []
                    for elem in elems:
                        if path[1] == "custom":
                            data.append( [elem.attrib.get( 'labelID' ), elem.attrib.get( 'property' ), elem.text ] )
                        else:
                            data.append( [ elem.attrib.get( 'labelID' ), elem.text ] )
                    if len( data ) != 0:
                        dataFiles.append( [data, path[1]] )
                    
        # Check if we've loaded anything
        if len( dataFiles ) == 0:
            return listitems
            
        # Process the files we've loaded, and match any properties to listitems
        returnitems = []
        for listitem in listitems:
            # Copy this listitem
            listitemCopy = self._duplicate_listitem( listitem )
            
            # Loop through all the data we've loaded
            for dataFile in dataFiles:
                for listProperty in dataFile[0]:
                    #log( "Comparing " + listProperty[0] + " to " + listitemCopy.getProperty( "labelID" ) )
                    if listProperty[0] == listitemCopy.getProperty( "labelID" ):
                        setProperty = dataFile[1]
                        setValue = listProperty[1]
                        if dataFile[1] == "custom":
                            # If we're loading custom values, the properties we'll set are slightly different...
                            setProperty = listProperty[1]
                            setValue = listProperty[2]
                        # Add a custom property
                        listitemCopy.setProperty( setProperty, setValue )
                        # If there is already an additionalListItemProperties array, add this to it
                        if listitemCopy.getProperty( "additionalListItemProperties" ):
                            listitemProperties = eval( listitemCopy.getProperty( "additionalListItemProperties" ) )
                            listitemProperties.append( [setProperty, setValue] )
                            listitemCopy.setProperty( "additionalListItemProperties", repr( listitemProperties ) )
                        else:
                            # Create a new additionalListItemProperties array
                            listitemProperties = [[ setProperty, setValue ]]
                            listitemCopy.setProperty( "additionalListItemProperties", repr( listitemProperties ) )
            
            returnitems.append( listitemCopy )
            
        return returnitems
        
        
    def _duplicate_listitem( self, listitem ):
        # Create a copy of an existing listitem
        listitemCopy = xbmcgui.ListItem(label=listitem.getLabel(), label2=listitem.getLabel2(), iconImage=listitem.getProperty("icon"), thumbnailImage=listitem.getProperty("thumbnail"))
        listitemCopy.setProperty( "path", listitem.getProperty("path") )
        listitemCopy.setProperty( "icon", listitem.getProperty("icon") )
        listitemCopy.setProperty( "thumbnail", listitem.getProperty("thumbnail") )
        listitemCopy.setProperty( "localizedString", listitem.getProperty("localizedString") )
        listitemCopy.setProperty( "shortcutType", listitem.getProperty("shortcutType") )
        listitemCopy.setProperty( "labelID", listitem.getProperty("labelID") )
        if listitem.getProperty( "customThumbnail" ):
            listitemCopy.setProperty( "customThumbnail", listitem.getProperty( "customThumbnail" ) )
        if listitem.getProperty( "additionalListItemProperties" ):
            listitemCopy.setProperty( "additionalListItemProperties", listitem.getProperty( "additionalListItemProperties" ) )
            listitemProperties = eval( listitem.getProperty( "additionalListItemProperties" ) )
            for listitemProperty in listitemProperties:
                listitemCopy.setProperty( listitemProperty[0], listitemProperty[1] )
        return listitemCopy
        
    def _save_shortcuts( self ):
        # Save shortcuts
        listitems = []
        properties = []
        
        for x in range(0, self.getControl( 211 ).size()):
            # If the item has a path, push it to an array
            listitem = self.getControl( 211 ).getListItem(x)
            
            if listitem.getLabel() != __language__(32013):
                saveLabel = listitem.getLabel().decode('utf-8')
                saveLabel2 = listitem.getLabel2().decode('utf-8')
                
                if listitem.getProperty( "localizedString" ):
                    saveLabel = listitem.getProperty( "localizedString" ).decode('utf-8')
                    
                if listitem.getProperty( "customThumbnail" ):
                    savedata=[saveLabel, listitem.getProperty("shortcutType").decode('utf-8'), listitem.getProperty("icon").decode('utf-8'), listitem.getProperty("thumbnail").decode('utf-8'), listitem.getProperty("path").decode('utf-8'), listitem.getProperty("customThumbnail").decode('utf-8')]
                else:
                    savedata=[saveLabel, listitem.getProperty("shortcutType").decode('utf-8'), listitem.getProperty("icon").decode('utf-8'), listitem.getProperty("thumbnail").decode('utf-8'), listitem.getProperty("path").decode('utf-8')]
                    
                if listitem.getProperty( "additionalListItemProperties" ):
                    properties.append( [ listitem.getProperty( "labelID" ), eval( listitem.getProperty( "additionalListItemProperties" ) ) ] )
                    
                listitems.append(savedata)
                        
        path = os.path.join( __datapath__ , self.group.decode( 'utf-8' ) + ".shortcuts" )
        
        #if listitems:

        # If there are any shortcuts, save them
        try:
            f = xbmcvfs.File( path, 'w' )
            f.write( repr( listitems ) )
            f.close()
        except:
            print_exc()
            log( "### ERROR could not save file %s" % __datapath__ )
            
        # Save widgets, backgrounds and custom properties
        self._save_properties( properties )
            
        #else:
        #    # There are no shortcuts, delete the existing file if it exists
        #    try:
        #        xbmcvfs.delete( path )
        #    except:
        #        print_exc()
        #        log( "### No shortcuts, no existing file %s" % __datapath__ )            
    
    def _save_properties( self, properties ):
        # Load widget, background and custom properties and add them as properties of the listitems
        
        dataFiles = {"widget":[], "background":[], "custom":[]}
        
        # Load the files
        paths = [[os.path.join( __datapath__ , xbmc.getSkinDir() + ".widgets" ),"widget"], [os.path.join( __datapath__ , xbmc.getSkinDir() + ".backgrounds" ),"background"], [os.path.join( __datapath__ , xbmc.getSkinDir() + ".customproperties" ),"custom"]]
        overrides = False
        for path in paths:
            if xbmcvfs.exists( path[0] ):
                try:
                    # Try loading file
                    dataFiles[path[1]] = eval( xbmcvfs.File( path[0] ).read() )
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % path )   
            else:
                # Try to get defaults from skins overrides.xml
                if overrides == False:
                    # Load the overrides file
                    overridepath = os.path.join( __skinpath__ , "overrides.xml" )
                    if xbmcvfs.exists(overridepath):
                        try:
                            log( "### Loaded overrides" )
                            overrides = xmltree.fromstring( xbmcvfs.File( overridepath ).read() )
                        except:
                            print_exc()
                            overrides = "::NONE::"
                    else:
                        overrides = "::NONE::"
                        
                # If we have loaded an overrides file, get all defaults
                if overrides != "::NONE::":
                    elems = ""
                    if path[1] == "widget":
                        elems = overrides.findall('widgetdefault')
                    elif path[1] == "background":
                        elems = overrides.findall('backgrounddefault')
                    elif path[1] == "custom":
                        elems = overrides.findall('propertydefault')

                    # Add each default to data array
                    data = []
                    for elem in elems:
                        if path[1] == "custom":
                            data.append( [elem.attrib.get( 'labelID' ), elem.attrib.get( 'property' ), elem.text ] )
                        else:
                            data.append( [ elem.attrib.get( 'labelID' ), elem.text ] )
                    if len( data ) != 0:
                        dataFiles[path[1]] = data
        
        ## [ [labelID, [property name, property value]] , [labelID, [property name, property value]] ]
        for group in properties:
            # group[0] - labelID
            # group[1] - [ [property name, property value], [] ]
            for property in group[1]:
                type = "custom"
                if property[0] == "widget":
                    type = "widget"
                elif property[0] == "background":
                    type = "background"
                    
                datafile = dataFiles[type]
                    
                if len( datafile ) != 0:
                    # Look for an existing value
                    found = False
                    for currentProperty in datafile:
                        # currentProperty[0] = labelID
                        # currentProperty[1] = property value / (custom) property name
                        # currentProperty[2] = (custom) property value
                        if currentProperty[0] == group[0]:
                            found = True
                            if type == "custom":
                                currentProperty[2] = property[1]
                            else:
                                currentProperty[1] = property[1]
                    if found == False:
                        # No existing value found, add one
                        if type == "custom":
                            datafile.append( [ group[0], property[0], property[1] ] )
                        else:
                            datafile.append( [ group[0], property[1] ] )
                        
                    # Update the dataFiles
                    dataFiles[type] = datafile
                else:
                    # There is nothing in the datafile, so add this
                    if type == "custom":
                        datafile.append( [ group[0], property[0], property[1] ] )
                    else:
                        datafile.append( [ group[0], property[1] ] )
                    dataFiles[type] = datafile
        
        # Save the files
        for path in paths:
            if len( dataFiles[path[1]] ) == 0:
                # Try to delete any existing file
                try:
                    xbmcvfs.delete( path[0] )
                except:
                    print_exc()
                    log( "### No properties, no existing file %s" % __datapath__ )            
            else:
                # Try to save the file
                try:
                    f = xbmcvfs.File( path[0], 'w' )
                    f.write( repr( dataFiles[path[1]] ) )
                    f.close()
                except:
                    print_exc()
                    log( "### ERROR could not save file %s" % __datapath__ )                
    
    def _display_shortcuts( self ):
        # Load the currently selected shortcut group
        if self.shortcutgroup == 1:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayXBMCCommon)
            self.getControl( 101 ).setLabel( __language__(32029) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 2:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayVideoLibrary)
            self.getControl( 101 ).setLabel( __language__(32030) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 3:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayMusicLibrary)
            self.getControl( 101 ).setLabel( __language__(32031) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 4:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayPlaylists)
            self.getControl( 101 ).setLabel( __language__(32040) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 5:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayFavourites)
            self.getControl( 101 ).setLabel( __language__(32006) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 6:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayAddOns)
            self.getControl( 101 ).setLabel( __language__(32007) + " (%s)" %self.getControl( 111 ).size() )
            
    def updateEditControls( self ):
        # Try setting 402's text to the current label
        if self.has402403 == True:
            try:
                self.getControl( 402 ).setText( self.getControl( 211 ).getSelectedItem().getLabel() )
                self.getControl( 403 ).setText( urllib.unquote( self.getControl( 211 ).getSelectedItem().getProperty('path') ) )
            except:
                self.has402403 = False
                
    def onAction( self, action ):
        if action.getId() in ACTION_CANCEL_DIALOG:
            log( "### CLOSING WINDOW" )
            if self.getFocusId() == 402 and action.getId() == 61448: # Check we aren't backspacing on an edit dialog
                return
            if self.getFocusId() == 403 and action.getId() == 61448: # Check we aren't backspacing on an edit dialog
                return
            self._save_shortcuts()
            self._close()
        if self.getFocusId() == 211: # User focused on currently selected shortcut
            self.updateEditControls()

    def _close( self ):
            log('Gui closed')
            self.close()
