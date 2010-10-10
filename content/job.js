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
	
	job.js
	======
	
	Sends and processes jobs and does ajax calls

	$JOB

	Public Functions
	================
	
	add (request, data, type, fetch)
		adds a job to the list	
		request:	(obj) this will be sent to the server
		data:		(obj) this is retained to process the returned job
		type:		(string) this is the job type ('form', 'data', etc)

*/



REBASE.Job = function(){

    var outstanding_requests = 0;

    function loading_show(){
        $('#ajax_info').show();
    }

    function loading_hide(){
        $('#ajax_info').hide();
    }

    function process_return(return_data, sent_data){
        var i;
        var n;
        outstanding_requests--;
        if (outstanding_requests === 0){
            loading_hide();
        }
        if (return_data !== null){
            for (i = 0, n = return_data.length; i < n; i++){
                REBASE.Node.process(return_data[i], sent_data);
            }
        } else {
            REBASE.Dialog.dialog('Application Error', 'No data was returned.\n\nThe application may not be running.');
        }
    }

	function add(request, sent_data){
		// this is where we make the ajax request
		var body = $.toJSON(request);
		$.post("/ajax", {body: body},
		  function(return_data){
			 process_return(return_data, sent_data);
		  }, "json");
        outstanding_requests++;
        loading_show();
	}

    return {
        'add' : function (request, data){
            add(request, data);
        }
    };
}();


