# 'Just Select' method

The 'Just Select' method allows you to use Skin Shortcuts to let the user select a shortcut via the script, then have the details of their selection passed back to the skin.

When using this method, you specify which skin strings you want to be set. You can then access these via Skin.String.

The method is called via on onclick as follows:

`RunScript(script.skinshortcuts,type=shortcuts&amp;custom=[True/False]&amp;showNone=[True/False]&amp;grouping=[grouping]&amp;skinLabel=[skinLabel]&amp;skinAction=[skinAction]&amp;skinList=[skinList]&amp;skinType=[skinType]&amp;skinThumbnail=[skinThumbnail])`

| Property | Optional | Description |
| :------: | :------: | ----------- |
| `[True/False]` | Yes | A boolean saying whether the user can type their own shortcut, or whether a 'None' option will be shown |
| `[grouping]`| Yes | The custom groupings that will be shown to the user ([more details](../advanced/Custom groupings.md)) |
| `[skinLabel]` | Yes | The skin string the script will save the label of the selected shortcut to |
| `[skinAction]` | Yes | The skin string the script will save the action of the selected shortcut to |
| `[skinList]` | Yes | The skin string the script will save the action of the selected shortcut, without any 'ActivateWindow' elements, to |
| `[skinType]` | Yes | The skin string the script will save the type of the selected shortcut to |
| `[skinThumbnail]` | Yes | The skin string the script will save the thumbnail of the selected shortcut to |

***Quick links*** - [Readme](../../../README.md) - [Getting Started](../started/Getting Started.md) - [Advanced Usage](./Advanced Usage.md)