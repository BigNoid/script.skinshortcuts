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
            #xbmc.executebuiltin("ActivateWindow(Pictures)")
            xbmc.executebuiltin( self.PATH.replace( '!EQUALSCHAR!', '=' ) )
    
if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    
    SkinShortcuts()
            
    log('script stopped')