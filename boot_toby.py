#!/usr/bin/python

import reformed as r #import Table, Textbox, Boolean, OneToMany
import dataloader 

# forms

r.Table("form", r.TextBox("name"),
                   r.OneToMany("form_param","form_param"), r.OneToMany("form_item","form_item")).paramset()

r.Table("form_param", r.TextBox("key"), r.TextBox("value")).paramset()

r.Table("form_item" ,r.TextBox("name") ,
                   r.TextBox("label"),r.TextBox("item"),r.Boolean('active'),r.Integer('sort_order'),
                                   r.OneToMany("form_item_param","form_item_param")).paramset()


r.Table("form_item_param", r.TextBox("key"),r.TextBox("value")).paramset()

# User

r.Table("user", r.TextBox("username"),r.TextBox("password"),r.Boolean('active'), r.OneToMany("user_group","user_group")).paramset()

r.Table("user_group", r.TextBox("name"),r.TextBox("description")).paramset()


r.data=r.Database()
r.data.create_tables()


# dataloader

# Form

dataloader.put('form', name='form', id=1)
dataloader.put('form', name='form_item', id=2)
dataloader.put('form', name='form_item_param', id=3)
dataloader.put('form', name='test parent', id=4)
dataloader.put('form', name='Login', id=5)
dataloader.put('form', name='User', id=6)
dataloader.put('form', name='User Group', id=7)
dataloader.put('form', name='Form_param', id=8)
dataloader.put('form', name='Permission Group list', id=9)

# Form_param

dataloader.put('form_param', form_id=1, value='Form', key='form_object', id=1)
dataloader.put('form_param', form_id=2, value='Form_item', key='form_object', id=2)
dataloader.put('form_param', form_id=3, value='Form_item_param', key='form_object', id=3)
dataloader.put('form_param', form_id=6, value='User', key='form_object', id=4)
dataloader.put('form_param', form_id=8, value='Form_param', key='form_object', id=5)
dataloader.put('form_param', form_id=7, value='User_group', key='form_object', id=6)

# Form_item

dataloader.put('form_item', name='form.name', form_id=1, label='form name:', item='textbox', sort_order=1, active=1, id=1)
dataloader.put('form_item', name='save', form_id=1, label='save', item='submit', sort_order=3, active=1, id=2)
dataloader.put('form_item', name='form_item.name', form_id=2, label='name:', item='textbox', sort_order=1, active=1, id=3)
dataloader.put('form_item', name='form_item.label', form_id=2, label='label:', item='textbox', sort_order=2, active=1, id=4)
dataloader.put('form_item', name='form_item.item', form_id=2, label='item:', item='dropdown', sort_order=3, active=1, id=5)
dataloader.put('form_item', name='save', form_id=2, label='save', item='submit', sort_order=6, active=1, id=7)
dataloader.put('form_item', name='form_item_param.key', form_id=3, label='key', item='textbox', sort_order=1, active=1, id=8)
dataloader.put('form_item', name='form_item_param.value', form_id=3, label='value', item='textbox', sort_order=2, active=1, id=9)
dataloader.put('form_item', name='save', form_id=3, label='save', item='submit', sort_order=3, active=1, id=10)
dataloader.put('form_item', name='form.name', form_id=4, label='name', item='textbox', sort_order=0, active=1, id=11)
dataloader.put('form_item', name='sub1', form_id=1, label='subform', item='subform', sort_order=4, active=1, id=12)
dataloader.put('form_item', name='sub2', form_id=2, label='subform', item='subform', sort_order=7, active=1, id=13)
dataloader.put('form_item', name='delete', form_id=3, label='delete', item='submit', sort_order=4, active=1, id=15)
dataloader.put('form_item', name='username', form_id=5, label='name', item='textbox', sort_order=1, active=1, id=16)
dataloader.put('form_item', name='password', form_id=5, label='password', item='password', sort_order=2, active=1, id=17)
dataloader.put('form_item', name='login', form_id=5, label='login', item='submit', sort_order=3, active=1, id=18)
dataloader.put('form_item', name='user.username', form_id=6, label='user:', item='textbox', sort_order=1, active=1, id=19)
dataloader.put('form_item', name='user.password', form_id=6, label='password', item='password', sort_order=2, active=1, id=20)
dataloader.put('form_item', name='save', form_id=6, label='save', item='submit', sort_order=5, active=1, id=21)
dataloader.put('form_item', name='user.active', form_id=6, label='active', item='checkbox', sort_order=3, active=1, id=22)
dataloader.put('form_item', name='user.last_login', form_id=6, label='last login', item='textbox', sort_order=0, active=0, id=23)
dataloader.put('form_item', name='form_item.sort_order', form_id=2, label='sort order:', item='textbox', sort_order=4, active=1, id=24)
dataloader.put('form_item', name='form_item.active', form_id=2, label='active', item='checkbox', sort_order=5, active=1, id=25)
dataloader.put('form_item', name='user_group.name', form_id=7, label='name', item='textbox', sort_order=1, active=1, id=26)
dataloader.put('form_item', name='user_group.description', form_id=7, label='description', item='textbox', sort_order=2, active=1, id=27)
dataloader.put('form_item', name='save', form_id=7, label='save', item='submit', sort_order=3, active=1, id=28)
dataloader.put('form_item', name='form_param.key', form_id=8, label='key:', item='textbox', sort_order=1, active=1, id=29)
dataloader.put('form_item', name='form_param.value', form_id=8, label='value', item='textbox', sort_order=2, active=1, id=30)
dataloader.put('form_item', name='save', form_id=8, label='save', item='submit', sort_order=3, active=1, id=31)
dataloader.put('form_item', name='delete', form_id=8, label='delete', item='submit', sort_order=4, active=1, id=32)
dataloader.put('form_item', name='sub3', form_id=1, label='form parameters', item='subform', sort_order=3, active=1, id=33)
dataloader.put('form_item', name='sub1', form_id=9, label='permission groups', item='subform', sort_order=1, active=1, id=34)
dataloader.put('form_item', name='delete', form_id=7, label='delete', item='submit', sort_order=4, active=1, id=35)
dataloader.put('form_item', name='user.user_group_id', form_id=6, label='group', item='dropdown', sort_order=4, active=1, id=36)

