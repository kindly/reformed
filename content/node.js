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


function page_load(){
/*
    function called on page load by address jquery plug-in
    used for back/forward buttons, bookmarking etc
    gets correct 'address' string and passes to calling function
*/
    var link = $.address.value();
    node_call_from_string(link, true, true);
}


function node_load(arg){
/*
    force a page load of the node
*/
    if ($.address.value() == '/' + arg){
        // the address is already set so we need to force the reload
        // as changing the address will not trigger an event
		node_call_from_string(arg, true, true);
    } else {
        // sets the address which then forces a page load
		$.address.value(arg);
    }
}


function node_call_from_string(arg, change_state, insecure){
/*
    takes a string (arg) of the form
    "/n:<node_name>:<command>:<arguments>"

    change_state: if true will change the state for the root
    FIXME no root info yet defaults to 'main' further along the call chain
*/
    var link = arg.split(':');
    if (link[0]=='/n' || link[0]=='n'){
        var node = link[1];
        var command = link[2];
        var data_hash = {};
        // if arguments are supplied
        if (link.length>3){
            data_hash = convert_url_string_to_hash(link[3]);
        }
	// if the command starts with a underscore we don't want
	// to trigger the command from a url change as this can
	// let dangerous commands be sent via urls
	if (!insecure || command.substring(0,1) != '_'){
            get_node(node, command, data_hash, change_state);
	}
    }
}

function convert_url_string_to_hash(arg){
/*
    convert string to a hash
    input:  "a=1&b=2"
    output  {a:1, b:2}
*/
    var out = {};
    var args = arg.split('&');
    for (var i=0; i<args.length; i++){
        x = args[i];
        s = x.split('=');
        if (s.length == 2){
            out[s[0]] = s[1];
        }
    }
    return out;
}


function _wrap(arg, tag){
    // this wraps the item in <tag> tags
    return '<' + tag + '>' + arg + '</' + tag + '>';
}

function _subform(item, my_id, data, root){
    var out = '<div class="subform" id="' + my_id + '" >'+ item.title + '</br>';
    out += node_generate_html(item.params.form, data, root + '#' + item.name);
    out += '</div>';
    return out;

}

function _generate_fields_html(form, local_data, data, row_count){
    var formHTML = '';
    var my_id;
    var i;
    var value = '';
    var item;
    //local_data: count root i wrap_tag show_label
    for (i=0; i<form.fields.length; i++){

        item = form.fields[i];

        if (row_count !== null){
            my_id = local_data.root + "(" + row_count + ")#" + item.name;
        } else {
            my_id = local_data.root + "#" + item.name;
        }

        my_id = $INFO.addId(my_id);
        if (item.type == 'subform'){
            // get HTML for subform
            formHTML += _subform(item, my_id, data[item.name], local_data.root);
        } else {
            // get value
            if (data && typeof(data[item.name]) != 'undefined'){
                value = data[item.name];
            } else {
                value = '';
            }
            // add item
            var temp = $FORM_CONTROL.html(item, my_id, local_data.show_label, value);
            formHTML += _wrap(temp, local_data.wrap_tag);
        }
    }
    return formHTML;
}

function _generate_form_html_normal(form_info, local_data, data){
// local_data: count root i wrap_tag show_label
    var formHTML = _generate_fields_html(form_info.layout, local_data, data, null);

    return formHTML;
}

function _generate_form_html_continuous(form_info, local_data, data){
// local_data: count root i wrap_tag show_label
    var formHTML = '';
    var base_id;
    var div_id;

    if (data){
        for (i=0; i<data.length +1; i++){
            base_id = local_data.root + "(" + i + ")";
            div_id = $INFO.addId(base_id);

            formHTML += '<div id="' + div_id + '" class="form_body">';
            formHTML += _generate_fields_html(form_info.layout, local_data, data[i], i);
            formHTML += "</div>";
        }
    }
    formHTML += '<p id="' + $INFO.getId(local_data.root) + '__add" class="add_form_row" onclick="add_form_row(\'' + local_data.root + '\')" >add new</p>';
    return formHTML;
}

