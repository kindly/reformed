/*

    This file is part of Reformed.

    Reformed is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as 
    published by the Free Software Foundation.

    Reformed is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Reformed.  If not, see <http://www.gnu.org/licenses/>.

	-----------------------------------------------------------------
	
	Reformed
	Copyright (c) 2008-2009 Toby Dacre & David Raznick
	
	form.js
	======
	
	Does the stuff around displaying forms

	$FORM

	Public Functions
	================
	
	fill (data_id, form_id, root, link_id, parent_field)
		fills the form with data		
		data_id:		(int) the data to use
		form_id:		(string) form id
		root:			(string) the root	
		link_id:		(int) used by subforms - value of the linking field
		parent_field:	(string) used by subforms - parent linking field
			
	request (form_id, root, command)
		generates a new form and fills with data if needed		
		form_id:	(string) the form to create
		root:		(string) where the form will be placed
		command:	(string) command for data; 'first', 'new'
		
	buttonPress (item)
		called when a button is pressed		
		item:	(string) the id of the changed element
		
	itemChanged (item)
		called when a form items value changes		
		item:	(string) the id of the changed element

	dirty (root, row, state)
		sets the form as dirty	
		root:	(string) the root
		row:	(int/null) the row or null if single form
		state:	(bool) true = dirty, false = clean

*/


