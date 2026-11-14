# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess

from gi.repository import GObject, GnomeDesktop

from .config import config
from .preloadable import Preloadable

_available_locales = None


def _locale_available(locale):
    """Is this locale generated on this system?

    GnomeDesktop.get_language_from_locale() can block on a locale that is not
    in the archive (an installed system without locale-gen), so check first:
    an unavailable locale cannot be offered anyway.
    """
    global _available_locales
    if _available_locales is None:
        try:
            out = subprocess.run(['locale', '-a'], capture_output=True,
                                 text=True, timeout=5).stdout
            _available_locales = {line.strip() for line in out.splitlines()}
        except (OSError, subprocess.SubprocessError):
            _available_locales = set()
    return locale in _available_locales or locale.split('.')[0] in _available_locales


# generated via language_codes_to_x_generator.py
language_to_default_locale = {
    'ab': 'ab_GE.UTF-8', 'aa': 'aa_DJ.UTF-8', 'af': 'af_ZA.UTF-8', 'ak': 'ak_GH.UTF-8', 'sq': 'sq_AL.UTF-8',
    'am': 'am_ET.UTF-8', 'ar': 'ar_EG.UTF-8', 'an': 'an_ES.UTF-8', 'hy': 'hy_AM.UTF-8', 'as': 'as_IN.UTF-8',
    'ae_AE': 'ar_AE.UTF-8', 'az': 'az_AZ.UTF-8', 'ba_BA': 'bs_BA.UTF-8', 'eu': 'eu_ES.UTF-8', 'be': 'be_BY.UTF-8',
    'bn': 'bn_BD.UTF-8', 'bh_BH': 'ar_BH.UTF-8', 'bi': 'bi_VU.UTF-8', 'bs': 'bs_BA.UTF-8', 'br': 'br_FR.UTF-8',
    'bg': 'bg_BG.UTF-8', 'my': 'my_MM.UTF-8', 'ca': 'ca_ES.UTF-8', 'ch_CH': 'de_CH.UTF-8', 'ce': 'ce_RU.UTF-8',
    'zh': 'zh_CN.UTF-8', 'cv': 'cv_RU.UTF-8', 'kw': 'kw_GB.UTF-8', 'co_CO': 'es_CO.UTF-8', 'cr_CR': 'es_CR.UTF-8',
    'hr': 'hr_HR.UTF-8', 'cs': 'cs_CZ.UTF-8', 'da': 'da_DK.UTF-8', 'dv': 'dv_MV.UTF-8', 'nl': 'nl_NL.UTF-8', 'dz':
    'dz_BT.UTF-8', 'en': 'en_US.UTF-8', 'en_GB': 'en_GB.UTF-8', 'eo': 'eo.UTF-8', 'et': 'et_EE.UTF-8',
    'ee_EE': 'et_EE.UTF-8', 'fo': 'fo_FO.UTF-8', 'fj_FJ': 'hif_FJ.UTF-8', 'fi': 'fi_FI.UTF-8', 'fr': 'fr_FR.UTF-8',
    'ff': 'ff_SN.UTF-8', 'gl': 'gl_ES.UTF-8', 'ka': 'ka_GE.UTF-8', 'de': 'de_DE.UTF-8', 'el': 'el_GR.UTF-8',
    'gu': 'gu_IN.UTF-8', 'ht': 'ht_HT.UTF-8', 'ha': 'ha_NG.UTF-8', 'he': 'he_IL.UTF-8', 'hi': 'hi_IN.UTF-8',
    'hu': 'hu_HU.UTF-8', 'ia': 'ia_FR.UTF-8', 'id': 'id_ID.UTF-8', 'ie_IE': 'en_IE.UTF-8', 'ga': 'ga_IE.UTF-8',
    'ig': 'ig_NG.UTF-8', 'ik': 'ik_CA.UTF-8', 'is': 'is_IS.UTF-8', 'it': 'it_IT.UTF-8', 'iu': 'iu_CA.UTF-8',
    'ja': 'ja_JP.UTF-8', 'kl': 'kl_GL.UTF-8', 'kn': 'kn_IN.UTF-8', 'kr_KR': 'ko_KR.UTF-8', 'ks': 'ks_IN.UTF-8@devanagari',
    'kk': 'kk_KZ.UTF-8', 'km': 'km_KH.UTF-8', 'rw': 'rw_RW.UTF-8', 'ky': 'ky_KG.UTF-8', 'kg_KG': 'ky_KG.UTF-8',
    'ko': 'ko_KR.UTF-8', 'ku': 'ku_TR.UTF-8', 'la_LA': 'lo_LA.UTF-8', 'lb': 'lb_LU.UTF-8', 'lg': 'lg_UG.UTF-8',
    'li': 'li_NL.UTF-8', 'ln': 'ln_CD.UTF-8', 'lo': 'lo_LA.UTF-8', 'lt': 'lt_LT.UTF-8', 'lu_LU': 'fr_LU.UTF-8',
    'lv': 'lv_LV.UTF-8', 'gv': 'gv_GB.UTF-8', 'mk': 'mk_MK.UTF-8', 'mg': 'mg_MG.UTF-8', 'ms': 'ms_MY.UTF-8',
    'ml': 'ml_IN.UTF-8', 'mt': 'mt_MT.UTF-8', 'mi': 'mi_NZ.UTF-8', 'mr': 'mr_IN.UTF-8', 'mn': 'mn_MN.UTF-8',
    'ne': 'ne_NP.UTF-8', 'ng_NG': 'en_NG.UTF-8', 'nb': 'nb_NO.UTF-8', 'nn': 'nn_NO.UTF-8', 'no': 'no_NO.UTF-8',
    'nr': 'nr_ZA.UTF-8', 'oc': 'oc_FR.UTF-8', 'cu_CU': 'es_CU.UTF-8', 'om': 'om_ET.UTF-8', 'or': 'or_IN.UTF-8',
    'os': 'os_RU.UTF-8', 'pa': 'pa_IN.UTF-8', 'fa': 'fa_IR.UTF-8', 'pl': 'pl_PL.UTF-8', 'ps': 'ps_AF.UTF-8',
    'pt': 'pt_PT.UTF-8', 'ro': 'ro_RO.UTF-8', 'ru': 'ru_RU.UTF-8', 'sa': 'sa_IN.UTF-8', 'sc': 'sc_IT.UTF-8',
    'sd': 'sd_IN.UTF-8', 'se': 'se_NO.UTF-8', 'sm': 'sm_WS.UTF-8', 'sg_SG': 'en_SG.UTF-8', 'sr': 'sr_RS.UTF-8',
    'gd': 'gd_GB.UTF-8', 'sn_SN': 'wo_SN.UTF-8', 'si': 'si_LK.UTF-8', 'sk': 'sk_SK.UTF-8', 'sl': 'sl_SI.UTF-8',
    'so': 'so_SO.UTF-8', 'st': 'st_ZA.UTF-8', 'es': 'es_ES.UTF-8', 'sw': 'sw_KE.UTF-8', 'ss': 'ss_ZA.UTF-8',
    'sv': 'sv_SE.UTF-8', 'ta': 'ta_IN.UTF-8', 'te': 'te_IN.UTF-8', 'tg': 'tg_TJ.UTF-8', 'th': 'th_TH.UTF-8',
    'ti': 'ti_ER.UTF-8', 'bo': 'bo_CN.UTF-8', 'tk': 'tk_TM.UTF-8', 'tl': 'tl_PH.UTF-8', 'tn': 'tn_ZA.UTF-8',
    'to': 'to_TO.UTF-8', 'tr': 'tr_TR.UTF-8', 'ts': 'ts_ZA.UTF-8', 'tt': 'tt_RU.UTF-8', 'tw_TW': 'zh_TW.UTF-8',
    'ug': 'ug_CN.UTF-8', 'uk': 'uk_UA.UTF-8', 'ur': 'ur_PK.UTF-8', 'uz': 'uz_UZ.UTF-8@cyrillic', 've': 've_ZA.UTF-8',
    'vi': 'vi_VN.UTF-8', 'wa': 'wa_BE.UTF-8', 'cy': 'cy_GB.UTF-8', 'wo': 'wo_SN.UTF-8', 'fy': 'fy_NL.UTF-8',
    'xh': 'xh_ZA.UTF-8', 'yi': 'yi_US.UTF-8', 'yo': 'yo_NG.UTF-8', 'za_ZA': 'zu_ZA.UTF-8', 'zu': 'zu_ZA.UTF-8',
    'kab': 'kab_DZ.UTF-8',
    # manually added
    'pt_BR': 'pt_BR.UTF-8', 'pt_PT': 'pt_PT.UTF-8',
}


