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

    jQuery form plugin

*/




(function($) {
	
$.fn.extend({

	form: function(form_data, grid_data, paging_data){
		$.Form(this, form_data, grid_data, paging_data);
	}

});



$.Form = function(input, form_data, row_data, paging_data){

    $input = $(input)
    // remove any existing items from the input
    $input.children().trigger('custom', ['unbind_all']).remove();

    // make our div that everything will hang off
    var $form = $('<div class="f_form"></div>');
    $input.append($form);

    if (!row_data){
        row_data = {};
    }
    if (!row_data.length){
        $.Form.Build($form, form_data, row_data, paging_data);
        $.Form.Movement($form, form_data, row_data);
        $form.trigger('custom', ['register_events', {}]);
    } else {
        for (var i = 0, n = row_data.length; i < n; i++){
        var $sub = $('<div class="f_form_continuous"></div>');
        $form.append($sub);
        $.Form.Build($sub, form_data, row_data[i], paging_data);
        $.Form.Movement($sub, form_data, row_data[i]);
        }
    }
};

$.Form.Movement = function($input, form_data, row_data){

    function init(){

        // remove any previous bound events
        unbind_all();

        total_fields = form_data.fields.length;
        $input.mousedown(form_mousedown);

        focus();
        if (edit_mode){
            edit_mode_on();
        } else {
            edit_mode_off();
        }
        $input.bind('custom', function (e, type, data){
            custom_event(e, type, data);
        });

        $(document).keydown(keydown);
    }

    function unbind_all(){
        console.log('unbind');
        $input.unbind();
        $(document).unbind('keydown', keydown);
    }

    function save(){
        console.log('save');
        // make the form non-edit
        edit_mode_off();
        if (current.dirty){
            // get our data to save
            var save_data = {};
            for (var item in row_data){
                save_data[item] = row_data[item];
            }
            var copy_of_row_info = {};
            for (var item in row_info){
                save_data[item] = row_info[item];
                copy_of_row_info[item] = row_info[item];
            }
            // any extra data needed from the form
            params = form_data.params;
            if (params && params.extras){
                for (var extra in params.extras){
                    if (params.extras.hasOwnProperty(extra)){
                        save_data[extra] = params.extras[extra];
                    }
                }
            }
            get_node_return('test.AutoFormPlus', '_save', save_data, $input, copy_of_row_info); //FIXME node_name
        }
    }

    function remove_all_errors(){
        // remove error spans
        $input.find('span.f_error').remove();
        // remove any error classes
        $input.find('p.f_error').removeClass('f_error');
    }

    function save_errors(errors){
        remove_all_errors();
        var index;
        var $item;
        for (var field in errors){
            index = form_data.items[field].index;
            $item = $input.find('div').eq(index);
            // add the error span
            $item.append('<span class="f_error">ERROR: ' + errors[field] + '</span>');
            // add error class
            $item.addClass('f_error');
        }
    }

    function save_update(data, obj_data){
        if (row_data.id){
            // check if the id has changed (it shouldn't)
            if (row_data.id != data[1]){
                alert('something went wrong the id has changed during the save');
                return;
            }
        } else {
            // update id
            row_data.id = data[1];
        }
        // update _version
        row_data._version = data[2];

        // update the row_data with the stuff that was saved
        for (var field in obj_data){
            row_data[field] = obj_data[field];
        }

        // form is now clean
        current.dirty = false;
        dirty = false;
        remove_all_errors();
        $input.removeClass('dirty');
        $input.find('span.f_cell.dirty').removeClass('dirty');
    }

    function save_return(data){
        console.log('return');
        console.log(data);
        // errors
        if (data.errors && data.errors.null){
            save_errors(data.errors.null);
        }
        // saves
        if (data.saved){
            save_update(data.saved[0], data.obj_data); // single form so only want first saved item
        }
    }
    function register_events(data, e){
        console.log('registering');
        $.Util.Event_Delegator('register', {keydown:keydown, blur:blur})
        focus();
    }


    function custom_event(e, type, data){
        console.log('event triggered: ' + type);
        if (custom_events[type]){
            custom_events[type](data, e);
        } else {
            alert('event: <' + type + '> has no handler');
        }
    }

    function form_mousedown(e){
        var item = e.target;
        // switch on edit mode if needed
        if (!edit_mode){
            edit_mode_on();
        }
        if (item.nodeName == 'SPAN'){
            var $field = $(item).parent('div');
            var $item = $field.find('span').eq(1);
            // which field?
            field_number = $input.children().index($field);
            selected($item, $field);
        }
        return false;
    }



    function make_editable(){
        // make the cell editable
        var $item = current.$item;
        // is this a complex control?
        var complex_control = (current.field.params && current.field.params.control == 'dropdown');

        if (complex_control){
            for (var item in row_info){
                save_data[item] = row_info[item];
            }
        }
    }

    function form_mousedown(e){
        var actioned = false;
        var item = e.target;
        // switch on edit mode if needed
        if (!edit_mode){
            edit_mode_on();
        }
        if (item.nodeName == 'SPAN'){
            var $field = $(item).parent('div');
            var $item = $field.find('span').eq(1);
            // which field?
            field_number = $input.children().index($field);
            selected($item, $field);
            actioned = true;
        }
        return !actioned;
    }



    function make_editable(){
        // make the cell editable
        var $item = current.$item;
        // is this a complex control?
        var complex_control = (current.field.params && current.field.params.control == 'dropdown');

        if (complex_control){
            $item = $item.find('div.data');
        }

        current.$control = util.make_editable($item, current.field);
        current.value = row_data[current.field.name];
    }

    function check_row_dirty(){
        if (is_empty(row_info)){
            current.dirty = false;
            dirty = false;
            $input.removeClass('dirty');
        }
    }

    function make_normal(){
        // return the item to it's normal state
        var $item = current.$item;
        // is this a complex control?
        var complex_control = (current.field.params && current.field.params.control == 'dropdown');
        if (complex_control){
            $item = $item.find('div.data');
        }
        var value = util.make_normal($item, current.field);

        if (value === current.value){
            // not changed
            current.$item.removeClass('dirty');
            if (row_info[current.field.name]){
                delete row_info[current.field.name];
             }
            check_row_dirty();
        } else {
            // has changed
            row_info[current.field.name] = value;
            if (!dirty){
                $input.addClass('dirty');
                dirty = true;
            }
            current.dirty = true;
            current.$item.addClass('dirty');
        }
        current.$control = undefined;
    }

    function edit_mode_off(){
        // turn off edit mode
        if (current.$item !== undefined && edit_mode){
            make_normal(current.$item);
            current.$item.addClass('f_selected_cell');
            current.$item.removeClass('f_edited_cell');
        }
        edit_mode = false;
    }

    function edit_mode_on(){
        // turn on edit mode
        if (!edit_mode){
            edit_mode = true;
            make_editable(current.$item);
            current.$item.addClass('f_edited_cell');
            current.$item.removeClass('f_selected_cell');
        }
    }
/*
row_blur
row_focus
make_cell_viewable
*/
    function selected($new_item, $new_field){
        // a cell has been selected update as needed
        if ($new_item !== current.$item){
            if (current.$item !== undefined){
                if (edit_mode){
                    make_normal();
                }
                current.$item.removeClass('f_selected_cell');
                current.$item.removeClass('f_edited_cell');

            }
            if($new_field != current.$field){
                if (current.$field !== undefined){
       //             row_blur();
                }
                current.$field = $new_field;
                current.field_number = field_number;
       //         row_focus();
            }

            current.field = form_data.fields[field_number];
            current.$item = $new_item;

            if (edit_mode){
                current.$item.addClass('f_edited_cell');
                make_editable();
            } else {
                current.$item.addClass('f_selected_cell');
            }
        }
    }

    function focus(){
        // put the grid in focus
        move();
    }

    function move(){
        // find the cell and select it
        var $row = $input.find('p').eq(field_number);
        var $item = $row.children().eq(1);
        selected($item, $row);
    }

    function move_down(){
        field_number++;
        if(field_number >= total_fields){
            field_number = total_fields - 1;
        }
        move();
    }

    function move_up(){
        field_number--;
        if(field_number < 0){
            field_number = 0;
        }
        move();
    }

    function undo_field_change(){
        // revert the control to the origional sent value
        if (edit_mode){
            var value = row_data[current.field.name]
            var $item = current.$control;
            $item.val(value);
            make_null($item, (value === null));
        }
    }

    // general key bindings
    var keys = {
 //       '9': tab_right,
 //       '9s': tab_left,
        '38s': move_up,
        '40s': move_down,
        '27' : edit_mode_off,
        '27s' : edit_mode_off

    };

    // these key bindings are only valid in edit mode
    var edit_keys = {
        '13' : edit_mode_off,
        'Uc': undo_field_change
    };

    // these key bindings are only valid in non-edit mode
    var non_edit_keys = {
  //      '39': move_right,
  //      '37': move_left,
        '13' : edit_mode_on,
        '38': move_up,
        '40': move_down
    };
    function keydown(e){
        var key = util.get_keystroke(e);
        if (keys[key] !== undefined){
            keys[key]();
            e.preventDefault();
            return false;
        } else if (!edit_mode && non_edit_keys[key] !== undefined){
            non_edit_keys[key]();
            e.preventDefault();
            return false;
        } else if (edit_mode && edit_keys[key] !== undefined){
            edit_keys[key]();
            e.preventDefault();
            return false;
        } else if (key == '32c'){
            // toggle [NULL]
            null_toggle($(e.target));
            e.preventDefault();
            return false;
        }
    }


    function make_null($item, isnull){
        // mark item as null
        var $item_parent = $item.parent();
        if (!isnull){
            $item_parent.removeClass('null');
        } else {
            $item_parent.addClass('null');
            $item.val('');
        }
    }

    function null_toggle($item){
        // do toggling of [NULL] and ''
        var $item_parent = $item.parent();
        make_null($item, !$item_parent.hasClass('null'));
    }


    // custom events
    var custom_events = {
        'save' : save,
        'save_return' : save_return,
        'unbind_all' : unbind_all
    };


    var edit_mode = false;
    var dirty = false;
    var row_info = {};
    var current = {$control : undefined,
                   $item : undefined,
                   $field : undefined,
                   field : undefined,
                   dirty : false,
                   field_number : undefined,
                   value : undefined};
    var field_number = 0;
    var total_fields;
    var util = $.Util;
    
    init();

};


$.Form.Build = function($input, form_data, row_data, paging_data){

    function build_input(item){
            var html = [];
            html.push('<div>');

            // label
            html.push('<span class="form_label">' + item.title + '</span>');

            if (row_data && row_data[item.name] !== undefined){
                value = row_data[item.name];
            } else {
                if (item.params && item.params['default']){
                    value = item.params['default'];
                } else {
                    value = null;
                }
            }
            // correct data value if needed
            switch (item.type){
                case 'DateTime':
                case 'Date':
                    if (value !== null){
                        value = Date.ISO(value).toLocaleDateString();
                    }
                    break;
                default:
                    value = HTML_Encode(value);
            }
            if (item.params && item.params.control == 'dropdown'){
                if (value === null){
                    html.push('<span class="f_cell null complex"><span class="but_dd"/><span class="data">[NULL]</span></span>');
                } else {
                    html.push('<span class="f_cell complex"><span class="but_dd"/><span class="data">' + value + '</span></span>');
                }
            }
            else {
                if (value === null){
                    html.push('<span class="f_cell null">[NULL]</span>');
                } else {
                    html.push('<span class="f_cell">' + value + '</span>');
                }
            }
            html.push('</div>');
            return html.join('');

    }
    function link(value){
        var split = value.split("|");
        var link = split.shift();
        value = split.join('|');
  //      var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
        var x = '';
        if (link.substring(0,1) == 'n'){
            x += '<a href="#" onclick="node_load(\'' + link + '\');return false">' + (value ? value : '&nbsp;') + '</a>';
        }
        if (link.substring(0,1) == 'd'){
            x += '<a href="#" onclick ="link_process(this,\'' + link + '\');return false;">' + (value ? value : '&nbsp;') + '</a>';
        }
        return x;
    }

    function build_control(item){
        var html = [];
        var value = row_data[item.name];

        html.push('<div>');
        switch (item.params.control){
            case 'info':
                if (value){
                    html.push(value);
                }
                break;
            case 'link':
                html.push(link(value));
                break;
            case 'link_list':
                for (var i = 0, n = value.length; i < n; i++){
                    html.push(link(value[i]));
                    html.push(' ');
                }
                break;
            case 'subform':
                html.push('<div class="SUBFORM"></div>');
                subforms.push({item: item, data: value})
                break;
            default:

                html.push(item.params.control);
        }
        html.push('</div>');

        return html.join('');
    }

    function build_form(){
        var html = [];
        num_fields = form_data.fields.length;
        for (var i = 0; i < num_fields; i++){
            item = form_data.fields[i];
            if (!(item.params && item.params.control)){
                html.push(build_input(item));
            } else {
                html.push(build_control(item));
            }
        }
        return html.join('');
    }

    var subforms = [];
    var HTML_Encode = $.Util.HTML_Encode;
    $input.html(build_form());

    // subforms
    var $subforms = $input.find('div.SUBFORM');
    for (var i = 0, n = subforms.length; i < n; i ++){
        $subforms.eq(i).form(subforms[i].item.params.form, subforms[i].data);
    }

};

})(jQuery);
