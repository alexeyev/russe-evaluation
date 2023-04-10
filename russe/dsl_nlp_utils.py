# -*- coding: utf-8 -*-

import plumbum.cmd as cmd
import pprint
import re
import os

from sys import stdout

re_number = re.compile(r"\d+", re.U|re.I)


def get_pos(token):
    pass
    # """ Get main part-of-speech tag for token. """
    # analysis = token.get('analysis')
    # if not analysis:
    #     return None
    #
    # gr = analysis[0].get('gr', '')
    # return gr.split('=')[0].split(',')[0]


def wc(fpath):
    return int(cmd.wc["-l"](fpath).split()[0])


class PrettyPrinterUtf8(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def prt(string):
    stdout.write("%s\n" % string)


def exists(dir_path):
    return os.path.isdir(dir_path) or os.path.isfile(dir_path)