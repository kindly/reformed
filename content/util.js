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

$.Util.stress_test_offset = 0;

$.Util.stress_test = function (node, max_offset){
    node_load(node + $.Util.stress_test_offset)
    if ($.Util.stress_test_offset++ > max_offset){
        $.Util.stress_test_offset = 0;
        }
    setTimeout("$.Util.stress_test('" + node + "', " + max_offset + ")", 1000 )
};

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

$.Util.allowedKeys = function (key){

    // this returns true for allowed key presses
    // eg arrows cut/paste tab...

    // special keys
    if (key.ctrlKey || key.altKey){
        return true;
    }
    // list of allowed keys
    switch (key.keyCode){
        case 0: // special key
        case 8: // backspace
        case 9: // TAB
        case 13: // Return
        case 20: // Caps Lock
        case 27: // Escape
        case 35: // Home
        case 36: // End
        case 37: // Left
        case 38: // Up
        case 39: // Right
        case 40: // Down
        case 45: // Insert
        case 46: // Delete
        case 144: // Num Lock
        case 145: // Scroll Lock
            return true;
            break;
        default:
            return false;
    }
};

$.Util.datebox_key = function(e){
    var key = e.keyCode;
    if ((key > 47 && key < 59) /* numbers */ ||
         (key == 191) /* forward slash */ ||
          $.Util.allowedKeys(e) ){
        return true;
    } else {
        return false;
    }
};

$.Util.intbox_key = function(e){
    var key = e.keyCode;
    if ((key > 47 && key < 59) /* numbers */
         ||  $.Util.allowedKeys(e) )
    {
        return true;
    } else {
        return false;
    }
};

$.Util.intbox_change = function(obj){
    if (isNaN(parseInt($(obj).val(), 10))){
        $(obj).val('');
    }
};

$.Util.clone_hash_shallow = function (arg){
    var new_hash = {};
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
            $control.change($.Util.intbox_change);
            $control.keydown($.Util.intbox_key);
            break;
        case 'DateTime':
        case 'Date':
            $control.keydown($.Util.datebox_key);
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
            value = $.Util.date_from_value(value);
            if (value){
                update_value = value.makeLocaleString();
                value = value.toISOString();
            } else {
                value = null;
            }
            break;
        case 'Boolean':
            if (value !== null){
                if (value == 'true' || value === true){
                    value = true;
                } else {
                    value = false;
                }
            }
            update_value = value;
            break;
        case 'Integer':
            if (value !== null){
                value = parseInt(value, 10);
                if (isNaN(value)){
                    value = null;
                }
            }
            update_value = value;
            break;
    }

    // FIXME it would be nicer if we do not need to check for this
    // but at the moment we get data from none existant objects on occasions
    // this is just to stop these causing problems
    if (value === undefined){
        value = null
    };

    return {"value" : value,
            "update_value" : update_value};


};

$.Util.unbind_all_children = function ($div){
    // remove any existing items from the give div
    var $children = $div.children();
    for (var i = 0, n = $children.size(); i < n; i++){
            if ($children.eq(i).data('command')){
                $children.eq(i).data('command')('unbind_all');
            }
    }
    $children.remove();
    $children = null;
};

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
        html += '<a href="#" onclick="node_load_grid(\'' + base + '&o=0&l=' + limit +'\');return false;">|&lt;</a> ';
        html += '<a href="#" onclick="node_load_grid(\'' + base + '&o=' + (current-1) * limit + '&l=' + limit +'\');return false;">&lt;</a> ';
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
                html += '<a href="#" onclick="node_load_grid(\'' + base + '&o=' + i * limit + '&l=' + limit +'\');return false;">' + (i+1) + '</a> ';
            }
        }
    }
    if (current<pages - 1){
        html += '<a href="#" onclick="node_load_grid(\'' + base + '&o=' + (current+1) * limit + '&l=' + limit +'\');return false;">&gt;</a> ';
        html += '<a href="#" onclick="node_load_grid(\'' + base + '&o=' + (pages-1) * limit + '&l=' + limit +'\');return false;">&gt;|</a> ';
    } else {
        html += '&gt; ';
        html += '&gt;| ';
    }

    html += 'page ' + (current+1) + ' of ' + pages;
    return html;
};

