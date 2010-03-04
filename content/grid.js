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
    Copyright (c) 2008-2010 Toby Dacre & David Raznick

    jQuery grid resize plugin

*/




(function($) {
	
$.fn.extend({

	grid: function(form_data, grid_data, paging_data){
		$.Grid(this, form_data, grid_data, paging_data);
	}
});



$.Grid = function(input, form_data, grid_data, paging_data){

/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            EVENT HANDLERS

*/

    // GRID RESIZING EVENTS

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
            resize_grid_timeout = setTimeout(resize_grid_call, 25);
        }
        return false;
    }


    // COLUMN RESIZING EVENTS

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
        // Resize grid in case we need to add/remove scroll bars.
        resize_grid();
        return false;
    }

    function move_column_resize(e){
        // resize
        if ($drag_col){
            var new_width = Math.floor(e.clientX - $drag_col.offset().left + 15);
            if (new_width < $.Grid.MIN_COLUMN_SIZE){
                new_width = $.Grid.MIN_COLUMN_SIZE;
            }
            if (new_width > $.Grid.MAX_COLUMN_WIDTH_HARD){
                new_width = $.Grid.MAX_COLUMN_WIDTH_HARD;
            }
            column_widths[drag_col] = new_width;

            if (drag_col == column_widths.length - 1){
                last_column_user_width = new_width;
            }
            // remove any pending resize
            if (resize_column_timeout){
                clearTimeout(resize_column_timeout);
            }
            resize_column_timeout = setTimeout(resize_table, 25);
        }
        return false;
    }



    // EVENTS FOR THE TABLE


    function scroll(e){
        var new_left = $grid_main.scrollLeft();
        var new_top = $grid_main.scrollTop();
        if (new_left != scroll_left){
            scroll_left = new_left;
            $grid_head.scrollLeft(scroll_left);
        }
        if (new_top != scroll_top){
            scroll_top = new_top;
            $grid_side.scrollTop(scroll_top);
        }
    }

    function click_side(e){
        // click on the side selector
        if (!form_in_focus){
            focus();
        }
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
        if (!form_in_focus){
            focus();
        }
        var actioned = false;
        var $item = $(e.target);
        var fn_finalise;
        // if this control is complex eg. dropdown.
        if ($item[0].nodeName == 'DIV'){
            if ($item.hasClass('data')){
                $item = $item.parent();
            } else if ($item.hasClass('but_dd')){
                $item = $item.parent();
                fn_finalise = function(){
                    var $form = $item.find('input');
                    $form.trigger('dropdown');
                };
            }
        }
        // switch on edit mode if needed
        if (!edit_mode){
            edit_mode_on();
        }
        if ($item[0].nodeName == 'TD'){
            var $row = $item.parent('tr');
            row = $row.parent().children().index($row);
            var $row_side = $side.find('tr').eq(row);
            var this_col = $item.parent().children().index($item);
            col = this_col;
            cell_selected($item, $row, $row_side);
            actioned = true;
        }
        if (fn_finalise){
            fn_finalise();
        }
        return !actioned;
    }

    // BINDING AND UNBINDING


    function unbind_column_resizers(){
        for (var i = 0, n = $header_resizers.length; i < n ; i++){
            $header_resizers[i].unbind();
        }
    }

    function add_grid_functionality(){
        // add resizers
        var headers = $head.find('th');
        var $current;
        for (i = 0, n= headers.size() ; i < n ; i++){
            // add the resizer
            $current = $('<div class="t_resizer" ></div>').mousedown(start_column_resize).dblclick(auto_column_resize);
            $header_resizers.push($current);
            headers.eq(i).prepend($current);
        }

        $grid_resizer.mousedown(start_grid_resize);
        // add grid movement functionality
        init_movement();

        resize_table();
        $form.addClass('grid_holder');

        // if top level form then give focus
        if (!$form.parent().hasClass('SUBFORM')){
            focus();
        }
        // add resize function so remotely accessable
        $form.data('show_loader', show_loader);
        $form.data('update_grid', update_grid);
        $form.data('resize_grid', resize_grid);

    }


    function unbind_all(){
        console_log('unbind');
        unbind_column_resizers();
        $side.unbind();
        $main.unbind();
        $grid_main.unbind();
        $form.unbind();
    }

    function add_row(){
        $form.data('build')('add_row');
    }