function add_form_row(root){
    // add a new row to a continuous form
    var form_info = $INFO.getState(root, 'form_info');
    var form_data = $INFO.getState(root, 'form_data');
    var row = form_info.clean_rows.length;
    // mark as clean plus also adds the row
    form_info.clean_rows[row] = true;
    var local_data = {root: root,
                  show_label: true,
                  wrap_tag: 'p'};
    var id =  $INFO.addId(root + '(' + row + ')');
    var formHTML = '<div id="' + id + '" class="form_body">';
    formHTML += _generate_fields_html(form_data, local_data, null, row);
    formHTML += "</div>";
    $('#' + $INFO.getId(root) + '__add').before(formHTML);
    
}
function node_generate_html(form, data, root, form_id, form_type){
    msg('node_generate_html: ');
    if (!data){
        data = {};
    }
    $INFO.newState(root);
    $INFO.setState(root, 'form_data', form);
    $INFO.setState(root, 'sent_data', data);
    // create the form and place in the div

    if (!form.fields){
        return "FORM NO ENTRY";
    }
    if (form.params && form.params.form_type){
        form_type = form.params.form_type;
    } else {
        form_type = "normal";
    }
    var local_data = {};
    local_data.count = 0;
    local_data.wrap_tag = 'div';
    local_data.show_label = true;
    local_data.form_type = form_type;
    local_data.root = root;

    var form_info = {info:{}};
    form_info.info.top_level = true;
    form_info.info.clean = true;
    form_info.info.clean_rows = [];
    if (data){
        for (i=0; i<data.length + 1; i++){
            form_info.info.clean_rows[i] = true;
        }
    }
    form_info.info.form_type = local_data.form_type;
    form_info.info.grid_record_offset = 0;
    form_info.info.has_records = local_data.has_records;
    // place for record id data
    form_info.info.record_id = [];
    $INFO.setState(root, 'form_info', form_info.info);
    form_info.layout = form;
    var formHTML = '';

    // FORM HEADER

    formHTML += '<div class="form_header" >';
    formHTML += form_info.info.name;
    formHTML += '</div>';

    // FORM BODY

    formHTML += '<div id="' + $INFO.addId(root) + '" class="form_body" >';

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
 //         formHTML += $FORM._generate_form_html_grid(form_info, local_data, data);
            break;
        default:
            alert('unknown form type generation request');
    }

    formHTML += '</div>';  // end of form body div

    // FORM FOOTER
    if (!form_info.info.top_level && (local_data.form_many_side_not_null = false || local_data.form_type=='action')){
    // my_root has_records form.fields.length

        formHTML += _generate_footer_html(local_data);//########### @@@@@@
    }
    // grid footer
    // has_records my_root form.fields.length
    return formHTML;
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

function _parse_div(item){
    // parse  root
    // or      root(row)
    msg('_parse_div');
    var m = String(item).match(/^([^\(]*)(\((\d+)\))?$/);
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
        return {root:root,
                row:row,
                grid:grid};
    } else {
        alert("something went wrong with the div parser");
        return null;
    }
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
        return {root:root,
                row:row,
                control:control,
                grid:grid};
    } else {
        alert("something went wrong with the item parser");
        return null;
    }
}

function _parse_id(item){

    var item_id = $INFO.getReverseId(item.id);
    return _parse_item(item_id);
}

