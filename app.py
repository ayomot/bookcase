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
from hashlib import sha1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_DIR = os.path.join(BASE_DIR, 'static/css')
IMG_DIR = os.path.join(BASE_DIR, 'static/img')
DEFAULT_BOOK_DIR = os.path.join(BASE_DIR, 'debug/book')
DEFAULT_TMB_DIR = os.path.join(BASE_DIR, 'debug/TMB')
NUM_OF_TMB = 40
TABLE_LEN = 9
SPLIT_LEN = TABLE_LEN - 4
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

        if os.path.isdir(joinpath(path, name)):
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
        table = create_table(p, page)
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


def create_table(index, last_page):
    """
    ページ移動用のテーブルを作成する
    総ページ数がテーブルに収まらない場合、
    現在のページ数を中央に配置し、先頭と末尾に先頭・末尾のNo.を付加する。
    例: ["1", "...", "3", "4", "5", "...", "N"]

    Parameters
    ----------
    index : int
        現在のページNo.
    last_page : int
        最後尾のページNo.
    """
    start = 1
    end = last_page

    # ページ数がテーブルに収まらない場合は、テーブルを分割
    if TABLE_LEN < last_page:
        if index <= SPLIT_LEN:
            end = TABLE_LEN
        elif SPLIT_LEN < index < (last_page - SPLIT_LEN):
            start = index - (TABLE_LEN // 2)
            end = index + (TABLE_LEN // 2)
        else:
            start = last_page - TABLE_LEN + 1
            end = last_page

    # テーブル生成
    table = [str(i) for i in range(start, end + 1)]

    # テーブルを分割する場合、先頭ページと最終ページを追加
    if TABLE_LEN < last_page:
        if SPLIT_LEN < index:
            table[:2] = ["1", "..."]
        if index <= (last_page - SPLIT_LEN):
            table[-2:] = ["...", str(last_page)]

    return table


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

        def formatting(filepath):
            """
            ファイル名が数値のみのファイルのファイル名を0埋めして返す
            例： "path/0001.jpg", "path/0002.jpg", ...
            """
            path, filename = os.path.split(filepath)
            name, ext = os.path.splitext(filename)
            if name.isdigit():
                return os.path.join(path, name.zfill(4) + ext)
            return filepath

        self._files.sort(key=formatting)

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
        return self._files[index]

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
        tmbname = sha1(ext.get_filename(i).encode('utf-8')).hexdigest()
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
    if app.config['app.debug'] == 'True':
        app.config['app.book_root'] = DEFAULT_BOOK_DIR
        app.config['app.tmb_root'] = DEFAULT_TMB_DIR


if __name__ == '__main__':
    init_config()
    run(app, host='localhost', port=8080, debug=True, reloader=True)
