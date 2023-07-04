from sqlite3 import connect
from pathlib import Path
from os import sep
import json
import re

db = str(Path.home()) + sep + 'Zotero\\zotero.sqlite'

id_num = 0

# TODO: move connection object to zg

class Collection:

    attachs = list()

    def __init__(self, t: tuple):
        if len(t) > 0:
            self.id = t[0]
            self.name = t[1]
            self.parentId = t[2]
            self.attachs = self.get_attachs()
            self.childs = list() # self.get_childs()
        else:
            self.id = None
            self.name = None
            self.parentId = None
            self.attachs = list()
            self.childs = list()

    def __str__(self) -> str:
        return 'id: {id}\nname: {name}\nparentId: {parentId}\n'.format(id=str(self.id), name=self.name, parentId=self.parentId)

    def __repr__(self) -> str:
        # res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        # res += '{name}\n\n'.format(name=self.name)
        # res = ''.join([x.__repr__() for x in self.childs])
        res = ''.join([x.__repr__() for x in self.attachs if len(x.items) > 0])
        # res += '</gingko-card>\n'
        return res

    def exists_annotation(self) -> bool:
        for attach in self.attachs:
            if len(attach.items) > 0: return True
        return False
    
    def get_childs(self):
        with connect(db) as conn:
            cur = conn.cursor()
            cur.execute("""select collectionID,
                                  collectionName,
                                  parentCollectionID
                             from collections
                            where parentCollectionID = {id}
                            order by collectionID;""".format(id = self.id))
        return [Collection(result) for result in cur.fetchall()]
    
    def get_attachs(self):
        with connect(db) as conn:
            cur = conn.cursor()
            cur.execute("""select ia.itemID,
                                  ia.path,
                                  ia.contentType
                             from collectionItems ci
                             join items i on i.itemID = ci.itemID
                             join itemAttachments ia on ia.parentItemID = i.itemID
                            where collectionID = {id}
                              and ia.path is not null;
                        """.format(id = self.id))
        return [Attach(result) for result in cur.fetchall()]

    def set_bold(self):
        for attach in self.attachs:
            for item in attach.items:
                if item.rank in [1, 2]:
                    item.name = '*' + item.name.strip('*') + '*'

    def set_mnemo(self, d: dict):
        if d.get(self.id): self.name = d.get(self.id)
        for attach in self.attachs: attach.set_mnemo(d)


class Attach:

    name = ''
    items = list()
    tags = list()

    def __init__(self, t: tuple):
        if len(t) > 0:
            self.id = t[0]
            self.name = t[1].rpartition(':')[-1]
            self.type = t[2]
            self.items = self.get_items()
            self.tags = get_tags(id = self.id)
            self.resort()
            self.relink_items_rank()
        else:
            self.id = None
            self.name = None
            self.type = None
            self.items = list()
            self.tags = list()

    def __str__(self) -> str:
        return 'id: {id}\nname: {name}\ntype: {type}\n'.format(id=str(self.id), name=self.name, type=self.type)

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        res += '{name}\n\n'.format(name=self.name)
        if len(self.tags) > 0: res += '\n'.join(['`' + x + '`' for x in self.tags])
        # res += '\nID: {id}\n\n'.format(id=self.id)
        res += ''.join([x.__repr__() for x in self.items])
        res += '</gingko-card>\n'
        return res

    def get_items(self):
        with connect(db) as conn:
            cur = conn.cursor()
            cur.execute("""select ID, 
                                  text, 
                                  comment, 
                                  rank, 
                                  pageNum,
                                  position
                            from (select ian.itemID as ID,
                                         ian.text,
                                         ian.comment,
                                         case ian.color
                                           when '#ffd400' then 1
                                           when '#ff6666' then 2
                                           when '#5fb236' then 3
                                           when '#2ea8e5' then 4
                                           when '#a28ae5' then 5
                                           when '#e56eee' then 6
                                           when '#f19837' then 7
                                           when '#aaaaaa' then 8
                                         end as rank,
                                         cast(ian.pageLabel as decimal) as pageNum,
                                         position
                                    from itemAttachments ia
                                    join itemAnnotations ian on ian.parentItemID = ia.itemID
                                    where ia.itemID = {id}
                                      and ian.text is not null)
                        order by pageNum asc, position asc;
                        """.format(id = self.id))
        return [Item(result) for result in cur.fetchall()]
    
    def add_to_higher(self, d: dict, item, l_del_items) -> dict:
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

    def relink_items_rank(self):
        d = dict()
        l_del_items = list()
        for item in self.items: self.add_to_higher(d = d, item = item, l_del_items = l_del_items)
        self.items = [x for x in self.items if x not in l_del_items]

    def resort(self):
        l_res = list()
        for pn in sorted(list(set([x.pageNum for x in self.items]))):
            l_subitems = sorted([x for x in self.items if x.pageNum == pn],  key=lambda item: float(item.position), reverse=True)
            l_res.extend(l_subitems)
        self.items = l_res

    def set_mnemo(self, d: dict):
        if d.get(self.id): self.name = d.get(self.id)
        for item in self.items: item.set_mnemo(d)

