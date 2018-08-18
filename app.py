# -*- coding:utf-8 -*-

import bottle
from bottle import run, template
from bottle import route, get, static_file, HTTPError
from bottle import HTTPResponse
import zipfile
import base64
import os
from PIL import Image
import io
import math
from urllib import parse
from contextlib import closing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_DIR = os.path.join(BASE_DIR, 'static/css')
IMG_DIR = os.path.join(BASE_DIR, 'static/img')
DEFAULT_BOOK_DIR = os.path.join(BASE_DIR, 'debug/book')
DEFAULT_TMB_DIR = os.path.join(BASE_DIR, 'debug/TMB')
NUM_OF_TMB = 40
TABLE_LEN = 9
app = bottle.default_app()


@get('/')
def index():
    files, dirs = dirlist(app.config['app.book_root'])
    return template('index', files=files, dirs=dirs)


@get('/ls/<path:path>')
def ls(path):
    path = parse.unquote(path)
    try:
        directory = joinpath('/', path)
        files, dirs = dirlist(directory)
        return template('index', files=files, dirs=dirs)
    except FileNotFoundError:
        return HTTPError(404, "{0} is Not Found".format(path))


def dirlist(path):
    # 上位ディレクトリのパスを登録しておく
    dirs = {"..": os.path.dirname(path)}
    files = {}
    for name in os.listdir(path):
        root, ext = os.path.splitext(name)
        bpath = joinpath(path, name)
        bpath = parse.quote(bpath)

        if ext == '':
            dirs.update({name: bpath})
        elif ext == '.zip':
            files.update({name: bpath})

    return files, dirs


@get('/list/<path:path>/<p:int>')
def thumbnails(path, p):
    path = parse.unquote(path)
    src = joinpath('/', path)
    try:
        with closing(Extractor(src)) as ext:
            lst = index_list(p, len(ext.get_filelist()))
        page = int(math.ceil(ziplen(src) / NUM_OF_TMB))
        table = create_table(p, page, TABLE_LEN)
        path = parse.quote(src)
        base = parse.quote(os.path.dirname(src))
        return template('list', name=path, index=lst, table=table,
                        p=p, base=base)
    except FileNotFoundError:
        return HTTPError(404, "{0} is Not Found".format(path))


@get('/view/<path:path>/<index:int>')
def view(path, index):
    path = parse.unquote(path)
    src = joinpath('/', path)
    try:
        with closing(Extractor(src)) as ext:
            ifile = ext.img_ext(index)
            mvdict = move_dict(src, index, len(ext.get_filelist()))
        return template('main', mvdict=mvdict, img=ifile)
    except FileNotFoundError:
        return HTTPError(404, "{0} is Not Found".format(path))
    except IndexError:
        return HTTPError(500, "Index Is Out Of Range")


def move_dict(path, index, limit):
    mvdict = {"back": sub1(index),
              "next": add1(index, sub1(limit)),
              "pagetop": page_top(path, index)}
    return mvdict


def sub1(n):
    if n <= 0:
        return 0
    else:
        return n - 1


def add1(n, limit):
    if n >= limit:
        return limit
    else:
        return n + 1


def page_top(path, index):
    path = parse.quote(path)
    page = str(int(index / NUM_OF_TMB) + 1)
    return "/list/{0}/{1}".format(path, page)


def ziplen(src):
    with zipfile.ZipFile(src, 'r') as zfile:
        return len(zfile.namelist())


def joinpath(path1, path2):
    return os.path.join(path1, path2)


def create_table(index, index_len, table_len):
    med_of_table = int(math.ceil(table_len / 2))
    harf_len = int(table_len / 2)

    if index <= 0:
        pass
    if index_len <= table_len:
        table = list(range(1, (index_len + 1)))
        return table
    if index <= med_of_table:
        table = list(range(1, (table_len + 1)))
        table.append("...")
        table.append(index_len)
        return table
    if index >= index_len - harf_len:
        table = list(range((index_len - (harf_len * 2)), (index_len + 1)))
        table.insert(0, 1)
        table.insert(1, "...")
        return table
    if med_of_table < index < index_len - harf_len:
        table = list(range((index - harf_len), (index + harf_len + 1)))
        table.insert(0, 1)
        table.insert(1, "...")
        table.append("...")
        table.append(index_len)
        return table
    return


