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
        log('script version %s started' % __addonversion__)

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
            
            # Prepare to load favourites
            found, favourites = self._read_file()
            self.listing = favourites
            
            # Set control visibility / Focus
            self.getControl( 121 ).setVisible( False )
            self.getControl( 131 ).setVisible( False )
            self.getControl( 141 ).setVisible( False )
            
            # Load favourites, playlists, add-ons
            self._fetch_videoplaylists()
            self._set_visibility()
            self._fetch_musicplaylists()
            self._fetch_favourites()
            self._fetch_addons()
            
            self._set_visibility()
            
            # Load current shortcuts
            self.load_shortcuts()
            
            # Set default focus
            self.setFocus( self.getControl( 211 ) )
            
    def _fetch_favourites( self ):
        self._check_focus()
        
    def _fetch_videoplaylists( self ):
        listitems = []
        count = 0
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
                        count = count + 1
                        log('Video playlist found %s' % name)
                        listitem = xbmcgui.ListItem(label=name, iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                        listitem.setProperty( "path", "ActivateWindow(VideoLibrary," + playlist + ", return)" )
                        listitem.setProperty( "icon", "DefaultPlaylist.png" )
                        listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                        listitems.append(listitem)
                        break
            elif item.endswith('.m3u'):
                name = item[:-4]
                count = count + 1
                log('Video playlist found %s' % name)
                listitem = xbmcgui.ListItem(label=name, iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                listitem.setProperty( "path", "ActivateWindow(MusicLibrary," + playlist + ", return)" )
                listitems.append(listitem)

        self.getControl( 111 ).addItems( listitems )

    def _fetch_musicplaylists( self ):
        listitems = []
        count = 0
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
                        count = count + 1
                        log('Music playlist found %s' % name)
                        listitem = xbmcgui.ListItem(label=name, iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                        listitem.setProperty( "path", "ActivateWindow(MusicLibrary," + playlist + ", return)" )
                        listitem.setProperty( "icon", "DefaultPlaylist.png" )
                        listitem.setProperty( "thumbnail", "DefaultPlaylist.png" )
                        listitems.append(listitem)
                        break
            elif item.endswith('.m3u'):
                name = item[:-4]
                count = count + 1
                log('Music playlist found %s' % name)
                listitem = xbmcgui.ListItem(label=name, iconImage='DefaultPlaylist.png', thumbnailImage='DefaultPlaylist.png')
                listitem.setProperty( "path", "ActivateWindow(MusicLibrary," + playlist + ", return)" )
                listitems.append(listitem)

        self.getControl( 121 ).addItems( listitems )
                
    def _fetch_favourites( self ):
        listitems = []
        count = 1
        log('Loading favourites...')
        for favourite in self.listing :
            count = count + 1
            log('Favourite found %s' % favourite.attributes[ 'name' ].nodeValue)
            listitem = xbmcgui.ListItem( favourite.attributes[ 'name' ].nodeValue )
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
            listitem.setProperty( "path", fav_path.replace( '=', '!EQUALSCHAR!' ) )
            listitems.append(listitem)
        
        self.getControl( 131 ).addItems( listitems )
        
    def _fetch_addons( self ):
        listitems = []
        count = 0
        contenttypes = ["video", "audio", "image", "executable"]
        for contenttype in contenttypes:
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Addons.Getaddons", "params": { "content": "%s", "properties": ["name", "path", "thumbnail", "enabled"] } }' % contenttype)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = simplejson.loads(json_query)
            log(json_response['result'])
            
            if (json_response['result'] != None) and (json_response['result'].has_key('addons')):
                for item in json_response['result']['addons']:
                    count = count + 1
                    if item['enabled'] == True:
                        log('Addon found %s' % item['name'])
                        listitem = xbmcgui.ListItem(label=item['name'], iconImage=item['thumbnail'], thumbnailImage=item['thumbnail'])
                        listitem.setProperty( "path", "RunAddOn(" + item['addonid'] + ")" )
                        listitem.setProperty( "icon", item['thumbnail'] )
                        listitem.setProperty( "thumbnail", item['thumbnail'] )
                        listitems.append(listitem)
            
        self.getControl( 141 ).addItems( listitems )
    
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
        
    def _fetch_currentshortcuts( self ):
        listitems = []
        log('Loading current shortcuts...')
        # add a dummy item with no action assigned
        listitem = xbmcgui.ListItem( __language__(32008) )
        listitem.setProperty( "Path", 'noop' )
        listitems.append(listitem)
        
        self.getControl( 211 ).addItems( listitems )

        
    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.close()
        
    def onClick(self, controlID):
        if controlID == 102:
            self.shortcutgroup = self.shortcutgroup - 1
            if self.shortcutgroup == 0:
                self.shortcutgroup = 4
                
            self._set_visibility()

        if controlID == 103:
            self.shortcutgroup = self.shortcutgroup + 1
            if self.shortcutgroup == 5:
                self.shortcutgroup = 1
                
            self._set_visibility()
            
        if controlID == 111 or controlID == 121 or controlID == 131 or controlID == 141:
            # Create a copy of the listitem
            if controlID == 111:
                listitemCopy = self._duplicate_listitem( self.getControl( 111 ).getSelectedItem() )
                listitemCopy.setLabel2( __language__(32004) )
            if controlID == 121:
                listitemCopy = self._duplicate_listitem( self.getControl( 121 ).getSelectedItem() )
                listitemCopy.setLabel2( __language__(32005) )
            if controlID == 131:
                listitemCopy = self._duplicate_listitem( self.getControl( 131 ).getSelectedItem() )
                listitemCopy.setLabel2( __language__(32006) )
            if controlID == 141:
                listitemCopy = self._duplicate_listitem( self.getControl( 141 ).getSelectedItem() )
                listitemCopy.setLabel2( __language__(32007) )
            
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
                    
            log( listitems )
            self.getControl( 211 ).reset()
            self.getControl( 211 ).addItems(listitems)
            
            self.getControl( 211 ).selectItem( num )
        
        if controlID == 301:
            # Add a new item
            listitem = xbmcgui.ListItem( __language__(32008) )
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
                listitem = xbmcgui.ListItem( __language__(32008) )
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

    def load_shortcuts( self ):
        path = os.path.join( __datapath__ , self.group + ".db" )
        
        try:
            loaditems = eval( file( path, "r" ).read() )
            
            listitems = []
            
            for item in loaditems:
                # Generate a listitem
                log( item[0] )
                
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
                listitem = xbmcgui.ListItem( __language__(32008) )
                listitem.setProperty( "Path", 'noop' )
                
                self.getControl( 211 ).addItem( listitem )
                
                # Set focus
                self.getControl( 211 ).selectItem( self.getControl( 211 ).size() -1 )
                            
        except:
            print_exc()
            log( "### ERROR could not load file %s" % temp )
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
        
        # Save the array
        path = os.path.join( __datapath__ , self.group + ".db" )
        
        try:
            file( path , "w" ).write( repr( listitems ) )
        except:
            print_exc()
            log( "### ERROR could not save file %s" % __datapath__ )
    
    def _set_visibility( self ):
        # Adjust the visibility of the shortcut lists
        self.getControl( 111 ).setVisible( False )
        self.getControl( 121 ).setVisible( False )
        self.getControl( 131 ).setVisible( False )
        self.getControl( 141 ).setVisible( False )
        
        if self.shortcutgroup == 1:
            self.getControl( 111 ).setVisible( True )
            self.getControl( 101 ).setLabel( __language__(32004) + " (%s)" %self.getControl( 111 ).size() )
        if self.shortcutgroup == 2:
            self.getControl( 121 ).setVisible( True )
            self.getControl( 101 ).setLabel( __language__(32005) + " (%s)" %self.getControl( 121 ).size() )
        if self.shortcutgroup == 3:
            self.getControl( 131 ).setVisible( True )
            self.getControl( 101 ).setLabel( __language__(32006) + " (%s)" %self.getControl( 131 ).size() )
        if self.shortcutgroup == 4:
            self.getControl( 141 ).setVisible( True )
            self.getControl( 101 ).setLabel( __language__(32007) + " (%s)" %self.getControl( 141 ).size() )
            
                
    def onAction( self, action ):
        if action.getId() in ACTION_CANCEL_DIALOG:
            self._save_shortcuts()
            self._close()

    def _close( self ):
            log('Gui closed')
            self.close()
