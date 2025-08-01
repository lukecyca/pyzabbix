# -*- encoding: utf-8 -*-
#
# Copyright © 2014 Alexey Dubkov
#
# This file is part of py-zabbix.
#
# Py-zabbix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Py-zabbix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with py-zabbix. If not, see <http://www.gnu.org/licenses/>.
import logging
import re


class NullHandler(logging.Handler):
    """Null logger handler.

    :class:`NullHandler` will be used if there are no other logger handlers.
    """

    def emit(self, record):
        pass


class HideSensitiveFilter(logging.Filter):
    """Filter to hide sensitive Zabbix info (password, auth) in logs"""

    def __init__(self, *args, **kwargs):
        super(logging.Filter, self).__init__(*args, **kwargs)
        self.hide_sensitive = HideSensitiveService.hide_sensitive

    def filter(self, record):

        record.msg = self.hide_sensitive(record.msg)
        if record.args:
            newargs = [self.hide_sensitive(arg) if isinstance(arg, str)
                       else arg for arg in record.args]
            record.args = tuple(newargs)

        return 1


class HideSensitiveService(object):
    """
    Service to hide sensitive Zabbix info (password, auth tokens)
    Call classmethod hide_sensitive(message: str)
    """

    HIDEMASK = "********"
    _pattern = re.compile(
        r'(?P<key>password)["\']\s*:\s*u?["\'](?P<password>.+?)["\']'
        r'|'
        r'\W(?P<token>[a-z0-9]{32})')

    @classmethod
    def hide_sensitive(cls, message):
        def hide(m):
            if m.group('key') == 'password':
                return m.string[m.start():m.end()].replace(
                    m.group('password'), cls.HIDEMASK)
            else:
                return m.string[m.start():m.end()].replace(
                    m.group('token'), cls.HIDEMASK)

        message = re.sub(cls._pattern, hide, message)

        return message