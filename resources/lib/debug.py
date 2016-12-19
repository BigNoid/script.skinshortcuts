import xbmc, xbmcaddon, xbmcgui
from traceback import print_exc
import json

ADDON        = xbmcaddon.Addon()
LANGUAGE     = ADDON.getLocalizedString

# Common function for trying something that may possibly fail and, if it does, enabling all
# necessary debug options, capturing the error, and offering to upload debug log

def log(txt):
    if ADDON.getSetting( "enable_logging" ) == "true":
        try:
            if isinstance (txt,str):
                txt = txt.decode('utf-8')
            message = u'%s: %s' % (ADDONID, txt)
            xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)
        except:
            pass

def attempt( functionName, arguments, errorTitle, weEnabledSystemDebug = False, weEnabledScriptDebug = False ):
    # Attempt to run the function we've been passed
    try:
        log( "ATTEMPTING" )
        functionName( *tuple( value for value in arguments ) )
        return True
    except:
        print_exc()
    
    # We didn't manage to complete the function, so...

    # If we enabled debug logging
    if weEnabledSystemDebug or weEnabledScriptDebug:
        # Disable any logging we enabled
        if weEnabledSystemDebug:
            json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method":"Settings.setSettingValue", "params": {"setting":"debug.showloginfo", "value":false} } ' )
        if weEnabledScriptDebug:
            ADDON.setSetting( "enable_logging", "false" )
            
        # Offer to upload a debug log
        if xbmc.getCondVisibility( "System.HasAddon( script.kodi.loguploader )" ):
            ret = xbmcgui.Dialog().yesno( ADDON.getAddonInfo( "name" ), errorTitle, LANGUAGE( 32093 ) )
            if ret:
                xbmc.executebuiltin( "RunScript(script.kodi.loguploader)" )
        else:
            xbmcgui.Dialog().ok( ADDON.getAddonInfo( "name" ), errorTitle, LANGUAGE( 32094 ) )
            
    else:
        # Enable any debug logging needed                        
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettings" }')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        
        enabledSystemDebug = False
        enabledScriptDebug = False

        if json_response.has_key('result') and json_response['result'].has_key('settings') and json_response['result']['settings'] is not None:
            for item in json_response['result']['settings']:
                if item["id"] == "debug.showloginfo":
                    if item["value"] == False:
                        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method":"Settings.setSettingValue", "params": {"setting":"debug.showloginfo", "value":true} } ' )
                        enabledSystemDebug = True

        if ADDON.getSetting( "enable_logging" ) != "true":
            ADDON.setSetting( "enable_logging", "true" )
            enabledScriptDebug = True
            
        if enabledSystemDebug or enabledScriptDebug:
            # We enabled one or more of the debug options, re-run this function
            attempt( functionName, arguments, errorTitle, enabledSystemDebug, enabledScriptDebug )
        else:
            # Offer to upload a debug log
            if xbmc.getCondVisibility( "System.HasAddon( script.kodi.loguploader )" ):
                ret = xbmcgui.Dialog().yesno( ADDON.getAddonInfo( "name" ), errorTitle, LANGUAGE( 32093 ) )
                if ret:
                    xbmc.executebuiltin( "RunScript(script.kodi.loguploader)" )
            else:
                xbmcgui.Dialog().ok( ADDON.getAddonInfo( "name" ), errorTitle, LANGUAGE( 32094 ) )

    return False
