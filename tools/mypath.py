import os.path
import fnmatch
from collections import deque



def _contains(dirname, dirs=None, case=False):
    """
    如果dirname通过fnmatch能够和dirs(符合fnmatch规则)中的任意一项进行匹配，返回True。
    fnmatch规则
    * 任意多个任意字符
    ? 一个任意字符
    [seq] 表示范围
    [!seq] 表示不再范围内
    [?] 表示问号本身
    .是普通字符，可以通过?来匹配。
    比如./*/*.py表示当前目录下的任意子目录下的所有py文件。所以fnmatch.fnmatch('./mmm/a.py','./*/[!b-f].py')返回True。
    case表示是否忽略大小写，如果使用False，那么会使用系统默认的选项，也就是说Unix中仍然是区分大小写的，而Windows中不区分。如果使用True，那么总是区分大小写

    """
    if isinstance(dirs, str):
        dirs = (dirs, )


    if case:
        matchfunc = fnmatch.fnmatchcase
    else:
        matchfunc = fnmatch.fnmatch

    dirs = tuple() if dirs is None else dirs

    for d in dirs:
        if matchfunc(dirname, d):
            # print('matching name:', dirname, 'with rules: ', dirs)
            return True

    return False

def _reverse_subpath(surpath, sub_paths):
    """
    用来反转sub_paths中的元素，只是mywalk函数的一个测试函数。
    """
    final_sub_paths = []
    for sp in sub_paths:
        final_sub_paths.insert(0, sp)

    return final_sub_paths
        



def _mywalk(directory, skip_zero_files=False, skip_dirs=None, skip_filenames=None, skip_hidden_dir=False, skip_hidden_files=False, cb_subpaths=None, cb_subfiles=None):
    """
    工作方法和os.walk相同，但是增加了一些细粒度的控制参数。
    skip_dirs表示在dirs中所有不需要处理的有子目录。可以接受unix的shell相同的匹配规则。
    skip_filenames表示在dirs中所有不需要处理的文件类型。可以接受unix的shell相同的匹配规则。
    skip_zero_files 不遍历零字节文件
    skip_hidden_dir 不遍历隐藏文件夹
    skip_hidden_files 不遍历隐藏文件，也就是以点号开始的文件
    cb_subpaths是一个用户自定义的函数，传入参数surpath, sub_paths，可以按照用户需要进行定制，比如按照字母序列倒序，返回sub_paths。
    cb_subfiles是一个用户自定义的函数，传入surpath, sub_files，返回sub_files列表

    """
    # 存放需要遍历的目录
    walk_paths = deque()
    walk_paths.append(os.path.abspath(directory))

    skip_dirs = tuple() if skip_dirs is None else skip_dirs
    if isinstance(skip_dirs, str):
        skip_dirs = (skip_dirs, )

    skip_filenames = tuple() if skip_filenames is None else skip_filenames
    if isinstance(skip_filenames, str):
        skip_filenames = (skip_filenames, )



    while walk_paths:
        path = walk_paths.popleft()
        sub_files = []
        sub_paths = []
        # 有些目录可能不允许访问，所以os.listdir会报错(PermissionError)
        try:
            for name in os.listdir(path):
                fullname = os.path.join(path, name)
                
                # print(name, fullname)
                if os.path.isfile(fullname):
                    if skip_zero_files and os.path.getsize(fullname) == 0:
                        continue

                    if skip_hidden_files and name.startswith('.'):
                        continue

                    if _contains(name, skip_filenames):
                        continue

                    sub_files.append(name)

                elif os.path.isdir(fullname):
                    if skip_hidden_dir and name.startswith('.'):
                        continue

                    if _contains(name, skip_dirs):
                        continue

                    sub_paths.append(name)
            for p in sub_paths:
                walk_paths.append(os.path.join(path, p))

            if cb_subpaths is not None:
                sub_paths = cb_subpaths(path, sub_paths)

            if cb_subfiles is not None:
                sub_files = cb_subfiles(path, sub_files)
            yield [path, sub_paths, sub_files]
        except PermissionError:
            print('can\'t read folder:', path, file=sys.stderr)

