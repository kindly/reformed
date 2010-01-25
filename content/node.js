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
    // as we are reloading the page make sure everything has blured
    itemsBlurLast();
    var link = $.address.value();
    node_call_from_string(link, true, true);
}


function node_load(arg){
/*
    force a page load of the node
*/
    // as we are reloading the page make sure everything has blured
    itemsBlurLast();
    if ($.address.value() == '/' + arg){
        // the address is already set so we need to force the reload
        // as changing the address will not trigger an event
        node_call_from_string(arg, true, true);
    } else {
        // sets the address which then forces a page load
        var link = arg.split(':');
        if (link[2].substring(0,1) == '_'){
            node_call_from_string(arg, true, false);
        } else {
            $.address.value(arg);
        }
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
    var x;
    var s;
    for (var i=0; i<args.length; i++){
        x = args[i];
        s = x.split('=');
        if (s.length == 2){
            out[s[0]] = s[1];
        }
    }
    return out;
}


function _wrap(arg, tag, my_class){
    // this wraps the item in <tag> tags
    if (my_class){
        return '<' + tag + ' class="' + my_class + '" >' + arg + '</' + tag + '>';
    } else {
        return '<' + tag + '>' + arg + '</' + tag + '>';
    }
}








function _parse_div(item){
    // parse  root
    // or      root(row)
    msg('_parse_div');
    var m = String(item).match(/^([^\(]*)(\((\d+)\))?$/);
    if(m){
        var grid;
        var root = m[1] ;
        if (root === undefined){
            root = '';
        }
        var row = m[3];
        if (row !== undefined && row !== ''){
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
        if (root === undefined){
            root = '';
        }
        var row = m[3];
        if (row !== undefined && row !== ''){
            row = parseInt(row, 10);
            grid = true;
        } else {
            row = null;
            grid = false;
        }
        var control = m[4];
        if (control === undefined || control === ''){
            control = null;
        }
        var div;
        if (row !== null){
            div = root + '(' + row + ')';
        } else {
            div = root;
        }
        return {root:root,
                div:div,
                row:row,
                control:control,
                grid:grid};
    } else {
        alert("something went wrong with the item parser");
        return null;
    }
}

function _parse_id(id){

    var item_id = $INFO.getReverseId(id);
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
    var form_info = $INFO.getState(root, 'form_info');
    if (!form_info.form_type || form_info.form_type.form_type != 'action'){
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
                 if (state){
                    if (form_info.clean_rows.length-1 == row){
                        // this is the last row so we will add a new row
                        add_form_row(root, form_info.form_type);
                    }
                }
            }
            form_info.clean_rows[row] = !state;
        }
        if(state){
            if(update){
                $(my_root).addClass("dirty");
                $(my_root + '__info').html('D');
            }
        } else {
            $(my_root).removeClass("dirty");
        }
    }
}

function move_row(root, row, control){
    var id = '#' + $INFO.getId(root + '(' + row + ')#' + control);
    msg(id);
    itemsBlurLast();
    $(id).focus().select();
}

function keyDown(item, event){
    // the default onkeydown event
    // used to move up and down rows with arrow keys in grids
    if (event){
        var m = _parse_id(item.id);
        if (m){
            var key = getKeyPress(event);
            msg(key.code);
            // moving around between cells
            if (key.code == 38 && m.row>0){
                // up arrow
                move_row(m.root, m.row -1, m.control);
            } else {
                if (key.code == 40){
                    // down arrow
                    // // FIXME want to not just keep creating new rows
                    move_row(m.root, m.row + 1, m.control);
                }
            }
            // [NULL]
            // use Ctl+Space to toggle NULL values
            if (key.code == 32 && event.ctrlKey){
                if ($('#' + item.id).attr('isnull') == 'true'){
                    $('#' + item.id).attr('isnull', 'false');
                } else {
                    $('#' + item.id).attr('isnull', 'true');
                    $('#' + item.id).val('');
                }
            }
        }
    }
}


function itemChanged(item, update_control){

    msg('itemChanged');
    var m = _parse_id(item.id);
    if (m) {
        var errors;
        // validate stuff
        var form_data = $INFO.getState(m.root, 'form_info').form_data;
        var dont_update = true;
        if (update_control === true){
            dont_update = false;
        }
        var value = $FORM_CONTROL.get(item.id, form_data.items[m.control].type, dont_update);
        if (form_data.items[m.control].params && form_data.items[m.control].params.validation){
            var rules = form_data.items[m.control].params.validation;
            errors = validate(rules, value, dont_update);
        } else {
            errors = null;
        }

        form_show_errors_for_item(m.div, m.control, errors);

        var sent_data = $INFO.getState(m.root, 'sent_data');
        if (m.row !== null){
            if (sent_data[m.row]){
                sent_data = sent_data[m.row];
            } else {
                sent_data = {};
            }
        }
        // dirty
        var my_dirty;
        if (sent_data[m.control] && value != sent_data[m.control]){
            my_dirty = true;
        } else {
            // check all fields are clean
            var id;
            my_dirty = false;
            for (var i=0; i <form_data.fields.length; i++){
                id = $INFO.getId(m.div + '#' + form_data.fields[i].name);
                value = $FORM_CONTROL.get(id, form_data.fields[i].type, true);
                if (value != sent_data[form_data.fields[i].name]){
                    my_dirty = true;
                    break;
                }
            }
        }
        // FIXME can we only change if needed
        if (my_dirty){
            dirty(m.root, m.row, true);
        } else {
            dirty(m.root, m.row, false);
        }
    }
}


function setup_process_params(root, item){
    var value;
    var options;
    var id;
    for (var key in item.params){
            if (item.params.hasOwnProperty(key)){
            value = item.params[key];
            if (key == 'autocomplete'){
                if (item.params.auto_options){
                    options = item.params.auto_options;
                } else {
                    options = {};
                }
                id = $INFO.getId(root + '#' + item.name);
                $('#' + id).autocomplete(value, options);
            }
        }
    }
}

function form_setup(root, form_data){
    // do any setting up of the form
    var item;
    var id;

    var form_type = $INFO.getState(root, 'form_info').form_type;
    if (form_type == 'grid'){
        $('#' + $INFO.getId(root) + ' table').grid(form_data);
    }
    for (var i=0; i<form_data.fields.length; i++){
            item = form_data.fields[i];
            if (item.params){
                setup_process_params(root, item);
            }
            if (item.type == 'subform'){
                var rows = $INFO.getState(root + '#' + item.name, 'form_info').clean_rows.length;
                if (rows){
                    for (var j = 0; j<rows; j++){
                        form_setup(root + '#' + item.name + '(' + j + ')',form_data.items[item.name].params.form);
                    }
                }
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

    if (bookmark_array.length === 0){
        info.get_bookmarks = true
    }

    $JOB.add(info, {}, 'node', true);
}

function get_node_return(node_name, node_command, node_data, $obj, obj_data){
    // works like get_node but adds a jquery item to call on the return
    // we also drop the state stuff as we will deal with that better
    // when needed
    var info = {node: node_name,
                lastnode: '',  //fixme
                command: node_command };

    if (node_data){
        info.data = node_data;
    }
    $JOB.add(info, {obj : $obj, obj_data : obj_data}, 'node', true);
}


function node_get_form_data_for_row(form_info, row, root){
    var my_root;
    var value;
    var name;
    var item;
    var id;
    var data_changed = false;
    var data_error = false;
    var validation;
    var validation_errors = {};
    if (!form_info.clean_rows[row]){
        // the row is dirty so needs to be saved
        var out_row = $INFO.getState(root, 'sent_data')[row];
        if (out_row === undefined){
            out_row = {};
        }
        my_root = root + '(' + row + ')';
        out_row.__root = my_root;
        for (var i=0; i<form_info.form_data.fields.length; i++){
            item = form_info.form_data.fields[i];
            name = item.name;
            id = $INFO.getId(my_root + '#' + name);
            value = $FORM_CONTROL.get(id, item.type);
            if (value === undefined){
                value = null;
            }
            // only care if the value has changed
            if (out_row[name] != value){
                if (item.params && item.params.validation){
                    // validate the item
                    validation = validate(item.params.validation, value);
                    if (validation.length > 0){
                        validation_errors[name] = validation;
                        data_error = true;
                    } else {
                        out_row[name] = value;
                        data_changed = true;
                    }
                } else {
                    // there are no validation rules so it must be ok
                    out_row[name] = value;
                    data_changed = true;
                }
            }
        }
        // check we have any linking data
        if(!out_row[form_info.form_data.child_id]){
            // get the parent root (we get no match if we are a top level form)
            var m = String(root).match(/^(.*)#([^#]*)$/);
            if (m){
                var parent_root = m[1];
                var parent_id = $INFO.getState(parent_root, 'sent_data')[form_info.form_data.parent_id];
                if (parent_id){
                out_row[form_info.form_data.child_id] = parent_id;
                }
            }
        }
        // any errors?
        if (data_error){
            return {errors: validation_errors};
        }

        // only return data if things have changed
        if (data_changed){
            return {data: out_row};
        }
    }
    // row was clean so return nothing
    return null;
}

function node_get_form_data_rows(root){
    var form_info = $INFO.getState(root, 'form_info');
    var out = [];
    var row_data;
    for(var row=0; row<form_info.clean_rows.length; row++){
        row_data = node_get_form_data_for_row(form_info, row, root);
        // if we get {data:...} back we have a good row
        // {errors:...} means the row did not validate
        if (row_data && row_data.data){
            out.push(row_data.data);
        } else {
            if (row_data && row_data.errors){
                alert(row_data.errors);
            }
        }
    }
    return out;
}

function node_get_form_data(root){
    var form_data = $INFO.getState(root, 'form_info').form_data;
    if (form_data.params && form_data.params.form_type && form_data.params.form_type == 'grid'){
        // this is a continuous style form
        return {data: node_get_form_data_rows(root)};
    } else {
        // this is a 'single style form'
        var out = $INFO.getState(root, 'sent_data');
        out.__root = root;
        var value;
        var name;
        var item;
        var id;
        for (var i=0; i<form_data.fields.length; i++){
            item = form_data.fields[i];
            name = item.name;
            if (item.type == 'subform'){
                out[name] = node_get_form_data_rows(root + '#' + name);
            } else {
                id = $INFO.getId(root + '#' + name);
                value = $FORM_CONTROL.get(id, item.type);
                if (value === undefined){
                    value = null;
                }
                out[name] = value;
            }
        }
        return out;
    }
}

function link_process(item, link){
    var div = _parse_id(item.id).div;
    var info = link.split(':');
    // we will call the function given by info[1]
    if (info[1] && typeof this[info[1]]== 'function'){
        this[info[1]](div);
    } else {
        alert(info[1] + ' is not a function.');
    }
}

function node_save(root, command){
    msg('node_save');
    $('#main').find('div').data('command')('save'); //FIXME these want to be found properly
/*
    var out = node_get_form_data(root);

    var node =  $INFO.getState(root, 'node');
    var params = $INFO.getState(root, 'form_data').params;
    if (params && params.extras){
        for (var extra in params.extras){
            if (params.extras.hasOwnProperty(extra)){
                out[extra] = params.extras[extra];
            }
        }
    }
    get_node(node, '_save', out, false);
    */
}

function node_grid_save(root, row){

  //  var form_data = $INFO.getState(root, 'form_data');
    var form_info = $INFO.getState(root, 'form_info');
    var row_data;
    row_data = node_get_form_data_for_row(form_info, row, root);
    // if {data:...} we have data
    // {errors:...} there was a validation error
    if (row_data && row_data.data){
        var out = {};
        out.data = [row_data.data];
        var params = form_info.form_data.params;
        if (params && params.extras){
            for (var extra in params.extras){
                if (params.extras.hasOwnProperty(extra)){
                    out[extra] = params.extras[extra];
                }
            }
        }
        var node =  $INFO.getState(root, 'node', true);
        get_node(node, '_save', out, false);
    } else {
        if (row_data && row_data.errors){
            form_show_errors(root + '(' + row + ')', row_data.errors);
        } else {
            // nothing to save so mark it as clean
            dirty(root, row, false);
            $('#' + $INFO.getId(root + '(' + row + ')') + '__info').html('&nbsp;');
        }
    }
  //  return out;


}
function autosave(div){
  //  msg('autosave: ' + div);
    // FIXME this is a dirty hack
    // if this is a subform we should just save the row that is dirty,
    // instead we are just saving the main record as this will save dirty rows
    // as part of it's job. This means all the data is resaved etc.
    // I want to just save the subform row but this needs more
    // work but for now this will do.
    if (div.indexOf('#')>0){
        div = div.substring(0, div.indexOf('#'));
    }

    msg('autosave: ' + div);
    var info = _parse_div(div);
    if (info.grid){
        // this is a grid
        node_grid_save(info.root, info.row);
    } else {
        // this is the main form
        node_save(div);
    }


}


function node_delete(root, command){
    msg('node_delete');
    var parsed_root = _parse_div(root);
    var my_root = parsed_root.root;
    var sent_data = $INFO.getState(my_root, 'sent_data');
    // FIXME we don't have the node for subforms yet
    // do we set them up with the correct node or backtrack to their parent?
    var node =  $INFO.getState(my_root, 'node', true);
    var out = {__root: root};
    var id;
    var __id;
    if (parsed_root.row === null){
        // single form
        id = sent_data.id;
        __id = sent_data.__id;
    } else {
        // continuous form
        if (sent_data[parsed_root.row]){
            id = sent_data[parsed_root.row].id;
            __id = sent_data[parsed_root.row].__id;
        } else {
            // this row has not been saved so let's just hide it
            // we need to make it clean too so it won't trigger a save
            var state = $INFO.getState(my_root, 'form_info');
            state.clean_rows[parsed_root.row] = true;
            $('#' + $INFO.getId(root)).hide();
        }
    }

    if (__id){
        out.__id = __id;
    }
    if (id){
        out.id = id;
    }
    var form_data = $INFO.getState(my_root, 'form_info').form_data;
    if (form_data && form_data.params && form_data.params.id_field){
        var id_field = form_data.params.id_field;
        out[id_field] = sent_data[parsed_root.row][id_field];
    }

    if (form_data && form_data.table_name){
        out.table_name = form_data.table_name;
    }

    var params = form_data.params;
    if (params && params.extras){
        for (var extra in params.extras){
            if (params.extras.hasOwnProperty(extra)){
                out[extra] = params.extras[extra];
            }
        }
    }
    get_node(node, '_delete', out, false);
}


function node_button(item, node, command){
    var out = $('#main div.f_form').data('command')('get_form_data');
    get_node(node, command, out, false);
}

function node_button_input_form(item, node, command){
    var out = $('#main div.INPUT_FORM').data('command')('get_form_data');
    get_node(node, command, out, false);
}



function search_box(){
    var node = 'n:test.Search::q=' + $('#search').val();
    node_load(node);
    return false;
}


function tooltip_add(jquery_obj, text){
    jquery_obj.attr('title', text);
    jquery_obj.tooltip();
}


function tooltip_clear(jquery_obj){
    jquery_obj.attr('title', '');
    jquery_obj.tooltip();
}

function item_add_error(jquery_obj, text, tooltip){
    jquery_obj.addClass('error');
    if (tooltip){
        tooltip_add(jquery_obj, text.join(', '));
    } else {
        var next = jquery_obj.next();
        if (next.is('span')){
            next.remove();
        }
        jquery_obj.after("<span class='field_error'>ERROR: " + text.join(', ') + "</span>");
    }
}

function item_remove_error(jquery_obj){
    jquery_obj.removeClass('error');
    var next = jquery_obj.next();
    if (next.is('span')){
        next.remove();
    } else {
        tooltip_clear(jquery_obj);
    }
}


function form_show_errors_for_item(root, field_name, errors){
    var id = $INFO.getId(root + '#' + field_name);
    var jquery_obj = $('#' + id);
    if (errors && errors.length > 0){
        use_tooltip = (root.indexOf('(') > -1);
        item_add_error(jquery_obj, errors, use_tooltip);
    } else {
        item_remove_error(jquery_obj)
    }
}


function form_show_errors(root, errors){
    // display errors on form for bad rows
    // ensure 'good' rows do not show errors
    msg('SHOW_ERRORS' + root + $.toJSON(errors));
    var form_root = parse_strip_subform_info(root);
    var form_info = $INFO.getState(form_root, 'form_info');
    var field_name;
    var id;
    var jquery_obj;
    // show error if grid form
    // FIXME this is not a very good test as it gets continous forms too
    if (root.indexOf('(') > -1){
        var jquery_obj = $('#' + $INFO.getId(root) + '__info');
        if (errors){
            jquery_obj.html('E');
            var error = ($.toJSON(errors)).replace(/"/g,'&quot;');
            tooltip_add(jquery_obj, error);
        } else {
            jquery_obj.html('&nbsp;');
            tooltip_clear(jquery_obj);
        }
    }
    var use_tooltip = (root.indexOf('(') > -1);
    if (form_info && form_info.form_data){
        for (var field in form_info.form_data.fields){
            // ignore subforms
            if (form_info.form_data.fields[field].type != 'subform'){
                field_name = form_info.form_data.fields[field].name;
                id = $INFO.getId(root + '#' + field_name);
                jquery_obj = $('#' + id);
                if (errors && errors[field_name]){
                    item_add_error(jquery_obj, [errors[field_name]], use_tooltip)
                } else {
                    item_remove_error(jquery_obj)
                }
            }
        }
    }
}


function form_process_deleted(deleted){
    // FIXME should check that this is ok to delete
    var root;
    var info;
    for (var i=0; i<deleted.length; i++){
        root = deleted[i].__root;
        info = _parse_div(root);

        // we want to mark the form as clean
        dirty(info.root, info.row, false);
        $('#' + $INFO.getId(root)).hide();
    }

}


function form_save_process_saved(saved){
    // process the saved data
    // store the insered id if needed
    // set the form as clean and remove error css messages etc
    var state_sent_data;
    var inserted_id;
    var div;
    var version;
    var info;

    for (var i=0; i<saved.length; i++){
        div = saved[i][0];
        inserted_id = saved[i][1];
        version = saved[i][2];

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
                state_sent_data._version = version;
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
                state_sent_data[info.row] = {id: inserted_id, _version: version};
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


function get_status(call_string){
    node_call_from_string(call_string, false);
}


var status_timer;

function job_processor_status(data, node, root){
    // display the message form if it exists
    if (data.form){
     //   data.form = $.Util.FormDataNormalize(data.form);
        $('#' + root).status_form();
    }
    // show info on form
    if (data.status){
        $('div.STATUS_FORM').data('command')('update', data.status);
    }
    // set data refresh if job not finished
    if (!data.status || !data.status.end){
        status_timer = setTimeout("get_status('/n:" + node + ":status:id=" + data.jobId + "')",1000);
    }
}

var bookmark_array = [];
var BOOKMARKS_SHOW_MAX = 6;
var BOOKMARK_ARRAY_MAX = 6;

function bookmark_add(bookmark){
    // remove the item if already in the list
    for (var i=0; i<bookmark_array.length; i++){
        if (bookmark_array[i].bookmark==bookmark.bookmark){
            bookmark_array.splice(i, 1);
            break;
        }
    }
    // trim the array if it's too long
    if (bookmark_array.length >= BOOKMARK_ARRAY_MAX){
        bookmark_array.splice(BOOKMARK_ARRAY_MAX - 1, 1);
    }
    bookmark_array.unshift(bookmark);
}

function bookmark_display(){
    categories = [];
    category_items = {};

    for(var i=0; i<bookmark_array.length && i<BOOKMARKS_SHOW_MAX; i++){
        entity_table = bookmark_array[i].entity_table
        if (category_items[entity_table] === undefined){
            categories.push(entity_table);
            category_items[entity_table] = []
        }

        html  = '<li class ="bookmark-item-' + entity_table + '">';
        html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
        html += bookmark_array[i].title + '</span>';
        html += '</li>';

        category_items[entity_table].push(html);
    }

    var html = '<ol class = "bookmark">';
    for(var i=0; i<categories.length; i++){
        category = categories[i];
        html += '<li class ="bookmark-category-title-' + category + '">';
        html += category;
        html += '</li>';
        html += '<ol class ="bookmark-category-list-' + category + '">';
        html += category_items[category].join('\n');
        html += '</ol>';
    }

    html += '</ol>';


/*
    var html = '<ol>';
    for(var i=0; i<bookmark_array.length && i<BOOKMARKS_SHOW_MAX; i++){
        html += '<li>';
        html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
        html += bookmark_array[i].title + '</span>';
        html += '</li>';
    }
    html += '</ol>';
*/


    $('#bookmarks').html(html);
}

function page_build_section_links(data){
    var html = '<ul>';
    for (var i=0; i<data.length; i++){
        html += '<li><a href="#/' + data[i].link + '">';
        html += data[i].title;
        html += '</a></li>';
    }
    html += '</ul>';
    return html;
}


function page_build_section(data){
    var html = '<div class="page_section">';
    html += '<div class="page_section_title">' + data.title + '</div>';
    html += '<div class="page_section_summary">' + data.summary + '</div>';
    html += page_build_section_links(data.options);
    html += "</div>";
    return html;
}

function page_build(data){
    var html = '';
    for (var i=0; i<data.length; i++){
        html += page_build_section(data[i]);
    }
    return html;
}

var current_focus = null;
var current_focus_item = null;

function itemFocus(item){
    var info = _parse_id(item.id);
    if (info.div != current_focus){
        itemsBlurLast();
        msg('FOCUS ' + info.div);
        current_focus = info.div;
    }
    current_focus_item = info.item;
    // deal with [NULL] values
    if ($('#' + item.id).hasClass('null')){
        $('#' + item.id).removeClass('null');
        $('#' + item.id).val('');
        $('#' + item.id).attr('isnull', 'true');

    }
}

function itemBlur(item, blank_is_null){
     if ($('#' + item.id).val() === '' && (blank_is_null || $('#' + item.id).attr('isnull') == "true")){
        $('#' + item.id).addClass('null');
        $('#' + item.id).val('[NULL]');
    } else {
        $('#' + item.id).attr('isnull', 'false');
    }
}

function itemsBlurLast(){
    if (current_focus !== null){
        msg('BLUR ' + current_focus);
        // check if autosave disabled
        var info = _parse_div(current_focus);
        var form_info = $INFO.getState(info.root, 'form_info');
        if (!(form_info && form_info.form_data && form_info.form_data.params && form_info.form_data.params.noautosave && form_info.form_data.params.noautosave == true)){
            autosave(current_focus);
        }
    }
    current_focus = null;

}

function grid_add_row(){
    console.log('add_row');
    $('#main div.GRID').data('command')('add_row');
}


var fn = function(packet, job){
     var root = 'main'; //FIXME

     var title = packet.data.title;
     if (title){
         $.address.title(title);
     }

    var bookmark = packet.data.bookmark;
    if (bookmark){
        if ($.isArray(bookmark)){
            for (i = 0; i < bookmark.length; i++){
               bookmark_add(bookmark[i]);
            }
        } else {
            bookmark_add(bookmark);
        }
        bookmark_display();
    }
    var data;
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
             var form = packet.data.data.form;
             form = $.Util.FormDataNormalize(form, packet.data.node);
             data = packet.data.data.data;
             var paging = packet.data.data.paging;
             if (form.params.form_type == 'grid'){
                $('#' + root).grid(form, data, paging);
             } else if (form.params.form_type == 'action'){
                $('#' + root).input_form(form, data, paging);
             } else {
                $('#' + root).form(form, data, paging);
             }
             break;
         case 'save_error':
            data = packet.data.data;
            // clear form items with no errors
            break;
         case 'save':
            data = packet.data.data;
            if (job && job.obj){
                // copy the obj_data that was saved with the job
                data.obj_data = job.obj_data;
                job.obj.data('command')('save_return', data);
            } else {
                // errors
                if (data.errors){
                    form_save_process_errors(data.errors);
                }
                // saved records
                if (data.saved){
                    form_save_process_saved(data.saved);
                }
            }
            break;
         case 'delete':
            data = packet.data.data;
            if (data.deleted){
                form_process_deleted(data.deleted);
            }
            break;
         case 'general_error':
            alert(packet.data.data);
            break;
        case 'status':
            job_processor_status(packet.data.data, packet.data.node, root);
            break;
    }
};

$JOB.addPacketFunction('node', fn);

