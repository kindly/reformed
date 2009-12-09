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
    Copyright (c) 2008-2009 Toby Dacre & David Raznick

    form_control.js
    ===============

    Provides HTML controls for forms.

    $FORM_CONTROL

    Public Functions
    ================

    html (item, id, show_label) returns (string)
        returns HTML for the control or an 'unknown' placeholder
        item:         (obj) object detailing the item
        id:            (string) the HTML id of the control
        show_label:    (bool) should a label be shown

    exists (type) returns (bool)
        returns true if we have this control type
        type:    (string) control type

    set (type, id, value)
        set value for the control

        type:    (string) control type
        id:        (string) the HTML id of the control
        value:    (string/int/bool) the value to assign

    get (type, id, value) returns (string/int/bool)
        get value for the control
        type:    (string) control type
        id:        (string) the HTML id of the control

    built-in controls
    -----------------
    textbox
    checkbox
    submit
    dropdown
    datebox


*/

$FORM_CONTROL = {

    html: function(item, id, show_label, value, readonly){
        // returns HTML of a control
        if (readonly){
            return this._controls_readonly.general(item, id, show_label, value);
        } else {
            if (this.exists(item.type)){
                // generate the HTML by calling the function
                return this._controls[item.type](item, id, show_label, value);
            } else {
                // can't find this control
                return this._unknown(item, id);
            }
        }
    },

    exists: function (type){
        // returns true if we have this control type
        if (typeof(this._controls[type]) != "undefined"){
            // control exists
            return true;
        } else {
            return false;
        }
    },

    set: function (type, id, value){
        msg('set');
        if (typeof(this['_' + type + '_set']) == "undefined"){
            // default set method
            var item = $("#" + id);
            item.val([value]);
            item.attr('_value', value);

        } else {
            // use the special set method for this control
            this['_' + type + '_set'](id, value);
        }
    },

    get: function (id, type, dont_update){
        if (typeof(this['_' + type + '_get']) == "undefined"){
            // default get method
            var value = $("#" + id).val();
            if (value == '[NULL]' && $('#' +id).hasClass('null')){
                value = null;
            }
            return value;
        } else {
            // use the special get method for this control
            return this['_' + type + '_get'](id, dont_update);
        }
    },

    _label: function(item, id){
        var x = '<label id="' + id + '__label" for="' + id ;
        x += '" class="label" >' + item.title + '</label>';
        return x;
    },

    _unknown: function(item, id){
        var x = '<span>unknown control: &lt;' + item.type + '&gt; for ';
        x += item.title + '</span>';
        return x;
    },

    _clean_value: function(arg){
        if (arg){
            arg = String(arg).replace(/"/g, '&quot;');
        } else {
            arg = '';
        }
        return arg;
    },

    _controls_readonly: {
        general: function(item, id, show_label, value){
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
            x += '<div id="' + id + '">' + (value ? value : '&nbsp;') + '</div>';
            return x;
        }
    },

    _controls: {

        // this is where our controls are defined
        info: function(item, id, show_label, value){
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
            x += '<div id="' + id + '">' + (value ? value : '&nbsp;') + '</div>';
            return x;
        },

        link: function(item, id, show_label, value){
            var split = value.split("|");
            var link = split.shift();
            value = split.join('|');
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
            if (link.substring(0,1) == 'n'){
                x += '<a id="' + id + '" href="#" onclick="node_load(\'' + link + '\');return false">' + (value ? value : '&nbsp;') + '</a>';
            }
            if (link.substring(0,1) == 'd'){
                x += '<a id="' + id + '" href="#" onclick ="link_process(this,\'' + link + '\');return false;">' + (value ? value : '&nbsp;') + '</a>';
            }
            return x;
        },


        link_list: function(item, id, show_label, value){
            var x = '<span class="link_list" onfocus="itemFocus(this)" >';
            for (var i=0; i<value.length; i++){
                x += $FORM_CONTROL._controls.link(item, id + '__' + i, false, value[i]);
                x += ' ';
            }
            x += '</span>';
            return x;
        },

        progress: function(item, id, show_label, value){
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
            x += '<div id="' + id + '" class="progressbar"></div>';
            return x;
        },

        textarea: function(item, id, show_label, value){
            // simple textbox
            var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
            x += '<textarea id="' + id + '" name="' + id + '" ';
            x += 'onfocus="itemFocus(this)" ';
            x += 'onblur="itemBlur(this)" ';
            x += 'onchange="itemChanged(this)"  ';
            x += 'onkeyup="itemChanged(this)" ';
            x += 'onkeydown="keyDown(this, event)" />';
            if (value){
                x += $FORM_CONTROL._clean_value(value);
            }
            x += '</textarea>';
            return x;
        },

        textbox: function(item, id, show_label, value){
            // simple textbox
            var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
            x += '<input id="' + id + '" name="' + id + '" type="text" ';
            if (value === null){
                x += 'value="[NULL]" class="null" ';
            } else {
                x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
            }
            // set max length if specified
            if (item.params && item.params.validation && item.params.validation && item.params.validation[0] && item.params.validation[0].max){
                x += 'maxlength="' + item.params.validation[0].max + '" ';
            }
            x += 'onfocus="itemFocus(this)" ';
            x += 'onblur="itemBlur(this)" ';
            x += 'onchange="itemChanged(this)"  ';
            x += 'onkeyup="itemChanged(this)" ';
            x += 'onkeydown="keyDown(this, event)" />';
            return x;
        },

        emailbox: function(item, id, show_label, value){
            // simple textbox
            var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
            x += '<input id="' + id + '" name="' + id + '" type="text" ';
            if (value === null){
                x += 'value="[NULL]" class="null" ';
            } else {
                x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
            }
            // set max length if specified
            if (item.params && item.params.validation && item.params.validation && item.params.validation[0] && item.params.validation[0].max){
                x += 'maxlength="' + item.params.validation[0].max + '" ';
            }
            x += 'onfocus="itemFocus(this)" ';
            x += 'onblur="itemBlur(this)" ';
            x += 'onchange="itemChanged(this, true)"  ';
            x += 'onkeyup="itemChanged(this)" ';
            x += 'onkeydown="keyDown(this, event)" />';
            return x;
        },

        intbox: function(item, id, show_label, value){
            // simple textbox
            var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
            x += '<input id="' + id + '" name="' + id + '" type="text" ';
            if (value === null || value === ''){
                x += 'value="[NULL]" class="null" ';
            } else {
                x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
            }
            x += 'maxlength="10" ';
            x += 'onfocus="itemFocus(this)" ';
            x += 'onblur="itemBlur(this, true)" ';
            x += 'onchange="$FORM_CONTROL._intbox_change(this)"  ';
            x += 'onkeyup="itemChanged(this)" ';
            x += 'onkeydown="return $FORM_CONTROL._intbox_key(this, event)" />';
            return x;
        },

        password: function(item, id, show_label, value){
            // simple textbox
            var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
            x += '<input id="' + id + '" name="' + id + '" type="password" ';
            x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
            // set max length if specified
            if (item.params && item.params.validation && item.params.validation && item.params.validation[0] && item.params.validation[0].max){
                x += 'maxlength="' + item.params.validation[0].max + '" ';
            }
            x += 'onchange="itemChanged(this)"  ';
            x += 'onfocus="itemFocus(this)" ';
            x += 'onkeydown="keyDown(this, event)" />';
            return x;
        },

        checkbox: function(item, id, show_label, value){
            // checkbox
            var x = '';
            if (show_label && !item.reverse){
                x += $FORM_CONTROL._label(item, id);
            }
            x += '<input id="' + id + '" name="' + id + '" type="checkbox" ';
            if (value){
                x += 'checked="checked" ';
            }
            x += 'value="true" class="checkbox" ';
            x += 'onfocus="itemFocus(this)" ';
            x += 'onchange="itemChanged(this)" ';
            x += 'onkeydown="keyDown(this, event);return false" />';
            if (show_label && item.reverse){
                x += $FORM_CONTROL._label(item, id);
            }
            return x;
        },

        submit: function(item, id, show_label){
            // button
            var x = '<button id="' + id + '" type="button" ';
            x += 'onclick="node_button(this, \'' + item.params.node + '\', \'' + item.params.action + '\')" >';
            x += item.title + '</button>';
            return x;
        },

        code_group: function(item, id, show_label, value){
            var codes = item.params.codes;
            var x = show_label && item.title ? '<p>' + item.title + '</p>' : '';
            x += '<table><tr>';
            for (var i=0; i<codes.length; i++){
                var my_item = {};
                my_item.title = codes[i];
                my_item.reverse = true;
                var selected = false;
                for (var j=0; j<value.length; j++){
                    if (value[j]==codes[i]){
                        selected = true;
                        break;
                    }
                }
                var my_id = id + '__' + i;
                x += '<td>' + $FORM_CONTROL._controls.checkbox(my_item, my_id, true, selected) + '</td>';
            }
            x += '</tr></table>';
            return x;
        },

        dropdown: function(item, id, show_label, value){
            // dropdown
            var x = show_label ? $FORM_CONTROL._label(item, id) : '';
            x += '<select id="' + id + '" name="' + id;
            x += '" onfocus="itemFocus(this)" ';
            x += 'onchange="itemChanged(this)" >';
            var type = item.params.type;
            var items = item.params.values.split('|');
            var i;
            switch (type){
                case 'list':
                    for (i=0;i<items.length;i++){
                        x += '<option value="' +  items[i] + '"';
                        if (value == items[i]){
                            x += ' selected="selected" ';
                        }
                        x += '>';
                        x += items[i] + '</option>';
                    }
                    break;
                default:
                    for (i=0;i<items.length;i++){
                        x += '<option value="' + i + '"';
                        x += '>';
                        x += items[i] + '</option>';
                    }
                    break;
            }
            x += '</select>';
            return x;
        },

        datebox: function(item, id, show_label, value){
            // datebox
            // value is ISO format date so convert to local
            try
            {
                value = Date.ISO(value).toLocaleDateString();
            }
            catch(e)
            {
                value = '';
            }
            var x = show_label ? $FORM_CONTROL._label(item, id) : '';
            x += '<input id="' + id + '" name="' + id ;
            x += '" type="text" ';
            if (value === null || value === ''){
                x += 'value="[NULL]" class="null" ';
            } else {
                x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
            }
            x += 'maxlength="10" ';
            x += 'onfocus="itemFocus(this)" ';
            x += 'onblur="itemBlur(this, true)" ';
            x += 'onchange="$FORM_CONTROL._datebox_change(this)" ';
            x += 'onkeyup="itemChanged(this)" ';
            x += 'onkeydown="return $FORM_CONTROL._datebox_key(this,event)" />';
            return x;
        }
    },

    _info_set: function(id,value){
        // FIXME value needs to be html escaped
        $("#" + id).html(value);
    },

    _checkbox_set: function(id, value){
        // sets value of checkbox
        $("#" + id).attr("checked", value === true ? "checked" : "");
    },

    _checkbox_get: function(id){
        // gets value of checkbox
        return $("#" + id).attr("checked");
    },

    _code_group_get: function(id){
        var item = _parse_id(id);
        var form_data = $INFO.getState(item.root, 'form_data');
        var form_item = form_data.items[item.control];
        var codes = form_item.params.codes;
        var out = [];
        for (var i=0; i<codes.length; i++){
            if ($("#" + id + '__' + i).attr("checked")){
                out.push(codes[i]);
            }
        }
        return out;
        //info = $("#" + id + '__*').attr("checked");
      //  alert(info);
    },

    _datebox_set: function(id, value){
        // set the datebox field from ISO format
        try
        {
            value = Date.ISO(value).toLocaleDateString();
        }
        catch(e)
        {
            value = '';
        }
        $("#" + id).val(value);
    },

    _datebox_get: function(id, dont_update){
        var value = $("#" + id).val();
        if (value === '' || value == '[NULL]'){
            value = null;
        } else {
            value = date_from_value(value);
            if (value){
                value = value.toISOString();
                if (value == 'Invalid Date'){
                    value = '';
                } else {
                    // update the date in case we have changed it
                    if (dont_update !== true){
                        $FORM_CONTROL._datebox_set(id,value);
                    }
                }
            }
        }
        return value;
    },

    _datebox_change: function (obj){
        // this is when the user date is changed
        var value = $(obj).val();
        if (isDate(value) || value === ''){
            // date is good
            $(obj).removeClass("error");
        } else {
            // date is bad
            $(obj).addClass("error");
        }
        itemChanged(obj, true);
    },

    _datebox_key: function(obj, event){
        var key = getKeyPress(event);
        if ((key.code > 47 && key.code < 59) /* numbers */ ||
             (key.code == 191) /* forward slash */ ||
              allowedKeys(key) ){
            keyDown(obj, event);
            return true;
        } else {
            return false;
        }
    },

    _intbox_change: function(obj){
        if (isNaN(parseInt($(obj).val(), 10))){
            $(obj).val('');
        }
        itemChanged(obj);
    },

    _intbox_key: function(obj, event){
        var key = getKeyPress(event);
        if ((key.code > 47 && key.code < 59) /* numbers */ ||
              allowedKeys(key) ){
            keyDown(obj, event);
            return true;
        } else {
            return false;
        }
    }


};

// FIXME this needs to be in sync with the locale or else dates go crazy
// maybe need to do own toLocaleString function to get balance
// or else determine this from the locale being used by probing the date object
var DATE_FORMAT = 'UK';

function date_from_value(value){

    var day;
    var month;
    var year;
    var parts = value.split('/');
    if (parts.length == 3){
        switch(DATE_FORMAT){
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
        if (day){
            return new Date(year, month, day);
        }
    }
    // not a valid date
    return '';
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

