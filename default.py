import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, urllib
from traceback import print_exc

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__     = __addon__.getLocalizedString
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__addonname__    = __addon__.getAddonInfo('name').decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')

sys.path.append(__resource__)

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
    
class SkinShortcuts:
    def __init__(self):
        self.WINDOW = xbmcgui.Window( 10000 )

        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
            self.TYPE = params.get( "type", "" )
        except:
            try:
                params = dict( arg.split( "=" ) for arg in sys.argv[ 2 ].split( "&" ) )
                log( "### params: %s" % params )
                self.TYPE = params.get( "?type", "" )
            except:
                params = {}
        log( "### params: %s" % params )
        
        self.GROUP = params.get( "group", "" )
        self.PATH = params.get( "path", "" )
        log( self.PATH )
        
        # Check for existance of certain groups, and create default if not found
        if self.TYPE=="manage" or self.TYPE=="list":
            # If the relevant datafile doesn't exist...
            path = os.path.join( __datapath__ , self.GROUP + ".db" )
            if not os.path.isfile( path ):
                # ... and the skin hasn't provided defaults ...
                if not os.path.isfile( os.path.join( __skinpath__ , self.GROUP + ".db" ) ):
                    # Try to create defaults
                    self._createdefaults()
        
        # Perform action specified by user
        if not self.TYPE:
            line1 = "This addon is for skin developers, and requires skin support"
            xbmcgui.Dialog().ok(__addonname__, line1)
        elif self.TYPE=="manage":
            import gui
            ui= gui.GUI( "script-skinshortcuts.xml", __cwd__, "default", group=self.GROUP )
            ui.doModal()
            del ui
        elif self.TYPE=="list":
            log( "### Listing shortcuts ..." )
            path = os.path.join( __datapath__ , self.GROUP + ".db" )
            
            try:
                # Try loading user-set shortcuts
                loaditems = eval( file( path, "r" ).read() )
                
                listitems = []
                
                for item in loaditems:
                    # Generate a listitem
                    path = sys.argv[0] + "?type=launch&path=" + item[4]
                    
                    listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                    listitem.setProperty('isPlayable', 'False')
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
                    
                # If we've loaded anything, save them to the list
                xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
                            
            except:
                try:
                    # Try loading skin-provided defaults
                    path = os.path.join( __skinpath__ , self.GROUP + ".db" )
                    loaditems = eval( file( path, "r" ).read() )
                    
                    listitems = []
                    
                    for item in loaditems:
                        # Generate a listitem
                        path = sys.argv[0] + "?type=launch&path=" + item[4]
                        
                        listitem = xbmcgui.ListItem(label=item[0], label2=item[1], iconImage=item[2], thumbnailImage=item[3])
                        listitem.setProperty('isPlayable', 'False')
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=listitem, isFolder=False)
                        
                    # If we've loaded anything, save them to the list
                    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
                                
                except:
                    print_exc()
                    log( "### ERROR could not load file %s" % self.GROUP )
                
        elif self.TYPE=="launch":
            log( "### Launching shortcut" )
            log( self.PATH )
            xbmc.executebuiltin( urllib.unquote(self.PATH) )
    
    def _createdefaults( self ):
        # Save shortcuts
        listitems = []
        
        if self.GROUP=="videos":
            # Music videos
            savedata=[__language__(32025), __language__(32014), "DefaultMusicVideos.png", "DefaultMusicVideos.png", urllib.quote( "ActivateWindow(Videos,MusicVideos,return)" )]
            listitems.append(savedata)
            
            # Files
            savedata=[__language__(32026), __language__(32014), "DefaultFolder.png", "DefaultFolder.png", urllib.quote( "ActivateWindow(Videos,Files,return)" )]
            listitems.append(savedata)
            
            # Add-ons
            savedata=[__language__(32052), __language__(32014), "DefaultAddonVideo.png", "DefaultAddonVideo.png", urllib.quote( "ActivateWindow(Videos,Addons,return)" )]
            listitems.append(savedata)
        
        if self.GROUP=="movies":
            # Recently added movies
            savedata=[__language__(32028), __language__(32015), "DefaultRecentlyAddedMovies.png", "DefaultRecentlyAddedMovies.png",  urllib.quote( "ActivateWindow(Videos,RecentlyAddedMovies,return)" )]
            listitems.append(savedata)
            
            # Sets
            savedata=[__language__(32033), __language__(32015), "DefaultSets.png", "DefaultSets.png", urllib.quote( "ActivateWindow(Videos,MovieSets,return)" )]
            listitems.append(savedata)
            
            # Titles
            savedata=[__language__(32036), __language__(32015), "DefaultMovieTitle.png", "DefaultMovieTitle.png", urllib.quote( "ActivateWindow(Videos,MovieTitles,return)" )]
            listitems.append(savedata)
            
            # Genres
            savedata=[__language__(32032), __language__(32015), "DefaultGenre.png", "DefaultGenre.png", urllib.quote( "ActivateWindow(Videos,MovieGenres,return)" )]
            listitems.append(savedata)
            
            # Years
            savedata=[__language__(32037), __language__(32015), "DefaultYear.png", "DefaultYear.png", urllib.quote( "ActivateWindow(Videos,MovieYears,return)" )]
            listitems.append(savedata)
            
            #Actors
            savedata=[__language__(32029), __language__(32015), "DefaultActor.png", "DefaultActor.png", urllib.quote( "ActivateWindow(Videos,MovieActors,return)" )]
            listitems.append(savedata)
            
        if self.GROUP=="tvshows":
            # Recently added
            savedata=[__language__(32028), __language__(32016), "DefaultRecentlyAddedEpisodes.png", "DefaultRecentlyAddedEpisodes.png", urllib.quote( "ActivateWindow(Videos,RecentlyAddedEpisodes,return)" )]
            listitems.append(savedata)
            
            # Title
            savedata=[__language__(32036), __language__(32016), "DefaultTVShowTitle.png", "DefaultTVShowTitle.png", urllib.quote( "ActivateWindow(Videos,TVShowTitles,return)" )]
            listitems.append(savedata)
            
            # Genres
            savedata=[__language__(32032), __language__(32016), "DefaultGenre.png", "DefaultGenre.png", urllib.quote( "ActivateWindow(Videos,TVShowGenres,return)" )]
            listitems.append(savedata)
            
            # Years
            savedata=[__language__(32037), __language__(32016), "DefaultYear.png", "DefaultYear.png", urllib.quote( "ActivateWindow(Videos,TVShowYears,return)" )]
            listitems.append(savedata)
            
            # Actors
            savedata=[__language__(32029), __language__(32016), "DefaultActor.png", "DefaultActor.png", urllib.quote( "ActivateWindow(Videos,TVShowActors,return)" )]
            listitems.append(savedata)
            
        if self.GROUP=="tvshows":
            # TV Channels
            savedata=[__language__(32038), __language__(32017), "DefaultTVShows.png", "DefaultTVShows.png", urllib.quote( "ActivateWindowAndFocus(MyPVR,32,0 ,11,0)" )]
            listitems.append(savedata)
            
            # Radio Channels
            savedata=[__language__(32039), __language__(32017), "DefaultTVShows.png", "DefaultTVShows.png", urllib.quote( "ActivateWindowAndFocus(MyPVR,33,0 ,12,0)" )]
            listitems.append(savedata)
            
            # Guide
            savedata=[__language__(32040), __language__(32017), "DefaultTVShows.png", "DefaultTVShows.png", urllib.quote( "ActivateWindowAndFocus(MyPVR,31,0 ,10,0)" )]
            listitems.append(savedata)
            
            # Recordings
            savedata=[__language__(32041), __language__(32017), "DefaultTVShows.png", "DefaultTVShows.png", urllib.quote( "ActivateWindowAndFocus(MyPVR,34,0 ,13,0)" )]
            listitems.append(savedata)
            
            # Timers
            savedata=[__language__(32042), __language__(32017), "DefaultTVShows.png", "DefaultTVShows.png", urllib.quote( "ActivateWindowAndFocus(MyPVR,35,0 ,14,0)" )]
            listitems.append(savedata)
            
        if self.GROUP=="music":
            # Artists
            savedata=[__language__(32044), __language__(32019), "DefaultMusicArtists.png", "DefaultMusicArtists.png", urllib.quote( "ActivateWindow(MusicLibrary,Artists,return)" )]
            listitems.append(savedata)
            
            # Albums
            savedata=[__language__(32043), __language__(32019), "DefaultMusicAlbums.png", "DefaultMusicAlbums.png", urllib.quote( "ActivateWindow(MusicLibrary,Albums,return)" )]
            listitems.append(savedata)
            
            # Songs
            savedata=[__language__(32047), __language__(32019), "DefaultMusicSongs.png", "DefaultMusicSongs.png", urllib.quote( "ActivateWindow(MusicLibrary,Songs,return)" )]
            listitems.append(savedata)
            
            # Files
            savedata=[__language__(32045), __language__(32019), "DefaultFolder.png", "DefaultFolder.png", urllib.quote( "ActivateWindow(MusicFiles)" )]
            listitems.append(savedata)
            
            # Library
            savedata=[__language__(32046), __language__(32019), "DefaultMusicAlbums.png", "DefaultMusicAlbums.png", urllib.quote( "ActivateWindow(MusicLibrary,return)" )]
            listitems.append(savedata)
            
            # Add-ons
            savedata=[__language__(32052), __language__(32019), "DefaultAddonMusic.png", "DefaultAddonMusic.png", urllib.quote( "ActivateWindow(MusicLibrary,Addons,return)" )]
            listitems.append(savedata)
            
        if self.GROUP=="pictures":
            # Add-ons
            savedata=[__language__(32052), __language__(32020), "DefaultAddonPicture.png", "DefaultAddonPicture.png", urllib.quote( "ActivateWindow(Pictures,Addons,return)" )]
            listitems.append(savedata)
            
        # Save the array if we've added anything
        if listitems:
            path = os.path.join( __datapath__ , self.GROUP + ".db" )
            
            try:
                file( path , "w" ).write( repr( listitems ) )
            except:
                print_exc()
                log( "### ERROR could not save file %s" % __datapath__ )
    
if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    
    SkinShortcuts()
            
    log('script stopped')