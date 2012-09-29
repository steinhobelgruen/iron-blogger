#!/usr/bin/python
# This Python file uses the following encoding: utf-8
import yaml
from dateutil.parser import parse
import datetime
import dateutil.tz as tz
import sys
import os
import os.path
import subprocess
import settings
from mako.template import Template

config=settings.load_settings()

START = datetime.datetime.strptime(config['start_date'],"%Y/%m/%d")
HERE  = os.path.dirname(__file__)

def get_balance(acct):
    p = subprocess.Popen(['ledger', '-f', os.path.join(HERE,'ledger'),
                          '-n', 'balance', acct],
                         stdout=subprocess.PIPE)
    (out, _) = p.communicate()
    try:
        return int(out.split()[0][1:])
    except:
        return 0

def get_debts():
    p = subprocess.Popen(['ledger', '-f', os.path.join(HERE, 'ledger'),
                          '-n', 'balance', 'Pool:Owed:'],
                         stdout=subprocess.PIPE)
    (out, _) = p.communicate()
    debts = []
    for line in out.split("\n"):
        if not line: continue
        (val, acct) = line.split()
        user = acct[len("Pool:Owed:"):]
        val  = int(val[len("$"):])
        debts.append((user, val))
    return debts

def to_week_num(date):
    return (parse(date, default=START) - START).days / 7

def parse_skip(rec):
    spec = rec.get('skip', [])
    out = []
    for s in spec:
        if isinstance(s, list):
            out.append(map(to_week_num, s))
        else:
            out.append(to_week_num(s))
    return out

def should_skip(skips, week):
    for e in skips:
        if e == week:
            return True
        if isinstance(e, list) and e[0] <= week and e[1] > week:
            return True
    return False

def render_template(path, week=None, **kwargs):
    with open('out/report.yml') as r:
        report = yaml.safe_load(r)

    with open('bloggers.yml') as f:
        users = yaml.safe_load(f)
    if week:
        week = parse(week, default=START)
    else:
        week = START

    week = (week - START).days / 7
    week_start = START + (week * datetime.timedelta(7))
    week_end   = START + ((week + 1) * datetime.timedelta(7))

    good = []
    lame = []
    skip = []
    skipped_users = []
    userlist = []
    punted = []

    class User(object):
        pass

    for (un, rec) in users.items():
        u = User()
        u.username = un
        u.name  = rec['name']
        u.links = rec['links']
        u.twitter = rec.get('twitter')
        u.start_de = datetime.datetime.strptime(rec['start'],"%Y/%m/%d").strftime("%d.%m.%Y")
        u.start = rec['start']
        u.end   = rec.get('end')
        u.stop  = rec.get('stop')
        u.skip  = parse_skip(rec)
        u.weeks = report.get(un, [])

        userlist.append(u)

        # create a subset of punted users
        if u.end:
            u.end_de = datetime.datetime.strptime(rec.get('end'),"%Y/%m/%d").strftime("%d.%m.%Y")
            punted.append(u)

    def user_key(u):
        return (u.start, u.username)

    userlist.sort(key=user_key)
    punted.sort(key=user_key)

    for u in userlist:
        user_start = parse(u.start, default=START)
        if u.stop:
            continue
        if u.end and parse(u.end, default=START) <= week_start:
            continue

        if should_skip(u.skip, week):
            skipped_users.append(u)
        elif user_start > week_start:
            skip.append(u)
        elif len(u.weeks) <= week or not u.weeks[week]:
            lame.append(u)
        else:
            good.append(u)

    debts = get_debts()

    return Template(filename=path, output_encoding='utf-8').render(
        week=week, week_start=week_start,week_end=week_end,
        good=good, lame=lame, skip=skip, skipped_users=skipped_users, userlist=userlist,
        pool=(get_balance('Pool')-get_balance('Event')), paid=get_balance('Pool:Paid'),
        event=get_balance('Pool:Event'),
        debts=debts, punted=punted, **kwargs)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >>sys.stderr, "Usage: %s TEMPLATE [WEEK]"
        sys.exit(1)

    template = sys.argv[1]
    week = None
    if len(sys.argv) > 2: week = sys.argv[2]
    print render_template(template, week)
