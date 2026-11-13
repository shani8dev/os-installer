# SPDX-License-Identifier: GPL-3.0-or-later

from .config import config
from .installation_scripting import installation_scripting

from glob import glob
import os
from threading import Lock


page_order = [
    'language',
    'welcome',
    # required pre-install info
    'keyboard-overview',
    'internet',
    'disk',
    'encrypt',
    # optional security setup
    'secure-boot',
    'tpm',
    'desktop',
    'confirm',
    # configuration
    'user',
    'hostname',
    'region',
    'software',
    'feature',
    # fixed block towards end
    'summary',
    'install',
    'done',
    'restart']


class StateMachine:
    def __init__(self):
        self.availability_lock = Lock()
        self.available_pages = None
        self.latest_page = 0
        if not config.get('internet')['connection_required']:
            installation_scripting.can_run_prepare()

    def _assert_available_pages(self):
        with self.availability_lock:
            if self.available_pages:
                return
            page_conditions = {
                'language': self._offer_language_selection(),
                'welcome': config.get('welcome_page')['usage'],
                'internet': config.get('internet')['connection_required'],
                'encrypt': self._offer_encryption(),
                'secure-boot': self._offer_secure_boot(),
                'tpm': self._offer_tpm(),
                'desktop': config.get('desktop'),
                'confirm': config.get('scripts')['install'],
                'user': not config.get('skip_user'),
                'hostname': not config.get('hostname'),
                'region': not config.get('skip_region'),
                'software': config.get('additional_software'),
                'feature': config.get('additional_features'),
            }
            page_available = lambda page: page_conditions.get(page, True)

            self.available_pages = list(filter(page_available, page_order))
            # transition() truncates available_pages so navigation cannot go
            # back past the point of no return. Widgets ask "does this page
            # exist?" (a summary row deciding whether to show itself), and that
            # must not change when the list is shortened: keep the full set.
            self.all_available_pages = list(self.available_pages)

    def _offer_language_selection(self):
        # The fallback for language_use_fixed is False, which is also a valid
        # answer, so "not set" has to be checked separately: otherwise the
        # preload manager losing the race (it fills this in from a background
        # thread) is indistinguishable from "no fixed language" and the
        # language page appears even with one configured.
        if not config.has('language_use_fixed'):
            from .language_provider import language_provider
            language_provider.preload()
            config.set('language_use_fixed',
                       language_provider.future.result())

        use_fixed_language = config.get('language_use_fixed')
        if not isinstance(use_fixed_language, bool):
            use_fixed_language = use_fixed_language.result()
            config.set('language_use_fixed', use_fixed_language)
        return not use_fixed_language

    def _offer_encryption(self):
        encryption_settings = config.get('disk_encryption')
        if not encryption_settings['offered']:
            return False
        elif encryption_settings['forced'] and encryption_settings['generated']:
            config.set('use_encryption', True)
            return False
        else:
            return True

    def _offer_secure_boot(self):
        """MOK enrollment is only meaningful where the firmware can ask for it."""
        offered = config.get('secure_boot')['offered']
        if offered == 'no':
            return False
        if offered == 'yes':
            return True
        return os.path.isdir('/sys/firmware/efi')

    def _offer_tpm(self):
        """TPM unlock only helps an encrypted disk, and needs a TPM."""
        if not config.get('disk_encryption')['offered']:
            return False
        offered = config.get('tpm')['offered']
        if offered == 'no':
            return False
        if offered == 'yes':
            return True
        return bool(glob('/dev/tpmrm*') or glob('/sys/class/tpm/tpm[0-9]*'))

    ### public methods ###

    def is_page_available(self, page_name):
        self._assert_available_pages()
        match page_name:
            case 'format' | 'timezone':
                searched_name = 'region'
            case _:
                searched_name = page_name
        return searched_name in self.all_available_pages

    def get_available_pages(self):
        self._assert_available_pages()
        return self.available_pages

    def transition(self, prev_page, reached_page):
        ret_val = None

        if prev_page == 'language':
            ret_val = 'retranslate'

        new_index = page_order.index(reached_page)
        if self.latest_page >= new_index:
            return ret_val

        for page in page_order[self.latest_page+1:new_index+1]:
            match page:
                case 'disk':
                    installation_scripting.can_run_prepare()
                case 'user':
                    if prev_page == 'confirm':
                        installation_scripting.can_run_install()
                        ret_val = 'no_return'
                        confirm_index = self.available_pages.index('confirm')
                        del self.available_pages[0:confirm_index]
                case 'install':
                    installation_scripting.can_run_configure()
                    ret_val = 'no_return'
                case 'done' | 'failed' | 'restart' | 'summary':
                    ret_val = 'no_return'
        self.latest_page = new_index

        return ret_val


state_machine = StateMachine()
