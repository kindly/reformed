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
	
	node.js
	======

*/

	node_generate_html= function(form_data, data, root, form_id, form_type){
		msg('node_generate_html: ');
        $INFO.newState(root);
        $INFO.setState(root, 'form_data', form_data);
		// create the form and place in the div
//		var form_info = this._get_form_info(root);
		var form = form_data;

		if (!form.fields){
			return "FORM NO ENTRY";
		}
		var local_data = {}; //$FORM._generate_process_vars(form_info, root, form_type);
		local_data.count = 0;
		local_data.wrap_tag = 'p';
		local_data.show_label = true;
        local_data.form_type='normal';
        local_data.root = 'main'
        var form_info = {info:{}};
        form_info.info.top_level = true;
		form_info.info.clean = true;
		form_info.info.clean_rows = [];
		form_info.info.form_type = local_data.form_type;
		form_info.info.grid_record_offset = 0;
		form_info.info.has_records = local_data.has_records;
		// place for record id data
		form_info.info.record_id = [];
        $INFO.setState(root, 'form_info', form_info.info);
        form_info.layout = form
		var formHTML = '';
	
		// FORM HEADER
	
		formHTML += '<div class="form_header" >';
		formHTML += form_info.info.name;
//		formHTML += '<button onclick="$FORM._info(\'';
//		formHTML += local_data.my_root + '\')">info</button>';
		formHTML += '</div>';
	
		// FORM BODY
	
		formHTML += '<div class="form_body" >';	

		// ERROR message area
		
		if (form.params && form.params.form_error &&
		form.params.form_error == 'single'){
			error_id = $INFO.getId(local_data.root) + '__error';
			formHTML += '<div id="' + error_id; 
			formHTML += '" class="error_single">&nbsp;</div>';
		}

		switch (local_data.form_type){
			case 'action':
			case 'normal':
				formHTML += _generate_form_html_normal(form_info, local_data, data);
				break;
			case 'grid':
                alert('grid not defined')
	//			formHTML += $FORM._generate_form_html_grid(form_info, local_data);
				break;
			default:
				alert('unknown form type generation request');
		}

		formHTML += '</div>';  // end of form body div

		// FORM FOOTER
		if (!form_info.info.top_level && (local_data.form_many_side_not_null = False,type=='normal' || local_data.form_type=='action')){
			formHTML += _generate_footer_html(local_data);
		}

		return formHTML;
	};

function _generate_form_html_normal(form_info, local_data, data){

		if (local_data.root.substring(local_data.root.length - 1) == '#'){
			local_data.record_id = local_data.root;
			local_data.id = $INFO.addId(local_data.root + "*id");
		} else {
			local_data.record_id = local_data.root + '#';
			local_data.id = $INFO.addId(local_data.root + "#*id");
		}

		var formHTML = _generate_fields_html(form_info, local_data, data);
        if (data){
    		formHTML += '<input type="text" id="' + local_data.id + '" class="hidden" value = "' + data.__id + '" /> ';
        }
		return formHTML;
	}

function _generate_fields_html(form_info, local_data, data){
		var form = form_info.layout;
		var formHTML = '';
		var my_id;
		var i;
        var value = '';
        var item;

		for (i=0; i<form.fields.length; i++){

			item = form.fields[i];

			if (local_data.count){
				my_id = local_data.root + "(" + local_data.i + ")#" + item.name;
			} else {
				if (local_data.root.substring(local_data.root.length - 1) == '#'){
					my_id = local_data.root + item.name;
				} else {
					my_id = local_data.root + "#" + item.name;
				}
			}

			my_id = $INFO.addId(my_id);
			if (item.type == 'subform'){
				// get HTML for subform
				formHTML += this._subform(item, my_id, form_info);
			} else {
                // get value
                if (data && typeof(data[item.name]) != 'undefined'){
                    value = data[item.name];
                }
				// add item
				var temp = $FORM_CONTROL.html(item, my_id, local_data.show_label, value);
				formHTML += _wrap(temp, local_data.wrap_tag);
			}
		}
		return formHTML;
	}

function _generate_grid_footer(local_data, form){

//FIXME we aren't passing form at the moment
		var formHTML = '';
		if (local_data.has_records){
			formHTML += '<tfoot>';
			formHTML += '<tr><td>&nbsp</td><td colspan="' + form.fields.length + '" >' + this._navigation(local_data.my_root) + '</td></tr>';
			formHTML += '</tfoot>';
		}
		formHTML += '</tbody></table>';
		return formHTML;
	}

function _wrap(arg, tag){
		// this wraps the item in <tag> tags
		return '<' + tag + '>' + arg + '</' + tag + '>';
}
	// FORM housekeeping
function _parse_id(item){

		var item_id = $INFO.getReverseId(item.id);
		return _parse_item(item_id);
	}