class Gingko:

    def __init__(self, id: str, block: str):
        self.id = id
        self.block = block
        self.childs = list()
        self.tags = list()
        
    def __str__(self):
        return 'id: {id}\n\n{block}\n'.format(id=self.id, block=self.block)

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">'.format(id=self.id)
        # TODO: wrap each line in ``
        res += '\n\n{block}\n\n'.format(block=self.block)
        for tag in self.tags: res += '`#{tag}`\n'.format(tag=tag)
        res += ''.join([x.__repr__() for x in self.childs])
        res += '</gingko-card>\n'
        return res

    def get_mnemo(self, d: dict) -> dict:
        d[self.id] = self.block.split('\n')[0].strip().strip('*')
        for child in self.childs: d = child.get_mnemo(d)
        return d

class Item:
    
    name = ''

    def __init__(self, t: tuple):
        global id_num
        if len(t) > 0:
            self.id = t[0]
            self.text = t[1]
            self.comment = t[2]
            self.rank = t[3]
            self.pageNum = t[4]
            self.position = float(json.loads(t[5])['rects'][0][1])
            self.childs = list()
            self.tags = get_tags(id = self.id)
            self.get_is_numbered()
        else:
            id_num = id_num + 1
            self.id = id_num
            self.text = None
            self.comment = None
            self.rank = None
            self.pageNum = None
            self.position = None
            self.childs = list()
            self.tags = list()
            self.get_is_numbered()

    def __str__(self) -> str:
        return 'id: {id}\ntext: {text}\ncomment: {comment}\ntags: {tags}\n'.format(id=str(self.id), text=self.text, comment=self.comment, tags='\n'.join(self.tags))

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        res += '{text}\n'.format(text=self.text)
        if self.comment: res += '{comment}\n'.format(comment=self.comment)
        res += '\n'
        if len(self.tags) > 0: res += '\n'.join(['`' + x + '`' for x in self.tags])
        # res += '\nID: {id}\n\n'.format(id=self.id)
        res += ''.join([x.__repr__() for x in self.childs])
        res += '</gingko-card>\n'
        return res

    def get_is_numbered(self) -> None:
        if self.text:
            s = self.text.split('.')[0]
            try:
                x = int(s)
                self.text = '**{text}**'.format(text=self.text)
            except:
                None

    def set_mnemo(self, d: dict):
        if d.get(self.id): self.name = d.get(self.id)
        for child in self.childs: child.set_mnemo(d)

def get_collections(collectionName: str = None) -> list:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""select collectionID,
                              collectionName,
                              parentCollectionID
                         from collections
                        where parentCollectionID is null
                          and lower(collectionName) like lower('%{col_name}%')
                        order by collectionID;
                    """.format(col_name = collectionName if collectionName else ''))
    return [Collection(result) for result in cur.fetchall()]

def get_items(parentItemName: str) -> list:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute(""" select ID, 
                               text, 
                               comment, 
                               rank, 
                               pageNum,
                               position
                            from
                                (
                                    select ia.itemID as ID,
                                    ia.text,
                                    ia.comment,
                                    t.name as tag,
                                    case color
                                        when '#ffd400' then 1
                                            when '#ff6666' then 2
                                            when '#5fb236' then 3
                                            when '#2ea8e5' then 4
                                            when '#a28ae5' then 5
                                            when '#e56eee' then 6
                                            when '#f19837' then 7
                                            when '#aaaaaa' then 8
                                        end as rank,
                                    cast(ia.pageLabel as decimal) as pageNum,
                                    position
                                from itemAnnotations ia
                                left join items i on i.itemID = ia.itemID
                                where ia.parentItemID = (select itemID
                                                            from itemAttachments
                                                        where lower(path) like lower('%{book_name}%'))
                                and ia.text is not null
                                )
                         order by pageNum asc, position asc;
                    """.format(book_name = parentItemName))
    return [Item(result) for result in cur.fetchall()]
    
def get_tags(id: int) -> list:
     with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""select t.name
                        from itemTags it
                            join tags t on t.tagID = it.tagID
                        where it.itemID = {id}
                        order by t.name;
                    """.format(id=id))
        return [x[0] for x in cur.fetchall()]