/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            RESIZE FUNCTIONS

*/


    // GRID RESIZE FUNCTIONS

    function resize_grid_call(){
        var last_column = column_widths.length - 1;
        var grid_width = grid_size.width - $.Grid.SIDE_COLUMN_WIDTH - util_size.SCROLLBAR_WIDTH;
        var table_width = $head.width();
        if (grid_width > table_width){
            column_widths[last_column] += grid_width - table_width;
            resize_table(true);
        } else if (column_widths[last_column] > last_column_user_width){
            column_widths[last_column] -=  table_width - grid_width;
            if (column_widths[last_column] < last_column_user_width){
                column_widths[last_column] = last_column_user_width;
            }
            resize_table(true);
        } else {
            resize_grid();
        }
    }

    function autosize_grid(width_only){
        // get the grid  to display at the correct size for it's data
        var has_scrollbar = false;
        if (!width_only){
            var height = $main.height();
            height += util_size.GRID_HEADER_H + util_size.GRID_TITLE_H + util_size.GRID_FOOTER_H;
            if (height > util_size.MAIN_HEIGHT){
                height = util_size.MAIN_HEIGHT;
                has_scrollbar = true;
            }
            grid_size.height = height;
        }

        var width = $head.width();
        width += $.Grid.SIDE_COLUMN_WIDTH;
        if (has_scrollbar){
            width += util_size.SCROLLBAR_WIDTH;
        }
        if (width > util_size.MAIN_WIDTH){
            width = util_size.MAIN_WIDTH;
        }
        grid_size.width = width;
    }

    function resize_grid(){
        var foot_height = util_size.GRID_FOOTER_H;
        var head_height = util_size.GRID_HEADER_H;
        var side_width = $.Grid.SIDE_COLUMN_WIDTH;
        var scrollbar_width = util_size.SCROLLBAR_WIDTH;
        var title_height = util_size.GRID_TITLE_H;
        var width = grid_size.width;
        var height = grid_size.height;
        var main_height = $main.height();
        var main_width = $main.width();

        // make sure we have enough height to show grid elements
        var min_height = foot_height + head_height + title_height;
        if (height < min_height){
            height = min_height;
            grid_size.height = min_height;
        }

        $grid.width(width).height(height);

        // Css for $grid_main.
        // There may be scroll bars or not, so see if we need them.

        var grid_main_css = {};
        var right_scrollbar = 0;
        var bottom_scrollbar = 0;

        // This is horrible, but if there are scroll bars added
        // we need to see if this effects things.
        if (main_height + head_height + foot_height > height){
            right_scrollbar = 1;
        }
        if (main_width + side_width + (scrollbar_width * right_scrollbar) > width){
            bottom_scrollbar = 1;
            if (main_height + head_height + foot_height + scrollbar_width > height){
                    right_scrollbar = 1;
                    if (main_width + side_width + scrollbar_width > width){
                        bottom_scrollbar = 1;
                    }
            }
        }

        if (right_scrollbar === 0){
            grid_main_css['overflow-y'] = 'hidden';
        } else {
            grid_main_css['overflow-y'] = 'scroll';
        }

        if (bottom_scrollbar === 0){
            grid_main_css['overflow-x'] = 'hidden';
        } else {
            grid_main_css['overflow-x'] = 'scroll';
        }

        // store the scrollbar settings
        scrollbar_bottom = (bottom_scrollbar == 1);
        scrollbar_side = (right_scrollbar == 1);

        $grid_main.css(grid_main_css);

        var new_main_height = height - head_height - foot_height - title_height;
        position($grid_main, head_height + title_height, side_width, new_main_height, width - side_width);

        var new_head_width = width - side_width - (scrollbar_width * right_scrollbar);
        position($grid_head, title_height, side_width, null, new_head_width);

        // Make column resizers correct height.
        $grid_head.find('div.t_resizer').height(head_height);

        var side_height = height - head_height - (scrollbar_width * bottom_scrollbar) - foot_height - title_height;
        if (side_height < 0){
            side_height = 0;
        }
        position($grid_side, head_height + title_height, 0, side_height, side_width);

        position($grid_foot, height - foot_height, 0, foot_height, width);

        position($grid_title, 0, 0, title_height, width);

        position($grid_resizer, height - 15, width - 15, null, null);

        position($grid_loader, Math.floor((height - util_size.GRID_LOADER_H)/ 2), Math.floor((width - util_size.GRID_LOADER_W) / 2), null, null);

    }


    // COLUMN RESIZE FUNCTIONS

    function auto_column_resize(e){
        var $item = $(e.target).parent();
        var col;
        if ($item[0].nodeName == 'TH'){
            col = $item.parent().children().index($item);
        }
        column_widths[col] = measure_column_width(col);

        if (column_widths[col] > $.Grid.MAX_COLUMN_WIDTH_SOFT){
            column_widths[col] = $.Grid.MAX_COLUMN_WIDTH_SOFT;
        }
        resize_table();
    }

    function measure_column_width(col){
        // build column off screen and measure width
        var field = form_data.fields[col].name;
        var $div = $('<div style="top:0;left:-200px;position:absolute;width:100px;height:100px;overflow:hidden;"/>');
        var table = ['<table class="t_grid" >'];
        table.push('<tr><th><div class="t_header">' + form_data.fields[col].title + '</div></th></tr>');
        for (var i = 0, n = grid_data.length; i < n; i++){
            table.push('<tr><td>' + grid_data[i][field] + '</td></tr>');
        }
        table.push('</table>');
        $div.html(table.join(''));
        $('body').append($div);
        var width = $div.find('table').width();
        $div.remove();
        return width;
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
            if (column_widths[i] > $.Grid.MAX_COLUMN_WIDTH_SOFT){
                column_widths[i] = $.Grid.MAX_COLUMN_WIDTH_SOFT;
            }
        }
        // set the last_column_user_width
        last_column_user_width = column_widths[--i];
    }

    function resize_table(stop_autosize){
        table_size.width = 0;
        for (var i = 0, n = column_widths.length; i < n; i++){
            table_size.width += column_widths[i];
        }
        // resize table
        $head.width(table_size.width);
        $main.width(table_size.width);

        resize_table_columns();

        if (stop_autosize !== true){
            autosize_grid(true);
        }
        // sometime we need to add/remove scrollbars to the grid
        resize_grid();
    }

    function resize_table_columns(){
        // Chrome needs to add css to each table to render correct column width.
        $main.css({"table-layout" : "fixed"});
        $head.css({"table-layout" : "fixed"});

        var $head_cols = $head.find('th');
        var $main_cols = $main.find('tr').eq(0).find('td');
        for (i = 0, n = column_widths.length; i < n; i++){
            // headers
            $head_cols.eq(i).width(column_widths[i] - util_size.GRID_COL_RESIZE_DIFF);
            // main table
            if (current && current.editing && current.row === 0 && current.col === i && !current.complex_control){
                // control is on first row and being edited for this column
                $main_cols.eq(i).width(column_widths[i] - util_size.GRID_COL_EDIT_DIFF);
            } else {
                $main_cols.eq(i).width(column_widths[i]);
            }
        }
    }


