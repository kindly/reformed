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


$.Buttons = {};

$.Buttons.action_hash = {};

$.Buttons.action_list = [];

$.Buttons.action_call = function (action_name){
    // this function fires the event for action button clicks
    // we get the base object, function to call and the args from the
    // array action_hash
    var cmd_info = $.Buttons.action_hash[action_name][1];
    cmd_info[1].apply(cmd_info[0], cmd_info[2]);
};

var REBASE = {};


REBASE.LayoutManager = function (){
    var current_layout;

    var util_size = $.Util.Size;
    var position_absolute = $.Util.position_absolute;
    var position = $.Util.position;
    var $main;
    var $side;
    var $logo;
    var $actions;
    var first_run = true;
    var $body = $('<div id="layout_holder">');
    var BUTTONS_PER_COLUMN = 3;
    var ACTION_BUTTON_SPACING = 7;
    var ACTION_BUTTON_SPACING_H = 3;
    var ACTION_BUTTON_SPACING_V = 16;
    var ACTION_BUTTON_WIDTH = 200;

    var info = {
        margin_left : 10,
        margin_right : 10,
        margin_top : 10,
        left_width : 200,
        top_height : 100,
        spacing : 0,
        page_width : undefined
    };

    function position_main(){
        var top = info.margin_top + info.top_height + info.spacing;
        var left = info.margin_left + info.left_width + info.spacing;
        var height = null;
        var width = info.page_width - (info.left_width + info.spacing + info.margin_left + info.margin_right + util_size.SCROLLBAR_WIDTH);
        position_absolute($main, top, left, height, width);
        // Store the viewable size of the div.
        util_size.MAIN_WIDTH = width;
        util_size.MAIN_HEIGHT = util_size.PAGE_HEIGHT - top - info.spacing;
        // Store the offsets so we can recalculate if the browser window is resized
        util_size.MAIN_WIDTH_OFFSET = info.left_width + info.spacing + info.margin_left + info.margin_right + util_size.SCROLLBAR_WIDTH;
        util_size.MAIN_HEIGHT_OFFSET = top + info.spacing;
    }

    function position_actions(){
        var top = info.margin_top;
        var left = info.margin_left + info.left_width + info.spacing;
        var height = info.top_height;
        var width = info.page_width - (info.left_width + info.spacing + info.margin_left + info.margin_right + util_size.SCROLLBAR_WIDTH);

        position_absolute($actions, top, left, height, width);
    }

    function position_side(){
        position_absolute($side, info.margin_top + info.top_height + info.spacing, info.margin_left, null, info.left_width);
    }

    function position_logo(){
        position_absolute($logo, info.margin_top, info.margin_left, info.top_height, info.left_width);
    }

    function create_main(){
        $main = $('<div id="main"></div>');
        position_main();
        $body.append($main);
    }

    function create_actions(){

        var $button_holder;

        var action_list = $.Buttons.action_list;

        function add_action_button(name, data, button_number){
            
            var $button = $('<div id="action_' + name + '" class="action"></div>');
            var $link = $('<a href="javascript:node_load(\'' + data[4] + '\')"></a>');
            var $img = $('<img src="icon/22x22/' + data[1] + '" />');
            var $command = $('<span class="command">' + data[0] + '</span>');
            var $shortcut = $('<span class="shortcut">' + data[2] + '</span>');

            $link.append($img).append($command).append($shortcut);
            $button.append($link);

            var button_top = (button_number % BUTTONS_PER_COLUMN) * (util_size.ACTION_BUTTON_H + ACTION_BUTTON_SPACING_H) + ACTION_BUTTON_SPACING_H;
            var button_left = (ACTION_BUTTON_SPACING_V + ACTION_BUTTON_WIDTH) * Math.floor(button_number / BUTTONS_PER_COLUMN);
            var button_image_size = 12;

            //position_absolute($button, button_top, button_left, util_size.ACTION_BUTTON_H, ACTION_BUTTON_WIDTH);
            //position_absolute($link, 0, 0, util_size.ACTION_BUTTON_H, ACTION_BUTTON_WIDTH);
            //position_absolute($img, 0, 0, button_image_size, button_image_size);
            //position_absolute($command, 0, button_image_size, util_size.ACTION_BUTTON_H, ACTION_BUTTON_WIDTH - (2 * button_image_size));
            //position_absolute($shortcut, 0, ACTION_BUTTON_WIDTH - button_image_size, util_size.ACTION_BUTTON_H, button_image_size);

            $button_holder.append($button);
        }

        function user_bar(){
            var $user_bar = $('<div id="user_bar"></div>');
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
            return $user_bar;
        }


        function add_actions(){
            var action;
            var html = '';
            for (var i = 0, n = action_list.length; i < n; i++){
                action = action_list[i];
                if (action && $.Buttons.action_hash[action]){
                    add_action_button(action, $.Buttons.action_hash[action], i);
                }
            }
        }

        $actions = $('<div id="actions"></div>');
        position_actions();
    
        $button_holder = $('<div class="button_holder" style="position:relative"></div>');
        $actions.append($button_holder);


        add_actions();
        var $user_bar = user_bar();
        position_absolute($user_bar, (ACTION_BUTTON_SPACING_H + util_size.ACTION_BUTTON_H) * BUTTONS_PER_COLUMN + ACTION_BUTTON_SPACING_H*2, 0, null, info.page_width - (info.left_width + info.spacing + info.margin_left + info.margin_right + util_size.SCROLLBAR_WIDTH));
        $actions.append($user_bar);
        $body.append($actions);
    }

    function create_side(){
        $side = $('<div id="side"></div>');

        var html = [];
        // FIXME this wants to be ripped out asap
        html.push('<div style=\'font-size:12px\'>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', 1);" style="font-size:8px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', 2);" style="font-size:10px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', 3);" style="font-size:12px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', 4);" style="font-size:14px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', 5);" style="font-size:16px">A</span>');
        html.push('</div>');
    
    
