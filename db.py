from sqlite3 import connect
from pathlib import Path
from os import sep
import json

db = str(Path.home()) + sep + 'Zotero\\zotero.sqlite'

id_num = 0

class Item:
    id = 0
    text = None
    comment = None
    tag = None
    rank = None
    childs = list()
    nums = list()

    def __init__(self, t: tuple):
        global id_num
        if len(t) > 0:
            self.id = t[0]
            self.text = t[1]
            self.comment = t[2]
            self.tag = t[3]
            self.rank = t[4]
            self.pageNum = t[5]
            self.position = float(json.loads(t[6])['rects'][0][1])
            self.childs = list()
            self.nums = list()
            self.get_is_numbered()
        else:
            id_num = id_num + 1
            self.id = id_num
            self.text = None
            self.comment = None
            self.tag = None
            self.rank = None
            self.pageNum = None
            self.position = None
            self.childs = list()
            self.nums = list()
            self.get_is_numbered()

    def __str__(self) -> str:
        return 'id: {id}\ntext: {text}\ncomment: {comment}\ntag: {tag}\n'.format(id=str(self.id), text=self.text, comment=self.comment, tag=self.tag)

    def __repr__(self) -> str:
        res = '<gingko-card id="{id}">\n\n'.format(id=self.id)
        if self.tag is None:
            if self.comment is None:
                res += '{text}\n\n'.format(text=self.text)
            else:
                res += '{text}\n{comment}\n\n'.format(text=self.text, comment=self.comment)
        else:
            if self.comment is None:
                res += '{text}\n`#{tag}`\n\n'.format(text=self.text, tag=self.tag)
            else:
                res += '{text}\n{comment}\n`#{tag}`\n\n'.format(text=self.text, comment=self.comment, tag=self.tag)
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

def get_items(parentItemName: str) -> list:
    with connect(db) as conn:
        cur = conn.cursor()
        cur.execute(""" select ID, 
                               text, 
                               comment, 
                               tag, 
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
                                left join itemTags it on it.itemID	= ia.itemID
                                left join tags t on t.tagID = it.tagID
                                where ia.parentItemID = (select itemID
                                                            from itemAttachments
                                                        where lower(path) like lower('%{book_name}%'))
                                and ia.text is not null
                                )
                         order by pageNum asc, position asc;
                    """.format(book_name = parentItemName))

    return [Item(result) for result in cur.fetchall()]
    
