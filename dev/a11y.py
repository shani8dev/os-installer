#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""AT-SPI driver for the ShaniOS Installer dev harness.

The installer is a GTK4/libadwaita app, so its accessibility tree is the
native-app DOM: pages, headings, buttons, switches and entries can be found
by role and name instead of by pixel coordinates. Every command prints
`RESULT <name> PASS|FAIL <detail>` lines for dev/check.sh to count.

  dump [DEPTH]            print the tree (role 'name' @x,y wxh [states])
  find QUERY              list matches; QUERY is NAME-REGEX or ROLE:NAME-REGEX
  wait QUERY [SECS]       wait until something matches
  wait-title TEXT [SECS]  wait until a page with that title is showing
  click QUERY             activate a match (AT-SPI action, else a click)
  type QUERY TEXT         set a match's text (editable AT-SPI, else keys)
  shot FILE               screenshot the whole display (ImageMagick import)
  key COMBO               xdotool key, e.g. Return or ctrl+q
  states QUERY            print the AT-SPI states of the first match
  lint                    fail if an on-screen control has no accessible name
  walk [OUT] [--lint]     walk welcome -> done, screenshotting every page,
                          checking the OSI_* contract the scripts received,
                          and exiting non-zero on the first mismatch

Roles are normalised the way shani-testbed's a11y client does it: 'push
button' is 'button', 'table row'/'list row' are 'row'. GTK4 reports no SCREEN
extents, so coordinates come from WINDOW_COORDS; the dev display has no window
manager, so a window sits at 0,0 and window == screen.
"""

import os
import re
import subprocess
import sys
import time

import pyatspi

CONTROL_ROLES = {
    'button', 'toggle button', 'check box', 'radio button', 'entry',
    'password text', 'switch', 'combo box', 'menu item', 'link', 'slider',
    'spin button', 'row',
}
ROLE_ALIASES = {
    'push button': 'button',
    'table row': 'row',
    'list row': 'row',
    'list item': 'row',
    'text': 'entry',
}


class AppNotRunning(Exception):
    pass


class CheckFailed(AssertionError):
    pass


def result(name, ok, detail=''):
    print(f"RESULT {name} {'PASS' if ok else 'FAIL'}"
          + (f' {detail}' if detail and not ok else ''))
    return ok


def normalise_role(node):
    try:
        role = node.getRoleName().lower()
    except Exception:
        return ''
    return ROLE_ALIASES.get(role, role)


def shown(node):
    try:
        state = node.getState()
        return (state.contains(pyatspi.STATE_SHOWING) and
                state.contains(pyatspi.STATE_VISIBLE))
    except Exception:
        return False


def sensitive(node):
    try:
        return node.getState().contains(pyatspi.STATE_SENSITIVE)
    except Exception:
        return False


def name_of(node):
    try:
        name = node.name or ''
    except Exception:
        name = ''
    if not name:
        try:
            name = node.queryText().getText(0, -1)
        except Exception:
            name = ''
    return name.strip()


def descendants(node, depth=0, max_depth=40):
    if depth > max_depth:
        return
    yield node
    try:
        children = list(node)
    except Exception:
        return
    for child in children:
        yield from descendants(child, depth + 1, max_depth)


def apps():
    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        if app is None:
            continue
        try:
            yield app
        except Exception:
            continue


def on_display(node):
    """True when the node belongs to a window that is actually on screen."""
    parent = node
    while parent is not None:
        try:
            if parent.getRoleName() == 'frame':
                return shown(parent)
            parent = parent.parent
        except Exception:
            return False
    return False


def matches(node, query):
    if ':' in query:
        role_query, name_query = query.split(':', 1)
    else:
        role_query, name_query = '', query
    if role_query:
        role = normalise_role(node)
        if not re.fullmatch(role_query, role):
            return False
    if name_query:
        if not re.search(name_query, name_of(node)):
            return False
    return True


def find(query, include_hidden=False):
    found = []
    for app in apps():
        for node in descendants(app):
            if node is app:
                continue
            if not matches(node, query):
                continue
            if not include_hidden and not (shown(node) and on_display(node)):
                continue
            found.append(node)
    return found


def wait(query, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = find(query)
        if found:
            return found[0]
        time.sleep(0.2)
    raise AppNotRunning(f'nothing matched {query!r} within {timeout}s')


def wait_all(query, timeout=15.0):
    """All matches for a query, waiting for the first one to appear."""
    wait(query, timeout)
    return find(query)


def wait_title(title, timeout=30.0):
    query = f'label:^{re.escape(title)}$'
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for node in find(query):
            if shown(node) and on_display(node):
                time.sleep(0.3)   # let the push transition settle
                return node
        time.sleep(0.2)
    raise AppNotRunning(f'page {title!r} did not appear within {timeout}s')


def extents(node):
    try:
        component = node.queryComponent()
        rect = component.getExtents(pyatspi.WINDOW_COORDS)
        if rect.width and rect.height:
            return rect
    except Exception:
        pass
    return None


def click_point(x, y):
    subprocess.run(['xdotool', 'mousemove', str(int(x)), str(int(y)),
                    'click', '1'], check=False)


def activate(node):
    """Activate through AT-SPI if the widget exposes an action, else click it."""
    try:
        action = node.queryAction()
        if action.nActions:
            action.doAction(0)
            return 'action'
    except Exception:
        pass
    rect = extents(node)
    if rect is None:
        raise AppNotRunning(f'{name_of(node)!r} has neither an action nor a size')
    click_point(rect.x + rect.width / 2, rect.y + rect.height / 2)
    return 'click'


def focus(node):
    try:
        node.queryComponent().grabFocus()
        return True
    except Exception:
        pass
    rect = extents(node)
    if rect is not None:
        click_point(rect.x + rect.width / 2, rect.y + rect.height / 2)
        return True
    return False


def type_text(text):
    subprocess.run(['xdotool', 'type', '--delay', '30', text], check=True)


def type_into(node, text):
    """Prefer AT-SPI's editable text: no X focus, no dropped keystrokes."""
    try:
        node.queryEditableText().setTextContents(text)
        return 'editable'
    except Exception:
        pass
    focus(node)
    time.sleep(0.2)
    type_text(text)
    return 'keys'


