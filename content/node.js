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

    node_call_from_string('n:test.Bookmark:');
    $.address.change(page_load);
}



function page_load(){
/*
    function called on page load by address jquery plug-in
    used for back/forward buttons, bookmarking etc
    gets correct 'address' string and passes to calling function
*/
    // as we are reloading the page make sure everything has blured
    itemsBlurLast();
    var link = $.address.value();
    node_call_from_string(link, true, true);
}

function node_load_grid(arg){
    $obj = $('#main').find('div.GRID').eq(0);
    $obj.data('show_loader')();
    node_load(arg);
}

function node_load(arg){
/*
    force a page load of the node
*/
    // as we are reloading the page make sure everything has blured
    itemsBlurLast();
    if ($.address.value() == '/' + arg){
        // the address is already set so we need to force the reload
        // as changing the address will not trigger an event
        node_call_from_string(arg, true, true);
    } else {
        // sets the address which then forces a page load
        var link = arg.split(':');
        if (link[2].substring(0,1) == '_'){
            node_call_from_string(arg, true, false);
        } else {
            $.address.value(arg);
        }
    }
}


function node_call_from_string(arg, change_state, insecure){
/*
    takes a string (arg) of the form
    "/n:<node_name>:<command>:<arguments>"

    change_state: if true will change the state for the root
    FIXME no root info yet defaults to 'main' further along the call chain
*/
    var link = arg.split(':');
    if (link[0]=='/n' || link[0]=='n'){
        var node = link[1];
        var command = link[2];
        var data_hash = {};
        // if arguments are supplied
        if (link.length>3){
            data_hash = convert_url_string_to_hash(link[3]);
        }
        // if the command starts with a underscore we don't want
        // to trigger the command from a url change as this can
        // let dangerous commands be sent via urls
        if (!insecure || command.substring(0,1) != '_'){
            get_node(node, command, data_hash, change_state);
        }
    }
}

