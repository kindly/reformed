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
		item: 		(obj) object detailing the item
		id:			(string) the HTML id of the control
		show_label:	(bool) should a label be shown

	exists (type) returns (bool)
		returns true if we have this control type	
		type:	(string) control type
		
	set (type, id, value)
		set value for the control
		
		type:	(string) control type
		id:		(string) the HTML id of the control
		value:	(string/int/bool) the value to assign
		
	get (type, id, value) returns (string/int/bool)
		get value for the control
		type:	(string) control type
		id:		(string) the HTML id of the control

	built-in controls
	-----------------
	textbox
	checkbox
	submit 
	dropdown 
	datebox 


*/

$FORM_CONTROL = {

	html: function(item, id, show_label, value){
		// returns HTML of a control
		if (this.exists(item.type)){
			// generate the HTML by calling the function	
			return this._controls[item.type](item, id, show_label, value);
		} else {
			// can't find this control
			return this._unknown(item, id);
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

	get: function (id, type){
		if (typeof(this['_' + type + '_get']) == "undefined"){
			// default get method
			return $("#" + id).val();
		} else {
			// use the special get method for this control
			return this['_' + type + '_get'](id);
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
	
	_controls: {
	
		// this is where our controls are defined
		info: function(item, id, show_label, value){
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
			x += '<div id="' + id + '">&nbsp;</div>';
			return x;
		},

        progress: function(item, id, show_label, value){
            var x = (show_label ? '<span class="label">' + item.title + '</span>' : '');
			x += '<div id="' + id + '" class="progressbar"></div>'; 
			return x;
        },
	
		textbox: function(item, id, show_label, value){
			// simple textbox
			var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
			x += '<input id="' + id + '" name="' + id + '" type="text" ';
            x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
			x += 'onchange="itemChanged(this)"  ';
			x += 'onkeyup="itemChanged(this)" />'; 
			return x;
		},

		password: function(item, id, show_label, value){
			// simple textbox
			var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
			x += '<input id="' + id + '" name="' + id + '" type="password" ';
            x += 'value="' + $FORM_CONTROL._clean_value(value) + '" ';
			x += 'onchange="itemChanged(this)"  ';
			x += 'onkeyup="itemChanged(this)" />'; 
			return x;
		},

		checkbox: function(item, id, show_label, value){
			// checkbox
			var x = (show_label ? $FORM_CONTROL._label(item, id) : '');
			x += '<input id="' + id + '" name="' + id + '" type="checkbox" ';
	        if (value){
                x += 'checked="checked" ';
            }
    		x += 'value="true" class="checkbox" ';
			x += 'onchange="itemChanged(this)" />'; 
			return x;
		},

		submit: function(item, id, show_label){
			// button
			var x = '<button id="' + id + '" type="button" ';
			x += 'onclick="node_button(this, \'' + item.params.node + '\', \'' + item.params.action + '\')" >';
			x += item.title + '</button>';			
			return x;
		},

		dropdown: function(item, id, show_label, value){
			// dropdown
			var x = show_label ? $FORM_CONTROL._label(item, id) : '';
			x += '<select id="' + id + '" name="' + id;
			x += '" onchange="itemChanged(this)" >';
			var type = item.params.type;
			var items = item.params.values.split('|');
			var i;
			switch (type){
				case 'list':
					for (i=0;i<items.length;i++){
						x += '<option value="' +  items[i] + '">';
						x += items[i] + '</option>';
					}
					break;
				default:
					for (i=0;i<items.length;i++){
						x += '<option value="' + i + '">';
						x += items[i] + '</option>';
					}
					break;
			}
			x += '</select>';
			return x;
		},

		datebox: function(item, id, show_label, value){
			// datebox
			// need to add onchange="itemChanged(this)" etc
			var x = show_label ? $FORM_CONTROL._label(item, id) : '';
			x += '<input id="' + id + '__user" name="' + id ;
			x += '__user" type="text" ';
			x += 'onchange="$FORM_CONTROL._datebox_change(this)" ';
			x += 'onkeyup="$FORM_CONTROL._datebox_key(this)" />';
			x += '<input id="' + id + '" name="' + id; 
			x += '" type="text" class="hidden" />';
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
	
	_datebox_set: function(id, value){
		// this is when the actual date value gets set
		$("#" + id + "__user").val(UTC2Date(value));
		$("#" + id).val(value);
	},

	_datebox_change: function (obj){
		// this is when the user date is changed
		var item = getItemFromObj(obj);
		if (isDate($(obj).val())){
			// date is good so update our hidden date field
			date = new Date($(obj).val());
	//		$("#" + item.root).val(makeUTC(date));
			// update our control to the new date
			datebox_set(item.root, makeUTC(date));
	//		$(obj).val(date.toLocaleDateString());
			$(obj).removeClass("error");
		} else {
			// date is bad
			$("#" + item.root).val('');
			$(obj).addClass("error");
		}
	},

	_datebox_key: function(obj){
		var item = getItemFromObj(obj);
		if (isDate($(obj).val())){
			// date is good so update our hidden date field
			date = new Date($(obj).val());
			$("#" + item.root).val(makeUTC(date));
			$(obj).removeClass("error");
		} else {
			// date is bad
			$(obj).addClass("error");
		}
	}

};





