import hashlib


def _hash_func(funcname, filename, readsize=10*1024):
    """
    读取文件的内容，返回其hash的hexdigest值
    funcname 是一个hashlib的一个hash函数名，比如hashlib.md5
    filename 是一个文件名。
    readsize 表示每次读取多少个字节。
    """
    h = getattr(hashlib, funcname, hashlib.md5)()

    handler = open(filename,'rb')
    while True:
        c = handler.read(readsize)
        if c:
            h.update(c)
        else:
            break
    handler.close()

    return h.hexdigest()

def md5f(filename):
    return _hash_func('md5', filename)

def sha1f(filename):
    return _hash_func('sha1',filename)

def sha224f(filename):
    return _hash_func('sha224', filename)

def sha256f(filename):
    return _hash_func('sha256', filename)

def sha384f(filename):
    return _hash_func('sha384', filename)

def sha512f(filename):
    return _hash_func('sha512', filename)


if __name__ == '__main__':

    # filename = '/Users/lhq/test/IMG_0024.MOV'
    filename = __file__


    #仅仅用于测试
    def hashf(filename):
        h = hashlib.sha1()
        h.update(open(filename,'rb').read())
        return h.hexdigest()
    print(md5f(filename))
    print(sha1f(filename) == hashf(filename))
    print(sha1f(filename))
    print(sha224f(filename))
    print(sha256f(filename))
    print(sha384f(filename))
    print(sha512f(filename))