//        html.push('<ul>');
//        html.push('<li><span onclick="$.Util.stress_test(\'n:table.Edit:list:t=9&l=100&o=\', 9900)">stress test</span></li>');
//        html.push('<li><span onclick="node_load(\'n:table.Table:new\')">new table</span></li>');
//        html.push('<li><span onclick="node_load(\'n:table.Table:list\')">table</span></li>');
//        html.push('<li><span onclick="node_load(\'n:test.Sponsorship:\')">sponsor</span></li>');
//        html.push('<li><span onclick="$JOB.add({}, {}, \'reload\', true)" ><b>reload</b></span></li>');
//        html.push('<li><span onclick="get_node(\'test.DataLoader\', \'load\', {file:\'data.csv\', table:\'people\'})" ><b>load people</b></span></li>');
//        html.push('<li><span onclick="node_call_from_string(\'/n:test.DataLoader:load:file=donkeys.csv&table=donkey\', true)" ><b>load donkeys</b></span></li>');
//        html.push('</ul>');
        html.push('<div id="bookmarks"></div>');
    
        $side.html(html.join(''));

        position_side();
        $body.append($side);
    }

    function create_logo(){
        $logo = $('<div id="logo"><img id="logo_image" src="logo.png" /></div>');
        // fixme get height/width correct etc
        // $logo.find('img').css({width : 95, height : 95});
        $logo.css({overflow : 'hidden'});
        position_logo();
        $body.append($logo);
    }





    function create_layout(arg){
        if (first_run){
            $('body').append($body);
            first_run = false;
        }

        info.page_width = util_size.PAGE_WIDTH;

        if (current_layout != arg){
            $body.empty();
            if (arg == "main"){
                info.left_width = 200;
                // FIXME THis is a botch as the 30 is just a guess at the search bar size
                // also this needs to refresh on font resizes etc
                var button_top = BUTTONS_PER_COLUMN * (util_size.ACTION_BUTTON_H + ACTION_BUTTON_SPACING_H) + ACTION_BUTTON_SPACING_H + 30;
                info.top_height = button_top;
                create_logo();
                create_main();
                create_side();
                create_actions();
            } else {
                info.left_width = 10;
                info.top_height = 10;
                create_main();
            }

            current_layout = arg;
        }
    }



    return {
        layout : function (arg){
            create_layout(arg);
        }
    };
}();



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

        for(var i = 0; i < bookmark_array.length && i < BOOKMARKS_SHOW_MAX; i++){
            entity_table = bookmark_array[i].entity_table;
            if (category_items[entity_table] === undefined){
                categories.push(entity_table);
                category_items[entity_table] = [];
            }

            html  = '<li class ="bookmark-item-' + entity_table + '">';
            html += '<span onclick="node_load(\'' + bookmark_array[i].bookmark + '\')">';
            html += bookmark_array[i].title + '</span>';
            html += '</li>';

            category_items[entity_table].push(html);
        }

        html = '<ol class = "bookmark">';
        for(i = 0; i < categories.length; i++){
            category = categories[i];
            html += '<li class ="bookmark-category-title-' + category + '">';
            html += category;
            html += '</li>';
            html += '<ol class ="bookmark-items bookmark-category-list-' + category + '">';
            html += category_items[category].join('\n');
            html += '</ol>';
        }

        html += '</ol>';

        $('#bookmarks').html(html);
    }

    function bookmark_process(bookmark){
         if ($.isArray(bookmark)){
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
