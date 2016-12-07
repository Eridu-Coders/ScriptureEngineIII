#!/usr/bin/python3
# -*- coding: utf-8 -*-

from se3_utilities import *
from ec_utilities import *

__author__ = 'fi11222'

l_connectionPool = EcConnectionPool()

l_connection = l_connectionPool.getConnection()
l_connection.debugData = 'updateQuranNeighborhoods READ connection'

l_connectionWrite = l_connectionPool.getConnection()
l_connectionWrite.debugData = 'updateQuranNeighborhoods WRITE connection'

l_query = """
    select
        ID_INTERL
        , ID_BOOK
        , N_CHAPTER
        , N_VERSE
        , N_WORD
        , ID_WORD
        , N_VERSE_WORD_COUNT
        , TX_TRANSLATION
    from TB_INTERLINEAR
    where ID_INTERL = 'C'
    order by
        ID_WORD
;"""

print('l_query {0}'.format(l_query))
try:
    l_cursor = l_connection.cursor(buffered=True)
    l_cursor.execute(l_query)

    for l_idInterl, l_idBook, l_chapter, l_verse, l_wordNumber, l_idWord, l_wordCount, l_translation in l_cursor:
        # Neighborhood (3 on each side)
        l_wordStart = l_wordNumber - 3 if l_wordNumber - 3 >= 0 else 0
        l_wordEnd = l_wordStart + 6 if l_wordStart + 6 <= l_wordCount-1 else l_wordCount-1
        if l_wordEnd - l_wordStart < 6:
            l_wordStart = l_wordEnd - 6 if l_wordEnd - 6 >= 0 else 0

        l_neighborhood = getNeighborhood(
            l_connectionPool, l_idInterl, l_idBook, l_chapter, l_verse, l_wordStart, l_wordEnd, l_wordNumber)

        print(l_idWord, '-->', l_neighborhood, end='                     \r')

        l_queryWrite = """
            update TB_INTERLINEAR
            set TX_NEIGHBORHOOD = '{1}'
            where ID_WORD = {0}
        ;""".format(l_idWord,
                    l_neighborhood.replace("'", "''"))

        l_cursorWrite = l_connectionWrite.cursor()
        l_cursorWrite.execute(l_queryWrite)
        l_connectionWrite.commit()
        l_cursorWrite.close()

    l_cursor.close()
except Exception as l_exception:
    g_loggerUtilities.warning('Something went wrong {0}'.format(l_exception.args))