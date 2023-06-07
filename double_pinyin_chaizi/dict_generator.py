from pypinyin import Style, pinyin

def initial_map(x):
    m = {'zh': 'v', 'sh': 'u', 'ch': 'i'}
    if x not in m:
        return x
    return m[x]

def final_map(x):
    m = {
        'iu': 'q',
        'ia': 'w',
        'ua': 'w',
        'uan': 'r',
        'ue': 't',
        've': 't',
        'ing': 'y',
        'uai': 'y',
        'uo': 'o',
        'un': 'p',
        'iong': 's',
        'ong': 's',
        'iang': 'd',
        'uang': 'd',
        'en': 'f',
        'eng': 'g',
        'ang': 'h',
        'an': 'j',
        'ao': 'k',
        'ai': 'l',
        'ei': 'z',
        'ie': 'x',
        'iao': 'c',
        'ui': 'v',
        'ou': 'b',
        'in': 'n',
        'ian': 'm'
    }
    banned = ['n', 'm', 'ng']
    if x in banned:
        return ''
    if x not in m:
        return x
    return m[x]

def to_double_pinyin(py):
    init_two = ['zh', 'ch', 'sh']
    no_init = ['a', 'e', 'o']
    banned = ['n', 'm', 'ng']
    if py == '' or py in banned:
        return ''
    init = py[0]
    final = py[1:]
    if init in no_init:
        init = ''
        final = py
    if len(py) > 1 and py[0:2] in init_two:
        init = py[0:2]
        final = py[2:]
    inita = initial_map(init)
    finala = final_map(final)
    if inita == '':
        if finala == '' or len(finala) > 2:
            return []
        if len(finala) == 2:
            return [finala]
        ret = [final[0] + finala]
        if len(final) == 2:
            ret.append(final)
        return ret
    return [inita + finala]
    
def double_pinyin(s):
    pys = pinyin(s, style=Style.NORMAL, strict=False, heteronym=True)
    pys = [[to_double_pinyin(x) for x in y] for y in pys]
    return list(map(lambda nested: sum(nested, []), pys))

def char_map(c):
    special = {
        "一": ["yi", "hg"],
        "丨": ["uu"],
        "丿": ["px"],
        "丶": ["dm", "na"],
        "㇆": ["ve"],
        "乀": ["dm", "na"],
        "冂": ["kd"]
    }
    if c == '':
        return []
    pys = double_pinyin(c)[0]
    pys = list(filter(lambda py: py.isascii(), pys))
    if c in special:
        pys = special[c]
    return pys

def main():
    from itertools import chain
    import wget
    wget.download("https://raw.githubusercontent.com/kfcd/chaizi/master/chaizi-jt.txt")
    wget.download("https://raw.githubusercontent.com/kfcd/chaizi/master/chaizi-ft.txt")
    jtlines = open("chaizi-jt.txt", encoding='utf-8').readlines()
    ftlines = open("chaizi-ft.txt", encoding='utf-8').readlines()
    l = list(chain(jtlines, ftlines))
    l = list(dict.fromkeys(l))
    dst = open("chaizi.txt", 'w', encoding='utf-8')
    for line in l:
        dst.write(line)
    dst.close()

    import time
    from itertools import product
    lines = open("chaizi.txt", encoding='utf-8').readlines()
    dst = open("double_pinyin_chaizi.dict.yaml", 'w', encoding='utf-8', newline='\n')
    head = f'''# Rime dictionary
# encoding: utf-8
# 拆字词库

---
name: double_pinyin_chaizi
version: "{time.strftime("%Y.%m.%d", time.localtime())}"
sort: by_weight
use_preset_vocabulary: false
...

'''
    dst.write(head)
    for line in lines:
        items = line.strip().split('\t')
        char = items[0]
        items = items[1:]
        codes = []
        for item in items:
            chars = item.split(' ')
            pinyins = list(map(char_map, chars))
            pinyins = list(map(lambda t: ''.join(list(t)), product(*pinyins)))
            codes.extend(pinyins)
        codes = list(dict.fromkeys(codes))
        for code in codes:
            line_out = f"{char}\t{code}\t1\n"
            dst.write(line_out)

    dst.close()


if __name__ == '__main__':
    main()
