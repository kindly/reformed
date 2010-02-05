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


(function($) {
	
$.fn.extend({

	layout_manager: function(){
		$.LayoutManager(this);
	}
});
$.Buttons = {};

$.Buttons.action_hash = {
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    'delete':[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, node_load, ['n:test.HomePage:']]]
};

$.Buttons.action_call = function (action_name){
    // this function fires the event for action button clicks
    // we get the base object, function to call and the args from the
    // array action_hash
    var cmd_info = $.Buttons.action_hash[action_name][1];
    cmd_info[1].apply(cmd_info[0], cmd_info[2]);
};


$.LayoutManager = function () {

    function create_main(){
        $main = $('<div id="main"></div>');
        position_main();
        $body.append($main);
    }

    function create_actions(){


        function add_action_button(name, data, button_number){
            
            var button_data = data[0];
            var $button = $('<div id="action_' + name + '" class="action"></div>');
            var $link = $('<a href="javascript:$.Buttons.action_call(\'' + name + '\')"></a>');
            var $img = $('<img src="icon/22x22/' + button_data[1] + '" />');
            var $command = $('<span class="command">' + button_data[0] + '</span>');
            var $shortcut = $('<span class="shortcut">' + button_data[2] + '</span>');

            $link.append($img).append($command).append($shortcut);
            $button.append($link);

            var button_width = 200;
            var button_top = (button_number % BUTTONS_PER_COLUMN) * (util_size.ACTION_BUTTON_H + ACTION_BUTTON_SPACING) + ACTION_BUTTON_SPACING;
            var button_left = 10;
            var button_image_size = 12;

            position($button, button_top, button_left, util_size.ACTION_BUTTON_H, button_width);
            position($link, 0, 0, util_size.ACTION_BUTTON_H, button_width);
            position($img, 0, 0, button_image_size, button_image_size);
            position($command, 0, button_image_size, util_size.ACTION_BUTTON_H, button_width - (2 * button_image_size));
            position($shortcut, 0, button_width - button_image_size, util_size.ACTION_BUTTON_H, button_image_size);

            $button_holder.append($button);
        }


        function add_actions(){

            var html = '';
            for (var i = 0, n = action_list.length; i < n; i++){
                action = action_list[i];
                if (action && $.Buttons.action_hash[action]){
                    add_action_button(action, $.Buttons.action_hash[action], i);
                }
            }
        }


        var BUTTONS_PER_COLUMN = 4;
        var ACTION_BUTTON_SPACING = 5;
        $actions = $('<div id="actions"></div>');
        position_actions();
    
        var $button_holder = $('<div style="position:relative"></div>');
        $actions.append($button_holder);
    


        var action_list = ['home',  'save', 'delete'];

        add_actions();
        $body.append($actions);
    }

    function create_side(){
        $side = $('<div></div>');

        var html = [];
        // FIXME this wants to be ripped out asap
        html.push('<div style=\'font-size:12px\'>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', \'css/size1.css\');" style="font-size:8px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', \'css/size2.css\');" style="font-size:10px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', \'css/size3.css\');" style="font-size:12px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', \'css/size4.css\');" style="font-size:14px">A</span>');
        html.push('<span onclick="$.Util.selectStyleSheet(\'size\', \'css/size5.css\');" style="font-size:16px">A</span>');
        html.push('</div>');
    
        html.push('<form action="" onclick="$.Util.Event_Delegator(\'clear\');" onsubmit="return search_box();">');
        html.push('<input type=\'text\' name=\'search\' id=\'search\' />');
        html.push('</form>');
    
        html.push('<ul>');
        html.push('<li><span onclick="node_load(\'n:table.Table:new\')">new table</span></li>');
        html.push('<li><span onclick="node_load(\'n:table.Table:list\')">table</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.Permission:list\')">perm</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.Permission:new\')">new perm</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.UserGroup:list\')">usergroup</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.UserGroup:new\')">new usergroup</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.Sponsorship:\')">sponsor</span></li>');
        html.push('<li><span onclick="node_load(\'n:test.Login:\')">login</span></li>');
        html.push('<li><span onclick="$JOB.add({}, {}, \'reload\', true)" ><b>reload</b></span></li>');
        html.push('<li><span onclick="get_node(\'test.DataLoader\', \'load\', {file:\'data.csv\', table:\'people\'})" ><b>load people</b></span></li>');
        html.push('<li><span onclick="node_call_from_string(\'/n:test.DataLoader:load:file=donkeys.csv&table=donkey\', true)" ><b>load donkeys</b></span></li>');
        html.push('</ul>');
        html.push('<div id="bookmarks"></div>');
    
        $side.html(html.join(''));

        position_side();
        $body.append($side);
    }

    function create_logo(){
        $logo = $('<div><img src="logo.png" /></div>');
        // fixme get height/width correct etc
        $logo.find('img').css({width : 95, height : 95});
        $logo.css({overflow : 'hidden'});
        position_logo();
        $body.append($logo);
    }


    function position_main(){
        var top = info.margin_top + info.top_height + info.spacing;
        var left = info.margin_left + info.left_width + info.spacing;
        var height = null;
        var width = info.page_width - (info.left_width + info.spacing + info.margin_left + info.margin_right + util_size.SCROLLBAR_WIDTH);
        position($main, top, left, height, width);
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

        position($actions, top, left, height, width);
    }

    function position_side(){
        position($side, info.margin_top + info.top_height + info.spacing, info.margin_left, null, info.left_width);
    }

    function position_logo(){
        position($logo, info.margin_top, info.margin_left, info.top_height, info.left_width);
    }


    var info = {
        margin_left : 10,
        margin_right : 10,
        margin_top : 10,
        left_width : 200,
        top_height : 100,
        spacing : 10,
        page_width : undefined
    };
    

    var util_size = $.Util.Size;
    var position = $.Util.Position;
    var $main;
    var $side;
    var $logo;
    var $actions;
    var $body = $('body');

    info.page_width = util_size.PAGE_WIDTH;

    create_logo();
    create_main();
    create_side();
    create_actions();

};


})(jQuery);

$(document).ready($.LayoutManager);
