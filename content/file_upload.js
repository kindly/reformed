
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

    jQuery form plugin

*/




(function($) {
	
$.fn.extend({

	file_upload: function(){
		$.FileUpload(this);
	}
});

$.FileUpload = function (input){

    function create_uid(length){
        // generate a unique id
        var chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890";
        var out = '';
        for (var i = 0; i < length; i ++){
            out += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return out;

    }

    function nice_time(time){
        time = Math.floor(time);
        console_log(time);
        if (time < 60){
            return String(Math.floor(time)) + 's ';
        }
        if (time < 3600){
            return String(Math.floor(time / 60)) + 'm ' + nice_time(time - (Math.floor(time / 60) * 60));
        }
        return String(Math.floor(time / (3600))) + 'h ' + nice_time(time - (Math.floor(time / 3600) * 3600));
    }

    function process_return(return_data, data){
        if (return_data.completed == false){
            var bytes_left = return_data.bytes_left;
            var bytes = return_data.bytes;
            var now = new Date().getTime();
            var time = (now - data.start) / 1000;
            var percent = 1 - bytes_left/bytes;
            var remaining;
            if (bytes_left == 0){
                remaining = 'unknown';
            } else {
                remaining = nice_time((time/percent) - time + 1);
            }
            time = nice_time(time);
            percent = Math.floor(percent * 1000)/10;
            var time_info = time + ', ' + remaining + ' remaining';
            data.$info.text(percent + '% ' + time_info);
            var timer = setTimeout(function() {update_status(data)}, 1000);
        } else {
            data.$info.text('completed');
            data.$form.remove();
            data.$iframe.remove();
        }
    }

    function update_status(data){

		$.ajax({ url : "/uploadstatus?~" + data.uid , dataType : 'json', success : function(return_data){
			 process_return(return_data, data);
		}});
    }

    function file_changed(){
        var uid = create_uid(30);
        var $input = $(input);
        var $info = $('<div>hello</div>');
        $info.insertAfter($input);
        var $iframe = $('<iframe name="fileuploader_' + uid + '"></iframe>');
        $('body').append($iframe);
        var $form = $('<form action="/upload?~' + uid + '" method="POST" enctype="multipart/form-data" target="fileuploader_' + uid + '"></form>');
        $input.attr('name', uid);
        $input.detach();
        $form.append($input);
        $('body').append($form);
        $form.submit();

        var start = new Date().getTime();
        var data = { uid : uid, $info : $info, $form : $form, $iframe : $iframe, start : start};
        // delay the status update so that the file is registered on the server
        var timer = setTimeout(function() {update_status(data)}, 1000);
    }

    $(input).change(file_changed);

};
})(jQuery);