$.Util.position = function ($item, top, left, height, width){
    // position an element absolutely on the screen
    var css = {};
    if (top !== null){
        css.top = top;
    }
    if (left !== null){
        css.left = left;
    }
    if (height !== null){
        css.height = height;
    }
    if (width !== null){
        css.width = width;
    }
    $item.css(css);
};

$.Util.position_absolute = function ($item, top, left, height, width){
    // position an element absolutely on the screen
    var css = {position : 'absolute'};
    if (top !== null){
        css.top = top;
    }
    if (left !== null){
        css.left = left;
    }
    if (height !== null){
        css.height = height;
    }
    if (width !== null){
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
        // Some browsers e.g. webkit don't let us measure
        // the scrollbar using the easy method above.
        // If it didn't work we use a different approach instead.
        if (util_size.SCROLLBAR_WIDTH === 0){
            var $div = $('<div style="overflow:hidden; width:50px; height:50px; position:absolute; left:-100px; top:0px;"></div>');
            var $d1 = $('<div style="height:60px;width:1px;float:left"></div>');
            var $d2 = $('<div style="height:60px;width:1px;float:left"></div>');
            $div.append($d1);
            $div.append($d2);
            $('body').append($div);
            w1 = 1;
            do {
                $d1.width(w1++);
            } while ($d2.position().top === 0);

            $div.css('overflow-y', 'scroll');
            w2 = 1;
            do {
                $d1.width(w2++);
            } while ($d2.position().top === 0);

            $div.remove();
            util_size.SCROLLBAR_WIDTH = w1 - w2;
        }

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

        $x = $div.find('td').eq(0);
        util_size.GRID_BODY_BORDER_W = $x.outerWidth() - $x.width();
        util_size.GRID_BODY_H = $x.outerHeight();

        $x = $div.find('td').eq(1);
        util_size.GRID_BODY_BORDER_W_EDIT = $x.outerWidth() - $x.width();
        util_size.GRID_BODY_H_EDIT = $x.outerHeight();

        $x = $div.find('div.scroller-title');
        util_size.GRID_TITLE_H = $x.outerHeight();

        $x = $div.find('div.scroller-foot');
        util_size.GRID_FOOTER_H = $x.outerHeight();

        util_size.GRID_COL_RESIZE_DIFF = util_size.GRID_HEADER_BORDER_W - util_size.GRID_BODY_BORDER_W;
        util_size.GRID_COL_EDIT_DIFF = util_size.GRID_BODY_BORDER_W_EDIT - util_size.GRID_BODY_BORDER_W;

        if ($.browser.safari){
            util_size.GRID_COL_EDIT_DIFF = 0;
            util_size.GRID_COL_RESIZE_DIFF = 0;
        }

        $div.append('<div class="scroller-loader" style="display:block;">Loading ...</div>');
        $x = $div.find('div.scroller-loader');
        util_size.GRID_LOADER_H = $x.outerHeight();
        util_size.GRID_LOADER_W = $x.outerWidth();
        $div.remove();
    }

    var util_size = $.Util.Size;
    action_button();
    scrollbar();
    grid();
    $.Util.Size.page_size();

};

$.Util.Size.page_size = function (){
    var util_size = $.Util.Size;
    var $screen = $(window);
    util_size.PAGE_WIDTH = $screen.width();
    util_size.PAGE_HEIGHT = $screen.height();
    // recalculate main div sizes
    if (util_size.MAIN_WIDTH_OFFSET){
        util_size.MAIN_WIDTH = util_size.PAGE_WIDTH - util_size.MAIN_WIDTH_OFFSET;
        util_size.MAIN_HEIGHT = util_size.PAGE_HEIGHT - util_size.MAIN_HEIGHT_OFFSET;
    } else {
        util_size.MAIN_WIDTH = util_size.PAGE_WIDTH;
        util_size.MAIN_HEIGHT = util_size.PAGE_HEIGHT;
    }
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
                $grids.eq(i).data('resize_grid')();
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
            }
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
    if (typeof arg != 'string'){
        return arg;
    }
    return arg.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
};

