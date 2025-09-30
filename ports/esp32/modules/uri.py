# yapf: disable
_PERCEN_TABLE = {b'%20':b' ',
                b'%21':b'!',
                b'%22':b'"',
                b'%23':b'#',
                b'%24':b'$',
                b'%25':b'%',
                b'%26':b'&',
                b'%27':b"'",
                b'%28':b'(',
                b'%29':b')',
                b'%2A':b'*',
                b'%2B':b'+',
                b'%2C':b',',
                b'%2D':b'-',
                b'%2E':b'.',
                b'%2F':b'/',
                b'%3A':b':',
                b'%3B':b';',
                b'%3C':b'<',
                b'%3D':b'=',
                b'%3E':b'>',
                b'%3F':b'?',
                b'%40':b'@',
                b'%5B':b'[',
                b'%5C':b'\\',
                b'%5D':b']',
                b'%5E':b'^',
                b'%5F':b'_',
                b'%60':b'`',
                b'%7B':b'{',
                b'%7C':b'|',
                b'%7D':b'}',
                b'%7E':b'~'}
# yapf: enable


def URI_percent_decoding(s):
    s = s.replace(b'+', b'')
    for k in _PERCEN_TABLE.keys():
        s = s.replace(k, _PERCEN_TABLE[k])
    return s
