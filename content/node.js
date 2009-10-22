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

    node_generate_html= function(form, data, root, form_id, form_type){
        msg('node_generate_html: ');
        $INFO.newState(root);
        $INFO.setState(root, 'form_data', form);
        $INFO.setState(root, 'sent_data', data)
        // create the form and place in the div

        if (!form.fields){
            return "FORM NO ENTRY";
        }
        if (form.params && form.params.form_type){
            form_type = form.params.form_type
        } else {
            form_type = "normal"
        }
        var local_data = {}; //$FORM._generate_process_vars(form_info, root, form_type);
        local_data.count = 0;
        local_data.wrap_tag = 'p';
        local_data.show_label = true;
        local_data.form_type = form_type;
        local_data.root = root

        var form_info = {info:{}};
        form_info.info.top_level = true;
        form_info.info.clean = true;
        form_info.info.clean_rows = [];
        if (data){
            for (i=0; i<data.length + 1; i++){
                form_info.info.clean_rows[i] = true
            }
        }
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
// count root i wrap_tag show_label 
                formHTML += _generate_form_html_normal(form_info, local_data, data);//########### @@@@@@
                break;
            case 'grid':
                formHTML += _generate_form_html_continuous(form_info, local_data, data);
  //              formHTML += $FORM._generate_form_html_grid(form_info, local_data, data);
                break;
            default:
                alert('unknown form type generation request');
        }

        formHTML += '</div>';  // end of form body div

        // FORM FOOTER
        if (!form_info.info.top_level && (local_data.form_many_side_not_null = False,type=='normal' || local_data.form_type=='action')){
// my_root has_records form.fields.length

            formHTML += _generate_footer_html(local_data);//########### @@@@@@
        }
// grid footer
// has_records my_root form.fields.length
        return formHTML;
    };

function _generate_form_html_normal(form_info, local_data, data){
// local_data: count root i wrap_tag show_label 
        var id
        if (local_data.root.substring(local_data.root.length - 1) == '#'){
            id = $INFO.addId(local_data.root + "*id");
        } else {
            id = $INFO.addId(local_data.root + "#*id");
        }

        var formHTML = _generate_fields_html(form_info.layout, local_data, data);
        if (data){
            formHTML += '<input type="text" id="' + id + '" class="hidden" value = "' + data.id + '" /> ';
        }
        return formHTML;
    }


function _generate_form_html_continuous(form_info, local_data, data){
// local_data: count root i wrap_tag show_label
    formHTML = '';
    if (data){
        for (i=0; i<data.length +1; i++){
            base_id = local_data.root + "(" + i + ")";
            div_id = $INFO.addId(base_id);
            id_id = $INFO.addId(base_id + "#*id");
    
            local_data.i = i
            local_data.count = data.length + 1
            formHTML += "<div id='" + div_id + "'>";
            formHTML += '<div class="form_body">';
            formHTML += _generate_fields_html(form_info.layout, local_data, data[i]);
            if (data[i]){
                record_id = data[i].id;
            } else {
                record_id = 0;
            }
            formHTML += '<input type="text" id="' + id_id + '" class="hidden" value = "' + record_id + '" /> ';
            formHTML += "</div>";
            formHTML += "</div>";
        }
    }
    return formHTML;
}