$.Util.HTML_Encode_Clear = function (arg) {
    // encode html also show null as ''
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
        if (field.name){
            form_data.items[field.name] = field;
        }
        if (!field.params){
            field.params = {};
        }
        if (field.type == 'subform'){
            console_log(field);
            field.params.form = $.Util.FormDataNormalize(field.params.form, node);
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

$.Util.is_empty = function (obj){
    for(var key in obj) {
        return false;
    }
    return true;
};

// FIXME this needs to be in sync with the locale or else dates go crazy
// maybe need to do own toLocaleString function to get balance
// or else determine this from the locale being used by probing the date object
$.Util.DATE_FORMAT = 'UK';

$.Util.date_from_value = function (value){

    if (!value){
        return '';
    }

    var day;
    var month;
    var year;
    var parts = value.split('/');
    if (parts.length == 3){
        switch($.Util.DATE_FORMAT){
            case 'UK':
                // UK format (dd/mm/yyyy)
                year = parseInt(parts[2], 10);
                month = parseInt(parts[1], 10) - 1;
                day = parseInt(parts[0], 10);
                break;
            case 'US':
                // US format (mm/dd/yyyy)
                year = parseInt(parts[2], 10);
                month = parseInt(parts[0], 10) - 1;
                day = parseInt(parts[1], 10);
                break;
            case 'ISO':
                // ISO format (yyyy/mm/dd)
                year = parseInt(parts[0], 10);
                month = parseInt(parts[1], 10) - 1;
                day = parseInt(parts[3], 10);
                break;
        }
        if (day !== undefined){
            var new_date = new Date();
            new_date.setUTCFullYear(year);
            new_date.setUTCMonth(month);
            new_date.setUTCDate(day);
            new_date.setUTCHours(0);
            new_date.setUTCMinutes(0);
            new_date.setUTCSeconds(0);
            new_date.setUTCMilliseconds(0);
            return new_date;
        }
    }
    // not a valid date
    return '';
};

})(jQuery);

$(window).resize($.Util.Size.page_size);
// get our size calculations
$(document).ready($.Util.Size.get);
//trap keyboard events
$(document).keydown($.Util.Event_Delegator_keydown);

function console_log(obj){
    if (typeof console == "object"){
       console.log(obj);
    }
}

// the validators we have
var validation_rules = {

    'UnicodeString' : function(rule, value){
        var errors = [];
        if (value !== null && rule.max && value.length > rule.max){
            errors.push('cannot be over ' + rule.max + ' chars');
        }
        return errors;
    },

    'Int' : function(rule, value){
        var errors = [];
        if (value > 2147483647){
            errors.push('maximum integer size is 2,147,483,647');
        }
        if (value < -2147483648){
            errors.push('minimum integer size is -2,147,483,648');
        }
        return errors;
    },

    'DateValidator' : function(rule, value, currently_selected){
        if (currently_selected === true){
            return []
        }
        var errors = [];
        if (value === ''){
            errors.push('not a valid date' + value);
        }
        return errors;
    },

    'Email' : function(rule, value, currently_selected){
        if (currently_selected === true){
            return []
        }
        var usernameRE = /^[^ \t\n\r@<>()]+$/i;
        var domainRE = /^(?:[a-z0-9][a-z0-9\-]{0,62}\.)+[a-z]{2,}$/i;
        var parts = value.split('@');
        if (parts.length != 2){
            return ['An email address must contain a single @'];
        }
        if (!parts[0].match(usernameRE)){
            return ['The username portion of the email address is invalid (the portion before the @)'];
        }
        if (!parts[1].match(domainRE)){
            return ['The domain portion of the email address is invalid (the portion after the @)'];
        }
        return [];
    }
};