# Form_item_param

dataloader.put('form_item_param', form_id=8, value='red|blue|green', key='values', id=1)
dataloader.put('form_item_param', form_id=8, value='sql', key='type', id=2)
dataloader.put('form_item_param', form_id=12, value=2, key='subformID', id=3)
dataloader.put('form_item_param', form_id=12, value='form_id', key='child_id', id=4)
dataloader.put('form_item_param', form_id=12, value='id', key='parent_id', id=5)
dataloader.put('form_item_param', form_id=13, value='form_id', key='child_id', id=6)
dataloader.put('form_item_param', form_id=13, value='id', key='parent_id', id=7)
dataloader.put('form_item_param', form_id=13, value=3, key='subformID', id=8)
dataloader.put('form_item_param', form_id=12, value='Form_item', key='child_object', id=9)
dataloader.put('form_item_param', form_id=13, value='Form_item_param', key='child_object', id=10)
dataloader.put('form_item_param', form_id=13, value='datasheet', key='form_type', id=12)
dataloader.put('form_item_param', form_id=6, value='parent', key='subform_value', id=13)
dataloader.put('form_item_param', form_id=5, value='list', key='type', id=14)
dataloader.put('form_item_param', form_id=5, value='textbox|dropdown|password|submit|subform|checkbox', key='values', id=15)
dataloader.put('form_item_param', form_id=33, value=8, key='subformID', id=16)
dataloader.put('form_item_param', form_id=33, value='form_id', key='child_id', id=17)
dataloader.put('form_item_param', form_id=33, value='id', key='parent_id', id=18)
dataloader.put('form_item_param', form_id=33, value='Form_param', key='child_object', id=19)
dataloader.put('form_item_param', form_id=33, value='datasheet', key='form_type', id=20)
dataloader.put('form_item_param', form_id=34, value=7, key='subformID', id=21)
dataloader.put('form_item_param', form_id=34, value='User_group', key='child_object', id=23)
dataloader.put('form_item_param', form_id=34, value='true', key='show', id=24)
dataloader.put('form_item_param', form_id=34, value='datasheet', key='form_type', id=26)
dataloader.put('form_item_param', form_id=34, value='id', key='child_id', id=27)
dataloader.put('form_item_param', form_id=36, value='sql', key='type', id=28)
dataloader.put('form_item_param', form_id=36, value='SELECT id, name FROM user_group', key='sql', id=29)







