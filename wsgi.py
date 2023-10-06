# -*- coding: utf-8 -*-
from app import app, startup
import bottle

# bottle.debug(True)

startup()
application = bottle.default_app()