def index_list(p, limit):
    start = (p-1) * NUM_OF_TMB
    stop = p * NUM_OF_TMB
    if limit < stop:
        stop = limit
    lst = list(range(start, stop))
    return lst


class Extractor:
    def __init__(self, src):
        self._src = src
        self._zfile = zipfile.ZipFile(src, 'r')
        self._files = [
                item
                for item in self._zfile.namelist()
                if self._remove(item)]
        self._files.sort()

    def img_ext(self, index):
        name = self._files[index]
        img = self._zfile.read(name)
        return self._add_scheme(img)

    def close(self):
        self._zfile.close()

    def get_tmb(self, i):
        if len(self._files) <= i:
            return None
        name = self._files[i]
        return self._tmb_combert(self._zfile.open(name, 'r'))

    def get_filelist(self):
        return self._files

    def get_filename(self, index):
        return os.path.basename(self._files[index])

    def _remove(self, item):
        root, ext = os.path.splitext(item)
        return ext in ('.png', '.jpg', '.jpeg', '.JPG')

    def _add_scheme(self, img):
        img = base64.b64encode(img)
        scheme = 'data:img/jpg;base64,'
        return scheme + img.decode('utf-8')

    def _tmb_combert(self, fp):
        img = Image.open(fp, 'r')
        if img.mode != 'RGB':
            img = img.convert('RGB')
        jpg_img_buf = io.BytesIO()
        img.thumbnail((150, 150), Image.ANTIALIAS)
        img.save(jpg_img_buf, format='JPEG')
        return jpg_img_buf.getvalue()


@route('/css/<filename>')
def recoad_static(filename):
    return static_file(filename, root=CSS_DIR)


@route('/img/<filename>')
def recoad_static(filename):
    return static_file(filename, root=IMG_DIR)


@route('/tmb/<filename>')
def recoad_static(filename):
    return static_file(filename, root=app.config['app.tmb_root'])


@route('/tmb/<path:path>/<i:int>')
def return_tmb(path, i):
    path = parse.unquote(path)
    src = joinpath('/', path)
    with closing(Extractor(src)) as ext:
        book = get_bookname(path)
        bookpath = create_tmb_path(book)
        tmbname = ext.get_filename(i)
        tmbpath = os.path.join(bookpath, tmbname)

        if(not os.path.isdir(bookpath)):
            os.mkdir(bookpath)
        if(not os.path.isfile(tmbpath)):
            img = ext.get_tmb(i)
            save_tmb(img, tmbpath)
        else:
            img = get_tmb(tmbpath)

    ret = HTTPResponse(status=200, body=img)
    ret.set_header('Content-Type', 'image/jpeg')
    return ret


def save_tmb(tmb, path):
    with open(path, "wb") as fout:
        fout.write(tmb)
        fout.flush


def create_tmb_path(name):
    return os.path.join(app.config['app.tmb_root'], os.path.basename(name))


def get_bookname(path):
    name, ext = os.path.splitext(os.path.basename(path))
    return name


def get_tmb(path):
    with open(path, "rb") as fin:
        return fin.read()


def init_config():
    """ configの初期設定を行う
    """
    app.config.load_config('app.conf')

    # デバッグ設定の場合は、configを上書き
    if app.config['app.debug']:
        app.config['app.book_root'] = DEFAULT_BOOK_DIR
        app.config['app.tmb_root'] = DEFAULT_TMB_DIR


if __name__ == '__main__':
    init_config()
    run(app, host='localhost', port=8080, debug=True, reloader=True)
