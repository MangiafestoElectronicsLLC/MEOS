# -*- coding: utf-8 -*-
"""MEOS Hub startup service: sets up the default integrations on boot."""
import xbmc

from resources.lib.integrations import bootstrap
from resources.lib.utils import kodi

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    # Let Kodi finish starting (and repositories sync) before installing.
    if not monitor.waitForAbort(30) and kodi.get_setting_bool('auto_install_defaults', True):
        try:
            bootstrap.ensure_defaults()
        except Exception as exc:
            kodi.log('bootstrap failed: {0}'.format(exc), kodi.LOGERROR)
