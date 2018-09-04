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
from natsort import natsorted

##################################
# Initialize
##################################
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_DIR = os.path.join(BASE_DIR, 'static/css')
IMG_DIR = os.path.join(BASE_DIR, 'static/img')
CONFIG_FILE = os.path.join(BASE_DIR, 'app.conf')
BOOK_ROOT = os.path.join(BASE_DIR, 'debug/book')
TMB_ROOT = os.path.join(BASE_DIR, 'debug/TMB')
NUM_OF_TMB = 40
TABLE_LEN = 9
SPLIT_LEN = TABLE_LEN - 4
app = bottle.default_app()

# config設定を読み込む
app.config.load_config(CONFIG_FILE)

# デバッグ設定でない場合は、configを上書き
if not app.config['app.debug'] == 'True':
    BOOK_ROOT = app.config['app.book_root']
    TMB_ROOT = app.config['app.tmb_root']


def bookpath_filter(config):
    regexp = r'.+?'

    def to_python(match):
        ret = os.path.join(BOOK_ROOT, parse.unquote(match))

        if BOOK_ROOT not in ret:
            raise Exception()
        return ret

    def to_url(fullpath):
        return convert_url(fullpath)

    return regexp, to_python, to_url


app.router.add_filter('book', bookpath_filter)


##################################
# Routing
##################################
@get('/')
@get('/ls/')
def index():
    files, dirs = dirlist(BOOK_ROOT)
    return template('index', files=files, dirs=dirs)


@get('/ls/<path:book>')
def ls(path):
    try:
        files, dirs = dirlist(path)
        return template('index', files=files, dirs=dirs)
    except FileNotFoundError:
        filename = relative_bookpath(path)
        return HTTPError(404, "{0} is Not Found".format(filename))


@get('/list/<path:book>/<p:int>')
def thumbnails(path, p):
    try:
        with closing(Extractor(path)) as ext:
            lst = index_list(p, ext.length())
            page = int(math.ceil(ext.length() / NUM_OF_TMB))
        table = create_table(p, page)
        bookpath = convert_url(path)
        base = convert_url(os.path.dirname(path))
        return template('list', name=bookpath, index=lst, table=table,
                        p=p, base=base)
    except FileNotFoundError:
        filename = relative_bookpath(path)
        return HTTPError(404, "{0} is Not Found".format(filename))


@get('/view/<path:book>/<index:int>')
def view(path, index):
    try:
        with closing(Extractor(path)) as ext:
            ifile = ext.img_ext(index)
            mvdict = move_dict(path, index, ext.length())
            bookpath = convert_url(path)
        return template('main', name=bookpath, mvdict=mvdict, img=ifile)
    except FileNotFoundError:
        filename = relative_bookpath(path)
        return HTTPError(404, "{0} is Not Found".format(filename))
    except IndexError:
        return HTTPError(500, "Index Is Out Of Range")


@route('/css/<filename>')
def static_css(filename):
    return static_file(filename, root=CSS_DIR)


@route('/img/<filename>')
def static_img(filename):
    return static_file(filename, root=IMG_DIR)


@route('/tmb/<path:book>/<i:int>')
def return_tmb(path, i):
    with closing(Extractor(path)) as ext:
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


##################################
# Logic
##################################
def dirlist(path):
    # 上位ディレクトリのパスを登録しておく
    dirs = {"..": convert_url(os.path.dirname(path))}
    files = {}
    for name in os.listdir(path):
        root, ext = os.path.splitext(name)
        bpath = convert_url(os.path.join(path, name))

        if os.path.isdir(os.path.join(path, name)):
            dirs.update({name: bpath})
        elif ext == '.zip':
            files.update({name: bpath})

    return files, dirs


def move_dict(path, index, limit):
    def _sub1(n):
        return 0 if n <= 0 else n - 1

    def _add1(n, limit):
        return limit if n >= limit else n + 1

    mvdict = {"back": _sub1(index),
              "next": _add1(index, _sub1(limit)),
              "pagetop": index // NUM_OF_TMB + 1}
    return mvdict


def relative_bookpath(path):
    return os.path.relpath(path, BOOK_ROOT)


def convert_url(path):
    relpath = relative_bookpath(path)
    return parse.quote(relpath)


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
        self._files = natsorted(
                [item
                 for item in self._zfile.namelist()
                 if self._remove(item)],
                key=str.lower)

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

    def length(self):
        return len(self._files)

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


def save_tmb(tmb, path):
    with open(path, "wb") as fout:
        fout.write(tmb)
        fout.flush


def create_tmb_path(name):
    return os.path.join(TMB_ROOT, os.path.basename(name))


def get_bookname(path):
    name, ext = os.path.splitext(os.path.basename(path))
    return name


def get_tmb(path):
    with open(path, "rb") as fin:
        return fin.read()


if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True, reloader=True)
