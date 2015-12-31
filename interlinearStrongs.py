#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import mysql.connector

from ec_app_params import *

__author__ = 'fi11222'

l_connector = mysql.connector.connect(
                user=g_dbUser, password=g_dbPassword,
                host=g_dbServer,
                database=g_dbDatabase)

l_connectorWrite = mysql.connector.connect(
                user=g_dbUser, password=g_dbPassword,
                host=g_dbServer,
                database=g_dbDatabase)

l_connectorWrite2 = mysql.connector.connect(
                user=g_dbUser, password=g_dbPassword,
                host=g_dbServer,
                database=g_dbDatabase)

l_query = """
    select
        TX_STRONGS_LIST
        , ID_WORD
        , ID_INTERL
        , ID_BOOK
        , N_CHAPTER
        , N_VERSE
        , N_WORD
        , ST_GROUND
    from TB_INTERLINEAR
    where TX_STRONGS_LIST like '%NoStrong%'
;"""

l_cursor = l_connector.cursor(buffered=True)
l_cursor.execute(l_query)

# l_fSQL = open('InterlinearUpdate.sql', 'w')
for l_strongsStore, l_wordId, l_interl, l_book, l_chapter, l_verse, l_wordNumber, l_ground in l_cursor:
    l_newLinks = ''

    l_strongsList = json.loads(l_strongsStore)
    l_wordList = l_ground.split(' ')

    while len(l_strongsList) > len(l_wordList):
        for i in range(len(l_strongsList)-1, -1, -1):
            if l_strongsList[i] == 'NoStrong':
                del l_strongsList[i]
                break

    print(l_ground, l_wordId, '---------------------------------------------------------------------')
    i = 0
    for l_strongsId in l_strongsList:
        if l_strongsId == 'NoStrong':
            l_newLinks += l_wordList[i] + ' '
        else:
            l_newLinks += ('<a href="" class="GoOneWord" p_book="{1}" p_chapter="{2}" p_verse="{3}" ' +
                           'p_wordid="{4}">{0}</a> ').format(
                l_wordList[i],
                l_book, l_chapter, l_verse, str(l_wordNumber) + '-' + l_interl + '-' + l_strongsId)

        i += 1

    print(l_wordId, '-->', l_newLinks)

    l_queryInterlinear = """
        update TB_INTERLINEAR
        set TX_STRONGS_LINKS = '{0}'
        where ID_WORD = {1};""".format(l_newLinks.replace("'", "''").strip(), l_wordId)

    # l_fSQL.write(l_queryInterlinear)
    print(l_queryInterlinear)
    l_cursorWrite2 = l_connectorWrite2.cursor()
    l_cursorWrite2.execute(l_queryInterlinear)
    l_connectorWrite2.commit()
    l_cursorWrite2.close()

    print(l_wordId, '      ', end='\r')

print()
l_cursor.close()

l_connector.close()
