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

    node.js
    ======

*/

// JSLint directives
/*global document window */
/*global $ REBASE console_log */


var global_node_data = {};
var global_current_node;
var node_load;


function search_box(){
    var node = ':test.Search::q=' + $('#search').val();
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

function grid_add_row(){
    console_log('add_row');
    $('#main div.GRID').data('command')('add_row');
}


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    USER
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    User management functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.User = function (){

    function change_user_bar(){
        // update the user bar with the correct user info
        // log in/out options etc.
        var app_data = REBASE.application_data;
        var html;
        if (app_data.__user_id === 0){
            html = '<a href="#" onclick="node_load(\'d:user.User:login\',this);return false;">Log in</a>';
        } else {
            var impersonate = '';
            if (app_data.__real_user_id && app_data.__real_user_id != app_data.__user_id){
                impersonate = ' <a href="#" onclick="node_load(\':user.Impersonate:revert\',this);return false;">revert to ' + app_data.__real_username + '</a>';
            }
            html = app_data.__username + ' <a href="#" onclick="node_load(\':user.User:logout\',this);return false;">Log out</a>' + impersonate;
        }
        $('#user_login').html(html);
    }

    function update_user(user_data){
        // if we have new user data then update the application data
        if (user_data){
            var app_data = REBASE.application_data;
            app_data.__user_id = user_data.id;
            app_data.__username = user_data.name;
            if (user_data.real_user_id){
                app_data.__real_user_id = user_data.real_user_id;
            }
            if (user_data.real_user_name){
                app_data.__real_username = user_data.real_user_name;
            }
        }
        change_user_bar();
    }

    return {
        'update' : function (user_data){
            update_user(user_data);
        }
    };

}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    INTERFACE
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Create and manage the user interface.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Interface = function (){

    var $interface_layout;
    var $side;
    var $user_area;
    var $user_bar;
    var $logo;
    var $menu;

    function resize_north_pane(){
        // due to floats we have to measure the user bar items
        var size = $user_bar.outerHeight(true) + $menu.outerHeight(true);
        $interface_layout.sizePane('north', size);
        $logo.height(size - 10);
    }

    function make_menu(menu){
        // Build the menu.
        function build(data){
            var i;
            var item;
            var html = [];
            for(i = 0; i < data.length; i++){
                item = data[i];
                html.push('<li>');
                if (item.node){
                    html.push('<a onclick="node_load(\'' + item.node + '\');$(\'#menu\').hideSuperfishUl();" >');
                } else {
                    if (item['function']) {
                        html.push('<a onclick="REBASE.Functions.call(\'' + item['function'] + '\');$(\'#menu\').hideSuperfishUl();" >');
                    } else {
                        html.push('<a onclick="return false;" >');
                    }
                }
                html.push(item.title);
                html.push('</a>');
                if (item.sub){
                    html.push('<ul>');
                    html.push(build(item.sub));
                    html.push('</ul>');
                }
                html.push('</li>');
            }
            return html.join('');
        }
        $menu.empty();
        $menu.append(build(menu));
        $menu.superfish();
    }

    function add_logo(){
        $logo = $('<img id="logo_image" src="logo.png" />');
        $('#logo').append($logo);
    }

    function add_user_bar(){
        $user_bar = $('<div id="user_bar"></div>');
        // search box
        var html = [];
        html.push('<form action="" onclick="$.Util.Event_Delegator(\'clear\');" onsubmit="return search_box();" style="display:inline">');
        html.push('<input type="text" name="search" id="search" />');
        html.push('<input type="submit" name="search_button" id="search_button" value="search"/>');
        html.push('</form>');
        $user_bar.append(html.join(''));
        // ajax info
        $user_bar.append('<span id="ajax_info"><img src="busy.gif" /> Loading ...</span>');
        // login info
        $user_bar.append('<span id="user_login" style="float:right;">user login</span>');
        $user_area.append($user_bar);
    }

    function add_menu(){
        $menu = $('<ul id="menu" class="sf-menu" ><li><a onclick="return false;" >menu</a></li><ul>');
        $menu.superfish();
        var $menu_bar = $('<div id="menu_bar">');
        $menu_bar.append($menu);
        $user_area.append($menu_bar);
    }

    function make_resizer(){
        var html = [];
        var sizes = [8, 10, 12, 14, 16];
        html.push('<div id="resizer" >');
        for (var i = 0; i < sizes.length; i++){
            html.push('<span onclick="$.Util.selectStyleSheet(\'size\', ' + (i + 1) + ');" >');
            html.push('<span style="font-size:' + sizes[i] + 'px">A</span></span>');
        }
        html.push('</div>');
        return html.join('');
    }

    function add_side(){
        $side.empty();
        $side.append(make_resizer());
        $side.append('<div id="bookmarks"></div>');
    }

    function init(){
        /* initialise the layout */
        var $body = $('body');
        $body.append('<div class="ui-layout-center"><div id="main" /></div>');
        $body.append('<div class="ui-layout-west" id="left"><div id="side" /></div>');
        $body.append('<div class="ui-layout-north"><div id="logo" /><div id="user_area" /></div>');
        $side = $('#side');
        $user_area = $('#user_area');

        add_side();
        add_user_bar();
        add_menu();
        add_logo();

        // set options for the panes
        var layout_defaults = {spacing_open:3, spacing_close:6, padding:0, applyDefaultStyles:true};
        var layout_north = {resizable:true, closable: false, slidable:false, spacing_open:0};

        $interface_layout = $body.layout({defaults: layout_defaults, north : layout_north});
        resize_north_pane();
    }
    return {
        'init' : function (){
            init();
        },
        'resize_north_pane': function (){
            resize_north_pane();
        },
        'make_menu': function (menu_data){
            make_menu(menu_data);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    NODE
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Processing node calls and
 *          @()@||@@@@@'    deal with backend responses.
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

REBASE.Node = function (){


    /* Private functions. */

    function convert_url_string_to_hash(arg){
        /*
         *  convert string to a hash
         *  input:  "a=1&b=2"
         *  output  {a:1, b:2}
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

    function decode_node_string(node_string, item, target_form){
        /*
         *  Decodes a node string and returns an object.
         *  { node, type, command, url_data, node_data, layout_id, form_data, secure }
         *  or false if an error occurs
         */
        console_log(node_string);
        var error_msg = '';
        var decode = {};
        var split = node_string.split(':');
        var key;
        // check enough info
        if (split.length < 2){
            error_msg = 'Invalid node data.\n\nNot enough arguments.';
            REBASE.Dialog.dialog('Application Error', error_msg);
            return false;
        }
        // node
        decode.node = split[1];
        //command
        if (split.length > 2){
            decode.command = split[2];
            // if the command starts with a underscore we don't want
            // to trigger the command from a url change as this can
            // let dangerous commands be sent via urls
            decode.secure = (decode.command.substring(0,1) == '_');
        } else {
            decode.command = null;
            decode.secure = false;
        }
        decode.form_data = [];
        // url data converted to a hash
        if (split.length>3){
            var url_data = convert_url_string_to_hash(split[3]);
            if (target_form){
                decode.form_data.push({form : target_form, data : url_data});
            } else if (url_data.form){
                decode.form_data.push({form : url_data.form, data : url_data});
            } else {
                decode.url_data = url_data;
            }
        } else{
            decode.url_data = {};
        }
        decode.node_data = global_node_data;

        // if we have any extra node data we add it but
        // don't overwrite anything in the url.
        // I'm not sure if this is the best thing to do
        // but it is currently needed for the bookmarks to work correctly.
        for (key in decode.url_data){
            decode.node_data[key] = decode.url_data[key];
        }

        // FLAGS
        // The flags are used to indicate
        // the actions that the node call should perform.
        var flag_data = split[0];
        var flags = {};
        for (var i = 0; i < flag_data.length; i++){
            switch (flag_data.charAt(i)){
                case '/':
                    // ignore this
                    break;
                case 'a':
                    // authenticate
                    flags.authenticate = true;
                    break;
                case 'c':
                    // confirm
                    flags.confirm_action = true;
                    break;
                case 'd':
                    // open as dialog
                    flags.dialog = true;
                    break;
                case 'f':
                    // send form data
                    flags.form_data = true;
                    // get any form data
                    var $obj = $(item);
                    $obj = $obj.parents('div.INPUT_FORM');
                    var form_data = $obj.data('command')('get_form_data');
                    // update the form data with any items in decode.url_data that
                    // have not already been assigned
                    for (key in decode.url_data){
                        if (form_data.data[key] === undefined){
                            form_data.data[key] = decode.url_data[key];
                        }
                    }
                    // set the form data
                    decode.form_data.push(form_data);
                    break;
                case 'u':
                    // update address bar
                    if (decode.secure){
                        error_msg = 'Invalid node data.\n\nCannot update on a secure command.';
                        REBASE.Dialog.dialog('Application Error', error_msg);
                        return false;
                    }
                    flags.update = true;
                    break;
                default:
                    error_msg = 'Invalid node flag ' + flag_data.charAt(i);
                    REBASE.Dialog.dialog('Application Error', error_msg);
                    return false;
            }
        }
        // if we are doing an update we cannot pass form data
        // as we loose the refering item.  Throw an error
        if (flags.update && (flags.form_data || flags.confirm_action)){
            error_msg = 'Cannot process request.\n\nTrying to update address to a node with form data or that needs confirmation.';
            REBASE.Dialog.dialog('Application Error', error_msg);
            return false;
        }
        decode.flags = flags;
        return decode;
    }


    /* Public functions. */

    function get_node(decode){
        /*
         *  Takes a decoded node request does any processing needed
         *  and passes it to be the job processor to request
         */
        if (decode.flags.confirm_action){
            REBASE.Dialog.confirm_action(decode, 'Confirmation needed', 'are you sure?', decode);
            return false;
        }
        var info = decode;
        // application data
        if (!REBASE.application_data){
            info.request_application_data = true;
        }
        REBASE.Job.add(info);
    }

    function load_page(){
        /*
         *  function called on page load by address jquery plug-in
         *  used for back/forward buttons, bookmarking etc
         *  gets correct 'address' string and passes to calling function
         */
        var link = $.address.value();
        var decode = decode_node_string(link);
        if (!decode.secure){
            get_node(decode);
        }
    }

    function load_node(node_string, item, target_form){
        /*
         * Called from form buttons etc.
         * Get any form data needed and request node from backend.
         */

        // browser history back
        if (node_string == 'BACK'){
            window.history.back();
            return false;
        }
        // close any open dialog
        if (node_string == 'CLOSE'){
            REBASE.Dialog.close();
            return false;
        }

        var decode = decode_node_string(node_string, item, target_form);
        if (!decode){
            return false;
        }

        if (decode.flags.update &&
            $.address.value() != '/' + node_string &&
            $.address.value() != node_string){

            // Sets the address which then forces a page load.
            $.address.value(node_string);
            return;
        }
        get_node(decode);
    }



    // exported functions

    return {
        'load_page' : function (){
            /* Called by $.address.change() */
            load_page();
        },
        'load_node' : function (node_string, item, target_form){
            /* Called from form buttons etc sends the form
             * data and can call a target form. */
            load_node(node_string, item, target_form);
        },
        'get_node' : function (decode){
            // Called to automatically load a node decode
            // needed by confirm dialog.
            // DO NOT USE THIS FUNCTION
            // Use load_node() instead
            get_node(decode);
        }
    };
}();


/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    INITIALISATIONS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Code to initialise stuff.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

function init(){
    // turn off any jquery animations
    $.fx.off = true;
    // build the user interface
    REBASE.Interface.init();
    /* helper function */
    node_load = REBASE.Node.load_node;

    $.address.change(REBASE.Node.load_page);
    // if no node info is available go to the login node
    // FIXME this needs fixing with a default node
    // also if you are auto logged in etc
    var url = $.address.value();
    if (url == '/'){
        node_load('d:user.User:login:');
    }
}

$(document).ready(init);
