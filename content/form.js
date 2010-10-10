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

    jQuery form plugin

*/




(function($) {
	
$.fn.extend({

	checkbox: function(item, value){
		$.Checkbox(this, item, value);
	},

	input_form: function(form_data, grid_data, paging_data){
		$.InputForm(this, form_data, grid_data, paging_data);
	},

	grid2: function(form_data, grid_data, paging_data){
		$.Grid2(this, form_data, grid_data, paging_data);
	},

	status_form: function(){
		$.StatusForm(this);
	}
});

$.Checkbox = function(input, item, value){

    var $checkbox = $(input);
    var $img = $checkbox.find('img');

    // default to being a 2 state control
    // unless explicit validation rule
    var is_2_state = !(item.validation && item.validation[0].not_empty === false);

    function mousedown_2_state(){
        switch (value){
            case false:
                value = true;
                $img.show();
                $checkbox.removeClass('false');
                $checkbox.addClass('true');
                break;
            case true:
                value = false;
                $img.hide();
                $checkbox.removeClass('true');
                $checkbox.addClass('false');
                break;
        }
    }

    function mousedown_3_state(){
        switch (value){
            case false:
                value = null;
                $checkbox.removeClass('false');
                $checkbox.addClass('null');
                break;
            case null:
                value = true;
                $img.show();
                $checkbox.removeClass('null');
                $checkbox.addClass('true');
                break;
            case true:
                value = false;
                $img.hide();
                $checkbox.removeClass('true');
                $checkbox.addClass('false');
                break;
        }
    }

    function mousedown(){
        if (is_2_state){
            mousedown_2_state();
        } else {
            mousedown_3_state();
        }
        // store the value
        $checkbox.data('value', value);
    }

   function set_state(){
        switch (value){
            case null:
                $checkbox.addClass('null');
                $img.hide();
                break;
            case true:
                $checkbox.addClass('true');
                $img.show();
                break;
            case false:
                $checkbox.addClass('false');
                $img.hide();
                break;
        }
    }

    function keydown(e){
        // space toggles the control
        var key = e.keyCode;
        if (key == 32){
            mousedown();
        }
        return true;
    }

    if (is_2_state && value === null){
        value = false;
    }
    set_state();
    $checkbox.data('value', value);
    var $checkbox_wrapper = $checkbox.find("div");
    // FIXME need to unbind this
    $checkbox.mousedown(mousedown);
    $checkbox.keydown(keydown);

};


$.InputForm = function(input, form_data, row_data, extra_defaults){
    var custom_commands;
    var $input = $(input);

    $.Util.unbind_all_children($input);

    // make our div that everything will hang off
    var $form = $('<div class="INPUT_FORM"></div>');
    $input.append($form);


    if (!row_data){
        row_data = {};
    }



    function size_boxes(){
        // FIXME this has been disabled TD
        return;
        var $box;
        var width;
        var i, n;
        // BOX layouts
        var $boxes = $form.find('div.BOX');
        for (i = 0, n = $boxes.size(); i < n ; i++){
            $box = $boxes.eq(i);
            width = $box.parent().width() - util_size.FORM_BOX_W;
            $box.width(width);
        }
        // results list resizing
        $boxes = $form.find('div.RESULT_DATA');
        for (i = 0, n = $boxes.size(); i < n ; i++){
            $box = $boxes.eq(i);
            width = $box.parent().width() - util_size.FORM_BOX_W - 200;
            $box.width(width);
        }
        // record list resizing
        // for images
        var $img = $form.find('div.RECORD_IMG');
        if ($img.size() !== 0){
            var position = $img.position();
            var img_top = position.top;
            var img_bottom = img_top  + $img.outerHeight();
            var img_width = $img.outerWidth();
            $boxes = $img.parent().find('div.f_control_holder');
            for (i = 0, n = $boxes.size(); i < n ; i++){
                $box = $boxes.eq(i);
                width = $box.parent().width() - img_width;
                $box.width(width);
                // check if we have cleared the img float if so quit resizing
                if ($box.position().top + $box.outerHeight() > img_bottom){
                    break;
                }
            }
        }

    }

    var local_row_data;

    var subforms = [];
    var util_size = $.Util.Size;
    var HTML_Encode = $.Util.HTML_Encode;
    var process_html = $.Util.process_html;
    var HTML_Encode_Clear = $.Util.HTML_Encode_Clear;
    //FIXME how do we deal with data in the form

    function init(){
        build_form();
        size_boxes();
        init_movement();
        register_events();
    }

    function command_caller(type, data){
        if (custom_commands[type]){
            return custom_commands[type](data);
        } else {
            alert('command: <' + type + '> has no handler');
            return false;
        }
    }


    function init_movement(){

        // remove any previous bound events
        unbind_all();

        $form.mousedown(form_mousedown);

        total_fields = form_data.fields.length;
        $form.data('command', command_caller);
    }


    function unbind_all(){
        $form.unbind();
    }

    function register_events(){
    }

    function remove_all_errors(){
        // remove error spans
        $form.find('span.f_error').remove();
        // remove any error classes
        $form.find('div.f_error').removeClass('f_error');
    }

    function save_errors(errors){
        remove_all_errors();
        var index;
        var $item;
        var $desc;
        var error;
        for (var field in errors){
            index = form_data.items[field].index;
            $item = form_controls_hash[field];
            // add error class to the containing div
            $item.addClass('f_error_control');

            $item = $item.find('div.f_sub');
            // add the error span
            $desc = $item.find('div.f_description');
            error = '<div class="f_error">' + errors[field] + '</div>';
            if ($desc.length){
                $desc.after(error);
            } else {
                $item.prepend(error);
            }
        }
    }

    function get_form_data_listed_fields(fields){
        // get the fields from the list
        fields = fields.split(',');
        var data = {};
        var field;
        for (var i=0, n = fields.length; i < n; i++){
            field = fields[i].trim();
            data[field] = null;
            //normalise extra_defaults?
            if (extra_defaults && extra_defaults[field] !== undefined){
                data[field] = extra_defaults[field];
            }
            if (row_data[field] !== undefined){
                data[field] = row_data[field];
            }
        }
        return data;
    }

    function get_form_data_remote(fields){
        // is this used anywhere?
        if (fields){
            fields = fields.replace(/^\{|\}$/g, '') + ',';
            return get_form_data_listed_fields(fields);
        }
        //return get_form_data().save_data;
        var data = get_form_data().save_data;
        var errors = validate_form_data(data);
        var join_data;

        // join data allows additional data sent with the form to
        // be returned to the backend
        // currently used for join information
        if (form_data.join_data){
            join_data = form_data.join_data;
        } else {
            join_data = false;
        }

        if ($.Util.is_empty(errors)){
            //FIXME Toby {id}  if (fields){
            return {form:form_data.name, data : data, join_data : join_data};
        } else {
            save_errors(errors);
            return false;
        }
    }

    function get_form_data(){
        /* get our data to save.
         * we want to return any relevant sent data _version etc
         * but not unneeded info around buttons or messages
         * if the data has been updated this also needs to be reflected
         * additionally extra parameter data may also be present that needs returning
         *
         * we also make a copy of the row data for the fields that we have the
         * potential to update.
         */
        var save_data = {};

        for (var item in row_data){
            // skip unwanted data that we have been sent.
            if (item != '__buttons' && item != '__message'){
                save_data[item] = row_data[item];
            }
        }
        var copy_of_row_info = {};
        var row_info = get_row_info();
        var extra;

        for (item in row_info){
            save_data[item] = row_info[item];
            copy_of_row_info[item] = row_info[item];
        }
        // any extra data needed from the form
        params = form_data.params;
        if (params && params.extras){
            for (extra in params.extras){
                if (params.extras.hasOwnProperty(extra)){
                    save_data[extra] = params.extras[extra];
                }
            }
        }
        if (extra_defaults){
            for (extra in extra_defaults){
                if (extra_defaults.hasOwnProperty(extra)){
                    save_data[extra] = extra_defaults[extra];
                }
            }
        }
        return {save_data : save_data,
                copy_of_row_info : copy_of_row_info};
    }
    function validate_form_data(data){
        var item;
        var errors = {};
        var error;
        for (var i = 0, n = form_data.fields.length; i < n ; i++){
            item = form_data.fields[i];

            if (item.validation){
                error = validate(item.validation, data[item.name], false);
                if (error.length > 0){
                    errors[item.name] = error;
                }
            }
        }
        return errors;
    }

    function save(){
        var info = get_form_data();
        var errors = validate_form_data(info);
        if ($.Util.is_empty(errors)){
            get_node_return(form_data.node, '_save', info.save_data, $form, info.copy_of_row_info);
        } else {
            save_errors(errors);
        }
    }

    function save_return(data){
        // errors
        if (data.errors && data.errors['null']){
            save_errors(data.errors['null']);
        }
        // saves  FIXME what do we want to do here?
        if (data.saved){

            remove_all_errors();
//            save_update(data.saved[0], data.obj_data); // single form so only want first saved item
        }
    }

    function get_control_value(item, $item){

        switch (item.control){
            case 'image':
            case 'thumb':
            case 'file_upload':
                return $item.find("input:first").data('value');
            case 'wmd':
            case 'textarea':
                return $item.find("textarea:first").val();
            case 'dropdown_code':
                return get_key_from_description(item, $item.find("input:first").val());
            case 'checkbox':
                return $item.find("div.CHECKBOX").data('value');
            case 'codegroup':
                return get_codegroup_values($item, item);
            default:
                return $item.find("input:first").val();
        }
    }

    function get_codegroup_values($item, item){
        var $checkboxes = $item.find("div.CHECKBOX");
        var codes = item.codes;
        var values = {};
        for (var i = 0, n = $checkboxes.size(); i < n; i++){
            values[codes[i][0]] = $checkboxes.eq(i).data('value');
        }
        return values;
    }

    function get_key_from_description(item, value){
        // convert a description into a key
        // used by dropdown_code
        var descriptions = item.autocomplete.descriptions;
        var keys = item.autocomplete.keys;
        for (var i = 0, n = descriptions.length; i < n; i++){
            if (value == descriptions[i]){
                return keys[i];
            }
        }
        // There is no valid key.
        return null;
    }

    function get_row_info(){
        var row_info = {};
        var value;
        var cleaned;
        var field;
        var $control;
        var item;

        for (var i = 0, n = form_data.fields.length; i < n; i++){
            item = form_data.fields[i];
            if (item.name){
                $control = form_controls_hash[item.name];
                if (item.layout){
                    continue;
                } else if (item.control){
                    value = get_control_value(item, $control);
                } else {
                    value = $control.find("input:first").val();
                }
                cleaned = $.Util.clean_value(value, item);
                row_info[item.name] = cleaned.value;
            }
        }
        return row_info;

    }

    function form_mousedown(e){
        var actioned = false;
        var item = e.target;
        var $item = $(e.target);
        var fn_finalise;
        var $field;
        var $img;
        // if this control is complex eg. dropdown.
        if ($item[0].nodeName == 'DIV' || $item[0].nodeName == 'IMG'){
            if ($item.hasClass('data')){
                $item = $item.parent();
            } else if ($item.hasClass('but_dd_f')){
                $item = $item.parent().find('input');
                $item.focus();
                $item.trigger('dropdown');
                actioned = true;
            } else if ($item.hasClass('but_dd_img_f')){
                $item = $item.parent().parent().find('input');
                $item.focus();
                $item.trigger('dropdown');
                actioned = true;
            }
           // $field = $(item).parent().parent('div');
        }

        return !actioned;
    }

    var set_class_list = $.Util.set_class_list;

    var form_controls_hash; // holder for the form controls

    function build_form(){

        var $builder;
        var $control;
        var builder_depth;
        var num_fields;
        var item;
        var value;

        var paging_bar;

        function add_layout_item(item){
            switch (item.layout){
                case 'text':
                    var text = process_html(item.text, local_row_data);
                    $builder[builder_depth].append('<div class="f_control_holder f_text">' + text + '</div>');
                    break;
                case 'spacer':
                    $builder[builder_depth].append('<div class="f_control_holder f_spacer">');
                    break;
                case 'hr':
                    $builder[builder_depth].append('<div class="f_control_holder"><hr/></div>');
                    break;
                case 'column_start':
                    $builder.push($('<div ' + set_class_list(item, "COLUMN") + '>'));
                    builder_depth++;
                    break;
                case 'column_next':
                    if (builder_depth > 0){
                        $builder[--builder_depth].append($builder.pop());
                        $builder.push($('<div ' + set_class_list(item, "COLUMN") + '>'));
                        builder_depth++;
                    }
                    break;
                case 'column_end':
                    if (builder_depth > 0){
                        $builder[--builder_depth].append($builder.pop());
                    }
                    break;
                case 'box_start':
                    $builder.push($('<div ' + set_class_list(item, "BOX") + '>'));
                    builder_depth++;
                    break;
                case 'area_start':
                    $builder.push($('<div ' + set_class_list(item) + '>'));
                    builder_depth++;
                    break;
                case 'listing_start':
                    $builder.push($('<div ' + set_class_list(item, "RESULT_ITEM") + '>'));
                    builder_depth++;
                    var link_node = $.Util.build_node_link(local_row_data);
                    var img = '<div class="RESULT_IMG" onclick="' + link_node + '" ><img src="/attach?' + local_row_data.thumb + '.s" /></div>';
                    $builder[builder_depth].append(img);
                    $builder.push($('<div class="RESULT_DATA" >'));
                    builder_depth++;
                    break;
                case 'listing_end':
                    if (builder_depth > 0){
                        $builder[--builder_depth].append($builder.pop());
                    }
                    // drop through so outer div is also closed!
                    // JSlint complains here but intentional
                case 'box_end':
                case 'area_end':
                    if (builder_depth > 0){
                        $builder[--builder_depth].append($builder.pop());
                    }
                    break;
                default:
                    console_log('unknown layout ' + item.layout);
            }
        }

        function build_form_items(){
            var item;
            var value;
            var $control;
            var control_function;
            var ro = form_data.read_only;
            REBASE.FormControls.set_data(local_row_data);

            // results item box
            if (form_data.form_type == 'results'){
                item = {layout : 'listing_start'};
                add_layout_item(item, $builder, builder_depth);
            }
            // FIXME this needs to be something different __thumb?
            if (form_data.thumb){
                img_value = local_row_data[form_data.thumb.name];
                item = {control : 'image', css: 'img_large', size: 'l'};
                var $thumb = REBASE.FormControls.build(ro, item, img_value);
                $thumb = $('<div class="RECORD_IMG">').append($thumb);
                $builder[builder_depth].append($thumb);
                form_controls_hash[form_data.thumb.name] = $thumb;
            }

            for (var i = 0; i < num_fields; i++){
                item = form_data.fields[i];
                value = $.Util.get_item_value(item, local_row_data);
                if (item.layout){
                    add_layout_item(item, $builder, builder_depth);
                } else {
                    $control = REBASE.FormControls.build(ro, item, value);
                    if ($control){
                        $builder[builder_depth].append($control);
                        form_controls_hash[item.name] = $control;
                    }
                }
            }

            if (form_data.form_type == 'results'){
                item = {layout : 'listing_end'};
                add_layout_item(item, $builder, builder_depth);
            }

        }


        $form.empty();
        form_controls_hash = {};
        builder_depth = 0;
        num_fields = form_data.fields.length;
        $builder = [$('<div/>')];
        // form message
        if (!$.Util.is_empty(row_data.__message)){
            $control = REBASE.FormControls.build(true, {control : 'message_area'}, row_data.__message);
            $builder[builder_depth].append($control);
        }
        // paging bar
        // FIXME why extra_data should be paging_data?
        if (extra_defaults){
            // cache the html for reuse
            paging_bar = make_paging(extra_defaults);
            $builder[builder_depth].append(paging_bar);
        }
        item = {layout : 'area_start'};
        add_layout_item(item, $builder, builder_depth);
        // main form
        if (!row_data.__array){
            local_row_data = row_data;
            build_form_items();
        } else {
            // continuous forms
            for (var i = 0, n = row_data.__array.length; i <  n; i++){
                local_row_data = row_data.__array[i];
                build_form_items();
            }
        }
        // form buttons
        if (row_data.__buttons){
            item = { buttons : row_data.__buttons, control: 'button_box'};
            value = $.Util.get_item_value(item, row_data);
            $control = REBASE.FormControls.build(true, item, value);
            $builder[builder_depth].append($control);
        }
        // second paging bar
        if (paging_bar){
            $builder[builder_depth].append(paging_bar);
        }
        // close any builder divs
        while (builder_depth > 0){
            $builder[--builder_depth].append($builder.pop());
        }

        $form.append($builder[0].contents());

    }

    // custom events
    custom_commands = {
        'unbind_all' : unbind_all,
        'register_events' : register_events,
        'save' : save,
        'save_return' : save_return,
        'get_form_data' : get_form_data_remote
    };

    init();
};

$.StatusForm = function(input){
    var $input = $(input);
    $.Util.unbind_all_children($input);

    // make our div that everything will hang off
    var $form = $('<div class="STATUS_FORM"></div>');
    $input.append($form);

    var custom_commands;

    function command_caller(type, data){
        if (custom_commands[type]){
            return custom_commands[type](data);
        } else {
            alert('command: <' + type + '> has no handler');
            return false;
        }
    }


//   $form.data('command')('register_events');
    var html = [];

    html.push('<p>STATUS</p>');
    html.push('<p>Job #: <div id="status_job_id"></div></p>');
    html.push('<p>Started: <div id="status_job_started"></div></p>');
    html.push('<p>Message: <div id="status_job_message"></div></p>');
    html.push('<p>Progress: <div id="status_job_progress"></div></p>');

    $form.html(html.join(''));
    $("#status_job_progress").progressbar();

    $form.data('command', command_caller);

    function update_status(data){
        var message = data.message;
        if (message !== null){
            // make readable especially errors
            message = String(message).replace(/\n/g, '<br/>');
        }
        $('#status_job_id').text(data.id);
        $('#status_job_started').text($.Util.format_data(data.start, 'd'));
        $('#status_job_message').html(message);
        if (data.percent === null){
            data.percent = 0;
        }
        $('#status_job_progress').progressbar('value', data.percent);
    }

    function unbind_all(){
        $input.unbind();
    }

    // custom events
    custom_commands = {
        'unbind_all' : unbind_all,
        'update' : update_status
    };

};

function make_paging(extra_defaults){
    // FIXME this function is global and should be somewhere else
    // shared between grid2 and input_form
    // build a paging bar
    var PAGING_SIZE = 5;
    var offset = extra_defaults.offset;
    var limit = extra_defaults.limit;
    var count = extra_defaults.row_count;
    var base = extra_defaults.base_link;

    var pages = Math.ceil(count/limit);
    var current = Math.floor(offset/limit);
    var link;
    var href;

    var use_href = (base.substring(0,1) == 'n');

    var html = '<div class="PAGING_BAR">';

    function make_href(){
        if (use_href){
            return 'href="#' + link + '" ';
        } else {
            return 'href="#" ';
        }
    }

    html += 'paging: ';

    if (current>0){
        link = base + '&o=0&l=' + limit;
        html += '<a ' + make_href() + 'onclick="node_load(\'' + link +'\');return false;">|&lt;</a> ';
        link = base + '&o=' + (current-1) * limit + '&l=' + limit;
        html += '<a ' + make_href() + 'onclick="node_load(\'' + link +'\');return false;">&lt;</a> ';
    } else {
        html += '|&lt; ';
        html += '&lt; ';
    }
    for (var i=0; i < pages; i++){
        if (i == current){
            html += (i+1) + ' ';
        } else {
            if ( Math.abs(current-i)<PAGING_SIZE ||
                 (i<(PAGING_SIZE*2)-1 && current<PAGING_SIZE) ||
                 (pages-i<(PAGING_SIZE*2) && current>pages-PAGING_SIZE)
            ){
                link = base + '&o=' + i * limit + '&l=' + limit;
                html += '<a ' + make_href() + 'onclick="node_load(\'' + link + '\');return false;">' + (i+1) + '</a> ';
            }
        }
    }
    if (current<pages - 1){
        link = base + '&o=' + (current+1) * limit + '&l=' + limit;
        html += '<a ' + make_href() + 'onclick="node_load(\'' + link + '\');return false;">&gt;</a> ';
        link = base + '&o=' + (pages-1) * limit + '&l=' + limit;
        html += '<a ' + make_href() + 'onclick="node_load(\'' + link +'\');return false;">&gt;|</a> ';
    } else {
        html += '&gt; ';
        html += '&gt;| ';
    }

    html += 'page ' + (current+1) + ' of ' + pages + ' pages';
    html += ', ' + (count) + ' records';
    html += '</div>';
    return html;
}


$.Grid2 = function(input, form_data, row_data, extra_defaults){

    var $input = $(input);
    var message = row_data.__message;
    var buttons = row_data.__buttons;
    row_data = row_data.__array;

    var custom_commands;

    function command_caller(type, data){
        if (custom_commands[type]){
            return custom_commands[type](data);
        } else {
            alert('command: <' + type + '> has no handler');
            return false;
        }
    }
    function build_grid(){


        function build_header(){
            var html = [];
            var item;
            html.push('<tr>');
            for (var i = 0; i < num_fields; i++){
                html.push('<th>');
                item = form_data.fields[i];
                html.push(item.title);
                html.push('</th>');
            }
            html.push('</tr>');
            return html.join('');
        }


        function build_data_row(data){
            var html = [];
            var item;
            var control;

            function build_value(){
                var value = $.Util.get_item_value(item, data);
                if (value === ''){
                    value = '&nbsp;';
                } else if (value === null){
                    value = 'Null';
                }
                return correct_value(item, value);
            }

            function build_link(){
                var value = '';
                if (item.field && data[item.field] !== undefined){
                    value = item.field + '=' + data[item.field];
                }
                return '<a href="#" onclick="node_load(\'' + item.base_link + value + '\',this,\'' + item.target_form + '\');return false">' + item.title + '</a>';
            }


            html.push('<tr>');
            for (var i = 0; i < num_fields; i++){
                html.push('<td>');
                item = form_data.fields[i];
                if (item.control == 'grid_link'){
                    control = build_link();
                } else {
                    control = build_value();
                }
                html.push(control);
                html.push('</td>');
            }
            html.push('</tr>');
            return html.join('');

        }

        function build_empty_row(){
            var html = [];
            html.push('<tr>');
            for (var i = 0; i < num_fields; i++){
                html.push('<td>&nbsp;</td>');
            }
            html.push('</tr>');
            return html.join('');
        }

        function correct_value(item, value){

            // correct data value if needed
            switch (item.data_type){
                case 'DateTime':
                case 'Date':
                    if (value !== null){
                        return Date.ISO(value).makeLocaleString();
                    } else {
                        return null;
                    }
                    break;
                case 'Boolean':
                    if (value){
                        return "True";
                    } else {
                        return "False";
                    }
                    break;
                default:
                    return HTML_Encode_Clear(value);
            }
        }

        function build_data(){
            var html = [];
            for (var i = 0; i < row_data.length; i++){
                html.push(build_data_row(row_data[i]));
            }
            // add empty rows to make correct number
            for (; i < NUM_TABLE_ROWS; i++){
                html.push(build_empty_row());
            }
            return html.join('');
        }
        var NUM_TABLE_ROWS = 5;
        var $builder = $('<div class="INPUT_FORM" >');
        $builder.data('command', command_caller);
        var paging_bar;
        var $control;
        var value;
        var html = [];

        // form message
        if (!$.Util.is_empty(message)){
            $control = REBASE.FormControls.build(true, {control : 'message_area'}, message);
            $builder.append($control);
        }
        // paging bar
        // FIXME why extra_data should be paging_data?
        if (extra_defaults){
            // cache the html for reuse
            paging_bar = make_paging(extra_defaults);
            $builder.append(paging_bar);
        }
        html.push('<table>');
        html.push(build_header());
        html.push(build_data());
        html.push('</table>');
        $builder.append(html.join(''));
        // form buttons
        if (buttons){
            item = { buttons : buttons, control: 'button_box'};
            value = $.Util.get_item_value(item, row_data);
            $control = REBASE.FormControls.build(true, item, value);
            $builder.append($control);
        }
        // second paging bar
        if (paging_bar){
            $builder.append(paging_bar);
        }
        $input.append($builder);
    }

    function get_form_data(){
        return {form : form_data.form_name, data : {}};
    }


    // custom events
    custom_commands = {
        'get_form_data' : get_form_data
    };

    var HTML_Encode_Clear = $.Util.HTML_Encode_Clear;
    var num_fields = form_data.fields.length;
    build_grid();
};

})(jQuery);