class LanguageInfo(GObject.Object):
    __gtype_name__ = __qualname__

    def __init__(self, name, code, locale, available=True):
        super().__init__()

        self.available = available
        self.code = code
        self.locale = locale
        self.name = name


class LanguageProvider(Preloadable):
    def __init__(self):
        super().__init__(self._get_languages)

    def preload(self):
        # Deferred to preload() rather than submitted from __init__: this
        # class is instantiated as a module-level singleton, which runs at
        # import time — before Application.do_command_line() has called
        # config.init() to load the config file. Submitting the thread here
        # instead ties it to preload_manager.start(), which only runs from
        # do_activate(), strictly after config.init() has completed, so
        # _determine_fixed_language() can't read config before it's loaded.
        future = self.thread_pool.submit(self._determine_fixed_language)
        config.set('language_use_fixed', future)
        super().preload()

    def _determine_fixed_language(self):
        fixed_language = config.get('fixed_language')
        if not fixed_language:
            return False

        if fixed_info := self._create_info(fixed_language):
            config.set('language_chosen', fixed_info)
            return True
        else:
            print('Distribution developer hint: Fixed language '
                  f'{fixed_language} is not available in current system. '
                  'Falling back to default language selection.')
            config.set('fixed_language', False)
            return False

    def _create_info(self, language_code):
        locale = language_to_default_locale.get(language_code, None)
        if locale and not _locale_available(locale):
            print(f'Locale {locale} is not available on this system')
            return LanguageInfo(language_code, language_code, locale, False)
        if not locale and '_' in language_code:
            # already has territory, use as-is
            locale = f'{language_code}.UTF-8'
        elif not locale:
            print(f"Can't determine locale for {language_code}")
            return None

        if name := GnomeDesktop.get_language_from_locale(locale, locale):
            return LanguageInfo(name, language_code, locale)
        elif name := GnomeDesktop.get_language_from_locale(locale):
            return LanguageInfo(name, language_code, locale, False)

        national_code = language_code.split('_')[0]
        if lang := GnomeDesktop.get_language_from_code(national_code, locale):
            name = f'{lang} ({language_code})'
            return LanguageInfo(name, language_code, locale)
        elif lang := GnomeDesktop.get_language_from_code(national_code):
            name = f'{lang} ({language_code})'
            return LanguageInfo(name, language_code, locale, False)

    def _get_languages(self):
        # Assure that some language is set in testing mode
        if not config.has('language_chosen'):
            english_info = self._create_info('en')
            config.set('language_chosen', english_info)

        translations = config.get('available_translations')

        self.all_languages = []
        unavailable_languages = []
        for language_code in translations:
            if info := self._create_info(language_code):
                self.all_languages.append(info)
            else:
                unavailable_languages.append(language_code)

        if unavailable_languages:
            print('The following locales are not available on the current system: ',
                  sorted(unavailable_languages))
        self.all_languages.sort(key=lambda k: k.name)

    ### public methods ###

    def get_all_languages(self):
        self.assert_preloaded()
        return self.all_languages

    def get_available_languages(self):
        self.assert_preloaded()
        return self.all_languages


language_provider = LanguageProvider()
