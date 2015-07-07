# coding=utf-8
import os
import xbmc, xbmcaddon, xbmcvfs
import xml.etree.ElementTree as xmltree
import hashlib, hashlist
import copy
from traceback import print_exc

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id').decode( 'utf-8' )
__xbmcversion__  = xbmc.getInfoLabel( "System.BuildVersion" ).split(".")[0]
__skinpath__     = xbmc.translatePath( "special://skin/shortcuts/" ).decode('utf-8')

def log(txt):
    if __xbmcversion__ == "13" or __addon__.getSetting( "enable_logging" ) == "true":
        try:
            if isinstance (txt,str):
                txt = txt.decode('utf-8')
            message = u'%s: %s' % (__addonid__, txt)
            xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
        except:
            pass

class Template():
    def __init__( self ):
        # Load the skins template.xml file
        templatepath = os.path.join( __skinpath__ , "template.xml" )
        try:
            self.tree = xmltree.parse( templatepath )
            
            # Add the template.xml to the hash file
            self._save_hash( templatepath, xbmcvfs.File( templatepath ).read() )
        except:
            # We couldn't load the template.xml file
            if xbmcvfs.exists( templatepath ):
                # Unable to parse template.xml
                log( "Unable to parse template.xml. Invalid xml?" )
                self._save_hash( templatepath, xbmcvfs.File( templatepath ).read() )
            else:
                # No template.xml            
                self.tree = None
                self._save_hash( templatepath, None )
            
        # Empty variable which will contain our base elementree (passed from buildxml)
        self.includes = None
        
        # List which will contain 'other' elements we will need to finalize (we won't have all the
        # visibility conditions until the end)
        self.finalize = []
            
    def parseItems( self, menuType, level, items, profile, profileVisibility, visibilityCondition, menuName, mainmenuID = None ):
        # This will build an item in our includes for a menu
        if self.includes is None or self.tree is None:
            return
            
        if profile == "test":
            pass
            
        # Get the template for this menu
        if menuType == "mainmenu":
            template = copy.deepcopy( self.tree.find( "mainmenu" ) )
        else:
            template = self.findSubmenu( menuName, level )
            
        if template is None:
            # There is no template for this
            return
            
        log( " - Template found" )
        
        # We need to check that the relevant includes existing
        # First, the overarching include
        includeName = "skinshortcuts-template"
        if "include" in template.attrib:
            includeName += "-%s" %( template.attrib.get( "include" ) )
        
        treeRoot = self.getInclude( self.includes, includeName, profileVisibility, profile )
        includeTree = self.getInclude( self.includes, includeName + "-%s" %( profile ), None, None )
        
        # Now replace all <skinshortcuts> elements with correct data
        self.replaceElements( template, visibilityCondition, profileVisibility, items )
        
        # Add the template to the includes
        for child in template.find( "controls" ):
            includeTree.append( child )
            
        # Now we want to see if any of the main menu items match a template
        if menuType != "mainmenu":
            return
        for item in items:
            # First we need to build the visibilityCondition, based on the items
            # submenuVisibility element, and the mainmenuID
            visibilityName = ""
            for element in item.findall( "property" ):
                if "name" in element.attrib and element.attrib.get( "name" ) == "submenuVisibility":
                    visibilityName = element.text
                    break
            
            visibilityCondition = "StringCompare(Container(" + mainmenuID + ").ListItem.Property(submenuVisibility)," + visibilityName + ")"
            
            # Now find a matching template - if one matches, it will be saved to be processed
            # at the end (when we have all visibility conditions)
            template = self.findOther( item, profile, profileVisibility, visibilityCondition )
                    
    def writeOthers( self ):
        # This will write any 'other' elements we have into the includes file
        # (now we have all the visibility conditions for them)
        if self.includes is None or self.tree is None:
            return
        
        if len( self.finalize ) == 0:
            return
            
        for template in self.finalize:
            # Get the group name
            name = "skinshortcuts-template"
            if "include" in template.attrib:
                name += "-%s" %( template.attrib.get( "include" ) )
            
            # Loop through any profiles we have
            for profile in template.findall( "skinshortcuts-profile" ):
                visibilityCondition = None
                # Build the visibility condition
                for condition in profile.findall( "visible" ):
                    if visibilityCondition is None:
                        visibilityCondition = condition.text
                    elif condition.text != "":
                        visibilityCondition += " | " + condition.text
                
                # Get the include this will be done under
                root = self.getInclude( self.includes, name, profile.attrib.get( "visible" ), profile.attrib.get( "profile" ) )
                include = self.getInclude( self.includes, "%s-%s" %( name, profile.attrib.get( "profile" ) ), None, None ) #profile.attrib.get( "visible" ) )
                
                # Create a copy of the node with any changes within (this time it'll be visibility)
                final = copy.deepcopy( template )
                self.replaceElements( final, visibilityCondition, profile.attrib.get( "visible" ), [] )
                
                # Add the template to the includes
                for child in final.find( "controls" ):
                    include.append( child )
            
    def getInclude( self, tree, name, condition, profile ):
        # This function gets an existing <include/>, or creates it
        for include in tree.findall( "include" ):
            if include.attrib.get( "name" ) == name:
                if condition is None:
                    return include
                    
                # We've been passed a condition, check there's an include with that
                # as condition and name as text
                for visInclude in include.findall( "include" ):
                    if visInclude.attrib.get( "condition" ) == condition:
                        return include
                        
                # We didn't find condition,so create it
                visInclude = xmltree.SubElement( include, "include" )
                visInclude.set( "condition", condition )
                visInclude.text = name + "-" + profile
                
                return include
        
        # We didn't find the node, so create it
        newInclude = xmltree.SubElement( tree, "include" )
        newInclude.set( "name", name )
        
        # If we've been passed a condition, create an include with that as condition
        # and name as text
        if condition is not None:
            visInclude = xmltree.SubElement( newInclude, "include" )
            visInclude.set( "condition", condition )
            visInclude.text = name + "-" + profile
        
        return newInclude
        
        
    def findSubmenu( self, name, level ):
        # Find the correct submenu template
        returnElem = None
        for elem in self.tree.findall( "submenu" ):
            # Check if the level matched
            if level == 0:
                # No level, so there shouldn't be a level attrib
                if "level" in elem.attrib:
                    continue
            else:
                # There is a level, so make sure there's a level attrib
                if "level" not in elem.attrib:
                    continue
                # Make sure the level values match
                if elem.attrib.get( "level" ) != str( level ):
                    continue
            # If there's a name attrib, check if it matches
            if "name" in elem.attrib:
                if elem.attrib.get( "name" ) == name:
                    # This is the one we want :)
                    return copy.deepcopy( elem )
                else:
                    continue
            # Save this, in case we don't find a better match
            returnElem = elem
            
        return copy.deepcopy( returnElem )
        
    def findOther( self, item, profile, profileVisibility, visibilityCondition ):
        # Find a template matching the item we have been passed
        for elem in self.tree.findall( "other" ):
            template = copy.deepcopy( elem )
            match = True
            
            # Check the conditions
            for condition in template.findall( "condition" ):
                if match == False:
                    break
                if self.checkCondition( condition, item ) == False:
                    match = False
                    break
                
            # If the conditions didn't match, we're done here
            if match == False:
                continue
                
            # All the rules matched, so next we'll get any properties
            properties = self.getProperties( template, item )
            
            # Next up, we do any replacements - EXCEPT for visibility, which
            # we'll store for later (in case multiple items would have an
            # identical template
            self.replaceElements( template.find( "controls" ), None, None, [], properties )
            
            # Now we need to check if we've already got a template identical to this
            textVersion = None
            match = False
            for previous in self.finalize:
                # If we haven't already, convert our new template to a string
                if textVersion is None:
                    textVersion = xmltree.tostring( template.find( "controls" ), encoding='utf8' )
                    
                # Compare string representations
                if textVersion == xmltree.tostring( previous.find( "controls" ), encoding='utf8' ):
                    # They are the same
                    
                    # Add our details to the previous version, so we can build it
                    # with full visibility details later
                    for profileMatch in previous.findall( "skinshortcuts-profile" ):
                        if profileMatch.attrib.get( "profile" ) == profile:
                            # Check if we've already added this visibilityCondition
                            for visible in profileMatch.findall( "visible" ):
                                if visible.text == visibilityCondition:
                                    # The condition is already there
                                    return previous
                            
                            # We didn't find it, so add it
                            xmltree.SubElement( profileMatch, "visible" ).text = visibilityCondition
                            return previous
                            
                    # We didn't find this profile, so add it
                    newElement = xmltree.SubElement( previous, "skinshortcuts-profile" )
                    newElement.set( "profile", profile )
                    newElement.set( "visible", profileVisibility )
                    
                    # And save the visibility condition
                    xmltree.SubElement( newElement, "visible" ).text = visibilityCondition
                    
                    # And we're done
                    return previous
                    
            # We don't have this template saved, so add our profile details to it
            newElement = xmltree.SubElement( template, "skinshortcuts-profile" )
            newElement.set( "profile", profile )
            newElement.set( "visible", profileVisibility )
            
            # Save the visibility condition
            xmltree.SubElement( newElement, "visible" ).text = visibilityCondition
            
            # Add it to our finalize list
            self.finalize.append( template )
            
            return template
            
    def checkCondition( self, condition, items ):
        # Check if a particular condition is matched for an 'other' template
        if "tag" not in condition.attrib:
            # Tag attrib is required
            return False
        else:
            tag = condition.attrib.get( "tag" )
            
        attrib = None
        if "attribute" in condition.attrib:
            attrib = condition.attrib.get( "attribute" ).split( "|" )
            
        # Find all elements with matching tag
        matchedRule = False
        for item in items.findall( tag ):
            if attrib is not None:
                if attrib[ 0 ] not in item.attrib:
                    # Doesn't have the attribute we're looking for
                    continue
                if attrib[ 1 ] != item.attrib.get( attrib[ 0 ] ):
                    # This property doesn't match
                    continue
                    
            if item.text != condition.text:
                # This property doesn't match
                continue
            
            # The rule has been matched :)
            return True
            
        return False
        
    def getProperties( self, elem, items ):
        # Get any properties specified in an 'other' template
        properties = {}
        for property in elem.findall( "property" ):
            value = None
            if "name" not in property.attrib or "tag" not in property.attrib or property.attrib.get( "name" ) in properties:
                # Name and tag both required, so pass on this
                # (or we've already got a property with this name)
                continue
            else:
                name = property.attrib.get( "name" )
                tag = property.attrib.get( "tag" )
            if "attribute" in property.attrib and "value" not in property.attrib:
                # Attribute requires a value, so pass on this
                continue
            else:
                attrib = property.attrib.get( "attribute" ).split( "|" )
                value = property.attrib.get( "value" )
                
            # Let's get looking for any items that match
            matched = False
            for item in items.findall( tag ):
                if attrib is not None:
                    if attrib[ 0 ] not in item.attrib:
                        # Doesn't have the attribute we're looking for
                        continue
                    if attrib[ 1 ] != item.attrib.get( attrib[ 0 ] ):
                        # The attributes value doesn't match
                        continue
                        
                if value is not None and item.text != value:
                    # The value doesn't match
                    continue
                    
                # We've matched a property :)
                if property.text:
                    properties[ name ] = property.text
                else:
                    properties[ name ] = elem.text
                break
        
        return properties
    
    def replaceElements( self, tree, visibilityCondition, profileVisibility, items, properties = {} ):
        for elem in tree:
            # <tag skinshortcuts="visible" /> -> <tag condition="[condition]" />
            if "skinshortcuts" in elem.attrib:
                # Get index of the element
                index = list( tree ).index( elem )
                
                # Get existing attributes, text and tag
                attribs = []
                for singleAttrib in elem.attrib:
                    if singleAttrib == "skinshortcuts":
                        type = elem.attrib.get( "skinshortcuts" )
                    else:
                        attribs.append( ( singleAttrib, elem.attrib.get( singleAttrib ) ) )
                text = elem.text
                tag = elem.tag
                
                # Don't continue is type = visibility, and no visibilityCondition
                if type == "visibility" and visibilityCondition is None:
                    continue
                
                # Remove the existing element
                tree.remove( elem )
                
                # Make replacement element
                newElement = xmltree.Element( tag )
                if text is not None:
                    newElement.text = text
                for singleAttrib in attribs:
                    newElement.set( singleAttrib[ 0 ], singleAttrib[ 1 ] )
                    
                # Make replacements
                if type == "visibility" and visibilityCondition is not None:
                    newElement.set( "condition", visibilityCondition )
                    
                # Insert it
                tree.insert( index, newElement )
            
            # <tag>$skinshortcuts[var]</tag> -> <tag>[value]</tag>
            if elem.text is not None and elem.text.startswith( "$SKINSHORTCUTS[" ) and elem.text[ 15:-1 ] in properties:
                # Replace the text with the property value
                elem.text = properties[ elem.text[ 15:-1 ] ]
            
            # <tag attrib="$skinshortcuts[var]" /> -> <tag attrib="[value]" />
            for attrib in elem.attrib:
                value = elem.attrib.get( attrib )
                if value.startswith( "$SKINSHORTCUTS[" ) and value[ 15:-1 ] in properties:
                    elem.set( attrib, properties[ value[ 15:-1 ] ] )
            
            # <skinshortcuts>visible</skinshortcuts> -> <visible>[condition]</visible>
            # <skinshortcuts>items</skinshortcuts> -> <item/><item/>...
            if elem.tag == "skinshortcuts":
                # Get index of the element
                index = list( tree ).index( elem )
                
                # Get the type of replacement
                type = elem.text
                
                # Don't continue is type = visibility, and no visibilityCondition
                if type == "visibility" and visibilityCondition is None:
                    continue
                
                # Remove the existing element
                tree.remove( elem )
                
                # Make replacements
                if type == "visibility" and visibilityCondition is not None:
                    # Create a new visible element
                    newelement = xmltree.Element( "visible" )
                    newelement.text = visibilityCondition
                    # Insert it
                    tree.insert( index, newelement )
                elif type == "items":
                    # Firstly, go through and create an array of all items in reverse order, without
                    # their existing visible element, if it matches our visibilityCondition
                    newelements = []
                    if items == []:
                        break
                    for item in items.findall( "item" ):
                        newitem = copy.deepcopy( item )

                        # Remove the existing visible elem from this
                        for visibility in newitem.findall( "visible" ):
                            if visibility.text != profileVisibility:
                                continue
                            newitem.remove( visibility )
                        
                        # Add a copy to the array
                        newelements.insert( 0, newitem )
                    if len( newelements ) != 0:
                        for elem in newelements:
                            # Insert them into the template
                            tree.insert( index, elem )
            else:
                # Iterate through tree
                self.replaceElements( elem, visibilityCondition, profileVisibility, items, properties )
            
    def _save_hash( self, filename, file ):
        if file is not None:
            hasher = hashlib.md5()
            hasher.update( file )
            hashlist.list.append( [filename, hasher.hexdigest()] )
        else:
            hashlist.list.append( [filename, None] )            