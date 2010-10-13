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
/*global $ */

var REBASE = {};

/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    BOOKMARK
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Bookmark functions.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Bookmark = function (){

    var bookmark_array = [];
    var BOOKMARKS_SHOW_MAX = 100;
    var BOOKMARK_ARRAY_MAX = 100;

    function bookmark_add(bookmark){
        // create the bookmark view link
        if (bookmark.entity_id === null){
            alert('null bookmark');
        }
        // stop null bookmarks
        if (!bookmark.title){
            bookmark.title = 'untitled';
        }
        var table_data = REBASE.application_data.bookmarks[bookmark.entity_table];
        if (table_data){
            bookmark.bookmark = 'u:' + table_data.node + ':edit:id=' + bookmark.entity_id;
        } else {
            bookmark.bookmark = 'u:test.Auto:edit:id=' + bookmark.entity_id + '&table=' + bookmark.entity_table;
        }
        // remove the item if already in the list
        for (var i = 0, n = bookmark_array.length; i < n; i++){
            if (bookmark_array[i].bookmark == bookmark.bookmark){
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
        var categories = [];
        var category_items = {};
        var category;
        var entity_table;
        var html;
        // create an item for each bookmark and put it in
        // the array for its category
        for(var i = 0; i < bookmark_array.length && i < BOOKMARKS_SHOW_MAX; i++){
            entity_table = bookmark_array[i].entity_table;
            if (category_items[entity_table] === undefined){
                categories.push(entity_table);
                category_items[entity_table] = [];
            }
            html  = '<li>';
            html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
            html += bookmark_array[i].title + '</span>';
            html += '</li>';

            category_items[entity_table].push(html);
        }
        // create the actual bookmarks list
        html = '<ol class = "bookmark">';
        for(i = 0; i < categories.length; i++){
            category = categories[i];
            html += '<li class ="bookmark-title bookmark-category-' + category + '">';
            html += category;
            html += '<ol class ="bookmark-items">';
            html += category_items[category].join('\n');
            html += '</ol>';
            html += '</li>';
        }
        html += '</ol>';
        $('#bookmarks').html(html);
    }

    function bookmark_process(bookmark){
        if ($.isArray(bookmark)){
            // if we get an array of bookmarks
            // clear any existing bookmarks
            // and replace with the new ones
            bookmark_array = [];
            for (var i = 0, n = bookmark.length; i < n; i++){
                bookmark_add(bookmark[i]);
            }
        } else {
            if (bookmark == 'CLEAR'){
                // reset the bookmarks
                bookmark_array = [];
            } else {
                bookmark_add(bookmark);
            }
        }
        bookmark_display();
    }

    return {
        process : function (arg){
            bookmark_process(arg);
        }
    };

}();