$FORM = {

	
	_subform_num_rows: 5, // must be more than 1


	_get_data: function(root, form_root, row){
		// FIXME needs error trapping

		var form_id = $INFO.getState(form_root, 'form_id');
		var record_data = $INFO.getState(form_root, 'records');
	
		var out = {};
		out['form'] = form_id;
		out['data'] = {};
		var record = {};
		// provide extra data
		if (record_data){
			if (row == null){
				// single form
				record['id']=record_data[0];
			} else {
				record['id']=record_data[row];
			}
		}
		if (!$INFO.getState(form_root, 'is_top_level')){
			record['parent_field'] = $INFO.getState(form_root, 'parent_field');
			record['parent_id'] = $INFO.getState(form_root, 'link_id');	
		}
		out['record'] = record;
		// get the data from the form
		var form = $INFO.getForm(form_id);
		var fields = form.fields;

		for (var field in fields){
			var id = $INFO.getId(root + field);
			var type = fields[field].type
			if ($FORM_CONTROL.exists(type)){
				out['data'][field] = $FORM_CONTROL.get(id, type);
			}
		}
		return out;
	},



	fill: function(data_id, form_id, root, link_id, parent_field){
	//	alert('fill data_id: ' + data_id);
		// this fills outputs the form with the data
		// data and form supplied by reference id
		
		var f = $INFO.getForm(form_id);
		
		if (!f.fields){
			// we don't have this form so bale
			return;
		}
		
		if (root.substring(root.length - 1) == '#'){
			var my_root = root;
		} else {
			var my_root = root + '#';
		}

		var has_records = $INFO.getState(my_root, 'has_records');
		if (has_records){
			if ($INFO.getState(my_root, 'is_top_level')){
				if ($INFO.getState(my_root, 'form_type') == 'normal'){
					var records = $INFO.getRecords(form_id, data_id);
					var rowcount = $INFO.getRowcount(form_id, data_id);
				//	var record_data_id  = data_id
				} else {
					var records = $INFO.getRecords(form_id, null);
					var rowcount = $INFO.getRowcount(form_id, null);
					
				}
			} else {
				var records = $INFO.getRecords(form_id, link_id);
				var rowcount = $INFO.getRowcount(form_id, link_id);
			}
			$INFO.setState(my_root, 'rowcount', rowcount);
		}
		
		//alert($.toJSON(records));
		var form_type = $INFO.getState(my_root, 'form_type');
		switch (form_type){
			case 'grid':
				var count = this._subform_num_rows - 1;
				// if it's top level we need to
				// correct the root to remove the #
				if (//$INFO.getState(my_root, 'is_top_level') ||
				root.substring(root.length - 1) == '#'){
					root = root.substring(0, root.length - 1);
				}
				break;
			case 'continuous':
				var count = this._subform_num_rows - 1;
				break;
			default:
				var count = 0;
		}
		
		if (has_records){
			if (link_id && parent_field){
				$INFO.setState(my_root, 'link_id', link_id);
				$INFO.setState(my_root, 'parent_field', parent_field);
			} else {
				$INFO.setState(my_root, 'link_id', null);
				$INFO.setState(my_root, 'parent_field', null);
			}
			var d = $INFO.getData(form_id, data_id);
			if (d){
				$INFO.setState(my_root, 'recordset_id', d['__recordset_id']);
			} else {
				$INFO.setState(my_root, 'recordset_id', null);
			}
		}
	
		var grid_record_offset = $INFO.getState(my_root, 'grid_record_offset');
		if (!grid_record_offset){
			grid_record_offset = 0;
		}
	//	alert(grid_record_offset);
		var records_data = []
		//FIXME want to go through form setting data for each field
		// for continuous forms need to regenerate them or hide unused ones 
		// (generate for now)
		for (var i = 0;i<=count;i++){
		
			if (records && records.length>=i){
				var d = $INFO.getData(form_id, records[i + grid_record_offset]);
			} else {
				d = null;
			}
			// process the id
			if (count){
				var id = $INFO.getId(root + "(" + i + ")#*id");
			} else {
				var id = $INFO.getId(my_root + "*id");			
			}
			if (d){
				var my_id = d['__id']
			} else {
				var my_id = 0
			}		
			// store it
			records_data[i] = my_id;
			// show it
			$('#' + id).val(my_id)

			// do the nav buttons
			
			if (!count && has_records){
				var my_recordset_id = $INFO.getState(my_root, 'recordset_id');
				var my_root_id = '#' + $INFO.getId(my_root);

				if (my_recordset_id == 0){
					$(my_root_id + '__first').attr("disabled","disabled");
					$(my_root_id + '__prev').attr("disabled","disabled");
				} else {
					$(my_root_id + '__first').removeAttr("disabled");data_id
					
					$(my_root_id + '__prev').removeAttr("disabled");
				}
				if (my_recordset_id < rowcount - 1 || my_recordset_id == null){
					$(my_root_id + '__next').removeAttr("disabled");
					$(my_root_id + '__last').removeAttr("disabled");
				} else {
					$(my_root_id + '__next').attr("disabled","disabled");
					$(my_root_id + '__last').attr("disabled","disabled");
				}

			}
			for (var form_item in f.fields){

				id = f.fields[form_item].name;

				if (d && d[id]){
					var value = d[id];
				} else {
					var value = '';		
				}
				if (!count){
					if (root.substring(root.length - 1) == '#'){
						var full_id = root + id;				
					} else {
						var full_id = root + "#" + id;				
					}

				} else {
					var full_id = root + "(" + (i) + ")#" + id;
				}

				var coded_id = $INFO.getId(full_id);
			
				if (f.fields[form_item].type == "subform"){
					// this is a subform so process it
					var sub = f.fields[form_item].params.subform_name;
					var records2 = $INFO.getRecords(sub, data_id);
					if (records2 && records2.length>0){
						// we have some data
						var my_records = records2[0];
					} else {
						// we have no data
						var my_records = null
					}
					this.fill(my_records, 
						 f.fields[form_item].params.subform_name, 
						 full_id, 
						 data_id, 
						 f.fields[form_item].params.child_id); 
				} else {
					$FORM_CONTROL.set(f.fields[form_item].type, coded_id, value);
				}

				if (count){
					this.dirty(my_root, i, false);
				} else {
					this.dirty(my_root, null, false);
				}		
		
			}
		}
		$INFO.setState(my_root, 'records', records_data);
	},

	_fill_request: function(data_id, form_id, command, link_id, 
							parent_field, form_root){

		var request = {data: data_id, 
					   stamp : 12345, 
					   form: form_id, 
					   value: data_id, 
					   command:command, 
					   parent_id:link_id, 
					   parent_field:parent_field, 
					   field:'id', 
					   form_type:$INFO.getState(form_root + '#', 'form_type') };
		
		var data = {type: 'data', 
					form_id: form_id, 
					data_id: data_id, 
					parent_field:parent_field, 
					link_id:link_id, 
					form_root:form_root};
		$JOB.add(request, data, 'data', true);
	},


	request: function(form_id, location, command){
		// add the div to hold the generated form;	
		var root = $INFO.addId(location + '#')
		var form = '<div id="' + root + '" class="form"></div>';
		$("#" + location).html(form);
		this._fetch(form_id, location + '#', null, command);
	},

	_fetch: function(form_id, location, form_type, command){
	
		// we want to get this form
		// and add it at the location in the page (id)
		// we'll set the job up to do this
		// fetch is used to see if we need to check for new form data
		// if false we'll trust what we have in the cache
		
		// FIXME this stamp needs to be versioned
		if ($INFO.existsForm(form_id)){
			var stamp = false;
		} else {
			var stamp = true;
		}
		var request = {form: form_id, stamp: stamp, command: command };
		var data = {type: 'form', 
					subtype: 'show',
					form_id:form_id, 
					location: location, 
					form_type:form_type, 
					link_id: null,
					form_root:location}; 
					
		// if the form is known lets use that info rather than
		// doing a new request
	
		$JOB.add(request, data , 'form', true);
	},

	_generate: function(form_id, root, form_type){

		var form = this._generate_html(form_id, form_type, root)
		// place the generated form in the div
		// FIXME we can cache the form html for future use 
		// to make things snappier
		$("#" + $INFO.getId(root)).html(form);
		//alert(form.length);
	},

	_generate_html: function(form_id, form_type, root){

		// create the form and place in the div
		// FIXME I think I need to provide both the form_id and the div
		// not just one as at present
		var form = $INFO.getForm(form_id);	
		var fields = form.fields;
		var order = form.order;

		if (!fields){
			return "FORM NO ENTRY";
		}		
		
//		alert('generation root: ' + root);
		// am I a top level form
		if (root.substring(root.length - 1) == '#'){ 
			var is_top_level = true;
			var my_root = root;
		} else {
			var is_top_level = false;
			var my_root = root + '#';
		}
		// if form type not supplied use the one in the form parameters
		if (!form_type){
			if (form.params && form.params.form_type){
				form_type = form.params.form_type;
			} else {
				// default if not supplied
				form_type = 'normal';
			}
		}
		if (form_type == 'action') {
			var has_records = false;
		} else {
			var has_records = true;
		}		
		// clear the state for my_root and set as form
		$INFO.newState(my_root, 'form');
		$INFO.setState(my_root, 'clean', true) ;
		$INFO.setState(my_root, 'clean_rows', []); 
		$INFO.setState(my_root, 'form_id', form_id);
		$INFO.setState(my_root, 'is_top_level', is_top_level);
		$INFO.setState(my_root, 'has_records', has_records);
		$INFO.setState(my_root, 'form_type', form_type);
		$INFO.setState(my_root, 'grid_record_offset', 0);
		
		switch (form_type){
			case 'grid':
				var count = this._subform_num_rows - 1;
				var wrap_tag = 'td';
				var show_label = false;
				if (is_top_level){
					root = root.substring(0,root.length - 1);
			//		alert(root);
				}
				break;
			case 'continuous':
				var count = this._subform_num_rows - 1;
				var wrap_tag = 'p';
				var show_label = true;
				break;
			default:
				var count = 0;
				var wrap_tag = 'p';
				var show_label = true;
		}

		var formHTML = '';
	
		// FORM HEADER
	
		formHTML += '<div class="form_header" >';
		formHTML += 'Form Name';
		formHTML += '<button onclick="$FORM._info(\''
		formHTML += my_root + '\')">info</button>';
		formHTML += '</div>';
	
		// FORM BODY
	
		formHTML += '<div class="form_body" >';	

		// ERROR message area
		
		if (form.params && form.params.form_error &&
		form.params.form_error == 'single'){
			error_id = $INFO.getId(root) + '__error';
			formHTML += '<div id="' + error_id; 
			formHTML += '" class="error_single">&nbsp;</div>';
		}
		
		
		if (form_type == 'grid'){
			formHTML += '<table border="1" >';
			formHTML += '<thead><tr><th class="th_id" >#</th>';
			for (var ordered_item in order){
				item = order[ordered_item];
				formHTML += '<th>' + fields[item].title + '</th>';
			}		
			formHTML += '</tr></thead>';
			formHTML += '<tbody>';
		}
	
		for (var i = 0;i<=count;i++){
			if (form_type == 'grid'){
				var id = $INFO.addId(root + "(" + i + ")#");
				formHTML += '<tr id="' + id + '" >';
			}
		
			// add the id field FIXME needs to be hidden
			if (count){
				var id = $INFO.addId(root + "(" + i + ")#*id");
				var record_id = root + "(" + i +")" + "#";
			} else {
			
				if (root.substring(root.length - 1) == '#'){
					var record_id = root;
					var id = $INFO.addId(root + "*id");
				} else {
					var record_id = root + '#';
					var id = $INFO.addId(root + "#*id");
				}
			}
			if (form_type == 'grid'){
				var temp = '<input type="text" id="' + id + '" class="hidden" />';
				var my_root_id = $INFO.getId(root + "(" + i + ")#");
				temp += this._button("save record", 
									'$FORM._save(\'' + record_id + '\',\'\')',
									'save',
									my_root_id + '__save');
				temp += this._button("delete record", 
									'$FORM._delete(\'' + record_id + '\')',
									'delete',
									my_root_id + '__delete');	
				formHTML += this._wrap(temp, wrap_tag +  ' class="t_id" ');		
			}
		
			for (var ordered_item in order){

				var item = order[ordered_item];

				if (count){
				var my_id = root + "(" + i + ")#" + fields[item].name;
				} else {
					if (root.substring(root.length - 1) == '#'){
						var my_id = root + fields[item].name;
					} else {
						var my_id = root + "#" + fields[item].name;
					}
				}

				my_id = $INFO.addId(my_id);			
				if (fields[item].type == 'subform'){
					// get HTML for subform
					formHTML += this._subform(fields[item], my_id);
				} else {
					// add item
					var temp = $FORM_CONTROL.html(fields[item], my_id, show_label);
					formHTML += this._wrap(temp, wrap_tag);
				}
			}
		};
		if (form_type == 'grid'){ 
			if (has_records){
				formHTML += '<tfoot>';
				formHTML += '<tr><td>&nbsp</td><td colspan="' + order.length + '" >' + this._navigation(my_root) + '</td></tr>';
				formHTML += '</tfoot>';	
			}
		formHTML += '</tbody></table>' 
		}

		formHTML += '</div>';  // end of form body div

		// FORM FOOTER
		if (form_type=='normal' || form_type=='action'){
			formHTML += '<div class="form_footer" >';
			if (has_records){
				formHTML += '<span class="ctl" >';
				formHTML += '<input type="text" id="' + id + '" class="hidden" /> ';
				var my_root_id = $INFO.getId(my_root);
				formHTML += this._button("save record", 
										'$FORM._save(\'' + record_id + '\',\'\')',
										'save',
										my_root_id + '__save');
				formHTML += this._button("delete record", 
										'$FORM._delete(\'' + record_id + '\')',
										'delete',
										my_root_id + '__delete');	
				formHTML += '</span>';
				formHTML += this._navigation(my_root);
			} else {
				formHTML += '&nbsp;'
			}
			formHTML += '</div>';
		}
		return formHTML;	},


	_wrap: function(arg, tag){
		// this wraps the item in <tag> tags
		return '<' + tag + '>' + arg + '</' + tag + '>';
	},


	_subform: function(item, id){
		// we have a subform
		// we want to get the subform
		var id = $INFO.getReverseId(id);
		var subForm = '<div id="' + $INFO.addId(id + '#')
		subForm += '" class="subform" >';
		subForm += this._generate_html(item.params.subform_name,
									  item.params.form_type, 
									  id);
		subForm += '</div>';
		return subForm;
	},

	_navigation: function(root){

		var my_root_id = $INFO.getId(root);
		var out = "<span class='nav'>";
		out += this._button("first record", 
							'$FORM._move(\'' + root + '\',\'first\')',
							'|&lt;',
							my_root_id + '__first');
		out += this._button("previous record", 
							'$FORM._move(\'' + root + '\',\'prev\')',
							'&lt;',
							my_root_id + '__prev');
		out += this._button("next record", 
							'$FORM._move(\'' + root + '\',\'next\')',
							'&gt;',
							my_root_id + '__next');
		out += this._button("last record", 
							'$FORM._move(\'' + root + '\',\'last\')',
							'&gt;|',
							my_root_id + '__last');
		out += this._button("new record", 
							'$FORM._move(\'' + root + '\',\'new\')',
							'*',
							my_root_id + '__new');
		out += "</span>";
		return out;
	},

	_button: function(title, onclick, label, id){
		var html = '<button title="' + title + '" type="button"';
		html += ' id="' + id + '" ';
		html += ' onclick="';
		html += onclick + '">' + label + '</button>';
		return html;
	},

	buttonPress: function(item){

		var m = this._parse_id(item)
		var form_id = $INFO.getState(m.root, 'form_id');
		var control = $INFO.getForm(form_id).fields[m.control];
		if (control.params && control.params.object && control.params.command){
			var object = control.params.object;
			var command = control.params.command;
			var data = this._get_data(m.root, m.root, m.row).data
			var request = {object:object, action:'action',
						   command:command, data:data};
			var job_data = {'form_root':m.root};
			$JOB.add(request, job_data, 'action', true);
		}
	},

	_save: function(root, command){

		var m = this._parse_item(root)

		var field_data = this._get_data(root, m.root, m.row);
		var request = {action:'save', field_data : field_data, command:command};
		var form_id = $INFO.getState(m.root, 'form_id');

		var data = {form_id:form_id, root:root, form_root:m.root, row:m.row} 

		if (command){
			// add extra record movement data
			var current_id = $INFO.getState(root, 'recordset_id');
			request['value'] = current_id;
			var link_id = $INFO.getState(m.root, 'link_id');
			var parent_field = $INFO.getState(m.root, 'parent_field');
			if (m.row != null){
				request['parent_id'] = link_id;
				request['parent_field'] = parent_field;
				request['form_type'] = 'grid';
			} else {
				request['parent_id'] = link_id;
				request['parent_field'] = parent_field;
				request['form_type'] = 'normal';
			}
			data['type'] = 'data';
			
		}

		$JOB.add(request, data, 'edit', true);
	
	},

	_delete: function(root){

		var m = this._parse_item(root);
	
		var my_row = m.row;
		if (m.grid == false){ 
			my_row = 0;
			var my_form_type = 'normal';
		} else {
			var my_form_type = 'grid';
		}

		var records = $INFO.getState(m.root, 'records');
		var record_id = records[my_row];
		var form_id = $INFO.getState(m.root, 'form_id');
		var field_data = {record_id:record_id, form:form_id};
		var request = {action:'delete', field_data : field_data};
		var link_id = $INFO.getState(m.root, 'link_id');
		var parent_field = $INFO.getState(m.root, 'parent_field');
	
		if (m.row != null){
			request['parent_id'] = link_id;
			request['parent_field'] = parent_field;
			request['form_type'] = 'grid';
		} else {
			request['parent_id'] = link_id;
			request['parent_field'] = parent_field;
			request['form_type'] = 'normal';
		}

		var data = {form_id: form_id,
					type: 'data',
					form_root: m.root_stripped, 
					row: m.row, 
					form_type: my_form_type,
					parent_field: parent_field,
					link_id: link_id} 

		$JOB.add(request, data, 'edit', true);
	},

	_move: function(root, command){
		var parent_field = $INFO.getState(root, 'parent_field');
		var link_id = $INFO.getState(root, 'link_id');	
		var current_id = $INFO.getState(root, 'recordset_id');	
		var form_id = $INFO.getState(root, 'form_id');
		var strip_root = root.substring(0, root.length -1);
		
		if ($INFO.getState(root, 'form_type') == 'normal'){
			// normal
			var msg = 'Save Record?';
			if (!$INFO.getState(root, 'clean') && confirm(msg)){
			//	alert('moo');
				this._save(root, command);
			} else {
				this._fill_request(current_id, 
								   form_id,
								   command,
								   link_id,
								   parent_field,
								   strip_root);
			}
		} else {
			// grid etc
			this._grid_move(root, command);
			// FIXME code repeat see above

			this.fill(current_id, form_id, root, link_id, parent_field);
	//		this._fill_request(current_id, 
	//						   form_id,
	//						   command,
	//						   link_id,
	//						   parent_field,
	//						   strip_root);			
		}
	},
	
	_grid_move: function(root, command){

		var offset = $INFO.getState(root, 'grid_record_offset');
		if (!offset){offset = 0;}
		var max_offset = $INFO.getState(root, 'rowcount') - 1;
		switch (command){
			case 'first':
				offset = 0;
				break;
			case 'prev':
				offset--;
				break;
			case 'next':
				offset++;
				break;
			case 'last':
				offset= max_offset;
				break;
		}
		
		if (offset < 0){offset = 0;}
		if (offset > max_offset){offset = max_offset;}
		
		$INFO.setState(root, 'grid_record_offset', offset);
	},

	_info: function(root){
		var info = 'root: ' + root;
		if (!$INFO.getState(root, 'is_top_level')){
			info += '\nlink_id: ' + $INFO.getState(root, 'link_id');
			info += '\nparent_field: ' + $INFO.getState(root, 'parent_field');
			info += '\nrecordset_id: ' + $INFO.getState(root, 'recordset_id');
		}
		info += '\nrowcount: ' + $INFO.getState(root, 'rowcount');

		info += '\n' + $INFO.getStateDebug(root);
		alert(info);
	},

	_parse_id: function(item){

		var item = $INFO.getReverseId(item.id);
		return this._parse_item(item)
	},

	_parse_item: function(item){
		// parse  root#control
		// or	  root(row)#control
		var m = String(item).match(/^([^\(]*)(\((\d+)\))?#([^#]*)$/);
		if(m){
			var root = m[1] ;
			if (typeof(root) == "undefined"){
				root = '';
			}
			var row = m[3];
			if (typeof(row) != "undefined" && row != ''){
				row = parseInt(row);
				var grid = true;
			} else {
				row = null;
				var grid = false;
			}
			var control = m[4];
			if (typeof(control) == "undefined" || control == ''){
				control = null;
			}
			return {root:root + '#',
					root_stripped:root,
					row:row,
					control:control, 
					grid:grid};
		} else {
			alert("something went wrong with the item parser");
			return null;
		}
	},


	// FORM housekeeping

	itemChanged: function(item){

		var m = this._parse_id(item)
		if (m) {	
			this.dirty(m.root, m.row, true)
		}
	},

	dirty: function(root, row, state){

		// keeps track of form dirtyness
		// use css to show user

		// we don't dirty 'action' forms
		if ($INFO.getState(root, 'form_type') != 'action'){
			if (row == null){
				// single form
				if (state){
					// are we already dirty?
					if($INFO.getState(root,'clean')){
						$INFO.setState(root, 'clean', false);
						var my_root = '#' + $INFO.getId(root);
						$(my_root).addClass("dirty")
						// buttons
						$(my_root + '__save').removeAttr("disabled");
					}
				} else {
					$INFO.setState(root, 'clean', true);
					var my_root = '#' + $INFO.getId(root);
					$(my_root).removeClass("dirty")
					// buttons
					$(my_root + '__save').attr("disabled","disabled");
				}
			} else { 
				// grid etc
				var my_root = root.substring(0,root.length - 1) + '(' + row + ')#'
				if (state){
			
					// are we already dirty?
					if($INFO.getState(root, 'clean_rows')[row]){
						$INFO.setStateArray(root, 'clean_rows',row, false);
						var my_root_id = '#' + $INFO.getId(my_root);
						$(my_root_id).addClass("dirty")
						// buttons
						$(my_root_id + '__save').removeAttr("disabled");
					}
				} else {
					$INFO.setStateArray(root, 'clean_rows',row, true);
					var my_root_id = '#' + $INFO.getId(my_root);
					$(my_root_id).removeClass("dirty")
					// buttons
				//	alert(my_root_id)
					$(my_root_id + '__save').attr("disabled","disabled");
				}
			}
		}
	},
	
	_init: function(){
		// does any initialisation such as loading job processing functions
		// this is to ensure that all other modules are loaded
		
		// JOB FUNCTIONS
		
		// data job function
		var fn = function(data){
			
			$FORM.fill(data.data_id, 
					   data.form_id, 
					   data.form_root, 
					   data.link_id, 
					   data.parent_field); 
		};
		$JOB.addJobFunction('data', fn);
		
		// form job function
		fn = function(data){
			$FORM._generate(data.form_id, data.location, data.form_type);
			$FORM.fill(data.data_id,
					   data.form_id,
					   data.form_root,
					   data.link_id,
					   data.parent_field);
		};
		$JOB.addJobFunction('form', fn);
		
		// PACKET FUNCTIONS
		
		// save packet function	
  		fn = function(packet, job){
  			// update the id
			var row = job.row;
			var value = packet.record_id;
			$INFO.setStateArray(job.form_root, 'records', row, value);
			// and display
			var id = $INFO.getId(job.root + '*id');
			$('#' + id).val(value);
			// mark as clean
			$FORM.dirty(job.form_root, job.row, false);
  		};
		$JOB.addPacketFunction('save', fn);

		// action packet function	
  		fn = function(packet, job){
  			if (packet.data.showForm){
  				$FORM.request(packet.data.showForm, 'root', 'first');
  			}
		};
		$JOB.addPacketFunction('action', fn);
	
		// delete packet function	
  		fn = function(packet, job){};
		$JOB.addPacketFunction('delete', fn);


	} 

}