function parse_strip_subform_info(item){
    /*
        takes a sting like main#sub(1) and returns minus (x) part
    */
    var m = String(item).match(/^([^\(]*)/);
    if(m){
        return m[1];
    } else {
        alert("something went wrong with parse_strip_subform_info()");
        return null;
    }
}

function dirty(root, row, state){
    msg('dirty');
    // keeps track of form dirtyness
    // use css to show user
    // we don't dirty 'action' forms
    var form_data = $INFO.getState(root, 'form_data');
    if (!form_data.params ||  !form_data.params.form_type || form_data.params.form_type != 'action'){
        var form_info = $INFO.getState(root, 'form_info');
        var my_root;
        var update = false;
        if (row === null){
            // single form
            my_root = '#' + $INFO.getId(root);
            if(state && form_info.clean){
                update = true;
            }
            form_info.clean = !state;
        } else {
            // multi-row
            my_root = root.substring(0,root.length) + '(' + row + ')';
            my_root = '#' + $INFO.getId(my_root);
            if(state && form_info.clean_rows[row]){
                 update = true;
            }
            form_info.clean_rows[row] = !state;
        }
        if(state){
            if(update){
                $(my_root).addClass("dirty");
            }
        } else {
            $(my_root).removeClass("dirty");
        }
    }
}

function itemChanged(item){

    msg('itemChanged');
    // remove the error css
    $('#' + item.id).removeClass('error');
    // set dirty
    var m = _parse_id(item);
    if (m) {
        dirty(m.root, m.row, true);
    }
}


function setup_process_params(root, item){
    for (var key in item.params){
            if (item.params.hasOwnProperty(key)){
            v = item.params[key];
            if (key == 'autocomplete'){
                id = $INFO.getId(root + '#' + item.name);
                $('#' + id).autocomplete(v);
            }
        }
    }
}

function form_setup(root, form_data){
    // do any setting up of the form
    var item
    var id
    for (i=0; i<form_data.fields.length; i++){
            item = form_data.fields[i];
            if (item.params){
                setup_process_params(root, item);
            }
            if (item.type == 'progress'){
                id = $INFO.getId(root + '#' + item.name);
                $('#' + id).progressbar();
            }
    }
    dirty(root, null, false);
}

function get_node(node_name, node_command, node_data, change_state){

    // if change_state then we will set the status to that node
    // this helps prevent front-end confusion
    if (change_state){
        var root = 'main'; //FIXME
        $INFO.newState(root);
        $INFO.setState(root, 'node', node_name);
    }

    var info = {node: node_name,
                lastnode: '',  //fixme
                command: node_command };

    if (node_data){
        info.data = node_data;
    }
    $JOB.add(info, {}, 'node', true);
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
            out_row.__root = my_root;
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
            // check we have any linking data
            if(!out_row[form_data.child_id]){
                // get the parent root
                var m = String(root).match(/^(.*)#([^#]*)$/);
                parent_root = m[1];
                parent_id = $INFO.getState(parent_root, 'sent_data')[form_data.parent_id];
                out_row[form_data.child_id] = parent_id;
            }
            out.push(out_row);
        }
    }
    return out;
}

function node_get_form_data(root){
    var form_data = $INFO.getState(root, 'form_data');
    var out = $INFO.getState(root, 'sent_data');
    out.__root = root;
    for (i=0; i<form_data.fields.length; i++){
        item = form_data.fields[i];
        name = item.name;
        if (item.type == 'subform'){
            out[name] = node_get_form_data_rows(root + '#' + name);
        } else {
            id = $INFO.getId(root + '#' + name);
            value = $FORM_CONTROL.get(id, item.type);
            if (typeof value == 'undefined'){
                value = null;
            }
            out[name] = value;
        }
    }
    return out;
}

function node_save(root, command){
    msg('node_save');
    var out = node_get_form_data(root);
    var node =  $INFO.getState(root, 'node');
    get_node(node, '_save', out, false);
}




function node_delete(root, command){
    msg('node_delete');
 //   var form_data = $INFO.getState('#', 'form_data');
    var sent_data = $INFO.getState(root, 'sent_data');
    var node =  $INFO.getState(root, 'node');
    var out = {};
    var id = sent_data.id;
    if (id){
        out.id = id;
    }
    get_node(node, '_delete', out, false);
}


