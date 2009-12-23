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

    jQuery grid resize plugin

*/


(function($) {
	
$.fn.extend({
	grid: function(form_data, grid_data) {
		
		$.Grid(this, form_data, grid_data);
	}
});

$.Grid = function(input, form_data, grid_data){

    function start_grid_resize(e){
        // begin resizing
        $(document).mousemove(move_grid_resize).mouseup(end_grid_resize);
        return false;
    }

    function end_grid_resize(){
        // end resizing
        $(document).unbind('mousemove', move_grid_resize);
        $(document).unbind('mouseup', end_grid_resize);
        return false;
    }


    function move_grid_resize(e){
        // resize
        var pos = $grid.offset();
        var new_height = e.clientY - pos.top;
        var new_width = e.clientX - pos.left;
        if (new_width < $.Grid.MIN_GRID_WIDTH){
            new_width = $.Grid.MIN_GRID_WIDTH;
        }
        if (new_height < $.Grid.MIN_GRID_HEIGHT){
            new_height = $.Grid.MIN_GRID_HEIGHT;
        }
        // only update if we need to resize
        if (grid_size.width != new_width || grid_size.height != new_height){
            grid_size.width = new_width;
            grid_size.height = new_height;
            // remove any pending resize
            if (resize_grid_timeout){
                clearTimeout(resize_grid_timeout);
            }
            resize_grid_timeout = setTimeout(resize_grid, 25);
        }
        return false;
    }


    function start_column_resize(e){
        // begin resizing
        $drag_col = $(e.target).parent();
        drag_col = $drag_col.parent().children().index($drag_col);
        $(document).mousemove(move_column_resize).mouseup(end_column_resize);
        return false;
    }

    function end_column_resize(){
        // end resizing
        $(document).unbind('mousemove', move_column_resize);
        $(document).unbind('mouseup', end_column_resize);
        $drag_col = null;
        return false;
    }

    function move_column_resize(e){
        // resize
        if ($drag_col){
            var new_width = Math.floor(e.clientX - $drag_col.offset().left + 15);
            if (new_width < $.Grid.MIN_COLUMN_SIZE){
                new_width = $.Grid.MIN_COLUMN_SIZE;
            }
            column_widths[drag_col] = new_width;
            // remove any pending resize
            if (resize_column_timeout){
                clearTimeout(resize_column_timeout);
            }
            resize_column_timeout = setTimeout(resize_table_columns, 25);
        }
        return false;
    }


    function auto_resize(e){
        var $item = $(e.target).parent();
        var col;
        if ($item[0].nodeName == 'TH'){
            col = $item.parent().children().index($item);
        }
        column_widths[col] = 100;
        resize_table_columns();
    }


    function get_column_widths(){
        var $cols_main = $main.find('tr').eq(0).find('td');
        var $cols_head = $head.find('th');
        for (var i = 0, n = $cols_head.size(); i < n; i++){
            // get column widths for the headers and main table
            column_widths_main[i] = $cols_main.eq(i).width();
            column_widths_header[i] = $cols_head.eq(i).width();
            // store the higher value in column_widths
            if (column_widths_main[i] > column_widths_header[i]){
                column_widths[i] = column_widths_main[i];
            } else {
                column_widths[i] = column_widths_header[i];
            }
        }
    }
    function resize_grid(){
        var width = grid_size.width;
        var height = grid_size.height;
        $grid.width(width).height(height);
        //console.log($grid_head);
        $grid_main.css({top : $.Util.Size.GRID_HEADER_H,
                        left : $.Grid.SIDE_COLUMN_WIDTH,
                        width : width - $.Grid.SIDE_COLUMN_WIDTH,
                        height : height - $.Util.Size.GRID_HEADER_H});
        $grid_head.css({top:0, left:$.Grid.SIDE_COLUMN_WIDTH});
        $grid_head.width(width - $.Grid.SIDE_COLUMN_WIDTH - $.Util.Size.SCROLLBAR_WIDTH);

        $grid_side.css({top:$.Util.Size.GRID_HEADER_H, left:0});
        $grid_side.height(height - $.Util.Size.GRID_HEADER_H - $.Util.Size.SCROLLBAR_WIDTH);
        $grid_side.width($.Grid.SIDE_COLUMN_WIDTH);

        $grid_resizer.css({top:height - 15,
                           left: width - 15});

       // $grid.
    }

    function resize_table_columns(){
        // resize table
        var t_width = 0;
        for (var i = 0, n = column_widths.length; i < n; i++){
            t_width += column_widths[i];
        }
        $head.width(t_width);
        $main.width(t_width);

        // restore column widths
        var $head_cols = $head.find('th');
        var $main_cols = $main.find('tr').eq(0).find('td');
        for (i = 0, n = column_widths.length; i < n; i++){
                $head_cols.eq(i).width(column_widths[i] - $.Util.Size.GRID_COL_RESIZE_DIFF);
                $main_cols.eq(i).width(column_widths[i]);
        }
    }

    // remove any previous bound events
    $(document).unbind();

    if (!grid_data){
        grid_data = [];
    }


    var resize_grid_timeout;
    var resize_column_timeout;


    var grid_size = {width : 500, height : 300};
    // create the table
    $.Grid.Build(input, form_data, grid_data);


    var $grid = $(input).find('div.scroller');
    var $grid_side = $grid.find('div.scroller-side');
    var $grid_head = $grid.find('div.scroller-head');
    var $grid_main = $grid.find('div.scroller-main');
    var $grid_resizer = $grid.find('div.scroller-resizer');
    var $main = $(input).find('div.scroller-main table');
    var $head = $(input).find('div.scroller-head table');

    resize_grid();

    var $drag_col;
    var drag_col;

    var column_widths = [];
    var column_widths_main = [];
    var column_widths_header = [];
    get_column_widths();
    resize_table_columns();

    // add resizers
    var headers = $head.find('th');
    for (var i = 0, n=headers.size() ; i < n ; i++){
        // add the resizer
        headers.eq(i).dblclick(auto_resize).prepend($('<div class="t_resizer" ></div>').mousedown(start_column_resize));
    }
    $grid_resizer.mousedown(start_grid_resize);
    // add grid movement functionality
    $.Grid.Movement(input, form_data, grid_data);
};

$.Grid.MIN_COLUMN_SIZE = 25;
$.Grid.MIN_GRID_HEIGHT = 50;
$.Grid.MIN_GRID_WIDTH = 100;
$.Grid.SIDE_COLUMN_WIDTH = 50;

$.Grid.Movement = function(input, form_data, grid_data){

    function init(){
        total_rows = $main.find('tr').size();
        total_cols = $main.find('tr').eq(0).children().size();
        $main.click(click_main).keydown(keydown).dblclick(dblclick);
        $side.click(click_side).dblclick(dblclick);

        focus();
        if (edit_mode){
            edit_mode_on();
        } else {
            edit_mode_off();
        }
    }

    function click_side(e){
        // click on the side selector
        var $item = $(e.target);
        if ($item[0].nodeName == 'TD'){
            var $row = $item.parent('tr');
            row = $row.parent().children().index($row);
            move();
        }
        return false;
    }

    function click_main(e){
        // click in the main table body
        var $item = $(e.target);
        if ($item[0].nodeName == 'TD'){
            var $row = $item.parent('tr');
            row = $row.parent().children().index($row);
            var $row_side = $side.find('tr').eq(row);
            var this_col = $item.parent().children().index($item);
            col = this_col;
            selected($item, $row, $row_side);
        }
        return false;
    }

    function dblclick(e){
        // switch on edit mode if needed
        if (!edit_mode){
            edit_mode_on();
        }
        return false;
    }


    function make_editable(){
        // make the cell editable
        current.$control = util.make_editable(current.$item, current.field);
        // if this is the first row we need to adjust the width to compensate for
        // any differences in the padding etc
        if (current.row === 0){
            current.$item.width(current.$item.width() - $.Util.Size.GRID_COL_EDIT_DIFF);
        }
        current.value = grid_data[current.row][current.field.name];
    }

    function check_row_dirty(){
        if (is_empty(row_info[current.row])){
            current.$row.removeClass('dirty');
            current.$side.removeClass('dirty');
            current.dirty = false;
        }
    }

    function make_normal(){
        // return the item to it's normal state
        var value = util.make_normal(current.$item, current.field);
        // if this is the first row we need to adjust the width to compensate for
        // any differences in the padding etc
        if (current.row === 0){
            current.$item.width(current.$item.width() + $.Util.Size.GRID_COL_EDIT_DIFF);
        }
        if (value === current.value){
            // not changed
            current.$item.removeClass('dirty');
            if (row_info[current.row][current.field.name]){
                delete row_info[current.row][current.field.name];
                if (is_empty(row_info[current.row])){
                    delete row_info[current.row];
                }
            }
            check_row_dirty();
        } else {
            // has changed
            row_info[current.row][current.field.name] = value;
            current.dirty = true;
            current.$item.addClass('dirty');
            current.$row.addClass('dirty');
            current.$side.addClass('dirty');

//            console.log('changed was; ' + current.value + ', now: ' + value);
        }
        current.$control = undefined;
    }

    function autosave(){
        var node = 'table.Edit';
        var out = {};
        if (console){
            console.log('autosave: ' + row_info[current.row]);
        }
        //get_node(node, '_save', out, false);
    }

    function row_blur(){
        if (current.dirty){
            autosave();
        } else {
            if (row_info[current.row]){
                delete row_info[current.row];
            }
        }
        current.$row.removeClass('current');
        current.$side.removeClass('current');
    }

    function row_focus(){
        if (!row_info[current.row]){
            row_info[current.row] = {};
            current.dirty = false;
        } else {
            current.dirty = true;
        }
        current.$row.addClass('current');
        current.$side.addClass('current');
    }

    function make_cell_viewable(){
        // FIXME do complete rewrite as logic has gone for a walk ;)
        // however it appears to function correctly so is
        // good for checking any new approach against
        // but completely unreadable
        var div_pos = $scroll_div.position();
        var div_top = div_pos.top;
        var div_left = div_pos.left;

        var cell_pos = current.$item.position();
        var cell_top = cell_pos.top - div_top;
        var cell_left = cell_pos.left - div_left;

        var s = $.Util.Size.SCROLLBAR_WIDTH;
        var height = $scroll_div.innerHeight() - s;
        var width = $scroll_div.innerWidth() - s;
        var h = $.Util.Size.GRID_BODY_H;
        var h2 = $.Util.Size.GRID_HEADER_H;
        var w = current.$item.outerWidth();
        var top = $scroll_div.scrollTop();
        var left = $scroll_div.scrollLeft();

        if (cell_top < 0){
            $scroll_div.scrollTop(top + cell_top + s + (h-h2));
        } else if (cell_top + (h * 2) > height + (h-h2)){
            $scroll_div.scrollTop(top - height + cell_top + h + s + (h-h2))
        }

        if (cell_left < 0){
            $scroll_div.scrollLeft(left + cell_left + div_left);
        } else if (cell_left + w + s + s > width){
            $scroll_div.scrollLeft(left - width + cell_left + w + div_left);
        }
    }

    function selected($new_item, $new_row, $row_side){
        // a cell has been selected update as needed
        if ($new_item[0] !== current.$item[0]){
            if (current.$item[0] !== undefined){
                if (edit_mode){
                    make_normal();
                }
                current.$item.removeClass('t_selected_cell');
                current.$item.removeClass('t_edited_cell');

            }
            if($new_row[0] != current.$row[0]){
                if (current.$row[0] !== undefined){
                    row_blur();
                }
                current.$row = $new_row;
                current.$side = $row_side;
                current.row = row;
                row_focus();
            }

            current.field = form_data.fields[col];
            current.$item = $new_item;
            current.col = col;

            // check cell is viewable
            make_cell_viewable()

            if (edit_mode){
                current.$item.addClass('t_edited_cell');
                make_editable();
            } else {
                current.$item.addClass('t_selected_cell');
            }
        }
    }

    function edit_mode_off(){
        // turn off edit mode
        if (current.$item !== undefined && edit_mode){
            make_normal(current.$item);
            current.$item.addClass('t_selected_cell');
            current.$item.removeClass('t_edited_cell');
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
            current.$item.addClass('t_edited_cell');
            current.$item.removeClass('t_selected_cell');
        }
    }

    function focus(){
        // put the grid in focus
        move();
    }

    function move(){
        // find the cell and select it
        var $row = $main.find('tr').eq(row);
        var $row_side = $side.find('tr').eq(row);
        var $item = $row.children().eq(col);
        selected($item, $row, $row_side);
    }

    function move_right(){
        col++;
        if (col >= total_cols){
            col = total_cols - 1;
        }
        move();
    }

    function move_left(){
        col--;
        if (col < 0){
            col = 0;
        }
        move();
    }

    function tab_right(){
        col++;
        if (col >= total_cols){
            col = 0;
            row++;
            if (row >= total_rows){
                row = total_rows - 1;
            }
        }
        move();
    }

    function tab_left(){
        col--;
        if (col < 0){
            col = total_cols - 1;
            row--;
            if (row < 0){
                row = 0;
            }
        }
        move();
    }

    function move_down(){
        row++;
        if(row >= total_rows){
            row = total_rows - 1;
        }
        move();
    }

    function move_up(){
        row--;
        if(row < 0){
            row = 0;
        }
        move();
    }

    // general key bindings
    var keys = {
        '9': tab_right,
        '9s': tab_left,
        '38s': move_up,
        '40s': move_down,
        '13' : edit_mode_on,
        '27' : edit_mode_off,
        '27s' : edit_mode_off

    };

    // these key bindings are only valid in non edit mode
    var non_edit_keys = {
        '39': move_right,
        '37': move_left,
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

    // useful objects
    var $main = $(input).find('div.scroller-main table');
    var $head = $(input).find('div.scroller-head table');
    var $side = $(input).find('div.scroller-side table');
    var $scroll_div = $(input).find('div.scroller-main')

    var row = 0;
    var col = 0;
    var total_cols;
    var total_rows;
    var edit_mode = false;

    var row_info = {};

    // details of the currently selected control
    var current = {
        $item : [undefined],
        $row : [undefined],
        $side : undefined,
        dirty : false,
        row : undefined,
        col : undefined,
        value : undefined,
        field : undefined,
        $control : undefined
    };

    var util = $.Util;

    init();

};

$.Grid.Build = function(input, form_data, grid_data){

    var $side;
    var $head;
    var $main;
    var left = 0;
    var top = 0;

    function create(){
        $(input).empty();
        var $div = $('<div class="scroller"></div>');

        $head = $(header());
        $div.append($head);

        $side = $(selectors());
        $div.append($side);

        $main = $(body());
        $main.scroll(scroll);
        $div.append($main);

        $div.append('<div class="scroller-resizer"></div>');

        $(input).append($div);
    }

    function scroll(e){
        var new_left = $main.scrollLeft();
        var new_top = $main.scrollTop();
        if (new_left != left){
            left = new_left;
            $head.scrollLeft(left);
        }
        if (new_top != top){
            top = new_top;
            $side.scrollTop(top);
        }
    }

    function header(){
        var html = [];
        html.push('<div class="scroller-head"><table class="t_grid">');
        html.push('<thead><tr>');

        for (var i = 0; i < num_fields; i++){
            html.push('<th><div class="t_header">');
            html.push(form_data.fields[i].title);
            html.push('</div></th>');
        }
        html.push('</tr></thead>');
        html.push('</table></div>');
        return html.join('');
    }

    function footer(){
        var html = [];
        html.push('<tfoot><tr>');
        html.push('<td colspan="' + (num_fields + 1) + '">&nbsp;</td>');
        html.push('</tr></tfoot>');
        return html;
    }

    function selectors(){
        var html = [];
        html.push('<div class="scroller-side"><table class="t_grid">');
        html.push('<tbody>');
        for (var i = 0, n = grid_data.length; i < n ; i++){
            html.push('<tr><td>' + i + '</td></tr>');
        }
        html.push('</tbody>');
        html.push('</table></div>');
        return html.join('');
    }

    function body(){
        var html = [];
        html.push('<div class="scroller-main"><table class="t_grid">');
        html.push('<tbody>');
        for (var i = 0, n = grid_data.length; i < n ; i++){
            html.push(row(grid_data[i], i));
        }
        html.push('</tbody>');
        html.push('</table></div>');
        return html.join('');
    }

    function row(row_data, row_number){
        var html = [];
        var item, value;
        html.push('<tr class="form_body">');
        for (var i = 0; i < num_fields; i++){
            item = form_data.fields[i];
            if (row_data && row_data[item.name] !== null){
                value = row_data[item.name];
            } else {
                if (item.params && item.params['default']){
                    value = item.params['default'];
                } else {
                    value = null;
                }
            }
            if (item.type == 'datebox'){
                value = Date.ISO(value).toLocaleDateString();
            }
            if (value === null){
                html.push('<td class="null">[NULL]</td>');
            } else {
                html.push('<td>' + value + '</td>');
            }
        }
        html.push('</tr>');
        return html.join('');
    }

    var num_fields = form_data.fields.length;
    create();
};


// General functions
$.Util = {};

$.Util.get_keystroke = function (e){
    // make a simple key code string
    // eg          tab => 8
    //      ctrl + tab => 8c
    var key = String(e.keyCode);
    if (e.shiftKey){
        key += 's';
    }
    if (e.ctrlKey){
        key += 'c';
    }
    if (e.altKey){
        key += 'a';
    }
    return key;
};

$.Util.control_setup = function($control, field){
    // add any events needed by the control
    // but start by removing any existing bound events
    $control.unbind();
    switch (field.type){
        case 'intbox':
            $control.change($FORM_CONTROL._intbox_change);
            $control.keydown($FORM_CONTROL._intbox_key);
            break;
        case 'datebox':
            $control.keydown($FORM_CONTROL._datebox_key);
            break;
    }
};

$.Util.make_editable = function($item, field){
    // make the selected item an editable control
    // and return the new control
    var value = $item.html();
    if ($item.hasClass('null')){
        value = '';
    }
    if (value == '&nbsp;'){
        value = '';
    }
    $item.html('<input type="text" value="' + value + '" />');
    var $control = $item.find('input');
    $.Util.control_setup($control, field);
    $control.select();
    return $control;
};

$.Util.make_normal = function($item, field){
    // return the item to it's normal state
    // and return it's value
    var value = $item.find('input').val().trim();
    var update_value = value;
    // check for nulls
    if (value === ''){
       if ($item.hasClass('null')){
           value = null;
       } else {
           update_value = '';
       }
    }

    // special controls
    switch (field.type){
        case 'datebox':
            value = date_from_value(value);
            if (value){
                update_value = value.toLocaleDateString();
                value = value.toISOString();
            } else {
                value = null;
            }
            break;
        case 'checkbox':
            if (value == 'true'){
                value = true;
            } else {
                value = false;
            }
            update_value = value;
            break;
        case 'intbox':
            if (value !== null){
                value = parseInt(value, 10);
            }
            update_value = value;
            break;
    }

    // output
    if (value === null){
        update_value = '[NULL]';
        $item.addClass('null');
    } else {
        $item.removeClass('null');
    }
    if (update_value === ''){
        $item.html('&nbsp;');
    } else {
        $item.text(update_value);
    }
    return value;
};

// $.Util.Size
// this is used to calculate and store size related info
// needed to get placements correct etc
$.Util.Size = {};

$.Util.Size.get = function(){


    function scrollbar(){
        // get width of scrollbar
        var $div = $('<div style="overflow:hidden; width:50px; height:50px; position:absolute; left:-100px; top:0px;"><div style="height:60px;"></div></div>');
        $('body').append($div);
        var w1 = $div.find('div').width();
        $div.css('overflow-y', 'scroll');
        var w2 = $div.find('div').width();
        $.Util.Size.SCROLLBAR_WIDTH = w1 - w2;
        $div.remove()
    }

    function grid(){
        // get interesting stuff about grid cells
        // needed for acurate resizing
        var $div = $('<div style="overflow:hidden; width:100px; height:100px; position:absolute; left:-200px; top:0px;"></div>');
        $div.append('<table class="grid"><thead><tr><th>head</th></tr></thead><tbody><tr><td>body</td></tr><tr><td class="t_edited_cell">body</td></tr></tbody></table>');
        $('body').append($div);

        var $x = $div.find('th');
        $.Util.Size.GRID_HEADER_BORDER_W = $x.outerWidth() - $x.width();
        $.Util.Size.GRID_HEADER_H = $x.outerHeight();

        var $x = $div.find('td').eq(0);
        $.Util.Size.GRID_BODY_BORDER_W = $x.outerWidth() - $x.width();
        $.Util.Size.GRID_BODY_H = $x.outerHeight();

        var $x = $div.find('td').eq(1);
        $.Util.Size.GRID_BODY_BORDER_W_EDIT = $x.outerWidth() - $x.width();
        $.Util.Size.GRID_BODY_H_EDIT = $x.outerHeight();

        $.Util.Size.GRID_COL_RESIZE_DIFF = $.Util.Size.GRID_HEADER_BORDER_W - $.Util.Size.GRID_BODY_BORDER_W;
        $.Util.Size.GRID_COL_EDIT_DIFF = $.Util.Size.GRID_BODY_BORDER_W_EDIT - $.Util.Size.GRID_BODY_BORDER_W;
        $div.remove()
    }


    scrollbar();
    grid();

};

})(jQuery);

// get our size calculations
$(document).ready($.Util.Size.get);
