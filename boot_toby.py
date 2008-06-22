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

r.Table("user", r.TextBox("username"),r.TextBox("password"),r.Boolean('active'),r.Integer('user_group')).paramset()

r.Table("user_group", r.TextBox("name"),r.TextBox("description")).paramset()


# code
r.Table("code", r.TextBox("name"),r.TextBox("description"), r.OneToMany("code_group_code","code_group_code")).paramset()
r.Table("code_group", r.TextBox("name"),r.TextBox("description"), r.OneToMany("code_group_code","code_group_code")).paramset()
r.Table("code_group_code", r.Boolean("active"), r.Integer("sort_order")).paramset()

#code2
r.Table("code2", r.TextBox("name"),r.TextBox("description"), r.OneToMany("code2_group_code","code2_group_code")).paramset()
r.Table("code2_group", r.TextBox("name"),r.TextBox("description"), r.OneToMany("code2","code2"), r.OneToMany("code2_group_code","code2_group_code")).paramset()
r.Table("code2_group_code").paramset()

r.data=r.Database()
r.data.create_tables()


# dataloader




# forms
dataloader.put(
[
{'form':{ 'name':'form' }, 
'_data_': [
	{'form_param':{ 'value':'form', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'form.name', 'label':'form name:', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'sub1', 'label':'subform', 'item':'subform', 'sort_order':4, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'form_item', 'key':'subform_name' } },
		{'form_item_param':{ 'value':'form_id', 'key':'child_id' } },
		{'form_item_param':{ 'value':'id', 'key':'parent_id' } },
		{'form_item_param':{ 'value':'form_item', 'key':'child_object' } }
		]},
	{'form_item':{ 'name':'sub3', 'label':'form parameters', 'item':'subform', 'sort_order':3, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'form_param', 'key':'subform_name' } },
		{'form_item_param':{ 'value':'form_id', 'key':'child_id' } },
		{'form_item_param':{ 'value':'id', 'key':'parent_id' } },
		{'form_item_param':{ 'value':'form_param', 'key':'child_object' } },
		{'form_item_param':{ 'value':'grid', 'key':'form_type' } }
		]}
	]},
{'form':{ 'name':'form_item' }, 
'_data_': [
	{'form_param':{ 'value':'form_item', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'form_item.name', 'label':'name:', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'form_item.label', 'label':'label:', 'item':'textbox', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'form_item.item', 'label':'item:', 'item':'dropdown', 'sort_order':3, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'list', 'key':'type' } },
		{'form_item_param':{ 'value':'textbox|dropdown|password|submit|subform|checkbox|codelist', 'key':'values' } }
		]},
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':6, 'active':1 } },
	{'form_item':{ 'name':'sub2', 'label':'subform', 'item':'subform', 'sort_order':7, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'form_item_id', 'key':'child_id' } },
		{'form_item_param':{ 'value':'id', 'key':'parent_id' } },
		{'form_item_param':{ 'value':'form_item_param', 'key':'subform_name' } },
		{'form_item_param':{ 'value':'form_item_param', 'key':'child_object' } },
		{'form_item_param':{ 'value':'grid', 'key':'form_type' } }
		]},
	{'form_item':{ 'name':'form_item.sort_order', 'label':'sort order:', 'item':'textbox', 'sort_order':4, 'active':1 } },
	{'form_item':{ 'name':'form_item.active', 'label':'active', 'item':'checkbox', 'sort_order':5, 'active':1 } }
	]},
{'form':{ 'name':'form_item_param' }, 
'_data_': [
	{'form_param':{ 'value':'form_item_param', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'form_item_param.key', 'label':'key', 'item':'textbox', 'sort_order':1, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'red|blue|green', 'key':'values' } },
		{'form_item_param':{ 'value':'sql', 'key':'type' } }
		]},
	{'form_item':{ 'name':'form_item_param.value', 'label':'value', 'item':'textbox', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'delete', 'label':'delete', 'item':'submit', 'sort_order':4, 'active':1 } }
	]},
{'form':{ 'name':'test parent' } },
{'form':{ 'name':'Login' }, 
'_data_': [
	{'form_item':{ 'name':'username', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'password', 'label':'password', 'item':'password', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'login', 'label':'login', 'item':'submit', 'sort_order':3, 'active':1 } }
	]},
{'form':{ 'name':'User' }, 
'_data_': [
	{'form_param':{ 'value':'user', 'key':'form_object' } },
	{'form_param':{ 'value':'grid', 'key':'form_view' } }
	,
	{'form_item':{ 'name':'user.username', 'label':'user:', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'user.password', 'label':'password', 'item':'password', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':5, 'active':1 } },
	{'form_item':{ 'name':'user.active', 'label':'active', 'item':'checkbox', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'user.user_group', 'label':'group', 'item':'dropdown', 'sort_order':4, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'sql', 'key':'type' } },
		{'form_item_param':{ 'value':'SELECT code2.id, code2.name FROM code2 JOIN code2_group ON code2.code2_group_id =  code2_group.id WHERE code2_group.name = \'user group\'', 'key':'sql' } }
		]}
	]},
{'form':{ 'name':'User Group' }, 
'_data_': [
	{'form_param':{ 'value':'user_group', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'user_group.name', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'user_group.description', 'label':'description', 'item':'textbox', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'delete', 'label':'delete', 'item':'submit', 'sort_order':4, 'active':1 } },
	{'form_item':{ 'name':'code2_group_code.code2_id', 'label':'permissions', 'item':'codelist', 'sort_order':5, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'code2', 'key':'code_table' } },
		{'form_item_param':{ 'value':'code2_group_code', 'key':'flag_table' } },
		{'form_item_param':{ 'value':'code2_group_id', 'key':'flag_table_id_field' } },
		{'form_item_param':{ 'value':'code2_id', 'key':'code_table_id_field' } }
		]}
	]},
{'form':{ 'name':'form_param' }, 
'_data_': [
	{'form_param':{ 'value':'form_param', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'form_param.key', 'label':'key:', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'form_param.value', 'label':'value', 'item':'textbox', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'delete', 'label':'delete', 'item':'submit', 'sort_order':4, 'active':1 } }
	]},
{'form':{ 'name':'Permission Group list' }, 
'_data_': [
	{'form_item':{ 'name':'sub1', 'label':'permission groups', 'item':'subform', 'sort_order':1, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'user_group', 'key':'subform_name' } },
		{'form_item_param':{ 'value':'user_group', 'key':'child_object' } },
		{'form_item_param':{ 'value':'true', 'key':'show' } },
		{'form_item_param':{ 'value':'grid', 'key':'form_type' } },
		{'form_item_param':{ 'value':'id', 'key':'child_id' } }
		]}
	]},
{'form':{ 'name':'Codes' }, 
'_data_': [
	{'form_param':{ 'value':'grid', 'key':'form_view' } },
	{'form_param':{ 'value':'code', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'code.name', 'label':'code', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'code.description', 'label':'description', 'item':'textbox', 'sort_order':2, 'active':1 } }
	]},
{'form':{ 'name':'Code Group' }, 
'_data_': [
	{'form_param':{ 'value':'grid', 'key':'form_view' } },
	{'form_param':{ 'value':'code_group', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'code_group.name', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'code_group.description', 'label':'description', 'item':'textbox', 'sort_order':2, 'active':1 } }
	]},
{'form':{ 'name':'Grouped Codes' }, 
'_data_': [
	{'form_param':{ 'value':'code2_group', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'code2_group_code.code2_id', 'label':'code list', 'item':'codelist', 'sort_order':2, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'true', 'key':'code_list' } },
		{'form_item_param':{ 'value':'code', 'key':'code_table' } },
		{'form_item_param':{ 'value':'code2_group_code', 'key':'flag_table' } },
		{'form_item_param':{ 'value':'code2_group_id', 'key':'flag_table_id_field' } },
		{'form_item_param':{ 'value':'code2_id', 'key':'code_table_id_field' } }
		]},
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':3, 'active':1 } },
	{'form_item':{ 'name':'code2_group.name', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'code2_group.description', 'label':'description', 'item':'textbox', 'sort_order':1, 'active':1 } }
	]},
{'form':{ 'name':'Code2 Group' }, 
'_data_': [
	{'form_param':{ 'value':'code2_group', 'key':'form_object' } }
	,
	{'form_item':{ 'name':'code2_group.name', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'save', 'label':'save', 'item':'submit', 'sort_order':2, 'active':1 } },
	{'form_item':{ 'name':'sub', 'label':'x', 'item':'subform', 'sort_order':3, 'active':1 }, 
	'_data_': [
		{'form_item_param':{ 'value':'code2', 'key':'subform_name' } },
		{'form_item_param':{ 'value':'code2_group_id', 'key':'child_id' } },
		{'form_item_param':{ 'value':'id', 'key':'parent_id' } },
		{'form_item_param':{ 'value':'code2', 'key':'child_object' } },
		{'form_item_param':{ 'value':'grid', 'key':'form_type' } }
		]},
	{'form_item':{ 'name':'code2_group.description', 'label':'description', 'item':'textbox', 'sort_order':4, 'active':1 } }
	]},
{'form':{ 'name':'Code2' }, 
'_data_': [
	{'form_param':{ 'value':'code2', 'key':'form_object' } },
	{'form_param':{ 'value':'grid', 'key':'form_view' } }
	,
	{'form_item':{ 'name':'code2.name', 'label':'name', 'item':'textbox', 'sort_order':1, 'active':1 } },
	{'form_item':{ 'name':'code2.description', 'label':'description', 'item':'textbox', 'sort_order':2, 'active':1 } }
	]}

]
)
