$FormElements = function(){

    function add_label(item, prefix){
        if (item.title){
            return '<label class="form_label" for="' + prefix + item.name + '">' + item.title + '</label>';
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
                    return "True"
                } else {
                    return "False"
                }
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

    function input_box(item, value){
        value = correct_value(item, value);
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item) + ' value="' +  HTML_Encode_Clear(value) + '"/>');
        return $control;
    }

    function textbox(item, value){
        value = correct_value(item, value);
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item) + ' value="' +  HTML_Encode_Clear(value) + '"/>');
        return $control;
    }

    function datebox(item, value){
        value = correct_value(item, value); // FIXME should this be a more specific fix_date() call
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item) + ' value="' +  HTML_Encode_Clear(value) + '" />');
        // FIXME will fail if no label
        $control.eq(1).bind('keydown', $.Util.datebox_key);
        return $control;
    }

    function intbox(item, value){
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item) + ' value="' +  HTML_Encode_Clear(value) + '" />');
        // FIXME will fail if no label
        $control.eq(1).bind('keydown', $.Util.intbox_key);
        $control.eq(1).bind('change', $.Util.intbox_change);
        return $control;
    }


    function link(item, value){
        var split = value.split("|");
        var link_node = split.shift();
        value = split.join('|');
        var x = '';
        if (link_node.substring(0,1) == 'n'){
            x += '<a href="#"' + set_class_list(item, 'link') + ' onclick="node_load(\'' + link_node + '\');return false">' + (value ? value : 'untitled') + '</a>';
        }
        if (link_node.substring(0,1) == 'd'){
            x += '<a href="#"' + set_class_list(item, 'link') + ' onclick ="link_process(this,\'' + link_node + '\');return false;">' + (value ? value : 'untitled') + '</a>';
        }
        return x;
    }

    function result_link(item, value){
        var link_node = $.Util.build_node_link(local_row_data);
        var x = '<a href="#"' + set_class_list(item, 'link') + ' onclick="' + link_node + 'return false;">' + (value ? value : 'untitled') + '</a>';
        return x;
    }

    function result_image(item, value){
        var link_node = "n:" + REBASE.application_data.bookmarks[local_row_data.entity].node;
        link_node += ":edit:__id=" + local_row_data.__id
        if (item.size){
            size = '.' + item.size;
        } else {
            size = '.m';
        }
        var $control = '<div' + set_class_list(item, 'HOLDER') + ' onclick="node_load(\'' + link_node + '\');" ><img src="/attach?' + value + size + '" /></div>';
        return $control
    }

    function button_box(item, value){
        var html = '';
        var but = {};
        var buttons = item.buttons;
        if (item.css){
            button.css = item.css;
        }
        for (var i = 0, n = buttons.length; i < n; i++){
            but.node = buttons[i][1];
            but.title = buttons[i][0];
            html += button(but);
        }
        return html;
    }

    function button_link(item, value){
        return '<a href="#/n:' + item.node + '"' + set_class_list(item, 'link') + ' onclick="node_button_input_form(this, \'' + item.node + '\');return false">' + item.title + '</a>';
    }

    function button(item, value){
        return '<button' + set_class_list(item, 'button') + ' onclick="node_button_input_form(this, \'' + item.node + '\');return false">' + item.title + '</button>';
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
        $control = $(add_label(item, 'rf_') + '<span class="' + class_list + ' complex"><input id="rf_' + item.name + '" class="DROPDOWN ' + class_list + '" value="' + value + '" /><div class="but_dd_f"/></span>');
        $control.find('input').autocomplete(autocomplete, {dropdown : true});
        return $control;
    }

    function autocomplete(item, value){
        var $control;
        var autocomplete = '/ajax/' + item.autocomplete;
        var class_list = 'dropdown_f';
        value = correct_value(item, value);
        if (item.css){
            class_list += ' ' + item.css;
        }
        $control = $(add_label(item, 'rf_') + '<span class="' + class_list + ' complex"><input id="rf_' + item.name + '" class="DROPDOWN ' + class_list + '" value="' + value + '" /></span>');
        $control.find('input').autocomplete(autocomplete, {dropdown : false});
        return $control;
    }

    function wmd(item, value){
        var $control = $(add_label(item, 'rf_') + '<div' + set_class_list(item, 'HOLDER') + '><textarea>' + HTML_Encode_Clear(value) + '</textarea></div>');
        $control.find('textarea').wmd();
        return $control;
    }

    function file_upload(item, value){
        var $control = $(add_label(item, 'rf_') + '<div' + set_class_list(item, 'HOLDER') + '"><input class="img_uploader" type="file" /></div>');
        var data = {type : 'normal', value : value}
        $control.find('input').file_upload(data);
        return $control
    }

    function textarea(item, value){
        var $control = $(add_label(item, 'rf_') + '<textarea' + set_class_list(item) + '>' + HTML_Encode_Clear(value) + '</textarea>');
        return $control;
    }

    function plaintext(item, value){
        value = correct_value(item, value);
        var $control = $(add_label(item, 'rf_') + '<span' + set_class_list(item) + '>' + HTML_Encode_Clear(value) + '</span>');
        return $control;
    }

    function markdown(item, value){
        if (value){
            value = process_html(value, local_row_data);
        }
        var $control = $(add_label(item, 'rf_') + '<span' + set_class_list(item) + '>' + value + '</span>');
        return $control;
    }

    function plain_date(item, value){
        if (value === null){
            value = '';
        } else {
            value = Date.ISO(value).toLocaleDateString();
        }
        var $control = $(add_label(item, 'rf_') + '<span' + set_class_list(item) + '>' + value + '</span>');
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
        return add_label(item, 'rf_') + '<div' + set_class_list(item) + '>' + value + '</div>';
    }

    function text(item, value){
        if (item.text !== undefined){
            value = process_html(item.text, local_row_data);
        }
        return '<div' + set_class_list(item) + '>' + value + '</div>';
    }

    function password(item, value){
        return add_label(item, 'rf_') + '<input type="password"' + set_class_list(item) + ' value="' + HTML_Encode_Clear(value) + '"/>';
    }

    function checkbox(item, value){
        var class_list = '';
        if (item.css){
            class_list += ' ' + item.css;
        }
        if (item.reverse){
            $control = $('<div class="CHECKBOX ' + class_list + '"><input type="button" style="width:20px;" />&nbsp;</div>' + add_label(item, 'rf_'));
            $control.eq(0).filter('div').checkbox(item, value);
        } else {
            $control = $(add_label(item, 'rf_') + '<div class="CHECKBOX ' + class_list + '"><input type="button" style="width:20px;" />&nbsp;</div>');
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
        var m;
        if (value){
            m = value.length;
        } else {
            m = 0;
        }
        if (codes){
            for (var i = 0, n = codes.length; i < n; i++){
                code = codes[i][0]
                cbox_value = false
                for(var j = 0; j < m; j++){
                    if (value[j] == code){
                        cbox_value = true;
                        break;
                    }
                }
                cbox.title = codes[i][1];
                cbox.code = codes[i][0];
                if (codes[i].length > 2){
                    cbox.description = codes[i][2];
                }
                cbox.reverse = true;
                $holder = $('<div class="f_codegroup_holder">');
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


    function add_subform(item, value){
        subforms.push({item: item, data: value});
        return '<div class="SUBFORM"></div>';
    }


    function link_new(item, value){
        var link_node = value[1];
        value = value[0];
        var x = '';
        if (link_node.substring(0,1) == 'n'){
            x += '<a href="#/' + link_node + '"' + set_class_list(item, 'link') + ' onclick="node_load(\'' + link_node + '\');return false">' + (value ? value : '&nbsp;') + '</a>';
        }
        if (link_node.substring(0,1) == 'd'){
            x += '<a href="#"' + set_class_list(item, 'link') + ' onclick ="link_process(this,\'' + link_node + '\');return false;">' + (value ? value : '&nbsp;') + '</a>';
        }
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
             //temp += link(item, value[i]) + '  ';
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

        var $control = $(add_label(item, 'rf_') + '<div' + set_class_list(item, 'HOLDER') + '"><label class="img_upload_label"><input class="img_uploader" type="file" /></label></div>');
        var data = {type : 'image', value : value, size : size}
        $control.find('input').file_upload(data);
        return $control
    }

    function image_ro(item, value){
        if (item.size){
            size = '.' + item.size;
        } else {
            size = '.m';
        }
        var $control = '<div' + set_class_list(item, 'HOLDER') + '><img src="/attach?' + value + size + '" /></div>';
        return $control
    }

    function build(readonly, item, value){
        var ro = readonly ? 1 : 0;
        var control = item.control;
        var $div = $('<div class="f_control_holder"/>');
            if (control_build_functions[control]){
                $div.append(control_build_functions[control][ro](item, value));
            } else {
                $div.append('UNKNOWN: ' + item.control);
            }
        return $div;
    }

    var control_build_functions = {
        'normal': [input_box, plaintext],
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
        'image' : [image, image_ro],
        'autocomplete' : [autocomplete, plaintext],
        'subform': [add_subform, add_subform]
    }

    var local_row_data = {};
    var subforms = [];

    var HTML_Encode = $.Util.HTML_Encode;
    var HTML_Encode_Clear = $.Util.HTML_Encode_Clear;
    var set_class_list = $.Util.set_class_list;
    var process_html = $.Util.process_html;

    return {
        'build' : function(readonly, item, value){
            return build(readonly, item, value);
        },
        'set_data' : function(data){
            local_row_data = data;
        },
        'clear_subforms' : function (){
            subforms = [];
        },
        'get_subforms' : function (){
            return subforms;
        }
    }

}()
