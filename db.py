from sqlite3 import connect
from pathlib import Path
from os import sep
import json

db = str(Path.home()) + sep + 'Zotero\\zotero.sqlite'

id_num = 0
g_zot_start = 'zotero://open-pdf/library/items/'
g_link_title = 'zot'

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

    def __str_tabs__(self, n_tabs: int = 0, lvl_limit: int = 0):
        starter = '\t'
        res = starter*n_tabs + self.name.strip('*') + '\n'
        for child in self.childs: 
            res += child.__str_tabs__(n_tabs = n_tabs + 1, lvl_limit = lvl_limit)
        for attach in self.attachs:
            res += attach.__str_tabs__(n_tabs = n_tabs + 1, lvl_limit = lvl_limit)
        return res
    
    def __str_md__(self, n_tabs: int = 0):
        starter = '#'
        res = starter*n_tabs + ' ' + self.name.strip('*') + '\n'
        for child in self.childs: 
            res += child.__str_md__(n_tabs = n_tabs + 1)
        for attach in self.attachs:
            res += attach.__str_md__(n_tabs = n_tabs + 1)
        return res

    def __repr__(self) -> str:
        res = ''.join([x.__repr__() for x in self.attachs if len(x.items) > 0])
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
                                  ia.contentType,
                                  i.key
                             from collectionItems ci
                             join items i on i.itemID = ci.itemID
                             join itemAttachments ia on ia.parentItemID = i.itemID
                        left join itemData idat on idat.itemID = i.itemID and idat.fieldID = 16
                        left join itemDataValues ival on ival.valueID = idat.valueID
                            where collectionID = {id}
                              and ia.path is not null
                              and ival.valueID is null;
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
    key = ''
    items = list()
    tags = list()

    def __init__(self, t: tuple):
        if len(t) > 0:
            self.id = t[0]
            self.name = t[1].rpartition(':')[-1]
            self.type = t[2]
            self.key = t[3]
            self.items = self.get_items()
            self.tags = get_tags(id = self.id)
            self.resort()
            self.relink_items_rank()
            self.reset_attach_key()
        else:
            self.id = None
            self.name = None
            self.type = None
            self.items = list()
            self.tags = list()

    def __str__(self) -> str:
        return 'id: {id}\nname: {name}\ntype: {type}\n'.format(id=str(self.id), name=self.name, type=self.type)
    
    def __str_tabs__(self, n_tabs: int = 0, lvl_limit: int = 0):
        starter = '\t'
        res = starter*n_tabs + self.name.strip('*') + '\n'
        for item in self.items:
            if item.rank < lvl_limit:
                res += item.__str_tabs__(n_tabs = n_tabs + 1, lvl_limit = lvl_limit)
        return res
    
    def __str_md__(self, n_tabs: int = 0):
        starter = '#'
        res = starter*n_tabs + ' ' + self.name.strip('*') + '([{title}]({zot_link}))'.format(title=g_link_title, zot_link=self.get_zotero_link()) +'\n'
        for item in self.items:
            res += item.__str_md__(n_tabs = n_tabs + 1)
        return res

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        res += '{name}\n\n'.format(name=self.name)
        if len(self.tags) > 0: res += '\n'.join(['`' + x + '`' for x in self.tags])
        res += ''.join([x.__repr__() for x in self.items])
        res += '</gingko-card>\n'
        return res
    

    def find_child(self, name: str):
        """
        Find item by name
        """
        res = None
        for item in self.items:
            if item.text.strip().lower().find(name.strip().lower()) > -1:
                return item
            else:
                res = item.find_child(name=name)
                if res is not None:
                    return res
        return res



    def find_child(self, name: str):
        """
        Find item by name
        """
        res = None
        for item in self.items:
            if item.text.strip().lower().find(name.strip().lower()) > -1:
                return item
            else:
                res = item.find_child(name=name)
                if res is not None:
                    return res
        return res

    def find_child_by_key(self, item_key: str):
        """
        Find item by item key
        """
        res = None
        for item in self.items:
            if item.key.strip().lower().find(item_key.strip().lower()) > -1:
                return item
            else:
                res = item.find_child_by_key(item_key=item_key)
                if res is not None:
                    return res
        return res


    def get_items(self):
        with connect(db) as conn:
            cur = conn.cursor()
            cur.execute("""select ID, 
                                  text, 
                                  comment, 
                                  rank, 
                                  pageNum,
                                  position,
                                  key,
                                  type
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
                                         position,
                                         i.key,
                                         ian.type
                                    from itemAttachments ia
                                    join itemAnnotations ian on ian.parentItemID = ia.itemID
                                    join items i on i.itemID = ian.itemID
                                    where ia.itemID = {id})
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
    
    def get_zotero_link(self):
        global g_zot_start
        return g_zot_start + self.key

    def relink_items_rank(self):
        d = dict()
        l_del_items = list()
        for item in self.items: self.add_to_higher(d = d, item = item, l_del_items = l_del_items)
        self.items = [x for x in self.items if x not in l_del_items]

    def reset_attach_key(self):
        for item in self.items:
            item.attach_key = self.key
            item.reset_attach_key()

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
    
    attach_key = ''
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
            self.key = t[6]
            self.type = t[7]
            self.childs = list()
            self.tags = get_tags(id = self.id)
            self.get_is_numbered()
            self.get_extra()

        else:
            id_num = id_num + 1
            self.id = id_num
            self.text = None
            self.comment = None
            self.rank = None
            self.pageNum = None
            self.position = None
            self.key = None
            self.type = None
            self.childs = list()
            self.tags = list()
            self.get_is_numbered()

    def __str__(self) -> str:
        return 'id: {id}\ntext: {text}\ncomment: {comment}\ntags: {tags}\n'.format(id=str(self.id), text=self.text, comment=self.comment, tags='\n'.join(self.tags))


    def __str_tabs__(self, n_tabs: int = 0, lvl_limit: int = 0):
        starter = '\t'
        # pictures
        if self.type != 3:
            if len(self.childs) > 0:
                res = starter * n_tabs + (self.text.strip('*') + ' ' + ' '.join(['#' + tag for tag in self.tags])).strip() + '\n'
            else:
                res = (self.text.strip('*') + ' ' + ' '.join(['#' + tag for tag in self.tags])).strip() + '\n'
        else:
            res = '> [!todo] #make_pict' + '([{title}]({zot_link}))'.format(title=g_link_title, zot_link=self.get_zotero_link()) +'\n'
        if self.comment:
            res += starter * (n_tabs + 1) + self.comment.strip() + '\n'
        if self.type == 3:
            res += '\n> [!todo] #pict\n'
        for child in self.childs:
            if child.rank < lvl_limit:
                res += child.__str_tabs__(n_tabs = n_tabs + 1, lvl_limit = lvl_limit)
        return res

    def __str_md__(self, n_tabs: int = 0):
        starter = '#'
        # pictures
        if self.type != 3:
            if len(self.childs) > 0:
                res = starter * n_tabs + ' ' + (self.text.strip('*') + ' ' + ' '.join(['#' + tag for tag in self.tags])).strip() + '([{title}]({zot_link}))'.format(title=g_link_title, zot_link=self.get_zotero_link()) +'\n'
            else:
                res = (self.text.strip('*') + ' ' + ' '.join(['#' + tag for tag in self.tags])).strip() + '([{title}]({zot_link}))'.format(title=g_link_title, zot_link=self.get_zotero_link()) +'\n'            
        else:
            res = '> [!todo] #make_pict' + '([{title}]({zot_link}))'.format(title=g_link_title, zot_link=self.get_zotero_link()) +'\n'
        if self.comment:
            res += self.comment.strip() + '\n'
        for child in self.childs:
            res += child.__str_md__(n_tabs = n_tabs + 1)
        return res

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        res += '{text}\n'.format(text=self.text)
        if self.comment: res += '{comment}\n'.format(comment=self.comment)
        res += '\n'
        if len(self.tags) > 0: res += '\n'.join(['`' + x + '`' for x in self.tags])
        res += ''.join([x.__repr__() for x in self.childs])
        res += '</gingko-card>\n'
        return res
    
    def find_child(self, name: str):
        """
        Find item by name
        """
        res = None
        for child in self.childs:
            if child.text.strip().lower().find(name.strip().lower()) > -1:
                return child
            else:
                res = child.find_child(name=name)
                if res is not None:
                    return res
        return res
    
    def find_child_by_key(self, item_key: str):
        """
        Find item by key
        """
        res = None
        for child in self.childs:
            if child.key.strip().lower().find(item_key.strip().lower()) > -1:
                return child
            else:
                res = child.find_child_by_key(item_key=item_key)
                if res is not None:
                    return res
        return res

    def get_is_numbered(self) -> None:
        if self.text:
            s = self.text.split('.')[0]
            try:
                x = int(s)
                self.text = '**{text}**'.format(text=self.text)
            except:
                None
    
    def get_zotero_link(self):
        global g_zot_start
        return '{zot_start}/{attach_key}?page={page_num}&annotation={item_key}'.format(zot_start=g_zot_start, 
                                                                                       attach_key=self.attach_key, 
                                                                                       page_num = self.pageNum,
                                                                                       item_key=self.key)

    def reset_attach_key(self):
        for child in self.childs:
            child.attach_key = self.attach_key
            child.reset_attach_key()

    def set_mnemo(self, d: dict):
        if d.get(self.id): self.name = d.get(self.id)
        for child in self.childs: child.set_mnemo(d)

    def get_extra(self) -> int:
        with connect(db) as conn:
            cur = conn.cursor()
            cur.execute("""select ia.itemID,
                                  ia.path,
                                  ia.contentType,
                                  i.key
                             from itemDataValues ival
                             join itemData idat on idat.valueID = ival.valueID and idat.fieldID = 16
                             left join itemAttachments ia on ia.parentItemID = idat.itemID
                             left join items i on i.itemID = ia.itemID
                           where  ival.value = '{id}'
                        """.format(id = self.id))
        for att in [Attach(result) for result in cur.fetchall()]: self.childs.extend(att.items)


class Object:

    def __init__(self, t: tuple):

        if len(t) > 0:
            self.key = t[0]
            self.type = t[1]
            self.name = t[2]
        else:
            self.key = None
            self.type = None
            self.name = None



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


def get_attach(attach_name: str) -> Attach:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""select ia.itemID,
                              ia.path,
                              ia.contentType,
                              (select i.key
                                from itemAttachments ia
                                join items i on i.itemID = ia.itemID
                            where lower(ia.path) like lower('%{name}%')
                            limit 1)
                        from collectionItems ci
                        join items i on i.itemID = ci.itemID
                        join itemAttachments ia on ia.parentItemID = i.itemID
                left join itemData idat on idat.itemID = i.itemID and idat.fieldID = 16
                left join itemDataValues ival on ival.valueID = idat.valueID
                    where lower(path) like lower('%{name}%')
                        and ia.path is not null
                        and ival.valueID is null
                    limit 1;
                    """.format(name = attach_name))
    return Attach(cur.fetchone())

