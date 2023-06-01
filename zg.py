# coding: utf-8
from db import Item, get_items
from pathlib import Path
import typer
import re
import os

file_path = str(Path.home()) + os.sep + 'WD\\Gingko\\Mnemo'

app = typer.Typer()

def relink_items(items: list) -> list:
    l_del_items = list()
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            if '.'.join(items[j].nums).startswith('.'.join(items[i].nums)) and len(items[j].nums) - 1 == len(items[i].nums): 
                items[i].childs.append(items[j])
                l_del_items.append(items[j])
    return [x for x in items if x not in l_del_items]

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

@app.command(help='Generate markdown by attachment name')
def gen_md_attach(attach_name: str) -> None:
    with open(file=file_path + os.sep + attach_name + '.md', mode='w', encoding='utf-8') as f: 
        f.write(''.join([x.__repr__() for x in get_tree(parentItemName=attach_name)]))

@app.command(help='Generate markdown by attachment names from file')
def gen_md_attach_file(file_name: str) -> None:
    res = ''
    res_file = file_name.rpartition('.')[0].rpartition(os.sep)[-1]
    with open(file=file_path + os.sep + res_file + '.md', mode='w', encoding='utf-8') as f: 
        with open(file=file_name, mode='r', encoding='utf-8') as f_from:
            for attach in f_from.readlines(): res += ''.join([x.__repr__() for x in get_tree(parentItemName=attach.strip(),to_use_parent=True)]) + '\n'
            f.write(res.strip())

if __name__ == "__main__":
    app()