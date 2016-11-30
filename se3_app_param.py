# -*- coding: utf-8 -*-

from ec_app_params import *

__author__ = 'fi11222'

# global parameters specific to the application

class Se3AppParam(EcAppParam):
    # Index page Template
    gcm_templateIndex = os.path.join(EcAppParam.gcm_appRoot, 'Templates/index.html')

    # Verse display limits
    gcm_softLimit = 200
    gcm_hardLimit = 10000

    # character classes
    gcm_hebrewConsonants = '[\u05D0-\u05EF\u200D]'
    gcm_hebrewVowels = '[\u0590-\u05CF\u05F0-\u05FF]'

    # ------------------------- Parameters hexadecimal bit masks -------------------------------------------------------
    # Single Verse Display options
    gcm_svAllVersions = 0x001      # Display all versions (1) or only selected versions (0)
    gcm_svDisplayLxx = 0x002       # Display interlinear LXX (1) for OT verses or not (0)
    gcm_svDisplayKjv = 0x004       # Display KJV interlinear (1) for OT & NT verses or not (0)
    gcm_svDisplayNasb = 0x008      # Display NASB interlinear (1) for OT & NT verses or not (0)

    # Passage Display options
    gcm_pDisplayGround = 0x010     # Display ground text (1) or not (0)
    gcm_pParallel = 0x020          # Display versions in parallel (1) or in succession (0)
