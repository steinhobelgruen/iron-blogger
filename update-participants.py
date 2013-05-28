#!/usr/bin/python

import render
import os
import sys
import xmlrpclib
import subprocess
import settings
from datetime import datetime

config=settings.load_settings()

x = xmlrpclib.ServerProxy(config['xmlrpc_endpoint'])
page = x.wp.getPage(config['blog_id'], config['participants_page_id'], config['username'], config['password'])

text = render.render_template('templates/users.tmpl',datetime.now().strftime("%Y/%m/%d"))
page['description'] = text

x.wp.editPage(config['blog_id'], config['participants_page_id'], config['username'], config['password'],page,True)