def get_attach_by_key(attach_key: str) -> Attach:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""select ia.itemID,
                              ia.path,
                              ia.contentType,
                              i.key
                         from itemAttachments ia
                         join items i on i.itemID = ia.itemID
                        where i.key = '{item_key}'
                    """.format(item_key=attach_key))
    return Attach(cur.fetchone())


def get_items(parentItemName: str) -> list:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute(""" select ID, 
                               text, 
                               comment, 
                               rank, 
                               pageNum,
                               position,
                               key,
                               type
                            from
                                (
                                    select ia.itemID as ID,
                                    ia.text,
                                    ia.comment,
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
                                    position,
                                    i.key,
                                    ia.type
                                from itemAnnotations ia
                                left join items i on i.itemID = ia.itemID
                                where ia.parentItemID = (select itemID
                                                            from itemAttachments
                                                        where lower(path) like lower('%{book_name}%'))
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
     
def get_childs_item(id: int) -> list:
     with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""with t_tab as (select ia.itemID as ID,
										 ia.text,
										 ia.comment,
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
											position,
											row_number() over(order by cast(ia.pageLabel as decimal)) rn,
                                            ia.type    
									from itemAnnotations ia
									where ia.itemID >= {id}),
                                t_cur as (select *
                                            from t_tab
                                           where id = {id}),
                                t_next as (select id, text, comment, rank, pageNum, position, rn
                                            from (select row_number() over(order by t.pageNum, t.rank) as rownum,
                                                        t.*
                                                    from t_tab t
                                                    join t_cur c on c.rank = t.rank and t.pageNum >= c.pageNum and t.ID != c.ID)
                                                    where rownum = 1),
                                t_dif as (select id, text, comment, rank, pageNum, position
                                            from t_tab t
                                           where rn > (select rn from t_cur)
                                             and rn < (select rn from t_next))
                        select *
                        from t_dif;
                    """.format(id=id))
        return [Item(result) for result in cur.fetchall()]

def get_col_key(col_name: str) -> list:
     with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""
                    select i.key
                        from collectionItems ci
                        join items i on i.itemID = ci.itemID
                        join collections c on c.collectionID = ci.collectionID
                        where lower(collectionName) like lower('%' || '{col_name}' || '%')
            """.format(col_name=col_name))
        return [t[0] for t in cur.fetchall()]
     

