import sys
import xbmcplugin
import xbmcgui
import urllib.parse

handle = int(sys.argv[1])

def list_items():
    url = sys.argv[0] + '?action=play'
    li = xbmcgui.ListItem(label='Test Stream')
    li.setArt({'thumb': 'icon.png', 'fanart': 'fanart.jpg'})
    li.setInfo('video', {'title': 'Test Stream', 'genre': 'Demo'})
    li.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def play_video():
    stream_url = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
    li = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(handle, True, li)

params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
if params.get('action') == 'play':
    play_video()
else:
    list_items()
