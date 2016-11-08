import os, sys
from tools import hashf
from tools.mypath import mywalk_files

# 用来保存report文件需要存放的路径，在每次运行hash_report()函数时，会更新该目录为hash_report()函数中参数dirs的第一个路径。
dup_report_path = os.getcwd()

def name_in_rmfirst(name, rm_first):
    """
    如果name中包含rm_first中的出现的任意元素，返回True，比如name为f.backup， 而rm_first中包含('back', '~')，那么会返回True
    """
    result = any([True for rf in rm_first if (rf in name)])
    # print(name, rm_first, result)
    return result


def _under_skip_dirs(filename, skip_dirs):
    """
    检查filename是否包含在skip_dirs中，如果是，返回True
    """
    for sd in skip_dirs:
        if sd in filename:
            # print('return True')
            return True
    return False

def hash_report(dirs, hash_dict=None, tofile='dup_report', hashfunc=hashf.md5f, skip_zero_files=True, skip_dirs=None, skip_filenames=('__init__', )):
    """
    遍历dirs目录下的所有文件，取文件的内容的hash值作为字典的键，带目录的文件名组成的列表作为字典的值，生成一个字典。
    相同hash值的文件名，放在一个列表中。
    dirs可以是一个表示目录的字符串，也可以是多个目录字符串的元祖。
    hash_dict 可以是上一次hash_report传入不同的dirs运行过的结果，从而可以实现两次结果的合并
    tofile参数表示生成的字典内容，存在tofile的文件里。如果设为None，那么不会保存该文件。
    hashfunc表示用来哈希的函数，该函数传入一个文件名，返回文件类型哈希的hexdigest()值
    skip_dirs表示在dirs中所有不需要处理的有子目录。可以接受unix的shell相同的匹配规则。
    skip_filenames表示在dirs中所有不需要处理的文件类型。可以接受unix的shell相同的匹配规则。
    """
    hash_dict = {} if hash_dict is None else hash_dict

    if isinstance(dirs, str):
        dirs = (dirs, )
    dirs = tuple([os.path.abspath(d) for d in dirs])

    skip_dirs = tuple() if skip_dirs is None else skip_dirs
    if isinstance(skip_dirs, str):
        skip_dirs = (skip_dirs, )

    skip_filenames = tuple() if skip_filenames is None else skip_filenames
    if isinstance(skip_filenames, str):
        skip_filenames = (skip_filenames, )

    for filename in mywalk_files(dirs, skip_zero_files=skip_zero_files, skip_dirs=skip_dirs, skip_filenames=skip_filenames):
        # print(filename)
        h = hashfunc(filename)
        if h in hash_dict:
            hash_dict[h].append(filename)
        else:
            hash_dict[h] = [filename, ]

    if tofile:
        try:
            if (not os.path.isfile(tofile)):
                # 如果文件不存在，那么在dirs中的一个目录中建立该文件。
                tofile = os.path.join(dup_report_path, tofile)
            open(tofile, 'w', encoding='utf-8').write(str(hash_dict))
        except:
            raise Exception('Failed to write to', tofile, 'coz can\'t open this file.')

    return hash_dict



