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

// JSLint directives
/*global setTimeout window */
/*global $ REBASE console_log */

/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    JOB
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Send/receive ajax data calls.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */


REBASE.Job = function(){

    var outstanding_requests = 0;

    function loading_show(){
        $('#ajax_info').show();
    }

    function loading_hide(){
        $('#ajax_info').hide();
    }

    var status_timer;

    function job_processor_status(data, node, root){
        // display the message form if it exists
        if (data.form){
            $('#' + root).status_form();
        }
        // show info on form
        if (data.data){
            var $status_form = $('div.STATUS_FORM');
            if ($status_form.length){
                $status_form.data('command')('update', data.data);
            }
        }
        // set data refresh if job not finished
        if (!data.data || !data.data.end){
            var node_string = "/:" + node + ":_status:id=" + data.data.id;
            status_timer = setTimeout(function (){
                                          REBASE.Node.load_node(node_string);
                                      }, 1000);
        }
    }

    function process(packet, job){

        var message;

        if (packet.data === null){
            console_log("NULL DATA PACKET");
            return;
        }

        var root = 'main'; //FIXME

        var title = packet.data.title;
        if (title){
            $.address.title(title);
        }

        var sent_node_data = packet.data.node_data;
        if (sent_node_data){
            global_node_data = sent_node_data;
            global_current_node = packet.data.node;
            console_log('node data:', global_node_data);
        }

        var user = packet.data.user;
        if (user){
            REBASE.User.update(user);
        }

        var bookmark = packet.data.bookmark;
        if (bookmark){
           REBASE.Bookmark.process(bookmark);
        }

        var data;
        switch (packet.data.action){
            case 'redirect':
                var link = packet.data.link;
                if (link){
                    switch (link){
                        case 'BACK':
                            window.history.back();
                            break;
                        case 'CLOSE':
                            REBASE.Dialog.close();
                            break;
                        case 'RELOAD':
                            REBASE.Dialog.close();
                            REBASE.Node.load_node($.address.value());
                            break;
                        default:
                            REBASE.Node.load_node('u:' + link);
                            break;
                    }
                }
                break;
            case 'html':
                $('#' + root).html(packet.data.data.html);
                break;
            case 'page':
                //alert($.toJSON(packet.data.data));
                $('#' + root).html(page_build(packet.data.data));
                break;
            case 'form':
            case 'dialog':
                 REBASE.Layout.update_layout(packet.data);
                 break;
            case 'function':
                console_log('data', packet.data['function']);
                REBASE.Functions.call(packet.data['function'], packet.data.data);
                break;
            case 'save_error':
                data = packet.data.data;
                // clear form items with no errors
                break;
            case 'save':
                data = packet.data.data;
                if (job && job.obj){
                    // copy the obj_data that was saved with the job
                    data.obj_data = job.obj_data;
                    job.obj.data('command')('save_return', data);
                } else {
                    alert("we have not sent the object");
                }
                break;
            case 'delete':
                data = packet.data.data;
                if (data.deleted){
                    form_process_deleted(data.deleted);
                }
                break;
            case 'general_error':
                message = packet.data.data;
                REBASE.Dialog.dialog('Error', message);
                break;
            case 'message':
                message = packet.data.data;
                REBASE.Dialog.dialog('Message', message);
                break;
            case 'forbidden':
                message = 'You do not have the permissions to perform this action.';
                REBASE.Dialog.dialog('Forbidden', message);
                break;
            case 'status':
                job_processor_status(packet.data.data, packet.data.node, root);
                break;
            default:
                REBASE.Dialog.dialog('Error', 'Action `' + packet.data.action + '` not recognised');
                break;
        }
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
                process(return_data[i], sent_data);
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


