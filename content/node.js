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