function node_button(item, node, command){
    root = _parse_id(item).root;
    var out = node_get_form_data(root);
    get_node(node, command, out, false);
}


function show_listing(data, node, root){

    $INFO.newState(root);
    var html = '';
    for (i=0; i<data.length; i++){
        item = data[i];
        table = String(item.table);
        next_node = 'test.' + table.substring(0,1).toUpperCase() + table.substring(1,table.length);
        html += '<div class="list">';
        html += '<span class="list_title" ';
        html += 'onclick="node_load(\'n:' + next_node + ':view:__id=' + item.id + '\')"';
        html += '>' + item.table + ' - ' + item.title + '</span></br><span class="list_summary">' + item.summary + '</span></div>';
    }
    $('#' + root).html(html);
}

function search_box(){
    get_node('test.Search','',{q: $('#search').val()}, true);
    return false;
}



function form_show_errors(root, errors){
    // display errors on form for bad rows
    // ensure 'good' rows do not show errors
    var form_root = parse_strip_subform_info(root);
    var form_data = $INFO.getState(form_root, 'form_data');
    for (var field in form_data.fields){
        // ignore subforms
        if (form_data.fields[field].type != 'subform'){
            field_name = form_data.fields[field].name;
            id = $INFO.getId(root + '#' + field_name);
            if (errors && errors[field_name]){
                // there is an error for this field
                $('#' + id).addClass('error');
                $('#' + id + ' + span').remove();
                $('#' + id).after("<span class='field_error'>ERROR: " + errors[field_name] + "</span>");
            } else {
                // field is good
                $('#' + id).removeClass('error');
                $('#' + id + ' + span').remove();
            }
        }
    }
}

function form_save_process_saved(saved){
    // process the saved data
    // store the insered id if needed
    // set the form as clean and remove error css messages etc
    var state_sent_data;
    var inserted_id;
    var div;
    for (var i=0; i<saved.length; i++){
        div = saved[i][0];
        inserted_id = saved[i][1];

        info = _parse_div(div);
        // update the state info for this data
        // we want to check the correct id was updated
        // and store if it is new
        state_sent_data = $INFO.getState(info.root, 'sent_data');
        if (info.row === null){
            // single form
            if (state_sent_data && state_sent_data.id){
                // check correct record
                if (state_sent_data.id != inserted_id){
                     alert('data coruption on save');
                }
            } else {
                state_sent_data.id = inserted_id;
            }
        } else {
            // continuous or grid
            if (state_sent_data[info.row]){
                // check have correct record
                if (state_sent_data[info.row].id != inserted_id){
                    alert('data coruption on save continuous');
                }
            } else {
                // this is a new save so lets add the id to the state data
                state_sent_data[info.row] = {id: inserted_id};
            }
        }
        // remove any error messages/css etc
        form_show_errors(div, null);
        // we want to mark the form as clean
        dirty(info.root, info.row, false);
    }
}

function form_save_process_errors(errors){
    // this will get each of the errors for a form div
    // and show them on the form
    for (var form_root in errors){
        if (errors.hasOwnProperty(form_root)){
            form_show_errors(form_root, errors[form_root]);
        }
    }
}

function update_status(root, data){

    if (data && data.percent === null){
         data.percent = 0;
    }
    var form_root = parse_strip_subform_info(root);
    var form_data = $INFO.getState(form_root, 'form_data');
    for (var field in form_data.fields){
        // ignore subforms
        if (form_data.fields[field].type != 'subform'){
            field_name = form_data.fields[field].name;
            id = $INFO.getId(root + '#' + field_name);
            if (data[field_name]){
                if (form_data.fields[field].type == 'info'){
                    $('#' + id).html(data[field_name]);
                }
                if (form_data.fields[field].type == 'progress'){
                    $('#' + id).progressbar('option', 'value', data[field_name]);
                }
            }
        }
    }
}

function get_status(node, root, call_string){
    var current_node = $INFO.getState(root, 'node');
    if (node == current_node){
        node_call_from_string(call_string, false);
    }
}