function _generate_fields_html(form, local_data, data){
        var formHTML = '';
        var my_id;
        var i;
        var value = '';
        var item;
//local_data: count root i wrap_tag show_label
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
                formHTML += _subform(item, my_id, data[item.name]);
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

function _subform(item, my_id, data){
    out = '<div class="subform">' + item.title + '</br>'
    out += node_generate_html(item.params.form, data, root + '#' + item.name);
    out += '</div>';
    return out

}
function _generate_grid_footer(local_data){
// local_data: has_records my_root num_fields
        var formHTML = '';
        if (local_data.has_records){
            formHTML += '<tfoot>';
            formHTML += '<tr><td>&nbsp</td><td colspan="' + local_data.num_fields + '" >' + this._navigation(local_data.my_root) + '</td></tr>';
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
        // or      root(row)#control
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
                        my_root = '#' + root;
                        $(my_root).addClass("dirty");
                    }
                } else {
                    form_info.clean = true;
                    my_root = '#' + root;;
                    $(my_root).removeClass("dirty");
                }
            } else {
                // grid etc
                my_root = root.substring(0,root.length) + '(' + row + ')';
                var my_root_id;
                if (state){
                    // are we already dirty?
                    if(form_info.clean_rows[row]){
                        form_info.clean_rows[row] = false;
                        my_root_id = '#' + $INFO.getId(my_root);
                        $(my_root_id).addClass("dirty");
                    }
                } else {
                    $INFO.setStateArray(root, 'clean_rows',row, true);
                    my_root_id = '#' + $INFO.getId(my_root);
                    $(my_root_id).removeClass("dirty");
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
        id = $INFO.getId(root + '#*id');
        var node =  $INFO.getState(root, 'node');
        out['__id'] = $('#'+ id).val();
        get_node(node, 'save', out);
    }


function node_get_form_data(root){
        var form_data = $INFO.getState(root, 'form_data');
        var out = $INFO.getState(root, 'sent_data');
        out['__root'] = root;
        for (i=0; i<form_data.fields.length; i++){
            item = form_data.fields[i];
            name = item.name;
            if (item.type == 'subform'){
                out[name] = node_get_form_data_rows(root + '#' + name);
            } else {
                id = $INFO.getId(root + '#' + name);
                value = $('#' + id).val();
                if (typeof value == 'undefined'){
                    value = null;
                }
                out[name] = value;
            }
        }
        return out;
    }

function node_get_form_data_rows(root){
        var form_data = $INFO.getState(root, 'form_data');
        var form_info = $INFO.getState(root, 'form_info');
        var out = [];
        var my_root;
        for(var row=0; row<form_info.clean_rows.length; row++){
            if (!form_info.clean_rows[row]){
                // the row is dirty so needs to be saved
                out_row = $INFO.getState(root, 'sent_data')[row];
                if (typeof(out_row) == 'undefined'){
                    out_row = {};
                }
                my_root = root + '(' + row + ')';
                out_row['__root'] = my_root;
                for (var i=0; i<form_data.fields.length; i++){
                    item = form_data.fields[i];
                    name = item.name;
                    id = $INFO.getId(my_root + '#' + name);
                    value = $('#' + id).val();
                    if (typeof value == 'undefined'){
                        value = null;
                    }
                    out_row[name] = value;
                }
                out.push(out_row)
            }
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
        html += '<div class="list">'
        html += '<span class="list_title" onclick="$JOB.add({node: \'' + next_node + '\', lastnode: \'' + node + '\', data:{__id: '
        html += item.id + '}, command: \'view\'}';
        html += ', {}, \'node\', true)">' + item.table + ' - ' + item.title + '</span></br><span class="list_summary">' + item.summary + '</span></div>';
    }
    $('#main').html(html);
}

function search_box(){
    get_node('test.Search', $('#search').val());
    return false;
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
                 //    $INFO.setState(root, 'sent_data', data)
                     form_setup(root, form);
                     break;
                 case 'save_error':
               //     alert($.toJSON(packet.data.data));
                    data = packet.data.data
                    for (key in data){
             //           alert('key: ' + key + '\nvalue: ' + data[key]);
                        id = $INFO.getId(key);
                        $('#' + id).addClass('error');
                        $('#' + id + '__error').html(data[key]);
                    }
                    break;
                 case 'save':
                    saved = packet.data.data.saved;
                    for (var i=0; i<saved.length; i++){
                        div = saved[i][0];
                        inserted_id = saved[i][1];
                        id = $INFO.getId(div + '#*id');
                        $('#' + id).val(inserted_id);
                        info = _parse_item(div + '#x')
                        dirty(info.root_stripped, info.row, false);
     
                    }
                    break
                 case 'general_error':
                    alert(packet.data.data);
                    break;
                 case 'listing':
                    show_listing(packet.data.data, packet.data.node);
                    break;
            }
        }

        $JOB.addPacketFunction('node', fn);