def handle_report(report, tofile='dup_report', skip_dirs=None, skip_zero_files=True,  prefer_under=None, rm_first=( 'copy', '复制', '副本', '冲突', 'back', '~')):
    """
    可能在hash_report产生后且在真正删除重复文件之前，需要对符合某些规则的文件进行优先保留，而handle_report就是完成这个任务的。
    perfer_under 如果发生重复文件时，希望在perfer_under文件夹下的文件优先保存。
    rm_first 表示如果文件名中包含有rm_first中出现的字符，那么在重复出现时优先删除。
    tofile 如果设置为None，那么不会保存报告到文件
    """

    if skip_zero_files:
        # 空字符串的md5值为'd41d8cd98f00b204e9800998ecf8427e'.
        report.pop('d41d8cd98f00b204e9800998ecf8427e', 'to_avoid_KeyError')

    skip_dirs = tuple() if skip_dirs is None else skip_dirs
    if skip_dirs:
        if (isinstance(skip_dirs, str)):
            skip_dirs = (skip_dirs, )
        empty_keys = []
        for hash_value, filenames in report.items():
            for index, fn in enumerate(filenames):
                if _under_skip_dirs(fn, skip_dirs):
                    filenames.pop(index)
            if len(filenames) == 0:
                empty_keys.append(hash_value)
        for ek in empty_keys:
            report.pop(ek)

    prefer_under = tuple() if prefer_under is None else prefer_under
    if isinstance(prefer_under, str):
        prefer_under = (prefer_under,)
    prefer_under = tuple([os.path.abspath(path) for path in prefer_under])

    for filenames in report.values():
        for index, fn in enumerate(filenames):
            if name_in_rmfirst(fn, rm_first):
                # 放在列表的最后一项
                filenames.append(filenames.pop(index))
            elif any(True for item in prefer_under if (item in filenames)):
                # 放在列表的第一项
                filenames.insert(0, filenames.pop(index))

    if tofile:
        tofile = os.path.join(dup_report_path, tofile)
        open(tofile, 'w', encoding='utf-8').write(str(report))

    return report

def _print(key, values, tofile):
    print(key, ':', file=tofile)
    for v in values:
        print('\t\t', v, file=tofile)

def _write_to_file(key, values, fh):
    fh.write(str(key) + ' :\n')
    for v in values:
        fh.write('\t\t' + str(v) + '\n')

# 在brief为True的情况下，只有重复的项才会打印出来，如果为False，那么会打印整个报告
def _pretty_print(dup_report, brief=True, tofile=sys.stdout):
    if isinstance(tofile, str):
        f = open(tofile, 'w', encoding=encoding)

    for key, values in dup_report.items():
        if brief:
            if len(values) > 1:
                _print(key, values, tofile)
        else:
            _print(key, values, tofile)

def _pretty_write_to_file(dup_report, fh, brief=True):

    for key, values in dup_report.items():
        if brief:
            if len(values) > 1:
                _write_to_file(key, values, fh)
        else:
            _write_to_file(key, values, fh)

def pretty_print(dup_report, brief=True, tofile=sys.stdout, encoding='utf-8'):
    """
    传入dup_report，用更漂亮格式打印出其内容。
    dup_report可以是一个表示包含dup_report内容的文件名，也可以是dup_report本身。
    brief表示只会打印出包含有重复文件名的键值对。
    tofile 可以是一个文件名或者是sys.stdout
    encoding在tofile是一个文件名的情况下起作用，用来设置文件的编码。

    """
    if isinstance(dup_report, str):
        dup_report = eval(open(dup_report, 'r', encoding='utf-8').read())
    if isinstance(tofile, str):
        fh = open(tofile, 'w', encoding=encoding)
        _pretty_write_to_file(dup_report, fh, brief=brief)
        fh.close()
    else:
        _pretty_print(dup_report, brief=brief, tofile=tofile)

def _rm_dups(dup_report, tofile='after_rm_report', hashfunc=hashf.sha1f):
    """
    传入一个dup_files_report函数返回的字典，由于dups_files_report中的hashfunc可能会产生哈希碰撞，所以通过不同的hashfunc在删除前进行再次核对。然后把相同的项去掉
    """
    for h, files in dup_report.items():
        if len(files) > 1:
            # 由于md5在小概率事件下会发生碰撞，所以使用sha1函数再次验证
            sha1_value = hashfunc(files[0])
            temp = [files[0]]
            for f in files[1:]:
                if not os.path.isfile(f):
                    pass
                elif hashfunc(f) == sha1_value:
                    try:
                        os.remove(f)
                        try:
                            print('removed file:', f)
                        except UnicodeEncodeError:
                            pass
                    except PermissionError:
                        print('failed to remove file:', f, 'due to permission error', file=sys.stderr)
                        temp.append(f)
                    except FileNotFoundError:
                        pass
            dup_report[h] = temp
        elif len(files) == 0:
            dup_report.pop(h)
    if tofile:
        try:
            if (not os.path.isfile(tofile)):
                # 如果文件不存在，那么在dirs中的一个目录中建立该文件。
                tofile = os.path.join(dup_report_path, tofile)
            open(tofile, 'w', encoding='utf-8').write(str(dup_report))
        except:
            raise Exception('Failed to write to', tofile, 'coz can\'t open this file.')

