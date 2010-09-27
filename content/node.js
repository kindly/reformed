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

$(document).ready(init);

function init(){

    $.address.change(REBASE.Node.load_page);
    // if no node info is available go to the login node
    // FIXME this needs fixing with a default node
    // also if you are auto logged in etc
    var url = $.address.value();
    if (url == '/'){
        node_load('n:user.User:login:');
    }
}

REBASE.Node = function (){


    /* Public functions. */

    function load_page(){
        /*
         *  function called on page load by address jquery plug-in
         *  used for back/forward buttons, bookmarking etc
         *  gets correct 'address' string and passes to calling function
         */

        // as we are reloading the page make sure everything has blured
        itemsBlurLast();  // FIXME needed?
        var link = $.address.value();
        call_node(link, true);
    }


    function load_node(node_string){
        /*
         *  Force a page load of the node.
         */

        // as we are reloading the page make sure everything has blured
        itemsBlurLast();  // FIXME needed?
        if ($.address.value() == '/' + node_string){
            // The address is already set so we need to force the reload
            // as changing the address will not trigger an event.
            call_node(node_string, true);
        } else {
            // Check if this is an underscore command which should
            // not update the address.
            var link = node_string.split(':');
            if (link[2] && link[2].substring(0,1) == '_'){
                call_node(node_string, false);
            } else {
                // Sets the address which then forces a page load.
                $.address.value(node_string);
            }
        }
    }


    function load_node_form(item, node_string, target_form){
        /*
         * Called from form buttons etc.
         * Get any form data needed and request node from backend.
         */

        // browser history back
        if (node_string == 'BACK'){
            window.history.back();
            return false;
        }
        var decode = decode_node_string(node_string);
        // get any form data
        var $obj = $(item);
        var $obj = $obj.parents('div.INPUT_FORM');
        var form_data = $obj.data('command')('get_form_data');
        // update the form data with any items in decode.url_data that
        // have not already been assigned
        for (var key in decode.url_data){
            if (form_data[key] === undefined){
                form_data[key] = decode.url_data[key];
            }
        }
        // set the form data
        decode.form_data = [form_data];
        // set target form if not the button containing one.
        if (target_form){
            form_data.form = target_form;
        }
        get_node(decode);
    }




    /* Private functions. */

    function call_node(node_string, insecure){
        /*
         *  takes a string (node_string) of the form
         *  "/n:<node_name>:<command>:<arguments>"
         *
         *  insecure: allows 'dangerous' _underscored commands to be sent
         */
        var decode = decode_node_string(node_string);
        if (decode){
            // only call if it is secure to do so.
            if (!insecure || !decode.secure){
                get_node(decode);
            }
        }
    }


    function decode_node_string(node_string){
        /*
         *  Decodes a node string and returns an object.
         *  { node, type, command, url_data, node_data, layout_id, form_data, secure }
         *  or false if an error occurs
         */
        var error_msg;
        var decode = {};
        var split = node_string.split(':');
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
        // url data converted to a hash
        if (split.length>3){
            decode.url_data = convert_url_string_to_hash(split[3]);
        } else{
            decode.url_data = {};
        }
        // type
        var type = split[0];
        switch (split[0]){
            case 'n':
            case '/n':
                decode.type = 'node';
                // node calls return any url_data as the node_data
                decode.node_data = decode.url_data;
                // if we have any extra node data we add it but
                // don't overwrite anything in the url.
                // I'm not sure if this is the best thing to do
                // but it is currently needed for the bookmarks to work correctly.
                if (global_node_data){
                    for (var key in global_node_data){
                        if (decode.node_data[key] === undefined){
                            decode.node_data[key] = global_node_data[key];
                        }
                    }
                }
                decode.form_data = false;
                break;
            case 'l':
            case '/l':
                decode.type = 'layout';
                // layout calls return the global node_data
                decode.node_data = global_node_data;
                // if form supplied in url_data set in decode.form
                var data = {};
                data.form = decode.url_data.form || false;
                data.layout_id = REBASE.Layout.get_layout_id();
                data.data = decode.url_data;
                decode.form_data = [data];
                break;
            default:
                error_msg = 'Invalid node data.\n\nUnknown node type.';
                REBASE.Dialog.dialog('Application Error', error_msg);
                return false;
                break;
        }
        return decode;
    }


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


    function get_node(decode){
        /*
         *  Takes a decoded node request does any processing needed
         *  and passes it to be the job processor to request
         */
        var info = {node: decode.node,
                    lastnode: '',  //FIXME will we ever need this?
                    command: decode.command};
        // get any cached form info for the node
        var cache_info = REBASE.Layout.get_form_cache_info(decode.node);
        if (cache_info !== undefined){
            info['form_cache'] = cache_info;
        }
        // node data
        if (decode.node_data){
            info.node_data = decode.node_data
        }
        // form data
        if (decode.form_data){
            info.form_data = decode.form_data;
        }
        // application data
        if (!REBASE.application_data){
            info.request_application_data = true;
        }
        // close any open dialog
        // may possibly cause problems with status refreshes
        REBASE.Dialog.close();
        // FIXME if we never send data as second arg then
        // remove it.
        $JOB.add(info, {});
    }


    // exported functions

    return {
        'load_page' : function (){
            /* called by $.address.change() */
            load_page();
        },
        'load_node' : function (node_string){
            /* called to load a node changes the page url if needed. */
            load_node(node_string);
        },
        'load_node_form' : function (item, node_string, target_form){
            /* called from form buttons etc sends the form
             * data and can call a target form. */
            load_node_form(item, node_string, target_form);
        }
    }
}();