/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            GENERAL FUNCTIONS

*/



    function show_loader(){
        $grid_loader.show();
    }

    function update_grid(data){
        // The table data has been changed.
        blur();

        grid_data = data.grid_data;
        paging_data = data.paging_data
        // Update the grid.
        build_grid(false);
        find_grid_elements();
        $grid_loader.hide();
        // Update the paging info.
        var $paging = $grid_foot.find('span.paging');
        var paging = '';
        if (paging_data){
            paging = util.paging_bar(paging_data);
        }
        $paging.html(paging);
        // Update the grid_data in Movement.
        update_grid_movement();
        // FIXME do we need to do the focus here?
        focus();
    }

    function init(){
        // Check if we need to create the grid or just update the data.
        var form_string = $.toJSON(form_data);
        var current_form_string;
        $form = $input.children('div.GRID');
        if ($form.size() == 1){
            current_form_string = $form.data('form_string');
        }
        if (current_form_string == form_string){
            // Exists so tell it to update itself.
            console_log('existing');
            $form.data('update_grid')({ grid_data : grid_data, paging_data : paging_data});
        } else {
            console_log('new');
            util.unbind_all_children($input);
            $form = $('<div class="f_form GRID"></div>');
            $form.data('form_string', form_string);
            $input.append($form);
            // Create the table.
            build_grid(true);
            find_grid_elements();
            get_column_widths();
            add_grid_functionality();
        }
    }

    function find_grid_elements(){
        $grid = $form.find('div.scroller');
        $grid_side = $grid.find('div.scroller-side');
        $grid_head = $grid.find('div.scroller-head');
        $grid_main = $grid.find('div.scroller-main');
        $grid_foot = $grid.find('div.scroller-foot');
        $grid_title = $grid.find('div.scroller-title');
        $grid_resizer = $grid.find('div.scroller-resizer');
        $head = $form.find('div.scroller-head table');
        $main = $form.find('div.scroller-main table');
        $side = $grid.find('div.scroller-side table');
        $grid_loader = $form.find('div.scroller-loader');
    }


