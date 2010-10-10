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
        node_load('d:user.User:login:');
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


    /* Private functions. */

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

        // flags
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
                    var $obj = $obj.parents('div.INPUT_FORM');
                    var form_data = $obj.data('command')('get_form_data');
                    // update the form data with any items in decode.url_data that
                    // have not already been assigned
                    for (var key in decode.url_data){
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
                    // if we have any extra node data we add it but
                    // don't overwrite anything in the url.
                    // I'm not sure if this is the best thing to do
                    // but it is currently needed for the bookmarks to work correctly.
                    for (var key in decode.url_data){
                        decode.node_data[key] = decode.url_data[key];
                    }
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
        if (decode.flags.confirm_action){
           // && !confirm('Are you sure?')){
            REBASE.Dialog.confirm_action(decode, 'Confirmation needed', 'are you sure?', decode);
            return false;
        }
        info = decode;
        // application data
        if (!REBASE.application_data){
            info.request_application_data = true;
        }
        // close any open dialog
        // may possibly cause problems with status refreshes
    //    REBASE.Dialog.close();
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
        'load_node' : function (node_string, item, target_form){
            /* called from form buttons etc sends the form
             * data and can call a target form. */
            load_node(node_string, item, target_form);
        },
        'get_node' : function (decode){
            get_node(decode);
        }
    }
}();

/* helper function */
var node_load = REBASE.Node.load_node;


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
        var node_string = "/:" + node + ":_status:id=" + data.data.id;
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
    if (user.real_user_id){
        REBASE.application_data.__real_user_id = user.real_user_id;
    }
    if (user.real_user_name){
        REBASE.application_data.__real_username = user.real_user_name;
    }
    change_layout();
}

function change_user_bar(){

    if (REBASE.application_data.__user_id === 0){
        $('#user_login').html('<a href="#" onclick="node_load(\'d:user.User:login\',this);return false">Login</a>');
    } else {
        var impersonate = ''
        if (REBASE.application_data.__real_user_id && REBASE.application_data.__real_user_id != REBASE.application_data.__user_id){
            impersonate = ' <a href="#" onclick="node_load(\':user.Impersonate:revert\',this);return false">revert to ' + REBASE.application_data.__real_username + '</a>';
        }

        $('#user_login').html(REBASE.application_data.__username + ' <a href="#" onclick="node_load(\':user.User:logout\',this);return false">Log out</a>' + impersonate);
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

var global_node_data = {};
var global_current_node;

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
         global_current_node = packet.data.node;
         console_log('node data:', global_node_data);
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
                 switch (link){
                     case 'BACK':
                        window.history.back();
                        break;
                    case 'CLOSE':
                        REBASE.Dialog.close();
                        break;
                    case 'RELOAD':
                        REBASE.Dialog.close();
                        node_load($.address.value());
                        break;
                    default:
                        node_load('u:' + link);
                        break;
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
         case 'dialog':
             REBASE.Layout.update_layout(packet.data);
             break;
         case 'function':
            console_log('data', packet.data['function']);
            REBASE.Functions.call(packet.data['function'], packet.data.data);
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
         case 'message':
            message = packet.data.data
            REBASE.Dialog.dialog('Message', message);
            break;
         case 'forbidden':
            message = 'You do not have the permissions to perform this action.'
            REBASE.Dialog.dialog('Forbidden', message);
            break;
        case 'status':
            job_processor_status(packet.data.data, packet.data.node, root);
            break;
        default:
            REBASE.Dialog.dialog('Error', 'Action `' + packet.data.action + '` not recognised');
            break;

    }
}

