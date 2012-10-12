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
send_mail = True
quick_view = False
reminder = False

args = sys.argv[1:]

if len(args)>0:
    if args[0] == '-q':
        dry_run = True
        quick_view = True
	send_mail = False
        args = args[1:]

    if args[0] == '-r':
        dry_run = True
        reminder = True
        args = args[1:]

    if args[0] == '-n':
        dry_run = True
	send_mail = False
        args = args[1:]

date = args[0]

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
%(date)s Punt
  Pool:Owed:%(user)s  $-%(debt)s
  User:%(user)s
""" % {'user': user, 'debt': debt, 'date': date})


if not dry_run:
    text = render.render_template('templates/week.tmpl', date, punt=punt)

    lines = text.split("\n")
    title = lines[0]
    body  = "\n".join(lines[1:])

    page = dict(title = title, description = body)

    x = xmlrpclib.ServerProxy(config['xmlrpc_endpoint'])
    x.metaWeblog.newPost(config['blog_id'], config['username'], config['password'], page, True)
if not reminder:
    email = render.render_template('templates/email.txt', date, punt=punt,mail=config['mail'])
else:
    email = render.render_template('templates/reminder.txt', date, punt=punt,mail=config['mail'])
if quick_view:
    print(render.render_template('templates/quick_view.tmpl',date,punt=punt))
if dry_run and not quick_view:
    print email
if send_mail:
    # p = subprocess.Popen(['mutt', '-H', '/dev/stdin'],
    p = subprocess.Popen(['/usr/sbin/sendmail', '-oi', '-t'],
                         stdin=subprocess.PIPE)
    p.communicate(email)

if punt and not dry_run:
    with open('bloggers.yml') as b:
        bloggers = yaml.safe_load(b)
    for p in punt:
        if 'end' not in bloggers[p]:
            bloggers[p]['end'] = date
    with open('bloggers.yml','w') as b:
        yaml.safe_dump(bloggers, b)

    subprocess.check_call(["git", "commit", "ledger", "bloggers.yml",
                           "-m", "Punts for %s" % (date,)])

# if it's a dry run, lets set the ledger back to the beginning state
if dry_run:
    subprocess.check_call(["git", "checkout", "ledger"])