def get_attach_key(attach_name: str) -> list:
     with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""
                    select i.key
                    from itemAttachments ia
                    join items i on i.itemID = ia.itemID
                where lower(ia.path) like lower('%{attach_name}%') 
            """.format(attach_name=attach_name))
        return [t[0] for t in cur.fetchall()]

def get_item_key(attach_key: str, item_name: str) -> list:
     with connect(db) as conn:
        cur = conn.cursor()
        cur.execute("""
                    select i.key
                    from itemAttachments ia
                    join itemAnnotations ian on ian.parentItemID = ia.itemID
                    join items i on i.itemID = ian.itemID
                    join items i2 on i2.itemID = ia.itemID and i2.key = '{attach_key}'
                    where lower(ian.text) like lower('%' || '{item_name}' || '%'); 
            """.format(attach_key=attach_key, item_name=item_name))
        return [t[0] for t in cur.fetchall()]


# def get_obj_by_key(key: str) -> list:
#         with connect(db) as conn:
#             cur = conn.cursor()
#             cur.execute("""
#                         select i.key
#                         from itemAttachments ia
#                         join itemAnnotations ian on ian.parentItemID = ia.itemID
#                         join items i on i.itemID = ian.itemID
#                         join items i2 on i2.itemID = ia.itemID and i2.key = '{attach_key}'
#                         where lower(ian.text) like lower('%' || '{item_name}' || '%'); 
#                 """.format(attach_key=attach_key, item_name=item_name))
        
#         return [Object(result) for result in cur.fetchall()]


