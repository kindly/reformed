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
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '"/>');
        return $control;
    }

    function textbox(item, value){
        value = correct_value(item, value);
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '"/>');
        return $control;
    }

    function datebox(item, value){
        value = correct_value(item, value); // FIXME should this be a more specific fix_date() call
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '" />');
        // FIXME will fail if no label
        $control.eq(1).bind('keydown', $.Util.datebox_key);
        return $control;
    }

    function intbox(item, value){
        var $control = $(add_label(item, 'rf_') + '<input id="rf_' + item.name + '"' + set_class_list(item, 'inputbox') + ' value="' +  HTML_Encode_Clear(value) + '" />');
        // FIXME will fail if no label
        $control.eq(1).bind('keydown', $.Util.intbox_key);
        $control.eq(1).bind('change', $.Util.intbox_change);
        return $control;
    }


    function link(item, value){
        return '<a href="#/' + item.node + '"' + set_class_list(item, 'link') + ' onclick="node_load(\'' + item.node + '\',this);return false">' + item.title + '</a>';
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

    function result_link(item, value, base_link){
        var link_node = $.Util.build_node_link(local_row_data, base_link);
        var link_node_href = $.Util.build_node_link_href(local_row_data, base_link);
        var x = '<a href="' + link_node_href + '"' + set_class_list(item, 'link') + ' onclick="' + link_node + 'return false;">' + (value ? value : 'untitled') + '</a>';
        return x;
    }

    function result_image(item, value){
        var link_node = "u:" + REBASE.application_data.bookmarks[local_row_data.entity].node;
        link_node += ":edit:__id=" + local_row_data.__id
        if (item.size){
            size = '.' + item.size;
        } else {
            size = '.m';
        }
        var $control = '<div' + set_class_list(item, 'HOLDER') + ' onclick="node_load(\'' + link_node + '\',this);" ><img src="/attach?' + value + size + '" /></div>';
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
        return '<a href="#/' + item.node + '"' + set_class_list(item, 'link') + ' onclick="node_load(\'' + item.node + '\',this);return false">' + item.title + '</a>';
    }

    function button(item, value){
        var target_form = item.target_form || '';
        return '<button' + set_class_list(item, 'button') + ' onclick="node_load(\'' + item.node + '\',this,\'' + target_form + '\');return false">' + item.title + '</button>';
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
        $control = $(add_label(item, 'rf_') + '<div class="' + class_list + ' complex"><input id="rf_' + item.name + '" class="dropdown_input" value="' + value + '" /><div class="but_dd_f"><img class="but_dd_img_f" src="/bullet_arrow_down2.png" /></div></div>');
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
        return add_label(item, 'rf_') + '<input type="password"' + set_class_list(item, 'inputbox') + ' value="' + HTML_Encode_Clear(value) + '"/>';
    }

    function checkbox(item, value){
        var class_list = '';
        if (item.css){
            class_list += ' ' + item.css;
        }
        if (item.reverse){
            $control = $('<div class="CHECKBOX ' + class_list + '"><input type="button"/><img src="/tick.png" />&nbsp;</div>' + add_label(item, 'rf_'));
            $control.eq(0).filter('div').checkbox(item, value);
        } else {
            $control = $(add_label(item, 'rf_') + '<div class="CHECKBOX ' + class_list + '"><input type="button" /><img src="/tick.png" />&nbsp;</div>');
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
                cbox.reverse = true;
                $holder = $('<div class="f_codegroup_holder">');
                if (codes[i].length > 2){
                    cbox.description = codes[i][2];
                    $holder.append(form_description(cbox))
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
        // FIXME need to know if this is updatable node for proper href
        var x = '<a href="#/' + link_node + '"' + set_class_list(item, 'link') + ' onclick="node_load(\'' + link_node + '\',this);return false">' + (value ? value : '&nbsp;') + '</a>';
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

        var $control = $(add_label(item, 'rf_') + '<div' + set_class_list(item, 'HOLDER') + '"><label class="img_upload_label"><input class="img_uploader" type="file" tabindex="-1" /></label></div>');
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
                // dirty hack to stop thumb showing as unknown control
                if (control == 'thumb'){
                    return '';
                }
                $div.append('UNKNOWN: ' + item.control);
            }
        return $div;
    }

    // these are the available functions
    // the 3rd element set to a true value will stop the f_sub div being added
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



/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    LAYOUT
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Manage forms and layout.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Layout = function(){


    var root = '#main';

    // The version of the layout to make sure we do not mix
    // data between layouts.  All updates to forms should
    // have a matching layout_id
    var layout_id = 0;

    // Form data set by external set_data function.
    var forms;

    // Layout data set by external set_data function.
    var layout;

    // Array of layout section JQuery objects.
    // for the current layout.
    var $layout_divs;

    var form_count;
    // The hash of JQuery forms on the layout
    // by form name.
    var $forms = {};

    var layout_title;
    var $header;
    var $footer;


    /*
     *      (\  }\   (\  }\   (\  }\
     *     (  \_('> (  \_('> (  \_('>   FORM DATA PROCESSOR
     *     (__(=_)  (__(=_)  (__(=_)
     *   jgs  -"=      -"=      -"=
     */

    var FormProcessor = function(){
        /* FormProcessor processes form data sent by the
         * backend.  Cache form data where possible.
         * Normailises forms etc.
         */

        // form data is kept here key is 'node_name|form_name'
        var form_data_cache = {};
        var form_data_cache_info = {};

        function clear_form_cache(){
            // Clear the form cache.
            form_data_cache = {};
            form_data_cache_info = {};
            console_log('FORM CACHE deleted');
        }


        function process_form_data_all(forms_data, node){
            var full_form_data = {};
            var form_data;
            for (var form in forms_data){
                form_data = {};
                form_data.data = forms_data[form].data
                form_data.paging = forms_data[form].paging
                form_data.form = process_form_data(forms_data[form].form, node)
                full_form_data[form] = form_data;
            }
            return full_form_data;
        }

        function process_form_data(form_data, node){
            /* If we have a suitable version in the form cache
             * then just return that else normalise the form.
             */
            var cache_name;
            if (form_data.cache_form !== undefined){
                cache_name = form_data.cache_node + '|' + form_data.cache_form;
                return form_data_cache[cache_name];
            }

            form_data = form_data_normalise(form_data, node)
            // form caching
            cache_name = node + '|' + form_data.name;
            if (!form_data.version){
                // remove from cache if it exists
                if (form_data_cache_info[node] !== undefined){
                    delete form_data_cache_info[node][form_data.name];
                }
            } else {
                // store form in cache
                form_data_cache[cache_name] = form_data;
                if (!form_data_cache_info[node]){
                    form_data_cache_info[node] = {};
                }
                form_data_cache_info[node][form_data.name] = form_data.version;
            }
            return form_data;
        }

        function form_data_normalise(form_data, node){
            /* generally clean up the form data to
             * make things easier for us later on.
             * creates .items hash for quick reverse lookups etc.
             */

            form_data.node = node;
            // make hash of the fields
            form_data.items = {};
            for (var i = 0, n = form_data.fields.length; i < n; i++){
                var field = form_data.fields[i];
                field.index = i;
                if (field.name){
                    form_data.items[field.name] = field;
                }
                if (!field.control){
                    field.control = 'normal';
                }
                // get out the thumb field if one exists
                // makes life easier later on
                // TODO do we still use this?
                if (field.control == 'thumb'){
                    form_data.thumb = field;
                }
            }
            return form_data;
        }

        // exported functions
        return {
            'process' : function (form_data, node_data){
                return process_form_data_all(form_data, node_data)
            },
            'debug_form_info' : function (){
                return form_data_cache;
            },
            'clear_form_cache' : function (node_name){
                clear_form_cache();
            },
            'get_form_cache_data' : function (node_name){
                return form_data_cache_info[node_name];
            }
        }
    }()


    /*
     *      (\  }\   (\  }\   (\  }\
     *     (  \_('> (  \_('> (  \_('>   LAYOUT FUNCTIONS
     *     (__(=_)  (__(=_)  (__(=_)
     *   jgs  -"=      -"=      -"=
     */

    function add_forms_to_layout(packet){
        /* Create a new layout or update form(s)
         * depending on the data provided.
         * If the layout_type is provided then we
         * build a whole new layout.  If not we just replace the forms
         * This function is EXPORTED.
         */

        // retrieve layout data
        var layout_data = packet.layout;
        // Store the form data.
        forms = FormProcessor.process(packet.data, packet.node);
        layout_title = layout_data.layout_title;

        if (layout_data.layout_dialog){
            REBASE.Dialog.dialog(layout_data.layout_title, forms[layout_data.layout_dialog]);
        } else {

        REBASE.Dialog.close();
        if (layout_data.layout_type){
            // Layout has changed so update our stored data.
            layout = layout_data;
            create_layout();
        } else {
            // Update the layout forms
            layout.layout_forms = layout_data.layout_forms;
            replace_forms();
        }
        }
    }

    function replace_forms(){
        /* Replace a named form in the layout with
         * a newly created form of the same name.
         * Used for updating form(s) whilst keeping
         * the rest of the layout.
         */

        for (var i = 0; i< layout.layout_forms.length; i++){
            var form_name = layout.layout_forms[i];
            if ($forms[form_name]){
                $forms[form_name].empty();
                $forms[form_name].append(make_form(form_name));
            } else {
                console_log('TRIED TO USE UNINITIALISED FORM ' + form_name);
            }
        }
        set_layout_title_and_footer();
    }


    function create_layout(){
        /* Build the layout (including all contained forms)
         * and place it in the 'root' DOM element.
         *
         */
        var $layout;
        var sections;
        var section;
        var form_name;
        var $form;

        function build_layout(){
            /* Create the actual layout HTML.
             * Refreshes data relating to the layout
             * this destroys the 'knowledge' of the previous layout.
             */

            // reset the layout
            $layout_divs = [];
            $forms = {};
            // new layout so change id
            layout_id++;

            // This is the outer holder for the new layout.
            var $layout = $('<div class="LAYOUT_HOLDER">');

            function make_layout_section(layout_class){
                /* Creates a layout section of the requested class.
                 * Attaches it to the layout and stores the innermost div in
                 * $layout_divs for later access.
                 */

                var $section_subdiv = $('<div class="STYLE">');
                var $section = $('<div class="' + layout_class + '">');
                $section.append($section_subdiv);
                $layout_divs.push($section_subdiv);
                $layout.append($section);
            }

            // Create the layout.
            // These are the available layouts.
            $header = $('<div class="LAYOUT_HEADER"></div>');
            $layout.append($header);
            switch (layout.layout_type){
                case 'entity':
                    make_layout_section("LAYOUT_COL_LEFT");
                    make_layout_section("LAYOUT_COL_RIGHT");
                    make_layout_section("LAYOUT_COL_FULL");
                    break;
                case 'listing':
                    make_layout_section("LAYOUT_COL_FULL");
                    break;
                default:
                    console_log('UNKNOWN LAYOUT: ' + layout.layout_type);
                    break;
            }
            $footer = $('<div class="LAYOUT_FOOTER"></div>');
            $layout.append($footer);
            return $layout;

        }

        form_count = 0;
        // Create the base layout with sections
        $layout = build_layout();
        sections = layout.form_layout;
        // Add the required forms to the correct layout section.
        for (var i = 0; i < sections.length; i++){
            section = sections[i];
            for (var j = 0; j < section.length; j++){
                form_name = section[j];
                // ensure that we actually have data for this form
                if (forms[form_name] === undefined){
                    console_log('ERROR: form `' + form_name + '` is in the layout but no data exists.');
                } else {
                    $form = make_form(form_name);
                    $layout_divs[i].append($form);
                    // save it for future lookups
                    $forms[form_name] = $form;
                }
            }
        }
        // set the title
        set_layout_title_and_footer();
        // Replace root DOM elements content with the new layout.
        $(root).empty();
        $(root).append($layout);

    }

    function set_layout_title_and_footer(){
        if (layout_title){
            $header.text(layout_title);
        }
        footer = 'footer'
        $footer.text(footer);
    }

    function make_form(form_name){
        /* create the form requested and return it as a JQuery object */
        var form = forms[form_name].form
        var data = forms[form_name].data
        var paging = forms[form_name].paging;
        var form_type = forms[form_name].form.form_type;

        var $div = $('<div class="FORM_HOLDER" id="form_' + (form_count++) + '"/>');
        // FIXME move to switch statement
        if (form_type == 'grid'){
            $div.grid2(form, data, paging);
        } else if (form_type == 'action' || form_type == 'results'){
            $div.input_form(form, data, paging);
        } else {
            $div.input_form(form, data, paging);
        }
        return $div;

    }


    // exported functions
    return {
        'update_layout' : function (packet){
            // Create or update the layout.
            add_forms_to_layout(packet);
        },
        'get_layout_id' : function (){
            return layout_id;
        },
        'debug_form_info' : function (){
            return FormProcessor.debug_form_info();
        },
        'clear_form_cache' : function (node_name){
                FormProcessor.clear_form_cache();
            },
        'get_form_cache_info' : function (node_name){
            return FormProcessor.get_form_cache_data(node_name);
        }
    }

}()

/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    DIALOG BOX
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Pop up dialog box.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Dialog = function (){

    var dialog_decode;
    var $dialog_box;
    var $system_dialog_box;
    var is_setup = false;
    var is_open = false;
    var process_html = $.Util.process_html;

    function setup(){
        var options = {autoOpen: false, width: 'auto', modal: true};
        // dialog box
        $dialog_box = $('<div id="dialog_box"></div>');
        $('body').append($dialog_box);
        $dialog_box.dialog(options);
        // system dialog box
        $system_dialog_box = $('<div id="system_dialog_box"></div>');
        $('body').append($system_dialog_box);
        $system_dialog_box.dialog(options);

        is_setup = true;
    }


    function open(title, data){
        if (!is_setup){
            setup()
        }
        // If we have sent a string as data then we just want
        // to process it for any markdown and display it.
        // If it is form data then we want to process it as a form.
        if (typeof(data) == 'string'){
            $dialog_box.html(process_html(data));
        } else {
            // assuming it is form_data
            var form = data.form
            var form_data = data.data

            $dialog_box.input_form(form, form_data);
        }
        $dialog_box.dialog("option", "title", title)
        $dialog_box.dialog('open');
        is_open = true;
    }

    function close(){
        if (is_open){
            $dialog_box.dialog('close');
            is_open = false;
        }
    }

    function confirm_action(decode, title, message){
        if (!is_setup){
            setup()
        }
        dialog_decode = decode;
        var $form = $('<div class="INPUT_FORM"></div>');
        // clear any form data
        REBASE.FormControls.set_data({});
        $form.append(REBASE.FormControls.build(true, {control:'message_area'}, message));
        $form.append('<div class="f_control_holder"><div class="f_sub"><button onclick="REBASE.Dialog.confirm_action_return(false);return false" class="button">No</button><button onclick="REBASE.Dialog.confirm_action_return(true);return false" class="button">Yes</button></div></div>')
        $system_dialog_box.empty();
        $system_dialog_box.append($form);

        $system_dialog_box.dialog("option", "title", title)
        $system_dialog_box.dialog('open');

    }

    function confirm_action_return(result){
        $system_dialog_box.dialog('close');
        if (result){
            dialog_decode.flags.confirm_action = false;
            REBASE.Node.get_node(dialog_decode);
        }
    }

    // exported functions
    return {
        'dialog' : function (title, data){
            open(title, data);
        },
        'close' : function(){
            close();
        },
        'confirm_action' : function (decode, title, message){
            confirm_action(decode, title, message);
        },
        'confirm_action_return' : function(result){
            confirm_action_return(result);
        }

    }

}()


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    FUNCTIONS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Remote functions called by the backend.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Functions = function (){


    function call(fn, data){
        /* calls function if it exists */
        var f = functions[fn];
        if (f){
            f(data);
        } else {
            REBASE.Dialog.dialog('Error', '<pre>Function `' + fn + '` is not available.</pre>');
        }
    }

    // hash of functions available
    var functions = {}

    functions.debug_form_info = debug_form_info;

    // application data
    functions.application_data = function (data){
        REBASE.application_data = data;
        change_layout();
    };

    // bookmarks
    functions.load_bookmarks = function (data){
        REBASE.Bookmark.process(data);
    };

    // Clear form cache.
    functions.clear_form_cache = function (){
        REBASE.Layout.clear_form_cache();
    };

    function debug_form_info(){
        /* Output the current form cache information */
        var info = REBASE.Layout.debug_form_info();
        $('#main').empty();
        $('#main').append('<p><b>Cached form info</b><div id="treeview_control">		<a title="Collapse the entire tree below" href="#"><img src="jquery/images/minus.gif" /> Collapse All</a> | <a title="Expand the entire tree below" href="#"><img src="jquery/images/plus.gif" /> Expand All</a> | <a title="Toggle the tree below, opening closed branches, closing open branches" href="#">Toggle All</a></div></p>');
        var $treeview = $(REBASE.Utils.treeview_hash(info)).treeview({collapsed: true, control : '#treeview_control'});
        $('#main').append($treeview);
    }


    // exported functions
    return {
        'call' : function (fn, data){
            call(fn, data);
        }
    }

}()

/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    UTILS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Useful and shared functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Utils = function (){


    function treeview_hash(data, css_class){
        /* takes a hash of data and converts it into
         * a jQuery treeview ready unordered list
         */
        if (css_class === undefined){
            css_class = 'treeview-gray';
        }
        var output = [];
        if (css_class !== ''){
            output.push('<ul class="' + css_class + '" >');
        } else {
            output.push('<ul>');
        }
        for (var key in data){
            if (data[key] === null){
                output.push('<li>' + key + ' : null</li>');
            } else if (typeof(data[key]) == 'object'){
                if (data[key].length){
                    output.push('<li><span>' + key + ' : [\n</span>' + treeview_hash(data[key], '') + '<span>\n]</span></li>');
                } else {
                    output.push('<li><span>' + key + ' : {\n</span>' + treeview_hash(data[key], '') + '<span>\n}</span></li>');
                }
            } else {
                output.push('<li>' + key + ' : ' + data[key] + '</li>');
            }
        }
        output.push('</ul>');
        return output.join('\n');

    }

    // exported functions
    return {
        'treeview_hash' : function (data, css_class){
            return treeview_hash(data, css_class);
        }
    }


}()
