# coding=utf-8
import os, sys, datetime, unicodedata, re, types
import xbmc, xbmcaddon, xbmcgui, xbmcvfs, urllib
import xml.etree.ElementTree as xmltree
import hashlib, hashlist
import cPickle as pickle
from xml.dom.minidom import parse
from traceback import print_exc
from htmlentitydefs import name2codepoint
from unidecode import unidecode

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id').decode( 'utf-8' )
__addonversion__ = __addon__.getAddonInfo('version')
__xbmcversion__  = xbmc.getInfoLabel( "System.BuildVersion" ).split(".")[0]
__language__     = __addon__.getLocalizedString
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__addonname__    = __addon__.getAddonInfo('name').decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ )
__profilepath__  = xbmc.translatePath( "special://profile/" ).decode('utf-8')
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')
__defaultpath__  = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'shortcuts').encode("utf-8") ).decode("utf-8")

# character entity reference
CHAR_ENTITY_REXP = re.compile('&(%s);' % '|'.join(name2codepoint))

# decimal character reference
DECIMAL_REXP = re.compile('&#(\d+);')

# hexadecimal character reference
HEX_REXP = re.compile('&#x([\da-fA-F]+);')

REPLACE1_REXP = re.compile(r'[\']+')
REPLACE2_REXP = re.compile(r'[^-a-z0-9]+')
REMOVE_REXP = re.compile('-{2,}')

def log(txt):
    if __xbmcversion__ == "13" or __addon__.getSetting( "enable_logging" ) == "true":
        try:
            if isinstance (txt,str):
                txt = txt.decode('utf-8')
            message = u'%s: %s' % (__addonid__, txt)
            xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
        except:
            pass
    
class NodeFunctions():
    def __init__(self):
        self.indexCounter = 0
        
    def get_video_nodes( self, path ):
        dirs, files = xbmcvfs.listdir( path )
        nodes = {}
        
        try:
            for dir in dirs:
                self.parse_node( os.path.join( path, dir ), dir, nodes )
            for file in files:
                self.parse_view( os.path.join( path, file.decode( "utf-8" ) ), nodes, origPath = "library://video/%s" % (file ) )
        except:
            print_exc()
            return False
        
        return nodes
        
    def parse_node( self, node, dir, nodes ):
        # If the folder we've been passed contains an index.xml, send that file to be processed
        if xbmcvfs.exists( os.path.join( node, "index.xml" ) ):
            self.parse_view( os.path.join( node, "index.xml" ), nodes, True, "library://video/%s/" % (dir), node )
    
    def parse_view( self, file, nodes, isFolder = False, origFolder = None, origPath = None ):
        if origFolder is not None:
            log( repr( origFolder ) )
        if not isFolder and file.endswith( "index.xml" ):
            return
        try:
            # Load the xml file
            tree = xmltree.parse( file )
            root = tree.getroot()
            
            # Get the item index
            if "order" in tree.getroot().attrib:
                index = tree.getroot().attrib.get( "order" )
                origIndex = index
                while int( index ) in nodes:
                    index = int( index )
                    index += 1
                    index = str( index )
            else:
                self.indexCounter -= 1
                index = str( self.indexCounter )
                origIndex = "-"
                
            # Get label and icon
            label = root.find( "label" ).text
            
            icon = root.find( "icon" )
            if icon is not None:
                icon = icon.text
            else:
                icon = ""
            
            if isFolder:
                # Add it to our list of nodes
                nodes[ int( index ) ] = [ label, icon, origFolder.decode( "utf-8" ), "folder", origIndex ]
            else:
                # Check for a path
                path = root.find( "path" )
                if path is not None:
                    # Change the origPath (the url used as the shortcut address) to it
                    origPath = path.text
                    
                # Check for a grouping
                group = root.find( "group" )
                if group is None:
                    # Add it as an item
                    nodes[ int( index ) ] = [ label, icon, origPath, "item", origIndex ]
                else:
                    # Add it as grouped
                    nodes[ int( index ) ] = [ label, icon, origPath, "grouped", origIndex ]
        except:
            print_exc()
            
    def isGrouped( self, path ):        
        customPath = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video" ) )[:-1]
        defaultPath = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", "video" ) )[:-1]
        
        if xbmcvfs.exists( customPath ):
            path = customPath
        elif xbmcvfs.exists( defaultPath ):
            path = defaultPath
        else:
            return False
        
        # Open the file
        try:
            # Load the xml file
            tree = xmltree.parse( path )
            root = tree.getroot()

            group = root.find( "group" )
            if group is None:
                return False
            else:
                return True
        except:
            return False
            
    def get_visibility( self, path ):
        path = path.replace( "videodb://", "library://video/" )
        #log( "Getting visibility for " + path )
        
        customPath = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video" ) ) + "index.xml"
        customFile = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://profile".decode('utf-8') ), "library", "video" ) )[:-1] + ".xml"
        defaultPath = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", "video" ) ) + "index.xml"
        defaultFile = path.replace( "library://video", os.path.join( xbmc.translatePath( "special://xbmc".decode('utf-8') ), "system", "library", "video" ) )[:-1] + ".xml"
        
        #log( customPath )
        #log( customFile )
        #log( defaultPath )
        #log( defaultFile )
        
        # Check whether the node exists - either as a parent node (with an index.xml) or a view node (append .xml)
        # in first custom video nodes, then default video nodes
        if xbmcvfs.exists( customPath ):
            path = customPath
        elif xbmcvfs.exists( customFile ):
            path = customFile
        elif xbmcvfs.exists( defaultPath ):
            path = defaultPath
        elif xbmcvfs.exists( defaultFile ):
            path = defaultFile
        else:
            return ""
            
        # Open the file
        try:
            # Load the xml file
            tree = xmltree.parse( path )
            root = tree.getroot()

            if "visible" in root.attrib:
                return root.attrib.get( "visible" )
            else:
                return ""
        except:
            return False