function job_processor_status(data, node, root){

    if (node == $INFO.getState(root, 'node')){
        // display the message form if it exists
        if (data.form){
            $('#' + root).html(node_generate_html(data.form, null, root));
            form_setup(root, data.form);
            $INFO.setState(root, 'node', node);
        }
        // show info on form
        if (data.status){
            update_status(root, data.status);
        }
        // set data refresh if job not finished
        if (!data.status || !data.status.end){
            status_timer = setTimeout("get_status('" + node + "','" + root + "','/n:" + node + ":status:id=" + data.jobId + "')",1000);
        }
    }
}

bookmark_array = [];
BOOKMARKS_SHOW_MAX = 3;
BOOKMARK_ARRAY_MAX = 3;

function bookmark_add(link, title){
    // remove the item if already in the list
    for (var i=0; i<bookmark_array.length; i++){
        if (bookmark_array[i][0]==link){
            bookmark_array.splice(i, 1);
            break;
        }
    }
    // trim the array if it's too long
    if (bookmark_array.length >= BOOKMARK_ARRAY_MAX){
        bookmark_array.splice(BOOKMARK_ARRAY_MAX - 1, 1);
    }
    bookmark_array.unshift([link, title]);
    bookmark_display();
}

function bookmark_display(){
    var html = '<ol>';
    for(var i=0; i<bookmark_array.length && i<BOOKMARKS_SHOW_MAX; i++){
        html += '<li>';
        html += '<span onclick="node_load(\'' + bookmark_array[i][0] + '\')">';
        html += bookmark_array[i][1] + '</span>';
        html += '</li>';
    }
    html += '</ol>';

    $('#bookmarks').html(html);
}

function page_build_section_links(data){
    var html = '<ul>';
    for (var i=0; i<data.length; i++){
        html += '<li><a href="#/' + data[i].link + '">';
        html += data[i].title;
        html += '</a></li>'
    }
    html += '</ul>';
    return html;
}


function page_build_section(data){
    var html = '<div class="page_section">';
    html += '<div class="page_section_title">' + data.title + '</div>';
    html += '<div class="page_section_summary">' + data.summary + '</div>';
    html += page_build_section_links(data.options)
    html += "</div>";
    return html
}

function page_build(data){
    var html = '';
    for (var i=0; i<data.length; i++){
        html += page_build_section(data[i]);
    }
    return html;
}
fn = function(packet, job){
     var root = 'main'; //FIXME

     var title = packet.data.title;
     if (title){
         $.address.title(title);
     }

    var bookmark = packet.data.bookmark;
    if (bookmark){
        bookmark_add(bookmark, title);
    }
     switch (packet.data.action){
         case 'redirect':
             var link = packet.data.link;
             if (link){
                 node_load('n:' + link);
             }
             break;
         case 'html':
             $('#' + root).html(packet.data.data.html);
             break;
         case 'page':
            //alert($.toJSON(packet.data.data));
            $('#' + root).html(page_build(packet.data.data));
            break;
         case 'form':
             form = packet.data.data.form;
             data = packet.data.data.data;
             $('#' + root).html(node_generate_html(form, data, root));
             $INFO.setState(root, 'node', packet.data.node);
             form_setup(root, form);
             break;
         case 'save_error':
            data = packet.data.data;
            // clear form items with no errors
            break;
         case 'save':
            data = packet.data.data;
            // errors
            if (data.errors){
                form_save_process_errors(data.errors);
            }
            // saved records
            if (data.saved){
                form_save_process_saved(data.saved);
            }
            break;
         case 'general_error':
            alert(packet.data.data);
            break;
         case 'listing':
            show_listing(packet.data.data, packet.data.node, root);
            break;
        case 'status':
            job_processor_status(packet.data.data, packet.data.node, root);
            break;
    }
};

$JOB.addPacketFunction('node', fn);

