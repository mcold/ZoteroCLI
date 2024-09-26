# coding: utf-8

from db import get_items
import os

"""
Obsidian module
"""



dir_obs = 'C:\\Users\\mholo\\WD\\Obsidian\\ENGLISH\\Inbox'

d_type = {
            1: 'noun',
            2: 'verb',
            3: 'adjective',
            4: 'phrase',
            5: 'verb+'
         }

d_prop = {
    'tags': None,
    'sr-due': None,
    'sr-interval': None,
    'sr-ease': None

}

def gen_obs(book_name: str) -> None:
    l_items = get_items(parentItemName=book_name)
    
    for item in l_items:
        f_item = dir_obs + os.sep + item.text + '.md'
        if os.path.exists(f_item):
            # with open(f_item, 'r') as fr:
            #     f_text = fr.read()
            #     f_text = f_text + '\n' + item.comment
            with open(f_item, '+a') as fa:
                fa.write(item.comment)
        else:
            with open(f_item, 'w') as fw:
                """
                ---
                aliases: 
                tags: voc/adjective 
                transcription:
                url: 
                sr-due: 2024-05-15
                sr-interval: 32
                sr-ease: 190
                ---
                """
                fw.write(item.comment)