function validate(rules, value, currently_selected){
    var errors = [];
    for (var i=0; i < rules.length; i++){
        rule = rules[i];
        // the first rule states if we allow nulls or not
        if (i === 0){
            if (rule.not_empty && value === null && currently_selected !== true){
                return ['must not be null'];
            }
        }
        // validate the rules for the field if we know the validator
        if (validation_rules[rule.type] !== undefined){
            validation_errors = (validation_rules[rule.type](rule, value, currently_selected));
            if (validation_errors.length){
                errors.push(validation_errors);
            }
        }
    }
    return errors;
}




/*
 *
 * Object overloading
 *
 */


if(!Date.ISO)(function(){"use strict";
/** ES5 ISO Date Parser Plus toISOString Method
 * @author          Andrea Giammarchi
 * @blog            WebReflection
 * @version         2009-07-04T11:36:25.123Z
 * @compatibility   Chrome, Firefox, IE 5+, Opera, Safari, WebKit, Others
 */
function ISO(s){
    var m = /^(\d{4})(-(\d{2})(-(\d{2})(T(\d{2}):(\d{2})(:(\d{2})(\.(\d+))?)?(Z|((\+|-)(\d{2}):(\d{2}))))?)?)?$/.exec(s);
    if(m === null)
        throw new Error("Invalid ISO String");
    var d = new Date;
    d.setUTCFullYear(+m[1]);
    d.setUTCMonth(m[3] ? (m[3] >> 0) - 1 : 0);
    d.setUTCDate(m[5] >> 0);
    d.setUTCHours(m[7] >> 0);
    d.setUTCMinutes(m[8] >> 0);
    d.setUTCSeconds(m[10] >> 0);
    d.setUTCMilliseconds(m[12] >> 0);
    if(m[13] && m[13] !== "Z"){
        var h = m[16] >> 0,
            i = m[17] >> 0,
            s = m[15] === "+"
        ;
        d.setUTCHours((m[7] >> 0) + s ? -h : h);
        d.setUTCMinutes((m[8] >> 0) + s ? -i : i);
    };
    return toISOString(d);
};
var toISOString = Date.prototype.toISOString ?
    function(d){return d}:
    (function(){
        function t(i){return i<10?"0"+i:i};
        function h(i){return i.length<2?"00"+i:i.length<3?"0"+i:3<i.length?Math.round(i/Math.pow(10,i.length-3)):i};
        function toISOString(){
            return "".concat(
                this.getUTCFullYear(), "-",
                t(this.getUTCMonth() + 1), "-",
                t(this.getUTCDate()), "T",
                t(this.getUTCHours()), ":",
                t(this.getUTCMinutes()), ":",
                t(this.getUTCSeconds()), ".",
                h("" + this.getUTCMilliseconds()), "Z"
            );
        };
        return function(d){
            d.toISOString = toISOString;
            return d;
        }
    })()
;
Date.ISO = ISO;
})();


// date to local string
if (!Date.makeLocaleString){
    Date.prototype.makeLocaleString = function (){
        // output the date as a locally formated string
        var day = this.getUTCDate();
        var month = this.getUTCMonth() + 1;
        var year = this.getUTCFullYear();
        var separator = '/';
        switch($.Util.DATE_FORMAT){
            case 'UK':
                // UK format (dd/mm/yyyy)
                return day + separator + month + separator + year;
                break;
            case 'US':
                // US format (mm/dd/yyyy)
                return month + separator + day + separator + year;
                break;
            case 'ISO':
                // ISO format (yyyy/mm/dd)
                return year + separator + month + separator + day;
                break;
        }
    }
}



// string trim() function
if(!String.trim){
    String.prototype.trim = function() { return this.replace(/^\s*((?:[\S\s]*\S)?)\s*$/, '$1'); };
}