//
//
//
//
//
//

/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            GENERAL FUNCTIONS

*/

    function init_movement(){
        row = 0;
        col = 0;
        total_rows = $main.find('tr').size();
        total_cols = $main.find('tr').eq(0).children().size();
        $main.mousedown(click_main);
        $grid_main.scroll(scroll);
        $side.mousedown(click_side);
        $form.data('command', command_caller);
    }

    function update_grid_movement(){
        init_movement();
        move();
        // Scroll the table to align with the headers.
        $grid_main.scrollLeft($grid_head.scrollLeft());
    }

    var custom_commands = {
        'field_top' : field_top,
        'field_end' : field_end,
        'unbind_all' : unbind_all,
        'blur' : blur,
        'focus' : focus,
        'add_row' : add_row,
        'save' : save_all,
        'save_return' : save_return,
    };


    function command_caller(type, data){
        console_log('command triggered: ' + type);
        if (custom_commands[type]){
            return custom_commands[type](data);
        } else {
            alert('command: <' + type + '> has no handler');
            return false;
        }
    }

/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            FORM ACTIONS

*/

    function make_editable(){
        // make the cell editable
        var $item = current.$item;

        if (current.complex_control){
            $item = $item.find('div.data');
        }

        current.$control = util.make_editable($item, current.field);
        // if this is the first row we need to adjust the width to compensate for
        // any differences in the padding etc
        // don't do this for complex conrols as they do thier own wrapping
        if (!$.browser.safari && current.row === 0 && !current.complex_control){
            current.$item.width(current.$item.width() - util_size.GRID_COL_EDIT_DIFF);
        }
        current.value = grid_data[current.row][current.field.name];
    }

    function check_row_dirty(){
        if (util.is_empty(row_info[current.row])){
            current.$row.removeClass('dirty');
            current.$side.removeClass('dirty');
            current.dirty = false;
        }
    }

    function make_normal(){
        // return the item to it's normal state
        var $item = current.$item;

        if (current.complex_control){
            $item = $item.find('div.data');
        }
        var value = util.make_normal($item, current.field);
        // if this is the first row we need to adjust the width to compensate for
        // any differences in the padding etc
        // don't do this for complex conrols as they do thier own wrapping
        if (!$.browser.safari && current.row === 0 && !current.complex_control){
            current.$item.width(current.$item.width() + util_size.GRID_COL_EDIT_DIFF);
        }
        if (value === current.value){
            // not changed
            current.$item.removeClass('dirty');
            if (row_info[current.row] && row_info[current.row][current.field.name]){
                delete row_info[current.row][current.field.name];
                if (util.is_empty(row_info[current.row])){
                    delete row_info[current.row];
                }
            }
            check_row_dirty();
        } else {
            // has changed
            if (!row_info[current.row]){
                row_info[current.row] = {};
            }
            row_info[current.row][current.field.name] = value;
            current.dirty = true;
            current.$item.addClass('dirty');
            current.$row.addClass('dirty');
            current.$side.addClass('dirty');

        }
        current.$control = undefined;
    }

    function get_grid_row_data(this_row){
        // get our data to save
        var save_data = {};
        var row_data = grid_data[this_row];

        for (var item in row_data){
            if (row_data.hasOwnProperty(item)){
                save_data[item] = row_data[item];
            }
        }

        var this_row_info = row_info[this_row];
        var copy_of_row_info = {};
        for (item in this_row_info){
            if (this_row_info.hasOwnProperty(item)){
                console_log(this_row_info[item]);
                save_data[item] = this_row_info[item];
                copy_of_row_info[item] = this_row_info[item];
            }
        }
        return { data : save_data, copy : copy_of_row_info };
    }

    function save_all(){
        edit_mode_off();
        console_log('save');
        var save_data;
        var full_save_data = [];
        var full_copy_data = [];
        var counter = 0;
        for (var this_row in row_info){
            if (row_info.hasOwnProperty(this_row)){
                save_data = get_grid_row_data(this_row);
                // add some extra bits of info for processing on return
                save_data.data.__root = counter;
                save_data.copy.__row = grid_data[this_row];
                save_data.copy.__$row = $main.find('tr').eq(this_row);
                save_data.copy.__$side = $side.find('tr').eq(this_row);

                full_save_data.push(save_data.data);
                full_copy_data.push(save_data.copy);
                counter++;
            }
        }
        var out = {};
        out.data = full_save_data;
        // any extra data needed from the form
        params = form_data.params;
        if (params && params.extras){
            for (var extra in params.extras){
                if (params.extras.hasOwnProperty(extra)){
                    out[extra] = params.extras[extra];
                }
            }
        }
        if (counter !==0 ){
            get_node_return(form_data.node, '_save', out, $form, full_copy_data);
        }
    }

    function check_dirty_rows(){
        // check all rows_altered to see if they are still dirty
        // sort css etc
        var is_dirty;
        var $this_row;
        var $this_side;
        var $this_item;
        var this_col;
        for (var this_row in row_info){
            is_dirty = false;
            $this_row = $main.find('tr').eq(this_row);
            $this_side = $side.find('tr').eq(this_row);

            for (var field in row_info[this_row]){
                this_col = form_data.items[field].index;
                $this_item = $this_row.children().eq(this_col);
                if (grid_data[this_row][field] == row_info[this_row][field]){
                    // don't delete if we are editing this item
                    if (!current.editing && current.row != this_row && field != current.field.name){
                        delete row_info[this_row][field];
                    }
                    $this_item.removeClass('dirty');
                } else {
                    is_dirty = true;
                    $this_item.addClass('dirty');
                }
            }
            if (is_dirty){
                $this_row.addClass('dirty');
                $this_side.addClass('dirty');
            } else {
                $this_row.removeClass('dirty');
                $this_side.removeClass('dirty');
                // don't remove if current row
                if (current.row != this_row){
                    delete row_info[this_row];
                }
            }

        }
    }

    function save_update(data, obj_data){

        var row_data;
        var this_data;
        var $this_side;
        for (var i = 0, n = data.length; i < n; i++){
            row_data = obj_data[i].__row;
            this_data = obj_data[i];
            if (row_data.id){
                // check if the id has changed (it shouldn't)
                if (row_data.id != data[i][1]){
                    alert('something went wrong the id has changed during the save\nid = ' + row_data.id + ', returned ' + this_data[1]);
                    return;
                }
            } else {
                // update id
                row_data.id = data[i][1];
            }
            // update _version
            row_data._version = data[i][2];

            // update fields
            for (var field in this_data){
                if (row_data[field] !== undefined){
                    row_data[field] = this_data[field];
                }
            }

            $this_side = obj_data[i].__$side;
            tooltip_clear($this_side);
        }
        check_dirty_rows();
    }

    function save_errors(data, obj_data){
        // FIXME implement
        var $this_row;
        var $this_side;
        var $this_item;
        for (var error_row in data){
            $this_row = obj_data[error_row].__$row;
            $this_side = obj_data[error_row].__$side;
            for (var field in data[error_row]){
                if (field != '__row' && field != '__$row' && field != '__$side'){
                    console_log(field);
                    $this_item = $this_row.find('td').eq(form_data.items[field].index);
                    $this_item.addClass('error');
                }
            }
            // add error tooltip to the side selector
            tooltip_add($this_side, $.toJSON(data[error_row]));
        }
        check_dirty_rows();
    }

    function save_return(data){
        // errors
        if (data.errors){
            save_errors(data.errors, data.obj_data);
        }
        // saves
        if (data.saved){
            save_update(data.saved, data.obj_data); // single form so only want first saved item
        }
    }

    function autosave(){
        var node = 'table.Edit';
        var out = {};
        console_log('autosave: ' + row_info[current.row]);
        // FIXME implement
    }

    function row_blur(){
        if (current.dirty){
            autosave();
        } else {
            if (row_info[current.row]){
                delete row_info[current.row];
            }
        }
        if (current.$row[0]){
            current.$row.removeClass('current');
            current.$side.removeClass('current');
        }
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
        // Check if current grid cell is visible within the scroller div.
        // If not scroll so it is.

        var cell_pos = current.$item.position();
        var cell_top = cell_pos.top;
        var cell_left = cell_pos.left;
        var cell_height = util_size.GRID_BODY_H;
        var cell_width = current.$item.outerWidth();

        var scroller_top = $grid_main.scrollTop();
        var scroller_left = $grid_main.scrollLeft();
        var s = util_size.SCROLLBAR_WIDTH;

        var scroller_height = $grid_main.innerHeight();
        if (!$.browser.Safari && scrollbar_bottom){
            scroller_height -= s;
        }
        var scroller_width = $grid_main.innerWidth();
        if (!$.browser.Safari && scrollbar_side){
            scroller_width -= s;
        }

        if (cell_top < 0){
            $grid_main.scrollTop(scroller_top + cell_top);
        } else if (cell_top > scroller_height - cell_height){
            $grid_main.scrollTop(scroller_top + cell_top - scroller_height + cell_height);
        }

        if (cell_left < 0){
            $grid_main.scrollLeft(scroller_left + cell_left);
        } else if (cell_left > scroller_width - cell_width && cell_left !== 0){
            $grid_main.scrollLeft(scroller_left + cell_left - scroller_width + cell_width);
        }
    }


    function cell_selected($new_item, $new_row, $row_side){
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

            current.complex_control = (current.field.control == 'dropdown');

            // check cell is viewable
            make_cell_viewable();

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
        current.editing = false;
    }

    function edit_mode_on(){
        // turn on edit mode
        if (!edit_mode && !form_data.params.read_only){
            edit_mode = true;
            current.editing = true;
            // if we have a current item make it editable
            if (current.$item[0]){
                make_editable(current.$item);
                current.$item.addClass('t_edited_cell');
                current.$item.removeClass('t_selected_cell');
            }
        }
    }

    function focus(){
        // put the grid in focus
        if (!form_in_focus){
            if (edit_mode){
                edit_mode_on();
            } else {
                edit_mode_off();
            }
            util.Event_Delegator('register', {keydown:keydown, blur:blur});
            form_in_focus = true;
            move();
        }
    }

    function blur(){
        row_blur();
        // put the grid out of focus
        if (edit_mode){
            edit_mode_off();
        }
        if (current.$item[0]){
            current.$item.removeClass('t_selected_cell');
        }
        current.$item = [undefined];
        current.$row = [undefined];

        form_in_focus = false;
    }

    function move_parent(event_type){
        var $parent = $form.parent();
        if ($parent.hasClass('SUBFORM')){
            // is a subform
            var $new_item = $parent.parent().parent();

            var current_edit_mode = edit_mode;
            util.Event_Delegator('clear');
            $new_item.data('command')(event_type, {edit_mode: current_edit_mode});
        } else {
            // main form
            if (event_type == 'field_up'){
                event_type = 'field_end';
            } else if (event_type == 'field_down'){
                event_type = 'field_top';
            }
            $form.data('command')(event_type, {edit_mode: current_edit_mode});
        }
    }

