#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "lewin"
__date__ = "2019/5/11"
"""

"""

import os, sys
from urllib import parse
from datetime import datetime
from typing import List


# ------------------------- Project Environment -------------------------
def _find_root(n):
    if n > 0: return os.path.dirname(_find_root(n - 1))
    return os.path.abspath(__file__)


_path_project = _find_root(2)
if _path_project not in sys.path: sys.path.insert(0, _path_project)


# ------------------------- Functions -------------------------
def make(dirs: list) -> List[str]:
    dt_links = []
    link_mod = "<a style='text-decoration: none' href='%(addr)s'>%(name)s</a>"
    addr_head = "https://github.com/Saodd/Saodd.github.io/blob/master/"
    for dirname in dirs:
        for filename in os.listdir(dirname):
            addr = addr_head + parse.quote(os.path.basename(dirname) + "/" + filename)

            dt_str = filename[:8]
            tt_str = filename[9:]  # 中间是一个下划线
            dt = datetime.strptime(dt_str, "%Y%m%d")
            name = dt.strftime("%Y-%m-%d") + "&nbsp;" * 5 + str(tt_str.split(".")[0])
            link = link_mod % {"addr": addr, "name": name}
            dt_links.append([dt, link])

    return [dt_link[1] + "<br>\n" for dt_link in sorted(dt_links, reverse=True)]


# ------------------------- Main -------------------------
if __name__ == "__main__":
    DIRS = ["markdown"]
    DIRS = [os.path.join(_path_project, d) for d in DIRS]
    cache = make(DIRS)
    with open(os.path.join(_path_project, "index.html"), "w", encoding="utf-8") as f:
        f.writelines(cache)
