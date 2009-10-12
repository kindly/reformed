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
	
	job.js
	======
	
	Sends and processes jobs and does ajax calls

	$JOB

	Public Functions
	================
	
	add (request, data, type, fetch)
		adds a job to the list	
		request:	(obj) this will be sent to the server
		data:		(obj) this is retained to proces the returned job
		type:		(string) this is the job type ('form', 'data', etc)
		fetch:		(bool) should an ajax call be made?

	addJobFunction (type, fn)
		add a function for processing returned jobs
		type:	(string) the job type that is processed
		fn:		(function) the function to do the processing
					function(data){...} where data is sent with job request
					
	addPacketFunction (type, fn)
		add a function for processing returned packets
		type:	(string) the packet type that is processed
		fn:		(function) the function do the processing
					function(packet, job){...} 
					where job is sent with job request
					packet is the returned packet
			
*/

window.$JOB = {

	
	// PUBLIC
	
	add: function(request, data, type, fetch){
		// adds a new job to the job queue
		this._queue.push({'job_number': this._number, 'data': data});
		if (fetch){
			this._ajax(request, this._number, type);
		} else {
			this._data[this._number] = {type:null};
		}
		this._number++;
		// start waiting for a responce
		this._timer_on();
	},
	
	addJobFunction: function(type, fn){
		// adds job processing functions
		if (typeof(this._job_functions[type]) != 'undefined'){
			alert("job function type '" + type + "' already registered");
		} else {
			this._job_functions[type] = fn;
		} 
	
	},

	addPacketFunction: function(type, fn){
		// adds packet processing functions
		if (typeof(this._packet_functions[type]) != 'undefined'){
			alert("packet function type '" + type + "' already registered");
		} else {
			this._packet_functions[type] = fn;
		} 
	
	},
	
	// PRIVATE

	_queue: [],  // these are where the jobs are placed
	_data: {},   // this is where the return data (from ajax) or preset
			 // is placed
			 // when it has a value for a job then that job can be processed
	_number: 0,	// the job number (each job needs a uniqjue one) - 
			// this wants to be thread safe but isn't yet
	_timeout: null,   // the timeout lives here
	_process_wait_time: 50, // how long between job
	
	_timer_on: function (){
		// jslint does not like this line but we need it
		this._timeout = setTimeout("$JOB._process()", this._process_wait_time);
	},

	_timer_off: function(){
		// clear the timer
		if (this._timeout){
			clearTimeout(this._timeout);
			this._timeout = null;
		}
	},

	_process_return: function(data, job_number){
		// process ajax returned data
		// put the data into job_data
		this._data[job_number] = data;
	},

	_process: function(){
		// process any jobs in the queue that we have the data to process

		// do we have a pending job?
		var finalise_jobs = [];
		if (this._queue.length){
			var job_number = this._queue[0].job_number;
			// is it ready to complete
			while (this._queue[0] && this._data[this._queue[0].job_number]){
				var job = this._queue.shift();
				for (var i=0;i<this._data[job_number].length;i++){
					var packet = this._data[job_number][i];
					// get the function to process the packet
				  	if (typeof(this._packet_functions[packet.type]) != 'undefined'){
				  		this._packet_functions[packet.type](packet, job.data);
                        console.log(this)
				  	} else {
						var error = "unknown packet type: ";
						error += packet.type;
						alert(error);					  	
				  	}
			  	}
			  	// check if we have a job type process function
			  	if (typeof(this._job_functions[job.data.type]) != 'undefined'){
			  		this._job_functions[job.data.type](job.data);
			  	}
			}
		}
		// have we any outstanding jobs?
		if (this._queue.length){
			// set the job timer
			this._timer_on();
		} else {
			// stop the job timer
			this._timer_off();
		}
	},
	
	_job_functions: { 
		// DEFAULT job functions
		'function': function(data){
			obj = data.return_object;
			fn = data.return_function;
			params = data.return_params;
			fn.apply(obj, params);
		}

	},

	_packet_functions: {
		// DEFAULT packet handlers
  		 'page': function(packet, job){
  		 		var out = packet.data;
  		 		var root = job.root;
				$INFO.newState(root + '#', 'page');
  				$('#' + root).html(out);
  		/*		for (var i = 0; i < packet.items.length; i++){
  					var item = packet.items[i];
  					if (item.type == 'form'){
  						$FORM.request(item.form_id, item.root, item.command);
  					}
  				}*/
			},
					  		
		 'error': function(packet, job){
	  		//	var error_id = '#' + $INFO.getId(job.form_root) + '__error';
	  		//	$(error_id).html(packet.data['@main']);
				alert(packet.data['@main']);
			},
			
		'status': function(packet, job){}
	},

	_ajax: function(request, job_number, type){
		// this is where we make the ajax request
		var body = $.toJSON(request);
		$.post("/ajax", { head: type, body: body },
		  function(data){
			 $JOB._process_return(data, job_number);
		  }, "json");
	}

};

