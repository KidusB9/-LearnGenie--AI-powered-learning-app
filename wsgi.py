# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys

# Activate the virtual environment
activate_this = '/home/kidusb/abc/myenv/bin/activate_this.py'
with open(activate_this) as f:
    code = compile(f.read(), activate_this, 'exec')
    exec(code, dict(__file__=activate_this))

# Add your project directory to sys.path
project_home = '/home/kidusb/abc'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Append the path to your local site-packages
sys.path.append('/home/kidusb/.local/lib/python3.10/site-packages')

# Import the Flask app
from app import app as application

