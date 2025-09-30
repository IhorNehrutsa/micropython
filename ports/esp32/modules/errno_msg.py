from errno import errorcode


def errno_errorcode(err: int):
    try:
        return "{}:{}".format(err, errorcode[err])
    except KeyError:
        return "errno.errorcode[{}]-unnown message".format(err)
