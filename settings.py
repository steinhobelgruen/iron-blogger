#!/usr/bin/python
import ConfigParser, os

def load_settings():
    configfile = ConfigParser.ConfigParser()
    configfile.read('settings.cfg')
    config=dict()
    config['mail']=configfile.get("general","mail")
    config['start_date']=configfile.get("general","start_date")

    config['username']=configfile.get("blogsettings","username")
    config['xmlrpc_endpoint']=configfile.get("blogsettings","xmlrpc_endpoint")
    config['blog_id']=configfile.get("blogsettings","blog_id")
    config['participants_page_id']=configfile.get("blogsettings","participants_page_id")
    return config