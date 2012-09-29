#!/usr/bin/python

import render
import os
import sys
import xmlrpclib
import subprocess
import settings

config=settings.load_settings()

x = xmlrpclib.ServerProxy(config['xmlrpc_endpoint'])
page = x.wp.getPage(config['blog_id'], config['participants_page_id'], config['username'], config['password'])

text = render.render_template('templates/users.tmpl')
page['description'] = text

x.wp.editPage(config['blog_id'], config['participants_page_id'], config['username'], config['password'],page,True)
