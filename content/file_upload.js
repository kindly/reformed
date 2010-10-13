
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

// JSLint directives
/*global $ jQuery setTimeout */


(function($) {
	
$.fn.extend({

	file_upload: function(data){
		$.FileUpload(this, data);
	}
});


$.FileUpload = function (input, data){

    var type = 'normal';
    var size = '.m';
    var value = data.value;
    var $input = $(input);
    var $input_parent = $input.parent();

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
        if (time < 60){
            return String(Math.floor(time)) + 's ';
        }
        if (time < 3600){
            return String(Math.floor(time / 60)) + 'm ' + nice_time(time - (Math.floor(time / 60) * 60));
        }
        return String(Math.floor(time / (3600))) + 'h ' + nice_time(time - (Math.floor(time / 3600) * 3600));
    }

    function process_return(return_data, data){
        if (return_data.completed === false){
            var bytes_left = return_data.bytes_left;
            var bytes = return_data.bytes;
            var now = new Date().getTime();
            var time = (now - data.start) / 1000;
            var percent = 1 - bytes_left/bytes;
            var remaining;
            if (bytes_left === 0){
                remaining = 'unknown';
            } else {
                remaining = nice_time((time/percent) - time + 1);
            }
            time = nice_time(time);
            percent = Math.floor(percent * 1000)/10;
            var time_info = time + ', ' + remaining + ' remaining';
            data.$info.text(percent + '% ' + time_info);
            var timer = setTimeout(function() {update_status(data);}, 1000);
        } else {
            if (return_data.error !== ''){
                data.$info.text('ERROR: ' + return_data.error);
            } else {
                if (type == 'image' && return_data.id){
                    data.$info.remove();
                    $input_parent.css('background', 'url("/attach?' + return_data.id + size + '") center center no-repeat');
                } else {
                    data.$info.text('completed');
                }
                // store value
                var value = return_data.id;
            }
            $input = $('<input class="img_uploader" type="file" />').change(file_changed);
            $input.data('value', value);
            $input_parent.append($input);
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
        var $input_copy = $input;
        var $iframe = $('<iframe name="fileuploader_' + uid + '"></iframe>');
        $('body').append($iframe);
        var $form = $('<form action="/upload?~' + uid + '" method="POST" enctype="multipart/form-data" target="fileuploader_' + uid + '"></form>');
        $input_copy.attr('name', uid);
        $input_copy.detach();
        $form.append($input_copy);
        $('body').append($form);
        $form.submit();
        $input_parent.empty();
        var $info = $('<div>uploading</div>');
        $input_parent.append($info);

        var start = new Date().getTime();
        var data = { uid : uid, $info : $info, $form : $form, $iframe : $iframe, start : start};
        // delay the status update so that the file is registered on the server
        var timer = setTimeout(function() {update_status(data);}, 1000);
    }




    function init(){
        if (data && data.type){
            type = data.type;
        }

        if (data && data.size){
            size = '.' + data.size;
        }

        if (type == 'image'){
            if (value){
                $input_parent.css('background', 'url("/attach?' + value + size +'") center center no-repeat');
            } else {
                var $info = $('<div>click to add</div>');
                $info.insertBefore($input);
            }
        }
        $input.change(file_changed);
        $input.data('value', value);
    }

    init();
};
})(jQuery);
