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
	
	
	getState: function(root, item){

		if (root && this._state[root] && 
		typeof(this._state[root][item]) != 'undefined'){
			return this._state[root][item];
		} else {
		//	alert('getState:\nnot found\n' + root + ' : ' + item);
			return false;
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
	}

};


