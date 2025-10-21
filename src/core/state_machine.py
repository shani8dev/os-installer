# SPDX-License-Identifier: GPL-3.0-or-later

from .config import config
from .installation_scripting import installation_scripting

from threading import Lock


page_order = [
    'language',
    'welcome',
    # required pre-install info
    'keyboard-overview',
    'internet',
    'disk',
    'encrypt',
    'desktop',
    'confirm',
    # configuration
    'user',
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
                'desktop': config.get('desktop'),
                'confirm': config.get('scripts')['install'],
                'user': not config.get('skip_user'),
                'region': not config.get('skip_region'),
                'software': config.get('additional_software'),
                'feature': config.get('additional_features'),
            }
            page_available = lambda page: page_conditions.get(page, True)

            self.available_pages = list(filter(page_available, page_order))

    def _offer_language_selection(self):
        use_fixed_language = config.get('language_use_fixed')
        if type(use_fixed_language) is not bool:
            use_fixed_language = use_fixed_language.result()
            config.set('language_use_fixed', use_fixed_language)
        return not use_fixed_language
        list(filter(self._is_page_available, page_order))

    def _offer_encryption(self):
        encryption_settings = config.get('disk_encryption')
        if not encryption_settings['offered']:
            return False
        elif encryption_settings['forced'] and encryption_settings['generated']:
            config.set('use_encryption', True)
            return False
        else:
            return True

    ### public methods ###

    def is_page_available(self, page_name):
        self._assert_available_pages()
        match page_name:
            case 'format' | 'timezone':
                searched_name = 'region'
            case _:
                searched_name = page_name
        return searched_name in self.available_pages

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
