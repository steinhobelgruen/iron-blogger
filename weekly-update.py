#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import render
import os
import sys
import xmlrpclib
import subprocess
import datetime
import yaml
import settings

config=settings.load_settings()

dry_run = False
quick_view = False

args = sys.argv[1:]
if args[0] == '-q':
    dry_run = True
    quick_view = True
    args = args[1:]

if args[0] == '-n':
    dry_run = True
    args = args[1:]

date = args[0]
today = str(datetime.date.today())

with open('ledger', 'a') as f:
    f.write("\n")
    f.write(render.render_template('templates/ledger', date))

if not dry_run:
    subprocess.check_call(["git", "commit", "ledger",
                           "-m", "Update for %s" % (date,)])

debts = render.get_debts()
punt = []

with open('ledger', 'a') as f:
    f.write("\n")
    for (user, debt) in debts:
        if debt < 30: continue
        punt.append(user)
        f.write("""\
%(today)s Punt
  Pool:Owed:%(user)s  $-%(debt)s
  User:%(user)s
""" % {'user': user, 'debt': debt, 'today': today})


if not dry_run:
    text = render.render_template('templates/week.tmpl', date, punt=punt)

    lines = text.split("\n")
    title = lines[0]
    body  = "\n".join(lines[1:])

    page = dict(title = title, description = body)

    try:
        subprocess.call(['stty', '-echo'])
        passwd = raw_input("Password for %s: " % (config['username'],))
        print
    finally:
        subprocess.call(['stty', 'echo'])

    x = xmlrpclib.ServerProxy(config['xmlrpc_endpoint'])
    x.metaWeblog.newPost(config['blog_id'], config['username'], passwd, page, True)
email = render.render_template('templates/email.txt', date, punt=punt,mail=config['mail'])
quick = render.render_template('templates/quick_view.tmpl',date,punt=punt)
if quick_view:
    print quick
if dry_run and not quick_view:
    print email
if not dry_run:
    p = subprocess.Popen(['mutt', '-H', '/dev/stdin'],
                         stdin=subprocess.PIPE)
    p.communicate(email)

if punt:
    with open('bloggers.yml') as b:
        bloggers = yaml.safe_load(b)
    for p in punt:
        if 'end' not in bloggers[p]:
            bloggers[p]['end'] = today
    with open('bloggers.yml','w') as b:
        yaml.safe_dump(bloggers, b)

    subprocess.check_call(["git", "commit", "ledger", "bloggers.yml",
                           "-m", "Punts for %s" % (today,)])

# if it's a dry run, lets set the ledger back to the beginning state
if dry_run:
    subprocess.check_call(["git", "checkout", "ledger"])
