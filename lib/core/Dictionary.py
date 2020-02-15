# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Mauro Soria

import threading

import urllib.error
import urllib.parse
import urllib.request

from lib.utils.FileUtils import File
from thirdparty.oset import *


class Dictionary(object):

    def __init__(self, path, extensions, lowercase=False, forcedExtensions=False):
        self.entries = []
        self.currentIndex = 0
        self.condition = threading.Lock()
        self._extensions = extensions
        self._path = path
        self._forcedExtensions = forcedExtensions
        self.lowercase = lowercase
        self.dictionaryFile = File(self.path)
        self.generate()

    @property
    def extensions(self):
        return self._extensions

    @extensions.setter
    def extensions(self, value):
        self._extensions = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @classmethod
    def quote(cls, string):
        return urllib.parse.quote(string, safe=":/~?%&+-=$")

    """
    Dictionary.generate() behaviour

    Classic dirsearch wordlist:
      1. If %EXT% keyword is present, append one with each extension REPLACED.
      2. If the special word is no present, append line unmodified.

    Forced extensions wordlist (NEW):
      This type of wordlist processing is a mix between classic processing
      and DirBuster processing.
          1. If %EXT% keyword is present in the line, immediately process as "classic dirsearch" (1).
          2. If the line does not include the special word AND is NOT terminated by a slash,
            append one with each extension APPENDED (line.ext) and ONLYE ONE with a slash.
          3. If the line does not include the special word and IS ALREADY terminated by slash,
            append line unmodified.
    """

    def generate(self):
        result = []
        for line in self.dictionaryFile.getLines():

            # Skip comments
            if line.lstrip().startswith("#"):
                continue

            # Classic dirsearch wordlist processing (with %EXT% keyword)
            if '%EXT%' in line:
                for extension in self._extensions:
                    quote = self.quote(line.replace('%EXT%', extension))
                    result.append(quote)

            # If forced extensions is used and the path is not a directory ... (terminated by /)
            # process line like a forced extension.
            elif self._forcedExtensions and not line.rstrip().endswith("/"):
                quoted = self.quote(line)

                for extension in self._extensions:
                    # Why? check https://github.com/maurosoria/dirsearch/issues/70
                    if extension.strip() == '':
                        result.append(quoted)
                    else:
                        result.append(quoted + '.' + extension)

                if quoted.strip() not in ['']:
                    result.append(quoted + "/")

            # Append line unmodified.
            else:
                result.append(self.quote(line))

        # oset library provides inserted ordered and unique collection.
        if self.lowercase:
            self.entries = list(oset(map(lambda l: l.lower(), result)))

        else:
            self.entries = list(oset(result))
        del (result)

    def regenerate(self):
        self.generate(lowercase=self.lowercase)
        self.reset()

    def nextWithIndex(self, basePath=None):
        self.condition.acquire()

        try:
            result = self.entries[self.currentIndex]

        except IndexError:
            self.condition.release()
            raise StopIteration

        self.currentIndex = self.currentIndex + 1
        currentIndex = self.currentIndex
        self.condition.release()
        return currentIndex, result

    def generateByUrl(self,url):
        """
           从url中生成敏感文件待扫描列表
           :param url:
           :return:
           """
        suffixes = ['.rar', '.zip', '.sql', '.gz', '.sql.gz', '.tar.gz', '.bak', '.sql.bak', '.war', '.jar']
        file_dic = ['bak.rar', 'bak.zip','website.tar.gz', 'test.zip', 'test.tar.gz','test.rar','1.rar', '1.war']
        url = url.replace('http://', '').replace('https://', '')
        if '/' in url:
            url = url.split('/')[0]
        if ':' in url:
            url = url.split(':')[0]
        print(url)
        #自定义的一些字典
        host_items = url.split('.')
        for suffix in suffixes:
            file_dic.append("".join(host_items[1:]) + suffix)
            file_dic.append(host_items[1] + suffix)
            file_dic.append(host_items[-2] + suffix)
            file_dic.append("".join(host_items) + suffix)
            file_dic.append(url + suffix)
        self.entries = self.entries + list(set(file_dic))

    def __next__(self, basePath=None):
        _, path = self.nextWithIndex(basePath)
        return path

    def reset(self):
        self.condition.acquire()
        self.currentIndex = 0
        self.condition.release()

    def __len__(self):
        return len(self.entries)
