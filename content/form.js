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




    // remove any previous bound events
    $(document).unbind();
    $(input).unbind();

    $.Form.Build(input, form_data, row_data, paging_data);
    $.Form.Movement(input, form_data, row_data);
};

$.Form.Movement = function(input, form_data, row_data){

    function init(){

        total_fields = form_data.fields.length;
        $input.mousedown(form_mousedown).keydown(keydown);

        focus();
        if (edit_mode){
            edit_mode_on();
        } else {
            edit_mode_off();
        }
        $input.bind('save', function (){
            save();
        });
    }

    function save(){
        console.log('save');
        if (current.dirty){
            // get our data to save
            var save_data = {};
            for (var item in row_data){
                save_data[item] = row_data[item];
            }
            for (var item in row_info){
                save_data[item] = row_info[item];
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
            console.log(save_data);
            get_node('test.AutoFormPlus', '_save', save_data, false);
        }
    }

    function form_mousedown(e){
        var item = e.target;
        // switch on edit mode if needed
        if (!edit_mode){
            edit_mode_on();
        }
        if (item.nodeName == 'SPAN'){
            var $field = $(item).parent('p');
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
            var $field = $(item).parent('p');
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
        if (is_empty(row_info[current.row])){
            current.dirty = false;
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
        $(document).keydown(keydown);
    }

    function edit_mode_on(){
        // turn on edit mode
        if (!edit_mode){
            edit_mode = true;
            $(document).unbind('keydown', keydown);
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

    // general key bindings
    var keys = {
 //       '9': tab_right,
 //       '9s': tab_left,
        '38s': move_up,
        '40s': move_down,
        '13' : edit_mode_on,
        '27' : edit_mode_off,
        '27s' : edit_mode_off

    };

    // these key bindings are only valid in non edit mode
    var non_edit_keys = {
  //      '39': move_right,
  //      '37': move_left,
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
        } else if (key == '32c'){
            // toggle [NULL]
            null_toggle($(e.target));
        }
    }

    function null_toggle($item){
        // do toggling of [NULL] and ''
        var $item_parent = $item.parent();
        if ($item_parent.hasClass('null')){
            $item_parent.removeClass('null');
        } else {
            $item_parent.addClass('null');
            $item.val('');
        }
    }

    var $input = $(input);
    var edit_mode = false;
    var row_info = [];
    var current = {$control : undefined,
                   $item : undefined,
                   $field : undefined,
                   field : form_data.fields[0],
                   dirty : false,
                   field_number : undefined,
                   value : undefined};
    var field_number = 0;
    var total_fields;
    var util = $.Util;
    
    init();

};


$.Form.Build = function(input, form_data, row_data, paging_data){

    function build_form(){
        var html = [];
        num_fields = form_data.fields.length;
        for (var i = 0; i < num_fields; i++){
            item = form_data.fields[i];

            html.push('<p>');

            // label
            html.push('<span class="form_label">' + item.title + '</span>');

            if (row_data && row_data[item.name] !== null){
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
                    value = Date.ISO(value).toLocaleDateString();
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
            html.push('</p>');
        }
        return html.join('');
    }

    var HTML_Encode = $.Util.HTML_Encode;
    $(input).html(build_form());

};

})(jQuery);
