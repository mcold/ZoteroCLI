# coding: utf-8
from db import Gingko, Item, get_items, get_collections, get_attach, get_attach_by_key, get_col_key, get_attach_key as get_at_key, get_item_key as get_it_key, get_obj, unlock_ext_items
from pathlib import Path
import xml.etree.ElementTree as ET
import typer
import re
import os

file_path = str(Path.home()) + os.sep + 'WD\\Gingko\\Mnemo'
mnemo_postfix = '_MN'

xmind_limit_rank = 8

app = typer.Typer()

def add_to_higher(d: dict, item: Item, l_del_items: list) -> dict:
    for r in range(item.rank-1, 0, -1):
        item_parent = d.get(r)
        if item_parent: 
            item_parent.childs.append(item)
            for x in range(item.rank, 9): d.pop(x, None)
            d[item.rank] = item
            l_del_items.append(item)
            return d
    for r in range(item.rank, 9): d.pop(r, None)
    d[item.rank] = item
    return d

def relink_items_rank(items: list) -> list:
    d = dict()
    l_del_items = list()
    for item in items: add_to_higher(d = d, item = item, l_del_items = l_del_items)
    return [x for x in items if x not in l_del_items]

def resort(l_items: list) -> list:
    l_res = list()
    for pn in sorted(list(set([x.pageNum for x in l_items]))):
        l_subitems = sorted([x for x in l_items if x.pageNum == pn],  key=lambda item: float(item.position), reverse=True)
        l_res.extend(l_subitems)
    return l_res

def get_nums(textItem: str) -> list:
    return re.findall('\d+', re.split('\s\w*', textItem)[0])

def get_tree(parentItemName: str, to_use_parent: bool = False) -> None:
    l_items = get_items(parentItemName=parentItemName)
    l_items = resort(l_items = l_items)
    l_items = relink_items_rank(items=l_items)

    if to_use_parent:
        parent = Item(tuple())
        parent.text = '**{text}**'.format(text=parentItemName)
        parent.childs = l_items
        return [parent]
    else:
        return l_items

def get_gingko_tree(file: str) -> Gingko:
    parser = ET.XMLParser(encoding='utf-8')
    tree = ET.parse(file, parser=parser)
    root = tree.getroot()
    g = Gingko(root.attrib['id'], root.text.strip())
    g.childs = [get_gingko_child(gingko_xml = gi) for gi in root]
    g.id = g.id.rpartition('-')[-1] # only for root
    return g

def get_gingko_child(gingko_xml: ET.Element) -> Gingko:
    g = Gingko(gingko_xml.attrib['id'], gingko_xml.text.strip())
    g.childs = [get_gingko_child(gingko_xml = gci) for gci in gingko_xml]
    return g

######################

# TODO: check - if doesn't work -> delete
@app.command(help='Generate markdown by attachment name')
def gen_md_attach(attach_name: str) -> None:
    with open(file=file_path + os.sep + attach_name + '.md', mode='w', encoding='utf-8') as f: 
        f.write(''.join([x.__repr__() for x in get_tree(parentItemName=attach_name)]))

# TODO: check - if doesn't work -> delete
@app.command(help='Generate markdown by attachment names from file')
def gen_md_attach_file(file_name: str) -> None:
    res = ''
    res_file = file_name.rpartition('.')[0].rpartition(os.sep)[-1]
    with open(file=file_path + os.sep + res_file + '.md', mode='w', encoding='utf-8') as f: 
        with open(file=file_name, mode='r', encoding='utf-8') as f_from:
            for attach in f_from.readlines(): res += ''.join([x.__repr__() for x in get_tree(parentItemName=attach.strip(),to_use_parent=True)]) + '\n'
            f.write(res.strip())

@app.command(help='Collections')
def get_cols() -> None:
    l_col = get_collections()
    for col in l_col:
        print(col.__repr__())

@app.command(help='Generate collection by name')
def gen_col(col_name: str) -> None:
    with open(file=file_path + os.sep + col_name + '.md', mode='w', encoding='utf-8') as f: 
        f.write(get_collections(collectionName=col_name)[0].__repr__())