function _parse_item(item){
		// parse  root#control
		// or	  root(row)#control
		msg('_parse_item');
		var m = String(item).match(/^([^\(]*)(\((\d+)\))?#([^#]*)$/);
		if(m){
			var grid;
			var root = m[1] ;
			if (typeof(root) == "undefined"){
				root = '';
			}
			var row = m[3];
			if (typeof(row) != "undefined" && row !== ''){
				row = parseInt(row, 10);
				grid = true;
			} else {
				row = null;
				grid = false;
			}
			var control = m[4];
			if (typeof(control) == "undefined" || control === ''){
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
	}

function itemChanged(item){

		msg('itemChanged');
		var m = _parse_id(item);
		if (m) {
			dirty(m.root_stripped, m.row, true);
		}
	}

function dirty(root, row, state){
		msg('dirty');
		// keeps track of form dirtyness
		// use css to show user
		// we don't dirty 'action' forms
//		form_info = this._get_form_info(root);
        form_data = $INFO.getState(root, 'form_data');
        form_info = $INFO.getState(root, 'form_info');
		if (!form_data.params ||  !form_data.params.form_type || form_data.params.form_type != 'action'){
			var my_root;
			if (row === null){
				// single form
				if (state){
					// are we already dirty?
					if(form_info.clean){
						form_info.clean = false;
						my_root = '#' + root//$INFO.getId(root);
						$(my_root).addClass("dirty");
						// buttons
						$(my_root + '__save').removeAttr("disabled");
					}
				} else {
					form_info.clean = true;
					my_root = '#' + root;//$INFO.getId(root);
					$(my_root).removeClass("dirty");
					// buttons
					$(my_root + '__save').attr("disabled","disabled");
				}
			} else {
				// grid etc
				my_root = root.substring(0,root.length - 1) + '(' + row + ')#';
				var my_root_id;
				if (state){
			
					// are we already dirty?
					if(form_info.clean_rows[row]){
						$INFO.setStateArray(root, 'clean_rows',row, false);
						my_root_id = '#' + $INFO.getId(my_root);
						$(my_root_id).addClass("dirty");
						// buttons
						$(my_root_id + '__save').removeAttr("disabled");
					}
				} else {
					$INFO.setStateArray(root, 'clean_rows',row, true);
					my_root_id = '#' + $INFO.getId(my_root);
					$(my_root_id).removeClass("dirty");
					// buttons
					$(my_root_id + '__save').attr("disabled","disabled");
				}
			}
		}
	}

function form_setup(root, form_data){
    // do any setting up of the form
    for (i=0; i<form_data.fields.length; i++){
			item = form_data.fields[i];
            if (item.params){
                setup_process_params(root, item);
            }
    }
    dirty(root, null, false);
}

function setup_process_params(root, item){
    for (key in item.params){
        v = item.params[key]
        if (key == 'autocomplete'){
            id = $INFO.getId(root + '#' + item.name)
            $('#' + id).autocomplete(v);
        }
    }
}

function node_save(root, command){
		msg('node_save');
        out = node_get_form_data(root);
        id = $INFO.getId('main#*id');
        var node =  $INFO.getState(root, 'node');
        out['__id'] = $('#'+ id).val();
        get_node(node, 'save', out); 
    }


function node_get_form_data(root){
        var form_data = $INFO.getState(root, 'form_data');
        var out = $INFO.getState(root, 'sent_data');
		for (i=0; i<form_data.fields.length; i++){
			item = form_data.fields[i];
            name = item.name;
            id = $INFO.getId('main#' + name);
            value = $('#' + id).val();
            if (typeof value == 'undefined'){
                value = null;
            }
            out[name] = value;
        }
        return out;
    }

function node_delete(root, command){
		msg('node_delete');
        var form_data = $INFO.getState('#', 'form_data');
        var node =  $INFO.getState(root, 'node')
        var out = {};
        var id = $INFO.getId('main#*id');
        out['__id'] = $('#'+ id).val();
    }


function node_button(item, node, command){
    out = node_get_form_data(root);
    get_node(node, command, out);
}


function show_listing(data, node){

    html = '';
    for (i=0; i<data.length; i++){
        item = data[i];
        table = String(item.table);
        next_node = 'test.' + table.substring(0,1).toUpperCase() + table.substring(1,table.length);
        html += '<p onclick="$JOB.add({node: \'' + next_node + '\', lastnode: \'' + node + '\', data:{__id: '
        html += item.id + '}, command: \'view\'}';
        html += ', {}, \'node\', true)">' + item.title + '</p>';
    }
    $('#main').html(html);
}



function get_node(node_name, node_command, node_data){

    info = {node: node_name,
            lastnode: '',  //fixme
            command: node_command }

    if (node_data){
        info['data'] = node_data;
    }

    $JOB.add(info, {}, 'node', true)


}
        fn = function(packet, job){
             root = 'main';
             switch (packet.data.action){
                
                 case 'html':
                     $('#' + root).html(packet.data.data.html);
                     break;
                 case 'form':
                     form = packet.data.data.form;
                     data = packet.data.data.data;
                     $('#' + root).html(node_generate_html(form, data, root));
                     $INFO.setState(root, 'node', packet.data.node)
                     $INFO.setState(root, 'sent_data', data)
                     form_setup(root, form);
                     break;
                 case 'save_error':
                    alert($.toJSON(packet.data.data));
                    break;
                 case 'general_error':
                    alert(packet.data.data);
                    break;
                 case 'listing':
                    show_listing(packet.data.data, packet.data.node);
                    break;
            }
        }

		$JOB.addPacketFunction('node', fn);

