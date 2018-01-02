#!/usr/bin/env python3
# encoding: utf-8

import sys
import copy
import requests
from bs4 import BeautifulSoup
import json

class SessionGoogle:

    """
    Google Login code is based on http://stackoverflow.com/a/24881998
    googleKeep_data - Notes from GoogleKeep
    googleKeep_data['id']       - id of note
    googleKeep_data['parentId'] - id of parent "note"
    googleKeep_data['title']    - title of note
    googleKeep_data['text']     - text inside of note
    googleKeep_data['color']    - color of note
    data['serverId']
    data['timestamps']
    data['labelIds']
    data['baseVersion']
    data['abuseFeedback']
    data['errorStatus']
    data['kind']
    data['checked']
    data['type']
    data['shareRequests']
    data['nodeSettings']
    data['reminders']
    data['sortValue']
    data['roleInfo']
    data['parentServerId']
    data['isArchived']
    +other
    """
    googleKeep_data_raw = []
    googleKeep_data = []

    def __init__(self, login, pwd, url_login="https://accounts.google.com/ServiceLogin", url_auth="https://accounts.google.com/ServiceLoginAuth"):

        self.ses = requests.session()
        login_html = self.ses.get(url_login).text
        soup_login = BeautifulSoup(login_html, "lxml").find('form').findAll('input')
        dico = {}

        for u in soup_login:
            if u.get('value') is not None:
                dico[u['name']] = u['value']

        # override the inputs with out login and pwd:
        dico['Email'] = login
        dico['Passwd'] = pwd

        self.ses.post(url_auth, data=dico)
    def get(self, URL):

        return self.ses.get(URL).text

    def googleKeep_getNotes(self, raw=False):

        html = self.get("https://keep.google.com/")
        #with open('html_dump', 'w') as f:
        #    print("saving html to html_dump..."); f.write(html)
        # get part of html with notes data
        html_s = html.split("// Google Inc.")
        bs = BeautifulSoup("<html><body>"+html_s[-1].strip(), "lxml")

        # find correct script: "<script type="text/javascript">preloadUserInfo(JSON.parse("
        script = None

        for s in bs.body.findAll('script', attrs={'type': 'text/javascript'}):
            if s.text.strip().startswith("preloadUserInfo(JSON.parse("):
                script = s; continue

        if script is None:
            raise Exception("Couldn't find correct <script> tag!")

        # fill self.googleKeep_data_raw
        script_loadChunk = script.text.split(";loadChunk(JSON.parse('")[-1]
        data = "'), ".join(script_loadChunk.split("'), ")[:-1])

        # convert \x?? charcters
        while data.find('\\x') != -1:
            index = data.find('\\x')
            hex_str = data[index:index+4]
            val = int(data[index+2:index+4], 16)
            data = data.replace(hex_str, chr(val))

        # remove redundant \
        data = data.replace('\\\\','\\')
        # decode json string
        self.googleKeep_data_raw = json.loads(data) # encodes string to utf-8 ?

        if not raw:
            self.googleKeep_data = []
            for data in self.googleKeep_data_raw:
                # ignore trashed (removed) notes
                trashed = data['timestamps']['trashed']
                if trashed != '1970-01-01T00:00:00.000Z':
                    continue
                self.googleKeep_data.append(data)
            # create note tree
            self.googleKeep_data = self.googleKeep_getNotesTree(self.googleKeep_data)
        else:
            self.googleKeep_data = self.googleKeep_data_raw
        return self.googleKeep_data

    def googleKeep_getNotesTree(self, notes):

        """
        Autocalled by googleKeep_getNotes
        """
        root_notes = []
        for cn in notes:
            # get root notes
            if cn['parentId'] == 'root':
                root_notes.append(cn)
                continue
            # add child notes to parent notes
            for pn in notes:
                if cn['parentId'] == pn['id']:
                    if 'childNotes' not in pn:
                        pn['childNotes'] = []
                    pn['childNotes'].append(cn)
        return root_notes

    def googleKeep_formatNotes(self, notes, child=False):
        """
        requires 'childNotes' in note data
        """
        # create copy of notes before modifications
        notes = copy.deepcopy(notes)

        for rn in notes:
            # recursivelly format child notes
            if 'childNotes' in rn:
                childNotes = self.googleKeep_formatNotes(rn['childNotes'], child=True)

            # create formated text variable
            if 'text' not in rn:
                rn['text'] = ""
            rn['formatedText'] = rn['text']

            ## Root type notes
            if rn['type'] == "NOTE": # if text note (root note type)
                # add formated text from child notes
                for cn in childNotes:
                    if rn['formatedText'] != "":
                        rn['formatedText'] += "\n"
                    rn['formatedText'] += cn['formatedText']
            elif rn['type'] == "LIST": # if List note (root note type)
                for cn in childNotes:
                    if rn['formatedText'] != "":
                    	if cn['checked']:
                    		pass
                    	else:
                    		rn['formatedText'] += "\n"
                    if cn['checked']:
                        pass
                    else:
                        rn['formatedText'] += ""
                        rn['formatedText'] += cn['formatedText']
                    
            ## Child type notes
            elif rn['type'] == 'LIST_ITEM': # if text note or list item
                rn['formatedText'] = rn['text']
            elif rn['type'] == 'BLOB': # if image note
                rn['formatedText'] = "[BLOB mime='"+rn['blob']['mimetype']+"' url='https://keep.google.com/media/"+rn['blob']["media_id"]+"']"
            else:
                print("Unknown NoteType:%s not implemented!", (rn['type'],))

        # remove unneeded values and add missing default values
        if not child:
            formated_notes = []
            for n in notes:
                _note = {
                    'text': n['formatedText'],
                    'color': "DEFAULT",
                    'title': "",
                    'type': "NOTE",
                    'id': 0
                }
                if 'title' in n:
                    _note['title'] = n['title']
                if 'type' in n:
                    _note['type'] = n['type']
                if 'id' in n:
                    _note['id'] = n['id']
                formated_notes.append(_note)
        else:
            formated_notes = notes

        return formated_notes

if __name__ == "__main__":

    print("USAGE: python3 session_google.py USERNAME PASSWORD")

    if len(sys.argv)!=3:
        print("ERROR: Bad number of arguments")
        sys.exit(2)

    session = SessionGoogle(str(sys.argv[1]), str(sys.argv[2]))
    notes = session.googleKeep_getNotes()
    notes = session.googleKeep_getNotesTree(notes)
    f_notes = session.googleKeep_formatNotes(notes)
    for note in f_notes:
        print("---------------------------------------------------------------")
        print(note)