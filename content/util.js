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

// General functions
$.Util = {};

$.Util.get_keystroke = function (e){
    // make a simple key code string
    // eg          tab => 8
    //      ctrl + tab => 8c
    // alpha keys return the UPPER CASE letter plus any modifier
    // eg A, Ac, As
    var key = e.keyCode;
    if (key > 64 && key < 91){ // a-z
        key = String.fromCharCode(key);
    } else {
        key = String(key);
    }
    if (e.shiftKey){
        key += 's';
    }
    if (e.ctrlKey){
        key += 'c';
    }
    if (e.altKey){
        key += 'a';
    }
    return key;
};

$.Util.clone_hash_shallow = function (arg){
    var new_hash = {}
    for (var item in arg){
        new_hash[item] = arg[item];
    }
    return new_hash;
};

$.Util.control_setup = function($control, field){
    // add any events needed by the control
    // but start by removing any existing bound events
    $control.unbind();
    switch (field.type){
        case 'Integer':
            $control.change($FORM_CONTROL._intbox_change);
            $control.keydown($FORM_CONTROL._intbox_key);
            break;
        case 'DateTime':
        case 'Date':
            $control.keydown($FORM_CONTROL._datebox_key);
            break;
    }
    if (field.params && field.params.control == 'dropdown'){
        $control.autocomplete(field.params.autocomplete, {'dropdown':true});
    }
};

$.Util.control_takedown = function($control, field){
    // add any events needed by the control
    // but start by removing any existing bound events
    if (field.params && field.params.control == 'dropdown'){
        $control.unautocomplete();
    }
    $control.unbind();
};

$.Util.make_editable = function($item, field){
    // make the selected item an editable control
    // and return the new control
    var value = $item.html();
    if ($item.hasClass('null')){
        value = '';
    }
    if (value == '&nbsp;'){
        value = '';
    }
    $item.html('<input type="text" value="' + value + '" />');
    var $control = $item.find('input');
    $.Util.control_setup($control, field);
    $control.select();
    return $control;
};

$.Util.make_normal = function($item, field){
    // return the item to it's normal state
    // and return it's value
    var $control = $item.find('input');
    $.Util.control_takedown($control, field);
    var value = $control.val().trim();
    // check for nulls
    if (value === ''){
       if ($item.hasClass('null')){
           value = null;
       }
    }
    var cleaned = $.Util.clean_value(value, field);
    // output
    if (cleaned.value === null){
        cleaned.update_value = '[NULL]';
        $item.addClass('null');
    } else {
        $item.removeClass('null');
    }
    if (cleaned.update_value === ''){
        $item.html('&nbsp;');
    } else {
        $item.text(cleaned.update_value);
    }
    return cleaned.value;
};

$.Util.get_item_value = function (item, data){

    if (data && data[item.name] !== undefined){
        return data[item.name];
    }
    if (item.params['default']){
        return item.params['default'];
    }
    return null;
};

$.Util.clean_value = function (value, field){

    var update_value = value;
    // special controls
    switch (field.type){
        case 'DateTime':
        case 'Date':
            value = date_from_value(value);
            if (value){
                update_value = value.toLocaleDateString();
                value = value.toISOString();
            } else {
                value = null;
            }
            break;
        case 'Boolean':
            if (value == 'true'){
                value = true;
            } else {
                value = false;
            }
            update_value = value;
            break;
        case 'Integer':
            if (value !== null){
                value = parseInt(value, 10);
            }
            update_value = value;
            break;
    }

    return {"value" : value,
            "update_value" : update_value}


}


