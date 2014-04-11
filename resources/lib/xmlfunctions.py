# coding=utf-8
import os, sys, datetime, unicodedata
import xbmc, xbmcgui, xbmcvfs, xbmcaddon, urllib
import xml.etree.ElementTree as xmltree
from xml.dom.minidom import parse
from xml.sax.saxutils import escape as escapeXML
from traceback import print_exc

__addon__        = xbmcaddon.Addon()
__addonid__      = sys.modules[ "__main__" ].__addonid__
__datapath__     = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ).decode('utf-8'), __addonid__ ).encode('utf-8')
__language__     = __addon__.getLocalizedString

import datafunctions
DATA = datafunctions.DataFunctions()
import hashlib, hashlist

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)
    
class XMLFunctions():
    def __init__(self):
        log( "Loaded xml functions" )
        
    def buildMenu( self, mainmenuID, groups, numLevels, buildSingle ):
        # Entry point for building includes.xml files
        if xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-isrunning" ) == "True":
            return
        
        xbmcgui.Window( 10000 ).setProperty( "skinshortcuts-isrunning", "True" )
        
        if self.shouldwerun() == False:
            log( "Menu is up to date" )
            xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-isrunning" )
            return

        progress = None
        # Create a progress dialog
        progress = xbmcgui.DialogProgressBG()
        progress.create(__addon__.getAddonInfo( "name" ), __language__( 32049 ) )
        progress.update( 0 )

            
        # Write the menus
        try:
            self.writexml( mainmenuID, groups, numLevels, buildSingle, progress )
            complete = True
        except:
            log( "Failed to write menu" )
            print_exc()
            complete = False
            
        
        # Clear window properties for overrides, widgets, backgrounds, properties
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-overrides-skin" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-overrides-skin-data" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-overrides-user" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-overrides-user-data" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcutsWidgets" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcutsCustomProperties" )
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcutsBackgrounds" )
        
        # Mark that we're no longer running, clear the progress dialog
        xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-isrunning" )
        progress.close()
        
        # Reload the skin
        if complete == True:
            xbmc.executebuiltin( "XBMC.ReloadSkin()" )
        else:
            xbmcgui.Dialog().ok( __addon__.getAddonInfo( "name" ), "Unable to build menu" )
        
    def shouldwerun( self ):
        log( "Checking is user has updated menu" )
        try:
            property = xbmcgui.Window( 10000 ).getProperty( "skinshortcuts-reloadmainmenu" )
            xbmcgui.Window( 10000 ).clearProperty( "skinshortcuts-reloadmainmenu" )
            if property == "True":
                log( " - Yes")
                return True
        except:
            log( " - No" )
            
        log( "Checking include files exist" )
        # Get the skins addon.xml file
        addonpath = xbmc.translatePath( os.path.join( "special://skin/", 'addon.xml').encode("utf-8") ).decode("utf-8")
        addon = xmltree.parse( addonpath )
        extensionpoints = addon.findall( "extension" )
        paths = []
        skinpaths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get( "point" ) == "xbmc.gui.skin":
                resolutions = extensionpoint.findall( "res" )
                for resolution in resolutions:
                    path = xbmc.translatePath( os.path.join( "special://skin/", resolution.attrib.get( "folder" ), "script-skinshortcuts-includes.xml").encode("utf-8") ).decode("utf-8")
                    paths.append( path )
                    skinpaths.append( path )
        
        # Check for the includes file
        for path in paths:
            if not xbmcvfs.exists( path ):
                log( " - No" )
                return True
            else:
                log( " - Yes" )

        
        log( "Checking hashes..." )

        try:
            hashes = eval( xbmcvfs.File( os.path.join( __datapath__ , xbmc.getSkinDir() + ".hash" ) ).read() )
        except:
            # There is no hash list, return True
            print_exc()
            return True
            
        for hash in hashes:
            if hash[1] is not None:
                hasher = hashlib.md5()
                hasher.update( xbmcvfs.File( hash[0] ).read() )
                if hasher.hexdigest() != hash[1]:
                    log( "  - Hash does not match on file " + hash[0] )
                    return True
            else:
                if xbmcvfs.exists( hash[0] ):
                    log( "  - File now exists " + hash[0] )
                    return True
                
        return False


    def writexml( self, mainmenuID, groups, numLevels, buildSingle, progress ):        
        # Clear the hashlist
        hashlist.list = []
        
        # Create a new tree and includes for the various groups
        tree = xmltree.ElementTree( xmltree.Element( "includes" ) )
        root = tree.getroot()
        
        mainmenuTree = xmltree.SubElement( root, "include" )
        mainmenuTree.set( "name", "skinshortcuts-mainmenu" )
        
        submenuTrees = []
        for level in range( 0,  int( numLevels) + 1 ):
            subelement = xmltree.SubElement(root, "include")
            subtree = xmltree.SubElement( root, "include" )
            if level == 0:
                subtree.set( "name", "skinshortcuts-submenu" )
            else:
                subtree.set( "name", "skinshortcuts-submenu-" + str( level ) )
            submenuTrees.append( subtree )
        
        if buildSingle:
            allmenuTree = xmltree.SubElement( root, "include" )
            allmenuTree.set( "name", "skinshortcuts-allmenus" )
        
        # Get groups OR main menu shortcuts
        if not groups == "":
            menuitems = groups.split( "|" )
        else:
            menuitems = DATA._get_shortcuts( "mainmenu", True )
            
        if len( menuitems ) == 0:
            return
            
        # Work out percentages for dialog
        percent = 100 / len( menuitems )
            
        i = 0
        for item in menuitems:
            i += 1
            progress.update( percent * i )
            
            # Build the main menu item
            if groups == "":
                mainmenuItemA = self.buildElement( item, mainmenuTree, "mainmenu", None )
                if buildSingle:
                    mainmenuItemB = self.buildElement( item, allmenuTree, "mainmenu", None )
                submenu = item[5]
            else:
                submenu = item
            
            # Build the sub-menu items
            count = 0
            
            for submenuTree in submenuTrees:
                # Create trees for individual submenu's
                justmenuTreeA = xmltree.SubElement( root, "include" )
                justmenuTreeB = xmltree.SubElement( root, "include" )
                
                # Get the submenu items
                if count == 0:
                    justmenuTreeA.set( "name", "skinshortcuts-group-" + DATA.slugify( submenu ) )
                    justmenuTreeB.set( "name", "skinshortcuts-group-alt-" + DATA.slugify( submenu ) )
                    submenuitems = DATA._get_shortcuts( submenu, True )
                    
                    # Set whether there are any submenu items for the main menu
                    if groups == "":
                        if not len( submenuitems ) == 0:
                            hasSubMenu = xmltree.SubElement( mainmenuItemA, "property" )
                            hasSubMenu.set( "name", "hasSubmenu" )
                            hasSubMenu.text = "True"
                            if buildSingle:
                                hasSubMenu = xmltree.SubElement( mainmenuItemB, "property" )
                                hasSubMenu.set( "name", "hasSubmenu" )
                                hasSubMenu.text = "True"
                            
                else:
                    justmenuTreeA.set( "name", "skinshortcuts-group-" + DATA.slugify( submenu ) ) + "-" + str( count )
                    justmenuTreeB.set( "name", "skinshortcuts-group-alt-" + DATA.slugify( submenu ) ) + "-" + str( count )
                    submenuitems = DATA._get_shortcuts( submenu + "." + str( count ), True )
                    
                log( "Count: " + str( len( submenuitems ) ) )
                log( repr( submenuitems ) )
                
                # If there is a submenu, and we're building a single menu list, replace the onclick of mainmenuItemB AND recreate it as the first
                # submenu item
                if buildSingle and not len( submenuitems ) == 0:
                    onClickElement = mainmenuItemB.find( "onclick" )
                    altOnClick = xmltree.SubElement( mainmenuItemB, "onclick" )
                    altOnClick.text = onClickElement.text
                    altOnClick.set( "condition", "StringCompare(Window(10000).Property(submenuVisibility)," + DATA.slugify( submenu ) + ")" )
                    onClickElement.text = "SetProperty(submenuVisibility," + DATA.slugify( submenu ) + ",10000)"
                    onClickElement.set( "condition", "!StringCompare(Window(10000).Property(submenuVisibility)," + DATA.slugify( submenu ) + ")" )
                    
                    #self.buildElement( item, allmenuTree, submenu, "StringCompare(Window(10000).Property(submenuVisibility)," + escapeXML( DATA.slugify( submenu ) ) + ")" )
                    #xmltree.SubElement( mainmenuItemB, "onclick" ).text = "Replaced :)"
                    
                for subitem in submenuitems:
                    self.buildElement( subitem, submenuTree, submenu, "StringCompare(Container(" + mainmenuID + ").ListItem.Property(submenuVisibility)," + escapeXML( DATA.slugify( submenu ) ) + ")" )
                    self.buildElement( subitem, justmenuTreeA, submenu, None )
                    self.buildElement( subitem, justmenuTreeB, submenu, "StringCompare(Window(10000).Property(submenuVisibility)," + DATA.slugify( submenu ) + ")" )
                    if buildSingle:
                        self.buildElement( subitem, allmenuTree, submenu, "StringCompare(Window(10000).Property(submenuVisibility)," + DATA.slugify( submenu ) + ")" )
            
                # Increase the counter
                count += 1
            
        progress.update( 100 )
            
        # Get the skins addon.xml file
        addonpath = xbmc.translatePath( os.path.join( "special://skin/", 'addon.xml').encode("utf-8") ).decode("utf-8")
        addon = xmltree.parse( addonpath )
        extensionpoints = addon.findall( "extension" )
        paths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get( "point" ) == "xbmc.gui.skin":
                resolutions = extensionpoint.findall( "res" )
                for resolution in resolutions:
                    path = xbmc.translatePath( os.path.join( "special://skin/", resolution.attrib.get( "folder" ), "script-skinshortcuts-includes.xml").encode("utf-8") ).decode("utf-8")
                    paths.append( path )
        
        # Save the tree
        for path in paths:
            tree.write( path, encoding="UTF-8" )
            #tree.write( "C://temp//temp.xml", encoding="UTF-8" )
        
        # Save the hashes
        file = xbmcvfs.File( os.path.join( __datapath__ , xbmc.getSkinDir() + ".hash" ), "w" )
        file.write( repr( hashlist.list ) )
        file.close
        
    def buildElement( self, item, Tree, groupName, visibilityCondition ):
        # This function will build an element for the passed Item in
        # the passed Tree
        newelement = xmltree.SubElement( Tree, "item" )
        
        # Onclick
        action = urllib.unquote( item[4] )
        if action.find("::MULTIPLE::") == -1:
            # Single action, run it
            onclick = xmltree.SubElement( newelement, "onclick" )
            onclick.text = action
        else:
            # Multiple actions, separated by |
            actions = action.split( "|" )
            for singleAction in actions:
                if singleAction != "::MULTIPLE::":
                    onclick = xmltree.SubElement( newelement, "onclick" )
                    onclick.text = singleAction
        
        # Label
        label = xmltree.SubElement( newelement, "label" )
        label.text = item[0]
        
        # Label 2
        label2 = xmltree.SubElement( newelement, "label2" )
        if not item[1].find( "::SCRIPT::" ) == -1:
            label2.text = __language__( int( item[1][10:] ) )
        else:
            label2.text = item[1]


        # Icon
        icon = xmltree.SubElement( newelement, "icon" )
        icon.text = item[2]
        
        # Thumb
        thumb = xmltree.SubElement( newelement, "thumb" )
        thumb.text = item[3]
        
        # LabelID
        labelID = xmltree.SubElement( newelement, "property" )
        labelID.set( "name", "labelID" )
        labelID.text = item[5]
        
        # Group name
        group = xmltree.SubElement( newelement, "property" )
        group.set( "name", "group" )
        group.text = groupName
        
        # Submenu visibility
        if groupName == "mainmenu":
            submenuVisibility = xmltree.SubElement( newelement, "property" )
            submenuVisibility.set( "name", "submenuVisibility" )
            submenuVisibility.text = DATA.slugify( item[5] )
            
        # Visibility
        if visibilityCondition is not None:
            visibilityElement = xmltree.SubElement( newelement, "visible" )
            visibilityElement.text = visibilityCondition
            issubmenuElement = xmltree.SubElement( newelement, "property" )
            issubmenuElement.set( "name", "isSubmenu" )
            issubmenuElement.text = "True"
        
        # Additional properties
        if len( item[6] ) != 0:
            repr( item[6] )
            for property in item[6]:
                if property[0] == "node.visible":
                    visibleProperty = xmltree.SubElement( newelement, "visible" )
                    visibleProperty.text = property[1]
                else:
                    additionalproperty = xmltree.SubElement( newelement, "property" )
                    additionalproperty.set( "name", property[0] )
                    additionalproperty.text = property[1]
                    
        return newelement
        
    def findIncludePosition( self, list, item ):
        try:
            return list.index( item )
        except:
            return None
            
            
