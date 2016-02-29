#!/usr/bin/python3
# -*- coding: utf-8 -*-

import html
from ec_utilities import *

__author__ = 'fi11222'

l_connectionPool = EcConnectionPool()

l_connection = l_connectionPool.getConnection()
l_connectionWrite = l_connectionPool.getConnection()

l_query = """
    SELECT
        V.`ID_VERSE`
        , V.`TX_VERSE_INSENSITIVE`
    FROM `TB_VERSES` V JOIN TB_BOOK B ON B.`ID_BOOK` = V.`ID_BOOK`
    WHERE
        B.ID_GROUP_0 = 'OT'
        AND V.ID_VERSION = '_gr'
    ;"""

print('l_query {0}'.format(l_query))
try:
    l_cursor = l_connection.cursor(buffered=True)
    l_cursor.execute(l_query)

    for l_idVerse, l_hebTxt in l_cursor:

        l_hebUnicode = html.unescape(l_hebTxt)
        print(l_hebTxt, '-->', l_hebUnicode)

        l_queryWrite = """
            update TB_VERSES
            set
                TX_VERSE = '{0}'
                , TX_VERSE_INSENSITIVE = '{0}'
            where ID_VERSE = {1}
        ;""".format(l_hebUnicode.replace("'", "''"), l_idVerse)

        print(l_queryWrite)
        l_cursorWrite = l_connectionWrite.cursor()
        l_cursorWrite.execute(l_queryWrite)
        l_connectionWrite.commit()
        l_cursorWrite.close()

    l_cursor.close()
except Exception as l_exception:
    g_loggerUtilities.warning('Something went wrong {0}'.format(l_exception.args))