$.Util.paging_bar = function (data){

    var PAGING_SIZE = 5;
    var html ='paging: ';
    var offset = data.offset;
    var limit = data.limit;
    var count = data.row_count;
    var base = data.base_link;

    var pages = Math.ceil(count/limit);
    var current = Math.floor(offset/limit);

    if (current>0){
        html += '<a href="#" onclick="node_load(\'' + base + '&o=0&l=' + limit +'\');return false;">|&lt;</a> ';
        html += '<a href="#" onclick="node_load(\'' + base + '&o=' + (current-1) * limit + '&l=' + limit +'\');return false;">&lt;</a> ';
    } else {
        html += '|&lt; ';
        html += '&lt; ';
    }
    for (var i=0; i < pages; i++){
        if (i == current){
            html += (i+1) + ' ';
        } else {
            if ( Math.abs(current-i)<PAGING_SIZE ||
                 (i<(PAGING_SIZE*2)-1 && current<PAGING_SIZE) ||
                 (pages-i<(PAGING_SIZE*2) && current>pages-PAGING_SIZE)
            ){
                html += '<a href="#" onclick="node_load(\'' + base + '&o=' + i * limit + '&l=' + limit +'\');return false;">' + (i+1) + '</a> ';
            }
        }
    }
    if (current<pages - 1){
        html += '<a href="#" onclick="node_load(\'' + base + '&o=' + (current+1) * limit + '&l=' + limit +'\');return false;">&gt;</a> ';
        html += '<a href="#" onclick="node_load(\'' + base + '&o=' + (pages-1) * limit + '&l=' + limit +'\');return false;">&gt;|</a> ';
    } else {
        html += '&gt; ';
        html += '&gt;| ';
    }

    html += 'page ' + (current+1) + ' of ' + pages;
    return html;
};

$.Util.Position = function ($item, top, left, height, width){
    // position an element absolutely on the screen
    var css = {position : 'absolute'};
    if (top){
        css.top = top;
    }
    if (left){
        css.left = left;
    }
    if (height){
        css.height = height;
    }
    if (width){
        css.width = width;
    }
    $item.css(css);
};

// $.Util.Size
// this is used to calculate and store size related info
// needed to get placements correct etc
$.Util.Size = {};

$.Util.Size.get = function(){

    function action_button(){
        // get size of action buttons
        var $div = $('<div style="overflow:hidden; width:100px; height:100px; position:absolute; left:-200px; top:0px;"></div>');
        $div.append('<div class="action"><a href="#"><span class="command">button</span><span class="shortcut">A</span></a></div>');
        $('body').append($div);
        var $x = $div.find('div.action');
        util_size.ACTION_BUTTON_H = $x.outerHeight();
        $div.remove();
    }

    function scrollbar(){
        // get width of scrollbar
        var $div = $('<div style="overflow:hidden; width:50px; height:50px; position:absolute; left:-100px; top:0px;"><div style="height:60px;"></div></div>');
        $('body').append($div);
        var w1 = $div.find('div').width();
        $div.css('overflow-y', 'scroll');
        var w2 = $div.find('div').width();
        util_size.SCROLLBAR_WIDTH = w1 - w2;
        $div.remove();
    }

    function grid(){
        // get interesting stuff about grid cells
        // needed for acurate resizing
        var $div = $('<div style="overflow:hidden; width:150px; height:200px; position:absolute; left:-200px; top:0px;"></div>');
        $div.append('<div class="scroller-title">head</div><table class="grid"><thead><tr><th>head</th></tr></thead><tbody><tr><td style="width:100;">body</td></tr><tr><td class="t_edited_cell">body</td></tr></tbody></table><div class="scroller-foot">foot</div>');
        $('body').append($div);

        var $x = $div.find('th');
        util_size.GRID_HEADER_BORDER_W = $x.outerWidth() - $x.width();
        util_size.GRID_HEADER_H = $x.outerHeight();

        var $x = $div.find('td').eq(0);
        util_size.GRID_BODY_BORDER_W = $x.outerWidth() - $x.width();
        util_size.GRID_BODY_H = $x.outerHeight();

        var $x = $div.find('td').eq(1);
        util_size.GRID_BODY_BORDER_W_EDIT = $x.outerWidth() - $x.width();
        util_size.GRID_BODY_H_EDIT = $x.outerHeight();

        var $x = $div.find('div.scroller-title');
        util_size.GRID_TITLE_H = $x.outerHeight();

        var $x = $div.find('div.scroller-foot');
        util_size.GRID_FOOTER_H = $x.outerHeight();

        util_size.GRID_COL_RESIZE_DIFF = util_size.GRID_HEADER_BORDER_W - util_size.GRID_BODY_BORDER_W;
        util_size.GRID_COL_EDIT_DIFF = util_size.GRID_BODY_BORDER_W_EDIT - util_size.GRID_BODY_BORDER_W;

        if (!$.browser.mozilla){
            util_size.GRID_COL_EDIT_DIFF = 0;
            util_size.GRID_COL_RESIZE_DIFF = 0;
        }

        $div.remove();
    }

    var util_size = $.Util.Size;
    action_button();
    scrollbar();
    grid();

};

