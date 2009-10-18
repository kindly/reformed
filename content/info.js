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
	
	getForm (form_id) returns (object)
		gets the structure of a form		
		form_id:	(string) id of the form
	
	existsForm (form_id) returns (bool)
		checks if we know about this form		
		form_id:	(string) id of the form
		
	getData (obj, data_id) returns (object)
		gets data for object for the data_id record		
		obj:		(string) the object name (form_id)
		data_id:	(int) the record we want

	getRecords (obj, link_id) returns (array of int)
		gets records for object for the link_id
		returns an array of data_ids		
		obj:		(string) the object name (form_id)
		data_id:	(int) the record we want

	getRowcount: function(obj, data_id) //FIXME document
	
	
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

	_form: {},
	_data: {},
	_records: {}, 
	_id: {},
	_id_counter: 0,
	_reverse_id: [],
	_state: {}, 

	getForm: function(form_id){

		//this needs to dome some clever stuff 
		//to ensure that we have the proper (latest) versions of forms
		//talk to the webserver.
		if (typeof(this._form[form_id]) != 'undefined'){
			return this._form[form_id];
		} else {
			alert('form ' + form_id + ' does not exist!!!');
		}
	},

	existsForm: function (form_id){
		if (typeof(this._form[form_id]) != 'undefined' &&
		this._form[form_id].layout){
			return true;
		} else {
			return false;
		}			
	},

	_addForm: function(form_id, data){

		// set the form info
		this._form[form_id] = {};
		this._form[form_id].layout = data;
		this._form[form_id].html = null;
		this._form[form_id].subform = {};
		this._form[form_id].info = {top_level: true, name: form_id};
	},
	
	getData: function(data_obj, data_id){

		//this needs to dome some clever stuff 
		//to ensure that we have the proper (latest) data
		//talk to the webserver.
		if (typeof(this._data[data_obj]) != 'undefined' && 
		typeof(this._data[data_obj][data_id]) != 'undefined'){
			return this._data[data_obj][data_id];
		} else {
			return null;
		}
	},

	existsData: function(data_obj, data_id){

		//this needs to dome some clever stuff 
		//to ensure that we have the proper (latest) data
		//talk to the webserver.
		if (typeof(this._data[data_obj]) != 'undefined' && 
		typeof(this._data[data_obj][data_id]) != 'undefined'){
			return true;
		} else {
			return false;
		}
	},

	_addData: function(data_obj, data_id, data){

		// do we have the object already? if not create it
		if (typeof(this._data[data_obj]) == 'undefined'){
			this._data[data_obj] = {};
		}
		// set the value
		this._data[data_obj][data_id] = data;	},
	
	getRecords: function(obj, data_id){

		//this needs to do some clever stuff 
		//to ensure that we have the proper (latest) data
		//talk to the webserver. hacked for records
		if (data_id === 0){
			return null;
		}
		if (typeof(this._records[obj]) != 'undefined' &&
		typeof(this._records[obj][data_id]) != 'undefined'){
			return this._records[obj][data_id].records;
		}
	},

	getRowcount: function(obj, data_id){

		//this needs to do some clever stuff 
		//to ensure that we have the proper (latest) data
		//talk to the webserver. hacked for records
		if (data_id === 0){
			return null;
		}
		if (typeof(this._records[obj]) != 'undefined' &&
		typeof(this._records[obj][data_id]) != 'undefined'){
			return this._records[obj][data_id].rowcount;
		}
	},
	
	_addRecord: function(obj, parent_id, records, rowcount){

		// do we have the object already? if not create it
		if (typeof(this._records[obj]) == 'undefined'){
			this._records[obj] = {};
		}
		// set the value
		data = {'records':records, 'rowcount':rowcount};
		this._records[obj][parent_id] = data;

	},
	

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
	},
	
	_init: function(){
		// does any initialisation such as loading job processing functions
		// this is to ensure that all other modules are loaded
		
		// PACKET FUNCTIONS
		
		// form packet function
  		fn = function(packet, job){
  			var my_data = packet.data;
  			$INFO._addForm(packet.id, my_data);
  		};
		$JOB.addPacketFunction('form', fn);
		
		// data packet function
  		fn = function(packet, job){
			var record;
			var obj = packet.object;
			var data_id;
		//	var records = packet.records;
		//	var data_id = packet.data_id;
		//	var rowcount = packet.rowcount;
		//	$INFO._addRecord(obj, data_id, records, rowcount);
			// store the returned recordID for the initial packet
		//	job.data_id = data_id;
		//	for (var j = packet.data.length; j>0; j--){
		//		record = packet.data[j-1];
				for (data_id in packet.data){
					$INFO._addData(obj,data_id, packet.data[data_id]);
				}
		//	}
  		};
		$JOB.addPacketFunction('data', fn);
	
	}
};


