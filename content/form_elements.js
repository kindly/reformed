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

*/


// JSLint directives
/*global $ REBASE */


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    FORM CONTROLS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Generatable form items.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.FormControls = function(){

    var ID_STEM = 'RB_'

    // This will hold the current form data
    var local_row_data = {};
    var control_build_functions;
    var id_counter = 0;
    var id_name;

    var HTML_Encode_Clear;
    var make_item_class;
    var process_html;
    var is_update_node;

    var build_node_link;
    var build_node_link_href;

    function init(){
        HTML_Encode_Clear = REBASE.Form.HTML_Encode_Clear;
        make_item_class = REBASE.Form.make_item_class;
        process_html = REBASE.Form.process_html;
        is_update_node = REBASE.Node.is_update_node;
        build_node_link = $.Util.build_node_link;
        build_node_link_href = $.Util.build_node_link_href;
    }

    function add_label(item){
        // basic label
        if (item.title){
            return '<label class="form_label">' + item.title + '</label>';
        } else {
            return '';
        }
    }

    function add_label_for(item){
        // label with for attribute
        if (item.title){
            return '<label class="form_label" for="' + id_name + '">' + item.title + '</label>';
        } else {
            return '';
        }
    }

    function correct_value(item, value){
        if (value === null && item['default'] !== undefined){
            value = item['default'];
        }
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

    function form_description(item){
        if (item.description){
            return '<div class="f_description">' + process_html(item.description, local_row_data, true) + '</div>';
        } else {
            return '';
        }
    }

    function textbox(item, value){
        value = correct_value(item, value);
        var $control = add_label_for(item) + '<input id="' + id_name + '"' + make_item_class(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '"/>';
        return $control;
    }

    function datebox(item, value){
        value = correct_value(item, value); // FIXME should this be a more specific fix_date() call
        var $control = $(add_label_for(item) + '<input id="' + id_name + '"' + make_item_class(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '" />');
        var index = item.title ? 1 : 0
        $control.eq(index).bind('keydown', $.Util.datebox_key);
        return $control;
    }

    function intbox(item, value){
        var $control = $(add_label_for(item) + '<input id="' + id_name + '"' + make_item_class(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '" />');
        var index = item.title ? 1 : 0
        $control.eq(index).bind('keydown', $.Util.intbox_key);
        $control.eq(index).bind('change', $.Util.intbox_change);
        return $control;
    }

    function link(item, value){
        return '<a href="#/' + item.node + '"' + make_item_class(item, 'link') + ' onclick="node_load(\'' + item.node + '\',this);return false;">' + item.title + '</a>';
    }

    function result_link(item, value, base_link){
        var link_node = build_node_link(local_row_data, base_link);
        var link_node_href = build_node_link_href(local_row_data, base_link);
        var x = '<a href="' + link_node_href + '"' + make_item_class(item, 'link') + ' onclick="' + link_node + 'return false;">' + (value ? value : 'untitled') + '</a>';
        return x;
    }

    function result_link_list(item, value){
        var values;
        if (item.link_list){
            values = item.link_list;
        } else {
            values = value;
        }
        var temp = '';
        var info;
        for (var i = 0, n = values.length; i < n; i++){
            info = values[i];
            temp += result_link(item, info[0], info[1]) + '  ';
        }
        return temp;
    }

    function result_image(item, value){
        var size;
        var link_node = "" + REBASE.application_data.bookmarks[local_row_data.entity].node;
        link_node += ":edit?__id=" + local_row_data.__id;
        if (item.size){
            size = '.' + item.size;
        } else {
            size = '.m';
        }
        var $control = '<div' + make_item_class(item, 'HOLDER') + ' onclick="node_load(\'' + link_node + '\',this);" ><img src="/attach?' + value + size + '" /></div>';
        return $control;
    }

    function button(item, value){
        var target_form = item.target_form || '';
        return '<button' + make_item_class(item, 'button') + ' onclick="node_load(\'' + item.node + '\',this,\'' + target_form + '\');return false;">' + item.title + '</button>';
    }

    function button_box(item, value){
        var html = '';
        var but = {};
        var buttons = item.buttons;
        if (item.css){
            but.css = item.css;
        }
        for (var i = 0, n = buttons.length; i < n; i++){
            but.node = buttons[i][1];
            but.title = buttons[i][0];
            if (buttons[i].length > 2){
                but.target_form = buttons[i][2];
            } else {
                but.target_form = null;
            }
            html += button(but);
        }
        return html;
    }

    function button_link(item, value){
        return '<a href="#/' + item.node + '"' + make_item_class(item, 'link') + ' onclick="node_load(\'' + item.node + '\',this);return false">' + item.title + '</a>';
    }

    function dropdown_core(item, value, autocomplete){
        var $control;
        var class_list = 'dropdown_f';
        value = correct_value(item, value);
        if (item.css){
            class_list += ' ' + item.css;
        }
        // if autocomplete is 'DATA' then this uses form data for the items
        if (autocomplete == 'DATA' && item.data_field){
            autocomplete = local_row_data[item.data_field];
        }
        $control = $(add_label_for(item) + '<div class="' + class_list + ' complex"><input id="' + id_name + '" class="dropdown_input" value="' + value + '" /><div class="but_dd_f"><img onclick="REBASE.Form.dropdown_click(\'' + id_name + '\')" class="but_dd_img_f" src="/bullet_arrow_down2.png" /></div></div>');
        $control.find('input').autocomplete(autocomplete, {dropdown : true});
        return $control;
    }

    function dropdown_code(item, value){
        var descriptions = item.autocomplete.descriptions;
        var keys = item.autocomplete.keys;
        if (value !== null){
            value = value[1];
        }
        return dropdown_core(item, value, descriptions);
    }

    function dropdown(item, value){
        return dropdown_core(item, value, item.autocomplete);
    }

    function autocomplete(item, value){
        var $control;
        var autocomplete_url = '/ajax/' + item.autocomplete;
        var class_list = 'dropdown_f';
        value = correct_value(item, value);
        if (item.css){
            class_list += ' ' + item.css;
        }
        $control = $(add_label_for(item) + '<span class="' + class_list + ' complex"><input id="' + id_name + '" class="DROPDOWN ' + class_list + '" value="' + value + '" /></span>');
        $control.find('input').autocomplete(autocomplete_url, {dropdown : false});
        return $control;
    }

    function wmd(item, value){
        var $control = $(add_label_for(item) + '<div' + make_item_class(item, 'HOLDER') + '><textarea id="' + id_name + '" >' + HTML_Encode_Clear(value) + '</textarea></div>');
        $control.find('textarea').wmd();
        return $control;
    }

    function file_upload(item, value){
        var $control = $(add_label_for(item) + '<div' + make_item_class(item, 'HOLDER') + '"><input  id="' + id_name + '" class="img_uploader" type="file" /></div>');
        var data = {type : 'normal', value : value};
        $control.find('input').file_upload(data);
        return $control;
    }

    function textarea(item, value){
        var $control = $(add_label_for(item) + '<textarea id="' + id_name + '" ' + make_item_class(item) + '>' + HTML_Encode_Clear(value) + '</textarea>');
        return $control;
    }

    function plaintext(item, value){
        value = correct_value(item, value);
        var $control = $(add_label(item) + '<span' + make_item_class(item) + '>' + HTML_Encode_Clear(value) + '</span>');
        return $control;
    }

    function markdown(item, value){
        if (value){
            value = process_html(value, local_row_data);
        }
        var $control = $(add_label(item) + '<span' + make_item_class(item) + '>' + value + '</span>');
        return $control;
    }

    function plain_date(item, value){
        if (value === null){
            value = '';
        } else {
            value = Date.ISO(value).toLocaleDateString();
        }
        var $control = $(add_label(item) + '<span' + make_item_class(item) + '>' + value + '</span>');
        return $control;
    }

    function plain_dropdown_code(item, value){
        if (value !== null){
            value = value[1];
        }
        return plaintext(item, value);
    }

    function message_area(item, message){
        message = process_html(message, local_row_data);
        var css;
        if (message.type == 'error'){
            css = ' f_message_error';
        } else {
            css = '';
        }
        return '<div class="f_message' + css + '">' + message + '</div>';
    }

    function htmlarea(item, value){
        return add_label(item) + '<div' + make_item_class(item) + '>' + value + '</div>';
    }

    function text(item, value){
        if (item.text !== undefined){
            value = process_html(item.text, local_row_data);
        }
        return '<div' + make_item_class(item) + '>' + value + '</div>';
    }

    function password(item, value){
        return add_label_for(item) + '<input  id="' + id_name + '" type="password"' + make_item_class(item, 'inputbox') + ' value="' + HTML_Encode_Clear(value) + '"/>';
    }

    function checkbox(item, value){
        var $control;
        var class_list = '';
        if (item.css){
            class_list += ' ' + item.css;
        }
        if (item.reverse){
            $control = $('<div class="CHECKBOX ' + class_list + '"><input  id="' + id_name + '" type="button"/><img src="/tick.png" />&nbsp;</div>' + add_label_for(item));
            $control.eq(0).filter('div').checkbox(item, value);
        } else {
            $control = $(add_label_for(item) + '<div class="CHECKBOX ' + class_list + '"><input  id="' + id_name + '" type="button" /><img src="/tick.png" />&nbsp;</div>');
            $control.eq(1).filter('div').checkbox(item, value);
        }
        return $control;
    }

    function codegroup(item, value){

        var cbox = {'validation' : [{'not_empty' : true } ]};
        if (item.css){
            cbox.css = item.css;
        }
        var $div = $('<div class="CODEGROUP" />');
        if (item.title){
            $div.append('<div class="f_codegroup_title">' + item.title + '</div>');
        }
        var codes = item.codes;
        var holder;
        var code;
        var cbox_value;
        var $holder;
        var m;
        if (value){
            m = value.length;
        } else {
            m = 0;
        }
        if (codes){
            for (var i = 0, n = codes.length; i < n; i++){
                code = codes[i][0];
                cbox_value = false;
                for(var j = 0; j < m; j++){
                    if (value[j] == code){
                        cbox_value = true;
                        break;
                    }
                }
                cbox.title = codes[i][1];
                cbox.code = codes[i][0];
                cbox.reverse = true;
                $holder = $('<div class="f_codegroup_holder">');
                if (codes[i].length > 2){
                    cbox.description = codes[i][2];
                    $holder.append(form_description(cbox));
                }
                $div.append($holder.append(checkbox(cbox, cbox_value)));
            }
        }
        return $div;
    }

    function info_area(item, value){
        if (value){
            value = process_html(value, local_row_data);
        }
        return value;
    }

    function link_new(item, value){
        var link_node = value[1];
        value = value[0];
        var href;
        if (is_update_node(link_node)){
            href = "#" + link_node;
        } else {
            href = "#";
        }
        var x = '<a href="' + href + '"' + make_item_class(item, 'link') + ' onclick="node_load(\'' + link_node + '\',this);return false">' + (value ? value : '&nbsp;') + '</a>';
        return x;
    }

    function link_list(item, value){
        var values;
        if (item.values){
            values = item.values;
        } else {
            values = value;
        }
        var temp = '';
        for (var i = 0, n = values.length; i < n; i++){
             temp += link_new(item, values[i]) + '  ';
        }
        return temp;
    }

    function image(item, value){
        var size;
        if (!item.css){
            item.css = 'img_medium';
            size = 'm';
        }
        if (item.size){
            size = item.size;
        }

        var $control = $(add_label_for(item) + '<div' + make_item_class(item, 'HOLDER') + '"><label class="img_upload_label"><input id="' + id_name + '" class="img_uploader" type="file" tabindex="-1" /></label></div>');
        var data = {type : 'image', value : value, size : size};
        $control.find('input').file_upload(data);
        return $control;
    }

    function image_ro(item, value){
        var size;
        if (item.size){
            size = '.' + item.size;
        } else {
            size = '.m';
        }
        var $control = '<div' + make_item_class(item, 'HOLDER') + '><img src="/attach?' + value + size + '" /></div>';
        return $control;
    }

    function build(readonly, item, value){
        // create unique id_name for labels
        id_counter++;
        id_name = ID_STEM + id_counter;

        var ro = readonly ? 1 : 0;
        var control = item.control;
        var $div = $('<div class="f_control_holder"/>');
        var $div2;
            if (control_build_functions[control]){
                // the extra div is to help with styling
                // specifically padding etc
                // but some controls eg images do not want this
                if (!control_build_functions[control][2]){
                    $div2 = $('<div class="f_sub" >' + form_description(item) + '</div>');
                    $div2.append(control_build_functions[control][ro](item, value));
                    $div.append($div2);
                } else {
                    $div.append(form_description(item));
                    $div.append(control_build_functions[control][ro](item, value));
                }
            } else {
                $div.append('UNKNOWN: ' + item.control);
            }
        return $div;
    }

    // these are the available functions
    // the 3rd element set to a true value will stop the f_sub div being added
    control_build_functions = {
        'normal': [textbox, plaintext], // FIXME duplicate?
        'message_area': [message_area, message_area],
        'intbox': [intbox, plaintext],
        'textbox': [textbox, plaintext],
        'datebox': [datebox, plain_date],
        'dropdown_code': [dropdown_code, plain_dropdown_code],
        'wmd': [wmd, markdown],
        'textarea': [textarea, plaintext],
        'text': [text, text],
        'password': [password, plaintext],
        'button': [button, button],
        'button_link': [button_link, plaintext],
        'button_box': [button_box, button_box],
        'result_link_list': [result_link_list, result_link_list],
        'result_link': [result_link, result_link],
        'result_image': [result_image, result_image],
        'html': [htmlarea, plaintext],
        'checkbox': [checkbox, plaintext],
        'link': [link, link],
        'dropdown': [dropdown, plaintext],
        'info': [info_area, info_area],
        'link_list': [link_list, link_list],
        'codegroup': [codegroup, codegroup],
        'file_upload' : [file_upload, file_upload],
        'image' : [image, image_ro, true],
        'autocomplete' : [autocomplete, plaintext]
    };

    return {
        'build' : function(readonly, item, value){
            return build(readonly, item, value);
        },
        'set_data' : function(data){
            local_row_data = data;
        },
        'init' : function(){
            init();
        }
    };
}();