/* helper functions for transition */
var node_load = REBASE.Node.load_node;
var node_button_input_form = REBASE.Node.load_node_form;


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
    alert('broken');
    console_log('node_save');
    $('#main').find('div').data('command')('save'); //FIXME these want to be found properly
}


function node_button(item, node, command){
    alert('broken');
    var out = $('#main div.f_form').data('command')('get_form_data');
    get_node(node, command, out, false, false);
}



function node_load_grid(arg){
    $obj = $('#main').find('div.GRID').eq(0);
    $obj.data('show_loader')();
    node_load(arg);
}
function _wrap(arg, tag, my_class){
    // this wraps the item in <tag> tags
    if (my_class){
        return '<' + tag + ' class="' + my_class + '" >' + arg + '</' + tag + '>';
    } else {
        return '<' + tag + '>' + arg + '</' + tag + '>';
    }
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

function get_status(call_string){
    node_load(call_string);
}


var status_timer;

function job_processor_status(data, node, root){
    // display the message form if it exists
    if (data.form){
        $('#' + root).status_form();
    }
    // show info on form
    if (data.data){
        $('div.STATUS_FORM').data('command')('update', data.data);
    }
    // set data refresh if job not finished
    if (!data.data || !data.data.end){
        var node_string = "/n:" + node + ":_status:id=" + data.data.id;
        status_timer = setTimeout(function (){
                                      get_status(node_string);
                                  }, 1000);
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


function itemsBlurLast(){
    // FIXME called on page loads but does nothing
}


function grid_add_row(){
    console_log('add_row');
    $('#main div.GRID').data('command')('add_row');
}
// user bits

function change_user(user){
    REBASE.application_data.__user_id = user.id;
    REBASE.application_data.__username = user.name;
    change_layout();
}

function change_user_bar(){

    if (REBASE.application_data.__user_id === 0){
        $('#user_login').html('<a href="#" onclick="node_button_input_form(this, \'n:user.User:login\');return false">Login</a>');
    } else {
        $('#user_login').html(REBASE.application_data.__username + ' <a href="#" onclick="node_button_input_form(this, \'n:user.User:logout\');return false">Log out</a>');
    }
}

function change_layout(){
    if (!REBASE.application_data.public && !REBASE.application_data.__user_id){
         REBASE.LayoutManager.layout('mainx');
    } else {
         REBASE.LayoutManager.layout('main');
    }
    change_user_bar();
}

var global_node_data;

function process_node(packet, job){

    var message;

     if (packet.data === null){
         console_log("NULL DATA PACKET");
         return;
     }

     var root = 'main'; //FIXME

     var title = packet.data.title;
     if (title){
         $.address.title(title);
     }

     var sent_node_data = packet.data.node_data;
     if (sent_node_data){
         global_node_data = sent_node_data;
         console_log('node data:', global_node_data);
     }

    if (packet.data.application_data){
        REBASE.application_data = packet.data.application_data;
        change_layout();
    }

     var user = packet.data.user;
     if (user){
         change_user(user);
     }

     var bookmark = packet.data.bookmark;
     if (bookmark){
        REBASE.Bookmark.process(bookmark);
     }

    var data;
     switch (packet.data.action){
         case 'redirect':
             var link = packet.data.link;
             if (link){
                 if (link == 'BACK'){
                    window.history.back();
                 } else {
                    node_load('n:' + link);
                 }
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
             REBASE.Layout.update_layout(packet.data);
             break;
         case 'function':
            REBASE.Functions.call(packet.data.data);
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
                alert("we have not sent the object");
            }
            break;
         case 'delete':
            data = packet.data.data;
            if (data.deleted){
                form_process_deleted(data.deleted);
            }
            break;
         case 'general_error':
            message = packet.data.data
            REBASE.Dialog.dialog('Error', message);
            break;
         case 'forbidden':
            message = 'You do not have the permissions to perform this action.'
            REBASE.Dialog.dialog('Forbidden', message);
            break;
        case 'status':
            job_processor_status(packet.data.data, packet.data.node, root);
            break;
    }
}

