# -*- encoding: utf-8 -*-
"""
Python Aplication Template
Licence: GPLv3
"""

import os
from app import app,socketio


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	#app.run(host='0.0.0.0', port=port)
	socketio.run(app, "0.0.0.0", port=5000)