$.Util.selectStyleSheet = function (title, url){
    // disable all style sheets with the given title
    // enable the one with the correct url ending
    // if not found try to load it.
    function update_onloaded(){

        function update(){
            // refresh the sizes of elements
            $.Util.Size.get();
            // update any grids
            var $grids = $('div.GRID');
            for (var i = 0, n = $grids.size(); i < n; i++){
                $grids.eq(i).data('resize')();
            }
        }

        function check_loaded(){
            if ((--tries < 0) || $('#styleSheetCheck').css('font-family') == '"' + url + '"'){
                // stylesheet has loaded
                // remove our special div
                $('#styleSheetCheck').remove();
                update();
            } else {
                // wait and try again
                setTimeout(check_loaded, 50);
            }
        }

        var tries = 50; //number of attempts before giving up

        // add a special div that has the font-family set to the file name in the new stylesheet
        $('body').append('<div id="styleSheetCheck" style="display:none"></div>');
        check_loaded();
    }


    var $style_sheets = $('link[title]');
    var style_sheet;
    var found = false;
    for (var i = 0, n = $style_sheets.size(); i < n; i++){
        style_sheet = $style_sheets[i];
        if (style_sheet.title == title){
            if (style_sheet.href.search(url + '$') == -1){
                style_sheet.disabled = true;
            } else {
                found = true;
                style_sheet.disabled = false;
            };
        }
    }
    if (!found){
        console_log('load ' + url);
        $('head').append($('<link media="screen" title="'+ title + '" href="' + url + '" type="text/css" rel="alternate stylesheet"/>'));
    }
    update_onloaded();
};

$.Util.HTML_Encode = function (arg) {
    // encode html
    // replace & " < > with html entity
    if (arg === null){
        return '';
    }
    if (typeof arg != 'string'){
        return arg;
    }
    return arg.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
};

$.Util.FormDataNormalize = function (form_data, node) {
    // add parameters if not
    if (!form_data.params){
        form_data.params = {};
    }
    form_data.node = node;
    // make hash of the fields
    form_data.items = {};
    for (var i = 0, n = form_data.fields.length; i < n; i++){
        var field = form_data.fields[i];
        field.index = i;
        form_data.items[field.name] = field;
        if (!field.params){
            field.params = {};
        }
    }
    return form_data;
};

$.Util.Event_Delegator_Store = {};

$.Util.Event_Delegator = function (command, data){


    function clear(){
        info.keydown = undefined;
        if (info.blur){
            info.blur();
        }
        info.blur = undefined;
    }

    function register(){
        clear();
        if (data.keydown){
            info.keydown = data.keydown;
        }
        if (data.blur){
            info.blur = data.blur;
        }
    }

    var info = $.Util.Event_Delegator_Store;

    switch (command){
        case 'register':
            register();
            break;
        case 'clear':
            clear();
            break;
    }
};

$.Util.Event_Delegator_keydown = function (e){
    var keydown = $.Util.Event_Delegator_Store.keydown;
    if (keydown){
        keydown(e);
    } else {
        console_log('no bound keydown');
    }
};



})(jQuery);


// get our size calculations
$(document).ready($.Util.Size.get);
//trap keyboard events
$(document).keydown($.Util.Event_Delegator_keydown);

function console_log(obj){
    if (typeof console == "object"){
       console.log(obj);
    }
}