function convert_url_string_to_hash(arg){
/*
    convert string to a hash
    input:  "a=1&b=2"
    output  {a:1, b:2}
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


function _wrap(arg, tag, my_class){
    // this wraps the item in <tag> tags
    if (my_class){
        return '<' + tag + ' class="' + my_class + '" >' + arg + '</' + tag + '>';
    } else {
        return '<' + tag + '>' + arg + '</' + tag + '>';
    }
}

function get_node(node_name, node_command, node_data, change_state){

    // if change_state then we will set the status to that node
    // this helps prevent front-end confusion
    if (change_state){
        var root = 'main'; //FIXME
  //      $INFO.newState(root);
  //      $INFO.setState(root, 'node', node_name);
    }
    var info = {node: node_name,
                lastnode: '',  //fixme
                command: node_command };

    if (node_data){
        info.data = node_data;
    }

    $JOB.add(info, {}, 'node', true);
}

function get_node_return(node_name, node_command, node_data, $obj, obj_data){
    // works like get_node but adds a jquery item to call on the return
    // we also drop the state stuff as we will deal with that better
    // when needed
    var info = {node: node_name,
                lastnode: '',  //fixme
                command: node_command };

    if (node_data){
        info.data = node_data;
    }
    $JOB.add(info, {obj : $obj, obj_data : obj_data}, 'node', true);
}

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
    console_log('node_save');
    $('#main').find('div').data('command')('save'); //FIXME these want to be found properly
}

function node_delete(root, command){
    // FIXME this needs removal as references $INFO
    console_log('node_delete');
    var parsed_root = _parse_div(root);
    var my_root = parsed_root.root;
    var sent_data = $INFO.getState(my_root, 'sent_data');
    // FIXME we don't have the node for subforms yet
    // do we set them up with the correct node or backtrack to their parent?
    var node =  $INFO.getState(my_root, 'node', true);
    var out = {__root: root};
    var id;
    var __id;
    if (parsed_root.row === null){
        // single form
        id = sent_data.id;
        __id = sent_data.__id;
    } else {
        // continuous form
        if (sent_data[parsed_root.row]){
            id = sent_data[parsed_root.row].id;
            __id = sent_data[parsed_root.row].__id;
        } else {
            // this row has not been saved so let's just hide it
            // we need to make it clean too so it won't trigger a save
            var state = $INFO.getState(my_root, 'form_info');
            state.clean_rows[parsed_root.row] = true;
            $('#' + $INFO.getId(root)).hide();
        }
    }

    if (__id){
        out.__id = __id;
    }
    if (id){
        out.id = id;
    }
    var form_data = $INFO.getState(my_root, 'form_info').form_data;
    if (form_data && form_data.params && form_data.params.id_field){
        var id_field = form_data.params.id_field;
        out[id_field] = sent_data[parsed_root.row][id_field];
    }

    if (form_data && form_data.table_name){
        out.table_name = form_data.table_name;
    }

    var params = form_data.params;
    if (params && params.extras){
        for (var extra in params.extras){
            if (params.extras.hasOwnProperty(extra)){
                out[extra] = params.extras[extra];
            }
        }
    }
    get_node(node, '_delete', out, false);
}


function node_button(item, node, command){
    var out = $('#main div.f_form').data('command')('get_form_data');
    get_node(node, command, out, false);
}

function node_button_input_form(item, node, command){
    var $obj = $('#main div.INPUT_FORM');
    var out = $obj.data('command')('get_form_data');
    if (out){
        get_node_return(node, command, out, $obj);
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
    node_call_from_string(call_string, false);
}


var status_timer;

function job_processor_status(data, node, root){
    // display the message form if it exists
    if (data.form){
     //   data.form = $.Util.FormDataNormalize(data.form);
        $('#' + root).status_form();
    }
    // show info on form
    if (data.status){
        $('div.STATUS_FORM').data('command')('update', data.status);
    }
    // set data refresh if job not finished
    if (!data.status || !data.status.end){
        status_timer = setTimeout("get_status('/n:" + node + ":status:id=" + data.jobId + "')",1000);
    }
}

var bookmark_array = [];
var BOOKMARKS_SHOW_MAX = 6;
var BOOKMARK_ARRAY_MAX = 6;

function bookmark_add(bookmark){
    // remove the item if already in the list
    for (var i=0; i<bookmark_array.length; i++){
        if (bookmark_array[i].bookmark==bookmark.bookmark){
            bookmark_array.splice(i, 1);
            break;
        }
    }
    // trim the array if it's too long
    if (bookmark_array.length >= BOOKMARK_ARRAY_MAX){
        bookmark_array.splice(BOOKMARK_ARRAY_MAX - 1, 1);
    }
    bookmark_array.unshift(bookmark);
}

function bookmark_display(){
    categories = [];
    category_items = {};

    for(var i=0; i<bookmark_array.length && i<BOOKMARKS_SHOW_MAX; i++){
        entity_table = bookmark_array[i].entity_table
        if (category_items[entity_table] === undefined){
            categories.push(entity_table);
            category_items[entity_table] = []
        }

        html  = '<li class ="bookmark-item-' + entity_table + '">';
        html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
        html += bookmark_array[i].title + '</span>';
        html += '</li>';

        category_items[entity_table].push(html);
    }

    var html = '<ol class = "bookmark">';
    for(var i=0; i<categories.length; i++){
        category = categories[i];
        html += '<li class ="bookmark-category-title-' + category + '">';
        html += category;
        html += '</li>';
        html += '<ol class ="bookmark-category-list-' + category + '">';
        html += category_items[category].join('\n');
        html += '</ol>';
    }

    html += '</ol>';

    $('#bookmarks').html(html);
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


var fn = function(packet, job){

     if (packet.data === null){
         console_log("NULL DATA PACKET");
         return;
     }

     var root = 'main'; //FIXME

     var title = packet.data.title;
     if (title){
         $.address.title(title);
     }

     var bookmark = packet.data.bookmark;
     if (bookmark){
        bookmark_add(bookmark);
        bookmark_display();
     }

    var data;
     switch (packet.data.action){
         case 'update_bookmarks':
            bookmark = packet.data.data;
            if (bookmark){
                if ($.isArray(bookmark)){
                    for (i = 0; i < bookmark.length; i++){
                       bookmark_add(bookmark[i]);
                    }
                } else {
                    bookmark_add(bookmark);
                }
                bookmark_display();
             }

             break;
         case 'redirect':
             var link = packet.data.link;
             if (link){
                 node_load('n:' + link);
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
             var form = packet.data.data.form;
             form = $.Util.FormDataNormalize(form, packet.data.node);
             data = packet.data.data.data;
             var paging = packet.data.data.paging;
             if (form.params.form_type == 'grid'){
                $('#' + root).grid(form, data, paging);
             } else if (form.params.form_type == 'action'){
                $('#' + root).input_form(form, data, paging);
             } else {
                $('#' + root).form(form, data, paging);
             }
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
            alert(packet.data.data);
            break;
        case 'status':
            job_processor_status(packet.data.data, packet.data.node, root);
            break;
    }
};

$JOB.addPacketFunction('node', fn);