@app.command(help='Generate all collections')
def gen_cols() -> None:
    for col in get_collections():
        if col.exists_annotation():
            col.set_bold()
            with open(file=file_path + os.sep + col.name + '.md', mode='w', encoding='utf-8') as f: 
                f.write(col.__repr__())

@app.command(help='Generate mnemo version of collection')
def gen_mnemo(col_name: str) -> None:
    col = get_collections(collectionName=col_name)[0]
    d = dict()
    f_name = file_path + os.sep + col.name + mnemo_postfix + '.md'
    if os.path.exists(f_name):
        g = get_gingko_tree(f_name)
        d = g.get_mnemo(d)
        col.set_mnemo(d)
    col.name = col.name + mnemo_postfix
    with open(file=file_path + os.sep + col.name + '.md', mode='w', encoding='utf-8') as f: 
        f.write(col.__repr__())

@app.command(help='Generate collection in tabs tree for xmind')
def gen_col_xmind(col_name: str, lvl_limit: int = xmind_limit_rank) -> None:
    col = get_collections(collectionName=col_name)[0]
    with open(col_name + '.txt', 'w', encoding='utf-8') as f:
        f.write(col.__str_tabs__(lvl_limit = lvl_limit))

@app.command(help='Generate attach in tabs tree for xmind')
def gen_attach_xmind(attach_name: str, lvl_limit: int = xmind_limit_rank) -> None:
    attach = get_attach(attach_name=attach_name)
    with open(attach_name + '.txt', 'w', encoding='utf-8') as f:
        f.write(attach.__str_tabs__(lvl_limit = lvl_limit))

@app.command(help='Generate topic in tabs tree for xmind')
def gen_topic_xmind(attach_name: str, topic_name: str, lvl_limit: int = xmind_limit_rank) -> None:
    attach = get_attach(attach_name=attach_name)
    topic = attach.find_child(name = topic_name)
    if topic:
        with open(topic_name + '.txt', 'w', encoding='utf-8') as f:
            f.write(topic.__str_tabs__(lvl_limit = lvl_limit))

@app.command(help='Generate collection in markdown')
def gen_col_md(col_name: str) -> None:
    col = get_collections(collectionName=col_name)[0]
    with open(col_name + '.txt', 'w', encoding='utf-8') as f:
        f.write(col.__str_md__())

@app.command(help='Generate attach in markdown')
def gen_attach_md(attach_name: str) -> None:
    attach = get_attach(attach_name=attach_name)
    with open(attach_name + '.txt', 'w', encoding='utf-8') as f:
        f.write(attach.__str_md__())

@app.command(help='Generate item in markdown')
def gen_item_md(attach_key: str, item_key: str) -> None:
    attach = get_attach_by_key(attach_key=attach_key)
    topic = attach.find_child_by_key(item_key=item_key)
    if topic:
        with open(topic.text + '.md', 'w', encoding='utf-8') as f:
            f.write(topic.__str_md__())

@app.command(help='Get collection key')
def get_col_key(col_name: str) -> None:
    for col_key in get_col_key(col_name=col_name):
        print(col_key)

@app.command(help='Get attachment key')
def get_attach_key(attach_name: str) -> None:
    for attach_key in get_at_key(attach_name=attach_name):
        print(attach_key)

@app.command(help='Get item key')
def get_item_key(attach_key: str, item_name: str) -> None:
    for item_key in get_it_key(attach_key=attach_key, item_name=item_name):
        print(item_key)

@app.command(help='Get object tree')
def get_obj_tree(key: str, rank: int) -> None:
    obj = get_obj(key=key)
    for child in obj.childs:
        if child.rank <= rank:
            print(child.__str__(rank=rank))

@app.command(help='Get object tree')
def get_obj_tree_tag(key: str, rank: int, tag: str) -> None:
    obj = get_obj(key=key)
    for child in obj.childs:
        if child.rank <= rank:
            if tag is not None:
                if tag in child.tags:
                    print(child.__str__(rank=rank))
            else:
                print(child.__str__(rank=rank))

@app.command(help='Unlock imported items')
def unlock_items() -> None:
    unlock_ext_items()


if __name__ == "__main__":
    app()