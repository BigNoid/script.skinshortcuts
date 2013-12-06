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
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')
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
        
        # Empty arrays for different shortcut types
        self.arrayVideoLibrary = []
        self.arrayMusicLibrary = []
        self.arrayVideoPlaylists = []
        self.arrayAudioPlaylists = []
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
            self.getControl( 305 ).setLabel( __language__(32054) )
            self.getControl( 306 ).setLabel( __language__(32055) )
            self.getControl( 307 ).setLabel( __language__(32056) )
            self.getControl( 308 ).setLabel( __language__(32057) )
            
            # Prepare to load favourites
            found, favourites = self._read_file()
            self.listing = favourites
            
            # List video and music library shortcuts
            self._load_videolibrary()
            self._load_musiclibrary()
            
            # Load favourites, playlists, add-ons
            self._fetch_videoplaylists()
            self._fetch_musicplaylists()
            self._fetch_favourites()
            self._fetch_addons()
            
            self._display_shortcuts()
            
            # Load current shortcuts
            self.load_shortcuts()
        
    def _load_videolibrary( self ):
        listitems = []
        log('Listing video library...')
        
        # Videos
        listitem = xbmcgui.ListItem(label=__language__(32022), label2=__language__(32014), iconImage="DefaultMovies.png", thumbnailImage="DefaultMovies.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,Movies,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32023), label2=__language__(32014), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShows,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32024), label2=__language__(32014), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,34,0 ,13,0)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32025), label2=__language__(32014), iconImage="DefaultMusicVideos.png", thumbnailImage="DefaultMusicVideos.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideos,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32026), label2=__language__(32014), iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,Files,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32027), label2=__language__(32014), iconImage="DefaultVideoPlaylists.png", thumbnailImage="DefaultVideoPlaylists.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,Playlists,return)" ) )
        listitems.append(listitem)
        
        # Movies
        listitem = xbmcgui.ListItem(label=__language__(32028), label2=__language__(32015), iconImage="DefaultRecentlyAddedMovies.png", thumbnailImage="DefaultRecentlyAddedMovies.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,RecentlyAddedMovies,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32029), label2=__language__(32015), iconImage="DefaultActor.png", thumbnailImage="DefaultActor.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieActors,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32030), label2=__language__(32015), iconImage="DefaultCountry.png", thumbnailImage="DefaultCountry.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieCountries,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32031), label2=__language__(32015), iconImage="DefaultDirector.png", thumbnailImage="DefaultDirector.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieDirectors,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32032), label2=__language__(32015), iconImage="DefaultGenre.png", thumbnailImage="DefaultGenre.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieGenres,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32033), label2=__language__(32015), iconImage="DefaultSets.png", thumbnailImage="DefaultSets.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieSets,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32034), label2=__language__(32015), iconImage="DefaultStudios.png", thumbnailImage="DefaultStudios.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieStudios,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32035), label2=__language__(32015), iconImage="DefaultTags.png", thumbnailImage="DefaultTags.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieTags,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32036), label2=__language__(32015), iconImage="DefaultMovieTitle.png", thumbnailImage="DefaultMovieTitle.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieTitles,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32037), label2=__language__(32015), iconImage="DefaultYear.png", thumbnailImage="DefaultYear.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MovieYears,return)" ) )
        listitems.append(listitem)
        
        # TV Shows
        listitem = xbmcgui.ListItem(label=__language__(32028), label2=__language__(32016), iconImage="DefaultRecentlyAddedEpisodes.png", thumbnailImage="DefaultRecentlyAddedEpisodes.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,RecentlyAddedEpisodes,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32029), label2=__language__(32016), iconImage="DefaultActor.png", thumbnailImage="DefaultActor.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowActors,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32032), label2=__language__(32016), iconImage="DefaultGenre.png", thumbnailImage="DefaultGenre.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowGenres,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32034), label2=__language__(32016), iconImage="DefaultStudios.png", thumbnailImage="DefaultStudios.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowStudios,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32035), label2=__language__(32016), iconImage="DefaultTags.png", thumbnailImage="DefaultTags.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowTags,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32036), label2=__language__(32016), iconImage="DefaultTVShowTitle.png", thumbnailImage="DefaultTVShowTitle.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowTitles,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32037), label2=__language__(32016), iconImage="DefaultYear.png", thumbnailImage="DefaultYear.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,TVShowYears,return)" ) )
        listitems.append(listitem)

        # PVR
        listitem = xbmcgui.ListItem(label=__language__(32038), label2=__language__(32017), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,32,0 ,11,0)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32039), label2=__language__(32017), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,33,0 ,12,0)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32040), label2=__language__(32017), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,31,0 ,10,0)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32041), label2=__language__(32017), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,34,0 ,13,0)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32042), label2=__language__(32017), iconImage="DefaultTVShows.png", thumbnailImage="DefaultTVShows.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindowAndFocus(MyPVR,35,0 ,14,0)" ) )
        listitems.append(listitem)
        
        # Music Videos
        listitem = xbmcgui.ListItem(label=__language__(32043), label2=__language__(32018), iconImage="DefaultMusicAlbums.png", thumbnailImage="DefaultMusicAlbums.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoAlbums,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32044), label2=__language__(32018), iconImage="DefaultMusicArtists.png", thumbnailImage="DefaultMusicArtists.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoArtists,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32031), label2=__language__(32018), iconImage="DefaultDirector.png", thumbnailImage="DefaultDirector.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoDirectors,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32032), label2=__language__(32018), iconImage="DefaultMusicGenres.png", thumbnailImage="DefaultMusicGenres.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoGenres,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32034), label2=__language__(32018), iconImage="DefaultStudios.png", thumbnailImage="DefaultStudios.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoStudios,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32035), label2=__language__(32018), iconImage="DefaultTags.png", thumbnailImage="DefaultTags.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoTags,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32036), label2=__language__(32018), iconImage="DefaultMusicVideoTitle.png", thumbnailImage="DefaultMusicVideoTitle.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoTitles,return)" ) )
        listitems.append(listitem)        
        listitem = xbmcgui.ListItem(label=__language__(32037), label2=__language__(32018), iconImage="DefaultMusicYears.png", thumbnailImage="DefaultMusicYears.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,MusicVideoYears,return)" ) )
        listitems.append(listitem)        
        
        self.arrayVideoLibrary = listitems
        
    def _load_musiclibrary( self ):
        listitems = []
        log('Listing music library...')
        
        # Music
        listitem = xbmcgui.ListItem(label=__language__(32045), label2=__language__(32019), iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicFiles)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32046), label2=__language__(32019), iconImage="DefaultMusicAlbums.png", thumbnailImage="DefaultMusicAlbums.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,MusicLibrary,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32025), label2=__language__(32019), iconImage="DefaultMusicVideos.png", thumbnailImage="DefaultMusicVideos.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,MusicVideos,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32032), label2=__language__(32019), iconImage="DefaultMusicGenres.png", thumbnailImage="DefaultMusicGenres.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Genres,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32044), label2=__language__(32019), iconImage="DefaultMusicArtists.png", thumbnailImage="DefaultMusicArtists.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Artists,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32043), label2=__language__(32019), iconImage="DefaultMusicAlbums.png", thumbnailImage="DefaultMusicAlbums.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Albums,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32047), label2=__language__(32019), iconImage="DefaultMusicSongs.png", thumbnailImage="DefaultMusicSongs.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Songs,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32037), label2=__language__(32019), iconImage="DefaultMusicYears.png", thumbnailImage="DefaultMusicYears.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Years,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32048), label2=__language__(32019), iconImage="DefaultMusicTop100.png", thumbnailImage="DefaultMusicTop100.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Top100,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32049), label2=__language__(32019), iconImage="DefaultMusicTop100Songs.png", thumbnailImage="DefaultMusicTop100Songs.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Top100Songs,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32050), label2=__language__(32019), iconImage="DefaultMusicTop100Albums.png", thumbnailImage="DefaultMusicTop100Albums.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Top100Albums,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32028), label2=__language__(32019), iconImage="DefaultMusicRecentlyAdded.png", thumbnailImage="DefaultMusicRecentlyAdded.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,RecentlyAddedAlbums,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32051), label2=__language__(32019), iconImage="DefaultMusicRecentlyPlayed.png", thumbnailImage="DefaultMusicRecentlyPlayed.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,RecentlyPlayedAlbums,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32027), label2=__language__(32019), iconImage="DefaultMusicPlaylists.png", thumbnailImage="DefaultMusicPlaylists.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Playlists,return)" ) )
        listitems.append(listitem)
        
        self.arrayMusicLibrary = listitems
        
    def _fetch_videoplaylists( self ):
        listitems = []
        log('Loading playlists...')
        path = 'special://profile/playlists/video/'
        try:
            dirlist = os.listdir( xbmc.translatePath( path ).decode('utf-8') )
        except:
            dirlist = []
        log('dirlist: %s' % dirlist)
        for item in dirlist:
            playlist = os.path.join( path, item)
            playlistfile = xbmc.translatePath( playlist )
            if item.endswith('.xsp'):
                contents = xbmcvfs.File(playlistfile, 'r')
                contents_data = contents.read().decode('utf-8')
                xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                for line in xmldata.getiterator():
                    if line.tag == "name":
                        name = line.text
                        if not name:
                            name = item[:-4]
                        log('Video playlist found %s' % name)
                        listitem = xbmcgui.ListItem(label=name, label2=__language__(32004), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                        listitem.setProperty( "path", urllib.quote( "ActivateWindow(VideoLibrary," + playlist + ", return)" ) )
                        listitem.setProperty( "icon", "DefaultPlaylist.png" )
                        listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                        listitems.append(listitem)
                        break
            elif item.endswith('.m3u'):
                name = item[:-4]
                log('Video playlist found %s' % name)
                listitem = xbmcgui.ListItem(label=name, label2= __language__(32004), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                listitems.append(listitem)
                
        self.arrayVideoPlaylists = listitems

    def _fetch_musicplaylists( self ):
        listitems = []
        # Music Playlists
        log('Loading music playlists...')
        path = 'special://profile/playlists/music/'
        try:
            dirlist = os.listdir( xbmc.translatePath( path ).decode('utf-8') )
        except:
            dirlist = []
        log('dirlist: %s' % dirlist)
        for item in dirlist:
            playlist = os.path.join( path, item)
            playlistfile = xbmc.translatePath( playlist )
            if item.endswith('.xsp'):
                contents = xbmcvfs.File(playlistfile, 'r')
                contents_data = contents.read().decode('utf-8')
                xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                for line in xmldata.getiterator():
                    if line.tag == "name":
                        name = line.text
                        if not name:
                            name = item[:-4]
                        log('Music playlist found %s' % name)
                        listitem = xbmcgui.ListItem(label=name, label2= __language__(32005), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                        listitem.setProperty( "icon", "DefaultPlaylist.png" )
                        listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                        listitems.append(listitem)
                        break
            elif item.endswith('.m3u'):
                name = item[:-4]
                log('Music playlist found %s' % name)
                listitem = xbmcgui.ListItem(label=name, label2= __language__(32005), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                listitem.setProperty( urllib.quote( "path", "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                listitems.append(listitem)
                
        # Mixed Playlists
        log('Loading mixed playlists...')
        path = 'special://profile/playlists/mixed/'
        try:
            dirlist = os.listdir( xbmc.translatePath( path ).decode('utf-8') )
        except:
            dirlist = []
        log('dirlist: %s' % dirlist)
        for item in dirlist:
            playlist = os.path.join( path, item)
            playlistfile = xbmc.translatePath( playlist )
            if item.endswith('.xsp'):
                contents = xbmcvfs.File(playlistfile, 'r')
                contents_data = contents.read().decode('utf-8')
                xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                for line in xmldata.getiterator():
                    if line.tag == "name":
                        name = line.text
                        if not name:
                            name = item[:-4]
                        log('Music playlist found %s' % name)
                        listitem = xbmcgui.ListItem(label=name, label2= __language__(32008), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                        listitem.setProperty( "icon", "DefaultPlaylist.png" )
                        listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                        listitems.append(listitem)
                        break
            elif item.endswith('.m3u'):
                name = item[:-4]
                log('Music playlist found %s' % name)
                listitem = xbmcgui.ListItem(label=name, label2= __language__(32008), iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary," + playlist + ", return)" ) )
                listitems.append(listitem)
        
        self.arrayAudioPlaylists = listitems
                
    def _fetch_favourites( self ):
        listitems = []
        log('Loading favourites...')
        for favourite in self.listing :
            log('Favourite found %s' % favourite.attributes[ 'name' ].nodeValue)
            listitem = xbmcgui.ListItem( label=favourite.attributes[ 'name' ].nodeValue, label2= __language__(32006))
            fav_path = favourite.childNodes [ 0 ].nodeValue
            try:
                if 'playlists/music' in fav_path or 'playlists/video' in fav_path:
                    listitem.setIconImage( "DefaultPlaylist.png" )
                    listitem.setProperty( "icon", "DefaultPlaylist.png" )
                    listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                else:
                    listitem.setIconImage( favourite.attributes[ 'thumb' ].nodeValue )
                    listitem.setProperty( "icon", favourite.attributes[ 'thumb' ].nodeValue )
                    listitem.setProperty( "thumbnail", favourite.attributes[ 'thumb' ].nodeValue )
            except:
                pass
            if 'RunScript' not in fav_path:
                fav_path = fav_path.rstrip(')')
                fav_path = fav_path + ',return)'
            listitem.setProperty( "path", urllib.quote(fav_path) )
            listitems.append(listitem)
        
        self.arrayFavourites = listitems
        
    def _fetch_addons( self ):
        listitems = []
        log( 'Loading add-ons' )
        
        # Add links to each add-on type in library
        listitem = xbmcgui.ListItem(label=__language__(32052), label2=__language__(32014), iconImage="DefaultAddonVideo.png", thumbnailImage="DefaultAddonVideo.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Videos,Addons,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32052), label2=__language__(32019), iconImage="DefaultAddonMusic.png", thumbnailImage="DefaultAddonMusic.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(MusicLibrary,Addons,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32052), label2=__language__(32020), iconImage="DefaultAddonPicture.png", thumbnailImage="DefaultAddonPicture.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Pictures,Addons,return)" ) )
        listitems.append(listitem)
        listitem = xbmcgui.ListItem(label=__language__(32053), label2=__language__(32021), iconImage="DefaultAddonProgram.png", thumbnailImage="DefaultAddonProgram.png")
        listitem.setProperty( "path", urllib.quote( "ActivateWindow(Programs,Addons,return)" ) )
        listitems.append(listitem)
        
        
        
        contenttypes = ["executable", "video", "audio", "image"]
        for contenttype in contenttypes:
            if contenttype == "executable":
                contentlabel = __language__(32009)
            elif contenttype == "video":
                contentlabel = __language__(32010)
            elif contenttype == "audio":
                contentlabel = __language__(32011)
            elif contenttype == "image":
                contentlabel = __language__(32012)
                
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Addons.Getaddons", "params": { "content": "%s", "properties": ["name", "path", "thumbnail", "enabled"] } }' % contenttype)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = simplejson.loads(json_query)
            
            if (json_response['result'] != None) and (json_response['result'].has_key('addons')):
                for item in json_response['result']['addons']:
                    if item['enabled'] == True:
                        log('Addon found %s' % item['name'])
                        listitem = xbmcgui.ListItem(label=item['name'], label2=contentlabel, iconImage=item['thumbnail'], thumbnailImage=item['thumbnail'])
                        listitem.setProperty( "path", urllib.quote( "RunAddOn(" + item['addonid'] + ")" ) )
                        if item['thumbnail'] != "":
                            listitem.setProperty( "icon", item['thumbnail'] )
                            listitem.setProperty( "thumbnail", item['thumbnail'] )
                        else:
                            listitem.setProperty( "icon", "DefaultAddon.png" )
                            listitem.setProperty( "thumbnail", "DefaultAddon.png" )
                            listitem.setIconImage( "DefaultAddon.png" )
                        listitems.append(listitem)
        
        self.arrayAddOns = listitems
    
    def _read_file( self ):
        # Set path
        self.fav_file = xbmc.translatePath( 'special://profile/favourites.xml' ).decode("utf-8")
        # Check to see if file exists
        if xbmcvfs.exists( self.fav_file ):
            found = True
            self.doc = parse( self.fav_file )
            favourites = self.doc.documentElement.getElementsByTagName( 'favourite' )
        else:
            found = False
            favourites = []
        return found, favourites
        
    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.close()
        
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
                    # Duplicate the item and it to the listitems array
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
            custom_label = self.getControl( 211 ).getSelectedItem().getLabel()
            keyboard = xbmc.Keyboard( custom_label, xbmc.getLocalizedString(528), False )
            keyboard.doModal()
            if ( keyboard.isConfirmed() ):
                custom_label = keyboard.getText()
            # Create a copy of the listitem
            listitem = self.getControl( 211 ).getSelectedItem()
            listitemCopy = xbmcgui.ListItem(label=custom_label, label2=listitem.getLabel2(), iconImage=listitem.getProperty("icon"), thumbnailImage=listitem.getProperty("thumbnail"))
            listitemCopy.setProperty( "path", listitem.getProperty("path") )
            listitemCopy.setProperty( "icon", listitem.getProperty("icon") )
            listitemCopy.setProperty( "thumbnail", listitem.getProperty("thumbnail") )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered label
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    log ( "### Found the item" )
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
            
        if controlID == 306:
            # Change icon
            custom_icon = self.getControl( 211 ).getSelectedItem().getProperty( "Icon" )
            dialog = xbmcgui.Dialog()
            custom_icon = dialog.browse( 2 , xbmc.getLocalizedString(1030), 'files')
            # Create a copy of the listitem
            listitem = self.getControl( 211 ).getSelectedItem()
            listitemCopy = xbmcgui.ListItem(label=listitem.getLabel(), label2=listitem.getLabel2(), iconImage=custom_icon, thumbnailImage=listitem.getProperty("thumbnail"))
            listitemCopy.setProperty( "path", listitem.getProperty("path") )
            listitemCopy.setProperty( "icon", custom_icon )
            listitemCopy.setProperty( "thumbnail", listitem.getProperty("thumbnail") )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered icon
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    log ( "### Found the item" )
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

        if controlID == 307:
            # Change thumbnail
            custom_thumbnail = self.getControl( 211 ).getSelectedItem().getProperty( "thumbnail" )
            dialog = xbmcgui.Dialog()
            custom_thumbnail = dialog.browse( 0 , xbmc.getLocalizedString(1031), 'files')
            # Create a copy of the listitem
            listitem = self.getControl( 211 ).getSelectedItem()
            listitemCopy = xbmcgui.ListItem(label=listitem.getLabel(), label2=listitem.getLabel2(), iconImage=listitem.getProperty("icon"), thumbnailImage=custom_thumbnail)
            listitemCopy.setProperty( "path", listitem.getProperty("path") )
            listitemCopy.setProperty( "icon", listitem.getProperty("icon") )
            listitemCopy.setProperty( "thumbnail", custom_thumbnail )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered thumbnail
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    log ( "### Found the item" )
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )

        if controlID == 308:
            # Change path
            custom_path = self.getControl( 211 ).getSelectedItem().getProperty( urllib.unquote( "path" ) )
            keyboard = xbmc.Keyboard( custom_path, xbmc.getLocalizedString(528), False )
            keyboard.doModal()
            if ( keyboard.isConfirmed() ):
                custom_path = keyboard.getText()
            # Create a copy of the listitem
            listitem = self.getControl( 211 ).getSelectedItem()
            listitemCopy = xbmcgui.ListItem(label=listitem.getLabel(), label2=listitem.getLabel2(), iconImage=listitem.getProperty("icon"), thumbnailImage=listitem.getProperty("thumbnail"))
            listitemCopy.setProperty( urllib.quote( "path" ), custom_path )
            listitemCopy.setProperty( "icon", listitem.getProperty("icon") )
            listitemCopy.setProperty( "thumbnail", listitem.getProperty("thumbnail") )
            
            # Loop through the original list, and replace the currently selected listitem with our new listitem with altered path
            listitems = []
            num = self.getControl( 211 ).getSelectedPosition()
            for x in range(0, self.getControl( 211 ).size()):
                if x == num:
                    log ( "### Found the item" )
                    listitems.append(listitemCopy)
                else:
                    # Duplicate the item and it to the listitems array
                    listitemShortcutCopy = self._duplicate_listitem( self.getControl( 211 ).getListItem(x) )
                    
                    listitems.append(listitemShortcutCopy)
                    
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
            
    def load_shortcuts( self ):
        path = os.path.join( __datapath__ , self.group + ".shortcuts" )
        
        try:
            loaditems = eval( file( path, "r" ).read() )
            
            listitems = []
            
            for item in loaditems:
                # Generate a listitem
                
                listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                listitem.setProperty( "path", item[4] )
                listitem.setProperty( "icon", item[2] )
                listitem.setProperty( "thumbnail", item[3] )
                
                listitems.append(listitem)
                
            # If we've loaded anything, save them to the list
            if len(listitems) != 0:
                self.getControl( 211 ).addItems(listitems)
                
            # If there are no items in the list, add an empty one...
            if self.getControl( 211 ).size() == 0:
                listitem = xbmcgui.ListItem( __language__(32013) )
                listitem.setProperty( "Path", 'noop' )
                
                self.getControl( 211 ).addItem( listitem )
                
                # Set focus
                self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
                            
        except:
            path = os.path.join( __skinpath__ , self.group + ".shortcuts" )
            
            try:
                loaditems = eval( file( path, "r" ).read() )
                
                listitems = []
                
                for item in loaditems:
                    # Generate a listitem
                    
                    listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                    listitem.setProperty( "path", item[4] )
                    listitem.setProperty( "icon", item[2] )
                    listitem.setProperty( "thumbnail", item[3] )
                    
                    listitems.append(listitem)
                    
                # If we've loaded anything, save them to the list
                if len(listitems) != 0:
                    self.getControl( 211 ).addItems(listitems)
                    
                # If there are no items in the list, add an empty one...
                if self.getControl( 211 ).size() == 0:
                    listitem = xbmcgui.ListItem( __language__(32013) )
                    listitem.setProperty( "Path", 'noop' )
                    
                    self.getControl( 211 ).addItem( listitem )
                    
                    # Set focus
                    self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
                                
            except:
                print_exc()
                log( "### ERROR could not load file %s" % __datapath__ )
                return []
            
    def _duplicate_listitem( self, listitem ):
        listitemCopy = xbmcgui.ListItem(label=listitem.getLabel(), label2=listitem.getLabel2(), iconImage=listitem.getProperty("icon"), thumbnailImage=listitem.getProperty("thumbnail"))
        listitemCopy.setProperty( "path", listitem.getProperty("path") )
        listitemCopy.setProperty( "icon", listitem.getProperty("icon") )
        listitemCopy.setProperty( "thumbnail", listitem.getProperty("thumbnail") )
        
        return listitemCopy
        
    def _save_shortcuts( self ):
        # Save shortcuts
        listitems = []
        
        for x in range(0, self.getControl( 211 ).size()):
            # If the item has a path, push it to an array
            listitem = self.getControl( 211 ).getListItem(x)
            
            if listitem.getProperty( "path" ) != "noop":
                savedata=[listitem.getLabel(), listitem.getLabel2(), listitem.getProperty("icon"), listitem.getProperty("thumbnail"), listitem.getProperty("path")]
                listitems.append(savedata)
        
        path = os.path.join( __datapath__ , self.group + ".shortcuts" )
        
        if listitems:
            # If there are any shortcuts, save them
            try:
                file( path , "w" ).write( repr( listitems ) )
            except:
                print_exc()
                log( "### ERROR could not save file %s" % __datapath__ )
        else:
            # There are no shortcuts, delete the existing file if it exists
            try:
                os.remove( path )
            except:
                print_exc()
                log( "### No shortcuts, no existing file %s" % __datapath__ )            
    
    def _display_shortcuts( self ):
        # Load the currently selected shortcut group
        if self.shortcutgroup == 1:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayVideoLibrary)
            self.getControl( 101 ).setLabel( "Video Library (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 2:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayMusicLibrary)
            self.getControl( 101 ).setLabel( "Music Library (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 3:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayVideoPlaylists)
            self.getControl( 101 ).setLabel( __language__(32004) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 4:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayAudioPlaylists)
            self.getControl( 101 ).setLabel( __language__(32005) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 5:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayFavourites)
            self.getControl( 101 ).setLabel( __language__(32006) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 6:
            self.getControl( 111 ).reset()
            self.getControl( 111 ).addItems(self.arrayAddOns)
            self.getControl( 101 ).setLabel( __language__(32007) + " (%s)" %self.getControl( 111 ).size() )
            
                
    def onAction( self, action ):
        if action.getId() in ACTION_CANCEL_DIALOG:
            self._save_shortcuts()
            self._close()

    def _close( self ):
            log('Gui closed')
            self.close()
