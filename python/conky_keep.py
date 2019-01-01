#!/usr/bin/env python3
# encoding: utf-8

import os, sys

from bs4 import BeautifulSoup
from python.session_google import SessionGoogle

# get path to app dir
path = os.path.dirname(os.path.abspath(__file__))

# get config file path
# config file in same folde has higher priority
conf_file = 'config.xml'

if os.path.isfile(os.path.join(path, conf_file)): # config in same folder as conkyKeep.sh (../)

    conf_path = os.path.join(path, '..', conf_file)
else: # config in ~/.config/conkykeep folder
    try:
        import appdirs
        app_config_dir = appdirs.user_config_dir('GoogleIntegratedSystemConky')
    except:
        app_config_dir = os.path.join(os.path.expanduser("~"), '.config', 'GoogleIntegratedSystemConky')
    conf_path = os.path.join(app_config_dir, conf_file)

if not os.path.isfile(conf_path):
    print("ERROR: config file not found in: %s" % (conf_path,))

# get app resource paths
path = os.path.dirname(os.path.abspath(__file__))

line_height = 17
line_width = 8
line_height_title = 16
line_width_title = 10

def getNoteSize(note):
    """
    Get needed resolution for background
    """
    # background height
    background_height = len(note['text'].split('\n'))*line_height
    background_height += line_height # hr

    if note['title'].strip() != '':
        background_height += line_height_title

    # background width
    width_title = len(note['title'])*line_width_title

    maxl = 0
    for l in note['text'].split('\n'):
        maxl = max(maxl, len(l))

    width = maxl*line_width
    width = max(width, width_title)
    width = max(width, 330)

    return background_height, width

def format_conky_note(note, vertical_offset=0, conky_width=330):
    """
    note - dict with note info
    vertical_offset - vartical position of note
    conky_width - width of conky (max width of shown notes)
    """
    # background color height
    height, width = getNoteSize(note)
    background_height = height
    background_width = width+10

    # compute right goto
    rgoto = conky_width-(background_width-10)
    rgoto_text = rgoto+10

    print("${font monofur:pixelsize=14}", end="")

    for line in note['text'].split('\n'):
        line = line.strip().replace("#","\#").replace("$","$$")
        print("${goto %i}${voffset 0}${alignr}%s" % (rgoto_text, line))

    # reset font + color
    print("${color}${font}", end="")

    # return new vertical offset
    return background_height+vertical_offset-1

def get_config():

    bs_conf = BeautifulSoup(open(conf_path, "r"), "lxml").configuration
    conf = {}

    # login info
    login_conf = {'username': bs_conf.login.username.text.strip(),'password': bs_conf.login.password.text.strip()}
    conf['login'] = login_conf

    # filter
    filter_conf = {'ids':[], 'titles':[], 'removeall':False}

    filt = bs_conf.find('filter')
    if filt.find('removeall') is not None:
        if 'yes' == filt.find('removeall').text.lower().strip():
            filter_conf['removeall'] = True
        else:
            filter_conf['removeall'] = False

    if filter_conf['removeall']:
        ids = filt.findAll('allowid')
        titles = filt.findAll('allowtitle')
    else:
        ids = filt.findAll('removeid')
        titles = filt.findAll('removetitle')
    for a in ids:
        filter_conf['ids'].append(a.text.lower().strip())
    for a in titles:
        filter_conf['titles'].append(a.text.lower().strip())
    conf['filter'] = filter_conf

    return conf

def main():
    config = get_config()
    vertical_offset = int(line_height/2)
    try:
        session = SessionGoogle(config['login']['username'],config['login']['password'])
        notes = session.googleKeep_formatNotes(session.googleKeep_getNotes())

    except Exception as e:
    	print("Connection to Google Keep failed !")
    	print("Reason:")
    	print(e)
    	sys.exit(0)

    filtered_notes = []
    max_width = 0
    for note in notes:
        allowed = False
        if config['filter']['removeall']:
            if (note['id'] in config['filter']['ids']) or (note['title'].lower() in config['filter']['titles']):
                allowed = True
        else:
            if (note['id'] not in config['filter']['ids']) and (note['title'].lower() not in config['filter']['titles']):
                allowed = True
        if allowed:
            filtered_notes.append(note)
            height, width = getNoteSize(note)
            max_width = max(max_width, width)

    for note in filtered_notes:
        vertical_offset = format_conky_note(note, vertical_offset, max_width)


if __name__ == "__main__":
    main()