/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            CELL MOVEMENTS

*/

    function move(){
        // find the cell and select it
        var $row = $main.find('tr').eq(row);
        var $row_side = $side.find('tr').eq(row);
        var $item = $row.children().eq(col);
        cell_selected($item, $row, $row_side);
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
                move_parent('field_down');
                return;
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
                move_parent('field_up');
                return;
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

    function field_top(data){
        row = 0;
        col = 0;
        field_move(data);
    }

    function field_end(data){
        row = total_rows - 1;
        col = total_cols -1;
        field_move(data);
    }

    function field_move(data){
        focus();
        if (data.edit_mode){
            edit_mode_on();
        }
    }
    // general key bindings
    var keys = {
        '9': tab_right,
        '9s': tab_left,
        '38s': move_up,
        '40s': move_down,
        '27' : edit_mode_off,
        '27s' : edit_mode_off

    };

    var edit_keys = {
        '13' : edit_mode_off
    };

    // these key bindings are only valid in non edit mode
    var non_edit_keys = {
        '13' : edit_mode_on,
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
        } else if (edit_mode && edit_keys[key] !== undefined){
            edit_keys[key]();
            e.preventDefault();
            return false;
        } else if (edit_mode && key == '32c'){
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

    var scroll_left = 0;
    var scroll_top = 0;
    var row = 0;
    var col = 0;
    var total_cols;
    var total_rows;
    var edit_mode = false;
    var form_in_focus = false;

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
        $control : undefined,
        editing : false,
        complex_control : undefined
    };

    var scrollbar_side;
    var scrollbar_bottom;

/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            BUILD FUNCTIONS

*/

    function build_create(){
        $form.empty();
        var $div = $('<div class="scroller"></div>');

        var $title = $(build_title());
        $div.append($title);

        var $head = $(build_header());
        $div.append($head);

        var rows = build_rows();

        var $side = $('<div class="scroller-side">' + rows.selectors + '</div>');
        $div.append($side);

        var $main = $('<div class="scroller-main">' + rows.body + '</div>');
        $div.append($main);

        var $foot = $(build_foot());
        $div.append($foot);

        $div.append('<div class="scroller-resizer"></div>');
        $div.append('<div class="scroller-loader">Loading ...</div>');

        $form.append($div);

        $form.data('build', build_add_new_row);
    }

    function build_replace_table(){
        // Replace the existing grid with new data.
        var $main_table = $form.find('div.scroller-main table');
        var $side_table = $form.find('div.scroller-side table');

        var rows = build_rows();
        var $body = $(rows.body);
        var $selectors = $(rows.selectors);

        // Resize table.
        $body.css('width', table_size.width);
        $body.css({"table-layout" : "fixed"});
        // Resize columns.
        var $main_cols = $body.find('tr').eq(0).find('td');
        for (i = 0, n = column_widths.length; i < n; i++){
            $main_cols.eq(i).css('width', column_widths[i]);
        }

        $main_table.replaceWith($body);
        $side_table.replaceWith($selectors);
    }

    function build_header(){
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

    function build_title(){
        return '<div class="scroller-title">' + form_data.params.title + '</div>';
    }

    function build_foot(){
        var html = '<div class="scroller-foot">';
        html += '<span class="paging">';
        if (paging_data){
            html += util.paging_bar(paging_data);
        }
        html += '</span>';
        html += '<a href="#" onclick="grid_add_row();return false;">add new</a>';
        html += '</div>';
        return html;
    }

    function build_rows(){
        var body_html = [];
        var selectors_html = [];

        body_html.push('<table class="t_grid">');
        body_html.push('<tbody>');

        selectors_html.push('<table class="t_grid">');
        selectors_html.push('<tbody>');

        var offset = 0;
        if (paging_data && paging_data.offset){
            offset = paging_data.offset;
        }
        for (var i = 0, n = grid_data.length; i < n ; i++){
            body_html.push(build_row(grid_data[i], i));
            selectors_html.push('<tr><td>' + (i + offset) + '</td></tr>');
        }
        body_html.push('</tbody>');
        body_html.push('</table>');

        selectors_html.push('</tbody>');
        selectors_html.push('</table>');

        return {body : body_html.join(''),
                selectors : selectors_html.join('')};
    }

    function build_row(row_data, row_number){
        var html = [];
        var item, value;
        html.push('<tr class="form_body">');
        for (var i = 0; i < num_fields; i++){
            item = form_data.fields[i];
            if (row_data && row_data[item.name] !== null){
                value = row_data[item.name];
            } else {
                if (item['default']){
                    value = item['default'];
                } else {
                    value = null;
                }
            }
            // correct data value if needed
            switch (item.data_type){
                case 'DateTime':
                case 'Date':
                    if (value !== null){
                        value = Date.ISO(value).makeLocaleString();
                    }
                    break;
                default:
                    value = HTML_Encode(value);
            }
            // make sure we add &nbsp; to make cell show
            // FIXME can we do this via css better?
            if (value === ''){
                value = '&nbsp;';
            }

            if (item.control == 'dropdown'){
                if (value === null){
                    html.push('<td class="null complex"><div class="but_dd"/><div class="data">[NULL]</div></td>');
                } else {
                    html.push('<td class="complex"><div class="but_dd"/><div class="data">' + value + '</div></td>');
                }
            }
            else {
                if (value === null){
                    html.push('<td class="null">[NULL]</td>');
                } else {
                    html.push('<td>' + value + '</td>');
                }
            }
        }
        html.push('</tr>');
        return html.join('');
    }

    function build_add_new_row(data){
        var new_row = grid_data.length;
        grid_data[new_row] = {};
        $form.find('div.scroller-main table').append(build_row());
        $form.find('div.scroller-side table').append('<tr><td>' + new_row + '</td></tr>');
        if (new_row === 0){
            resize_table();
        }
    }

    function build_grid(build_new){

        if (build_new){
            build_create();
        } else {
            build_replace_table();
        }
    }


/*
       _          _          _          _          _
     >(')____,  >(')____,  >(')____,  >(')____,  >(') ___,
       (` =~~/    (` =~~/    (` =~~/    (` =~~/    (` =~~/
 jgs~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~^`---'~^~^~

            VARIABLES

*/

    var num_fields = form_data.fields.length;
    var $input = $(input);
    var $form;

    var $drag_col;
    var drag_col;
    var column_widths = [];
    var last_column_user_width;
    var column_widths_main = [];
    var column_widths_header = [];

    var resize_grid_timeout;
    var resize_column_timeout;

    var util = $.Util;
    var HTML_Encode = util.HTML_Encode;
    var util_size = $.Util.Size;
    var position = $.Util.position;
    var grid_size = {width : 500, height : 300};
    var table_size = {width : 0};

    var $grid;
    var $grid_side;
    var $grid_head;
    var $grid_main;
    var $grid_foot;
    var $grid_title;
    var $grid_resizer;
    var $head;
    var $main;
    var $side;

    var $header_resizers = [];

    if (!grid_data){
        grid_data = [];
    }

    init();

};

$.Grid.MIN_COLUMN_SIZE = 25;
$.Grid.MIN_GRID_HEIGHT = 50;
$.Grid.MIN_GRID_WIDTH = 100;
$.Grid.SIDE_COLUMN_WIDTH = 50;
$.Grid.MAX_COLUMN_WIDTH_SOFT = 300;
$.Grid.MAX_COLUMN_WIDTH_HARD = 500;


})(jQuery);