def mywalk(dirs, skip_zero_files=False, skip_dirs=None, skip_filenames=None, skip_hidden_dir=False, skip_hidden_files=False, cb_subpaths=None, cb_subfiles=None):
    """
    工作方法和os.walk相同，但是第一个参数可以使一个目录字符串，或者目录元祖，且增加了一些细粒度的控制参数。
    第一个参数可以是一个表示目录的字符串，也可以是一个表示目录的字符串元祖。如果是元祖，那么会依次遍历每个目录中的所有文件。
    """
    if isinstance(dirs, str):
        dirs = (os.path.abspath(dirs), )
    else:
        dirs = tuple([os.path.abspath(d) for d in dirs])


    for d in dirs:
        for res in  _mywalk(d, skip_zero_files=skip_zero_files, skip_dirs=skip_dirs, skip_filenames=skip_filenames, skip_hidden_dir=skip_hidden_dir, skip_hidden_files=skip_hidden_files, cb_subpaths=cb_subpaths, cb_subfiles=cb_subfiles):
            yield res


def mywalk_files(dirs, skip_zero_files=False, skip_dirs=None, skip_filenames=None, skip_hidden_dir=False, skip_hidden_files=False, cb_subpaths=None, cb_subfiles=None):
    """
    依次遍历dirs中的每一个文件，每次返回的是带有全目录的文件名。
    skip_dirs表示在dirs中所有不需要处理的有子目录。可以接受unix的shell相同的匹配规则。
    skip_filenames表示在dirs中所有不需要处理的文件类型。可以接受unix的shell相同的匹配规则。
    skip_zero_files 不遍历零字节文件
    skip_hidden_dir 不遍历隐藏文件夹
    skip_hidden_files 不遍历隐藏文件，也就是以点号开始的文件
    """
    for path, _, files in mywalk(dirs, skip_zero_files=skip_zero_files, skip_dirs=skip_dirs, skip_filenames=skip_filenames, skip_hidden_dir=skip_hidden_dir, skip_hidden_files=skip_hidden_files, cb_subpaths=cb_subpaths, cb_subfiles=cb_subfiles):
        for f in files:
            yield os.path.join(path, f)
        



if __name__ == '__main__':
    d = '/Users/lhq/nutstore/py/testfiles'
    d2 = '/Users/lhq/nutstore/learning/c pieces/myds'
    skip_dir = os.path.join(d, 'skipdir')

    m = mywalk_files(d)
    r = [item for item in m]
    assert('/Users/lhq/nutstore/py/testfiles/__init__.py' in r)
    assert('/Users/lhq/nutstore/py/testfiles/.hide/not_hidden.py' in r)
    assert('/Users/lhq/nutstore/py/testfiles/skipdir/skipfile.py' in r)
    assert('/Users/lhq/nutstore/py/testfiles/skipfile.f' in r)
    assert('/Users/lhq/nutstore/py/testfiles/zerosize.file' in r)
    assert('/Users/lhq/nutstore/py/testfiles/.hide.file' in r)

    m2 = mywalk(d, skip_dirs=(skip_dir,))
    assert(('/Users/lhq/nutstorepy/testfiles/skipdir/skipfile.py' in m2) == False)

    m3 = mywalk(d, skip_zero_files=True)
    assert(('/Users/lhq/nutstore/py/testfiles/zerosize.file' in m3) == False)

    m4 = mywalk(d, skip_filenames=('__init__.py',))
    assert(('/Users/lhq/nutstore/py/testfiles/__init__.py' in m4) == False)

    m5 = mywalk(d, skip_hidden_dir=True)
    assert(('/Users/lhq/nutstore/py/testfiles/.hide/not_hidden.py' in m5) == False)
    assert('/Users/lhq/nutstore/py/testfiles/.hide.file' in r)

    m6 = mywalk(d, skip_hidden_files=True)
    assert(('/Users/lhq/nutstore/py/testfiles/.hide.file' in m6) == False)
    assert('/Users/lhq/nutstore/py/testfiles/.hide/not_hidden.py' in r)

    # w = mywalk((d, d2),)
    # for m in w:
        # print(m)