def rm_dups_from_report_file(report_file, real_rm=False, report_file_encoding='utf-8', tofile='dup_report', hashfunc=hashf.sha1f, skip_zero_files=True, skip_dirs=None, prefer_under=None, rm_first=( 'copy', '复制', '副本', '冲突', 'back', '~')):
    """
    通过report_file传入一个包含hash report内容的文件名，在real_rm设置为True的情况下，进行真正的删除。
    """
    report = eval(open(report_file, 'r', encoding=report_file_encoding).read())
    report = handle_report(report, tofile=tofile, skip_dirs=skip_dirs, skip_zero_files=skip_zero_files,  prefer_under=prefer_under, rm_first=rm_first)
    if real_rm:
        _rm_dups(report, hashfunc=hashfunc)
    print("job finished.")

def rm_dups(dirs,real_rm=False, hash_dict=None, tofile='dup_report', hashfuncs=(hashf.md5f, hashf.sha1f), skip_zero_files=True, skip_dirs=None, skip_filenames=None, prefer_under=None, rm_first=( 'copy', '复制', '副本', '冲突', 'back', '~')):
    """
    通过dirs传入需要检验的目录，通过读取目录中我们期望读取的问的内容，如果文件的内容完全相同，那么删除重复的文件。
    dirs可以是一个表示目录的字符串，也可以是多个目录字符串的元祖。
    hash_dict 可以是上一次hash_report传入不同的dirs运行过的结果，从而可以实现两次结果的合并
    tofile参数表示生成的字典内容，存在tofile的文件里。如果设为None，那么不会保存该文件。
    hashfuncs表示用来哈希的函数，该函数传入一个文件名，返回文件类型哈希的hexdigest()值，其中第一个参数用来生成hash report，由于可能遇到小概率的hash碰撞事件，通过第二个参数(不同的hash函数)用来再次校验是否文件内容一致。
    skip_dirs表示在dirs中所有不需要处理的有子目录。可以接受unix的shell相同的匹配规则。
    skip_filenames表示在dirs中所有不需要处理的文件类型。可以接受unix的shell相同的匹配规则。
    perfer_under 如果发生重复文件时，希望在perfer_under文件夹下的文件优先保存。
    rm_first 表示如果文件名中包含有rm_first中出现的字符，那么在重复出现时优先删除。
    """
    report = hash_report(dirs, hash_dict=hash_dict, tofile=tofile, hashfunc=hashfuncs[0], skip_zero_files=skip_zero_files, skip_dirs=skip_dirs, skip_filenames=skip_filenames)
    report = handle_report(report, tofile=tofile, skip_dirs=skip_dirs, skip_zero_files=skip_zero_files,  prefer_under=prefer_under, rm_first=rm_first)
    if real_rm:
        _rm_dups(report, hashfunc=hashfuncs[1])
    print("job finished.")

# hash_report(('/Users/lhq/nutstore', '/Users/lhq/Documents/'), skip_dirs='/Users/lhq/Documents/source')



if __name__ == '__main__':

    import sys
    if len(sys.argv) > 1:
        r = hash_report(sys.argv[1])
        pretty_print(r)
    # 警告：下面的语句真正删除文件，请谨慎。
    # rm_dup_files(r)
    rm_dups('/Users/lhq/nutstore/py/rmdups/testfiles/')
    # pretty_print('dup_raw_report')