def key(combo):
    subprocess.run(['xdotool', 'key', combo], check=True)


def shot(path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    if os.path.exists(path):
        os.unlink(path)
    subprocess.run(['import', '-window', 'root', path], check=True)
    print(f'shot {path}')


def dump(depth=12):
    all_nodes = bool(os.environ.get('OSI_DUMP_ALL'))
    for app in apps():
        for node in descendants(app, max_depth=depth):
            if node is app:
                continue
            if not all_nodes and not shown(node):
                continue
            rect = extents(node)
            where = f'@{rect.x},{rect.y} {rect.width}x{rect.height}' if rect else ''
            states = []
            try:
                for flag in ('SENSITIVE', 'ENABLED', 'CHECKED', 'FOCUSED'):
                    if node.getState().contains(getattr(pyatspi, f'STATE_{flag}')):
                        states.append(flag.lower())
            except Exception:
                pass
            print(f"{normalise_role(node):16} {name_of(node)[:72]!r} {where} "
                  f"{' '.join(states)}")


def has_named_control_below(node, max_depth=4):
    """True when the widget contains a control that carries its own name.

    GTK wraps every child of a Gtk.ListBox in a Gtk.ListBoxRow, and that
    wrapper exposes no name of its own (the named Adw.ActionRow/ExpanderRow is
    inside it). A screen reader still reaches the named row, so this is not a
    control with no name — only a redundant wrapper.
    """
    try:
        children = list(node)
    except Exception:
        return False
    if max_depth <= 0:
        return False
    for child in children:
        if normalise_role(child) in CONTROL_ROLES and name_of(child):
            return True
        if has_named_control_below(child, max_depth - 1):
            return True
    return False


def nameless_controls():
    nameless = []
    for app in apps():
        for node in descendants(app):
            role = normalise_role(node)
            if role not in CONTROL_ROLES:
                continue
            if not (shown(node) and on_display(node)):
                continue
            if name_of(node) or has_named_control_below(node):
                continue
            rect = extents(node)
            where = f'@{rect.x},{rect.y} {rect.width}x{rect.height}' if rect else '@?'
            nameless.append(f'{role} {where}')
    return sorted(set(nameless))


def lint():
    nameless = nameless_controls()
    return result('a11y', not nameless,
                  'no accessible name: ' + ', '.join(nameless) if nameless else '')


### the page walk ###

class Walk:
    def __init__(self, out_dir, lint_pages=False):
        self.out = out_dir
        self.lint_pages = lint_pages
        self.n = 0
        self.checks = 0

    def step(self, label):
        self.n += 1
        print(f'\n== {self.n:02d} {label}')

    def shot(self, name):
        path = os.path.join(self.out, 'shots', f'{self.n:02d}-{name}.png')
        shot(path)

    def page(self, title, timeout=60):
        wait_title(title, timeout)
        print(f'page: {title}')
        if os.environ.get('OSI_DUMP'):
            dump(40)
        if self.lint_pages:
            self.checks += 1
            if not lint():
                raise CheckFailed(f'{title} has a control without a name')

    def click(self, query, timeout=15):
        node = wait(query, timeout)
        how = activate(node)
        print(f'click {query!r} ({how})')
        return node

    def type(self, query, text, nth=1, timeout=15):
        nodes = wait_all(query, timeout)
        if len(nodes) < nth:
            raise CheckFailed(f'{query!r}: wanted #{nth}, only {len(nodes)} match')
        node = nodes[nth - 1]
        how = type_into(node, text)
        print(f'type into {query!r} #{nth} ({how})')
        return node

    def expect(self, query, what, timeout=5):
        node = wait(query, timeout)
        if not sensitive(node):
            raise CheckFailed(f'{what}: {name_of(node)!r} is not sensitive')
        self.checks += 1
        print(f'ok {what}')

    def expect_absent(self, query, what):
        if find(query):
            raise CheckFailed(f'{what}: {query!r} is on screen but should not be')
        self.checks += 1
        print(f'ok {what}')

    def expect_disabled(self, query, what, timeout=5):
        """A control that must be there but must not be usable (too small)."""
        node = wait(query, timeout)
        if sensitive(node):
            raise CheckFailed(f'{what}: {name_of(node)!r} is selectable')
        self.checks += 1
        print(f'ok {what} (not selectable)')

    def expect_text(self, query, pattern, what):
        node = wait(query, 5)
        text = name_of(node)
        if not re.search(pattern, text):
            raise CheckFailed(f'{what}: {text!r} does not match {pattern!r}')
        self.checks += 1
        print(f'ok {what}: {text!r}')


def check_script_log(path):
    """The three steps ran, in order, with the OSI_* values the GUI collected."""
    try:
        with open(path) as log:
            text = log.read()
    except FileNotFoundError:
        return result('scripts', False, f'no log at {path}')

    steps = re.findall(r'^=== (\w+) pid=', text, re.M)
    ok = result('scripts-order', steps == ['prepare', 'install', 'configure'],
                f'got {steps}')
    sections = dict(re.findall(
        r'^=== (\w+) pid=\d+\n((?:OSI_[^\n]*\n?)*)', text, re.M))
    envs = {
        step: dict(line.split('=', 1) for line in body.splitlines() if '=' in line)
        for step, body in sections.items()
    }

    install = envs.get('install', {})
    expect_install = {
        'OSI_DEVICE_PATH': '/dev/sda',
        'OSI_DEVICE_IS_PARTITION': '0',
        'OSI_DEVICE_EFI_PARTITION': '/dev/sda_efi',
        'OSI_USE_ENCRYPTION': '1',
        'OSI_ENCRYPTION_PIN': '1234',
        'OSI_LOCALE': 'en_US.UTF-8',
        'OSI_KEYBOARD_LAYOUT': 'us',
    }
    for var, value in expect_install.items():
        ok &= result(f'install-{var}', install.get(var) == value,
                     f'{install.get(var)!r} != {value!r}')

    configure = envs.get('configure', {})
    expect_configure = {
        'OSI_USER_USERNAME': 'user',      # user_name is '' (skip_user: yes)
        'OSI_TIMEZONE': 'UTC',
        'OSI_FORMATS': 'en_US.UTF-8',
        'OSI_ROOT_PASSWORD': '',
    }
    for var, value in expect_configure.items():
        ok &= result(f'configure-{var}', configure.get(var) == value,
                     f'{configure.get(var)!r} != {value!r}')

    ok &= result('prepare-no-install-envs',
                 'OSI_DEVICE_PATH' not in envs.get('prepare', {}))
    return ok


def walk(out_dir, lint_pages=False):
    walker = Walk(out_dir, lint_pages)

    walker.step('welcome')
    walker.page('Welcome', 120)
    walker.shot('welcome')
    walker.expect_text('label:Shani OS',
                       'Shani OS', 'welcome text names the distribution')
    walker.click('button:^Continue$')

    walker.step('keyboard layout')
    walker.page('Keyboard Layout')
    walker.shot('keyboard')
    walker.click('button:^Continue$')

    walker.step('disk selection')
    walker.page('Disk Selection')
    walker.shot('disk')
    walker.expect_absent('button:^Continue$',
                         'no Continue before a disk is chosen')
    walker.expect_disabled('.*Dummy', 'the too-small demo disk is listed')
    walker.click('.*Totally real device')

    walker.step('encryption')
    walker.page('Disk Encryption')
    walker.shot('encrypt-off')
    walker.click('.*Encrypt Files')
    wait('password text:.*', 10)
    # The PIN and its confirmation are in template order; the root password
    # fields (also password texts) follow them.
    walker.type('password text:.*', '1234', nth=1)
    walker.type('password text:.*', '1234', nth=2)
    walker.shot('encrypt-on')
    walker.expect('button:^Continue$', 'PIN accepted by the continue button')
    walker.click('button:^Continue$')

    walker.step('confirmation')
    walker.page('Confirmation')
    walker.shot('confirm')
    walker.click('button:^Confirm$')

    walker.step('summary')
    walker.page('Summary')
    walker.shot('summary')
    walker.expect_text('label:^(Enabled|Disabled)$', 'Enabled',
                       'summary says encryption is on')
    walker.expect_text('label:^(Set|Not set)$', 'Not set',
                       'summary says no root password')
    walker.click('button:^Confirm$')

    walker.step('installing')
    walker.page('Installing')
    walker.shot('installing')
    walker.step('done')
    walker.page('Installation Complete', 180)
    walker.shot('done')
    walker.expect('button:^Restart System$', 'restart button')
    walker.expect('button:^Restart Later$', 'restart-later button')
    walker.click('button:^Restart Later$')

    walker.step('quit')
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if not find('frame:.*'):
            result('quit', True, 'installer exited after Restart Later')
            break
        time.sleep(0.3)
    else:
        raise CheckFailed('installer did not exit after Restart Later')

    log = os.environ.get('OSI_DEV_LOG', '/work/out/logs/scripts.log')
    ok = check_script_log(log)

    return 0 if (ok and result('walk', True, f'{walker.n} pages')) else 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    command, args = argv[0], [arg for arg in argv[1:]]
    os.environ.setdefault('DISPLAY', ':99')
    try:
        if command == 'dump':
            dump(int(args[0]) if args else 12)
            return 0
        if command == 'find':
            for node in find(args[0]):
                print(f'{normalise_role(node):16} {name_of(node)!r}')
            return 0
        if command == 'wait':
            wait(args[0], float(args[1]) if len(args) > 1 else 30)
            print('found')
            return 0
        if command == 'wait-title':
            wait_title(args[0], float(args[1]) if len(args) > 1 else 30)
            print(f'page {args[0]!r} shown')
            return 0
        if command == 'click':
            node = wait(args[0], 15)
            print(activate(node))
            return 0
        if command == 'type':
            node = wait(args[0], 15)
            print(type_into(node, ' '.join(args[1:])))
            return 0
        if command == 'shot':
            shot(args[0])
            return 0
        if command == 'key':
            key(args[0])
            return 0
        if command == 'states':
            node = wait(args[0], 15)
            state = node.getState()
            print(', '.join(name for name in dir(pyatspi)
                            if name.startswith('STATE_') and
                            state.contains(getattr(pyatspi, name))))
            return 0
        if command == 'lint':
            return 0 if lint() else 1
        if command == 'walk':
            out = os.environ.get('OUT', 'out')
            if args and not args[0].startswith('--'):
                out = args[0]
            return walk(out, '--lint' in args)
    except (AppNotRunning, CheckFailed) as error:
        result('walk', False, str(error))
        dump(40)
        return 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
