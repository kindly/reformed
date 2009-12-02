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
	
	info.js
	======
	
	Maintains lots of stuff for us froms, data, ids, etc

	$INFO

	Public Functions
	================
	
	clearId ()
		Resets the Id data

	getId (id) returns (string)
		returns the coded id for the id

	addId (id) returns (string)
		returns the coded id for the id, creating a new one if needed

	getReverseId (coded_id) returns (string)
		returns the id for a coded id
	
	getState (root, item) returns (string/int/bool)
		returns the state type for item of an object
		root:	(string) the id of the object on the HTML page
		item:	(string) the state being requested
		
	setState: (root, item, value)
		sets the state type for item of an object
		root:	(string) the id of the object on the HTML page
		item:	(string) the state to be updated
		value:	(string/int/bool) the new value

	setStateArray: function(root, item, row, value)
		sets the state type for array item of an object
		root:	(string) the id of the object on the HTML page
		item:	(string) the state to be updated
		row:	(int) the array index
		value:	(string/int/bool) the new value
	
	newState: function(root, type)
		sets the type of object in root and initialises state
		root:	(string) the id of the object on the HTML page
		type:	(string) the type of object being placed

	
	getStateDebug: function(root) returns (string)
		returns the state of the object at root 
		as JSON string for debug purposes
		root:	(string) the id of the object on the HTML page


	
*/


$INFO = {

	_id: {},
	_id_counter: 0,
	_reverse_id: [],
	_state: {}, 


	clearId: function(){

		// clears the ids info
		this._id_counter = 0;
		this._id = {};
		this._reverse_id = [];
	},

	getId: function(id){
	
		if (this._id[id]){
			return this._id[id];
		} else {
			alert('id ' + id + ' does not exist');
		}
	},

	addId: function(id){

		// if we already have this reuse it
		if (this._id[id]){
			return this._id[id];
		}
		// set the value
		this._id[id] = 'rfd_' + this._id_counter;
		this._reverse_id[this._id_counter] = id;		this._id_counter++;
		return this._id[id];
	},

	getReverseId: function(id){

		// get the name of the element with this id
		var my_id = parseInt(id.substring(4), 10);
		return this._reverse_id[my_id];
	},
	
	
	getState: function(root, item, search_parent){

        var my_root = _parse_div(root).root;
		if (my_root && this._state[my_root]){
            if (typeof(this._state[my_root][item]) != 'undefined'){
    			return this._state[my_root][item];
	    	} else {
                if (!search_parent){
			        return false;
                } else {
                    $INFO.getCallInfo();
                    // see if we can find the parent and if so look there
                    var split = my_root.split('#');
                    if (split.length >1){
                        var parent_root = '';
                        for (var i=0; i<split.length -1; i++){
                             parent_root += split[i] + '#';
                        }
                        parent_root = parent_root.substring(0, parent_root.length -1);
                        return $INFO.getState(parent_root, item);
                    }
                }
            }
		} else {
            alert('state: ' + item + ' not found in ' + root + '\n\n' + $INFO.getCallInfo());
        }
	},

	setState: function(root, item, value){

		if (root && this._state[root]){
			this._state[root][item] = value;
		} else {
			alert('setState:\nnot found\n' + root);
		}
	},

	setStateArray: function(root, item, row, value){
		//FIXME clean this up
		if (row === null){
			row = 0;
		} 
    //FIXME this don't work
	//	var form_info = $FORM._get_form_info(root);
	//	form_info.info[item][row] = value;
	},
	
	newState: function(root, type){

		if (root){
			this._state[root] = {};
			this._state[root].type = type;
		} else {
			alert('newState:\nroot undefined\n');
		}
	},
	
	getStateDebug: function(root){
		// returns the state for debug purposes
		return $.toJSON(this._state[root]);
	},

    getCallInfo: function(){
        var callList = 'Call trace\n==========\n';
        var callerFunc = arguments.callee.caller;
        var count = 0;
        do {
        var fn = callerFunc.toString();
        var callerFuncName = (fn.substring(fn.indexOf("function") + 8, fn.indexOf("("))).replace(/\s/g,'');

        if (callerFuncName === ''){
            callerFuncName = 'anon';
        }
        callList += count + ' => ' + callerFuncName + '\n';
        if (callerFunc.arguments && callerFunc.arguments.callee.caller !== callerFunc){
            callerFunc = callerFunc.arguments.callee.caller;
        } else {
            callerFunc = null;
        }
        count++;
        } while (count<10 && callerFunc);

        return callList;
    },


getStackTrace : function () {

var mode;
try {(0)();} catch (e) {
    mode = e.stack ? 'Firefox' : window.opera ? 'Opera' : 'Other';
}

switch (mode) {
    case 'Firefox' : return function () {
        try {(0)();} catch (e) {
            return e.stack.replace(/^.*?\n/,'').
                           replace(/(?:\n@:0)?\s+$/m,'').
                           replace(/^\(/gm,'{anonymous}(').
                           split("\n");
        }
    };

    case 'Opera' : return function () {
        try {(0)();} catch (e) {
            var lines = e.message.split("\n"),
                ANON = '{anonymous}',
                lineRE = /Line\s+(\d+).*?in\s+(http\S+)(?:.*?in\s+function\s+(\S+))?/i,
                i,j,len;

            for (i=4,j=0,len=lines.length; i<len; i+=2) {
                if (lineRE.test(lines[i])) {
                    lines[j++] = (RegExp.$3 ?
                        RegExp.$3 + '()@' + RegExp.$2 + RegExp.$1 :
                        ANON + RegExp.$2 + ':' + RegExp.$1) +
                        ' -- ' + lines[i+1].replace(/^\s+/,'');
                }
            }

            lines.splice(j,lines.length-j);
            return lines;
        }
    };

    default : return function () {
        var curr  = arguments.callee.caller,
            FUNC  = 'function', ANON = "{anonymous}",
            fnRE  = /function\s*([\w\-$]+)?\s*\(/i,
            stack = [],j=0,
            fn,args,i;

        while (curr) {
            fn    = fnRE.test(curr.toString()) ? RegExp.$1 || ANON : ANON;
            args  = stack.slice.call(curr.arguments);
            i     = args.length;

            while (i--) {
                switch (typeof args[i]) {
                    case 'string'  : args[i] = '"'+args[i].replace(/"/g,'\\"')+'"'; break;
                    case 'function': args[i] = FUNC; break;
                }
            }

            stack[j++] = fn + '(' + args.join() + ')';
            curr = curr.caller;
        }

        return stack;
    };
}
}
};
