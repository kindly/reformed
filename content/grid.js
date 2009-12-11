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

    JQuery grid resize plugin

*/


(function($) {
	
$.fn.extend({
	grid: function() {
		
		return this.filter('table').each(function() {
			new $.Grid(this);
		});
	}
});

$.Grid = function(input){

    var headers = $(input).find('th');
    for (i = 1; i < headers.size(); i++){
        // put the contents in a div so that it can slid under the resizer
        // and add the resizer
        // ignore the first column
        headers.eq(i).wrapInner('<div></div>').append(new $.Grid.Resizer(i));
        // set the width of the heading div to stop the resizer being knocked to the next line
        w = headers.eq(i).width();
        headers.eq(i).find('div').eq(0).width(w - $.Grid.RESIZE_SPACE).css('float','left');
    }
};

$.Grid.MIN_COLUMN_SIZE = 25;
$.Grid.RESIZE_SPACE = 15;

$.Grid.Resizer = function(col){
    

    function start(){
        // begin resizing
        drag = true;
        $(document).mousemove(move).mouseup(end);
        return false;
    }

    function end(){
        // end resizing
        drag = false;
        $(document).unbind('mousemove', move); 
        $(document).unbind('mouseup', end); 
        return false;
    }

    function move(e){
        // resize
        if (drag){
            th = control.parent();
            var old_width = th.outerWidth();
            var new_width = Math.floor(e.clientX - th.offset().left + 10);
            if (new_width < $.Grid.MIN_COLUMN_SIZE){
                new_width = $.Grid.MIN_COLUMN_SIZE;
            }

            // store the current table widths
            var widths = [];
            var cols = th.parent().find('th');
            for (var i = 0; i < cols.size(); i++){
                if (i != col){
                    widths[i] = cols.eq(i).width();
                }
            }

            // set our changed column width
            widths[col] = new_width;

            // resize table
            var table = th.parent('table');
            var table_width = table.width() + (new_width - old_width);
            table.width(table_width);

            // restore column widths
            for (i = 0; i < cols.size(); i++){
                    cols.eq(i).width(widths[i]);
                    cols.eq(i).find('div').eq(0).width(widths[i]-$.Grid.RESIZE_SPACE);
            }
        }
        return false;
    }

    var drag = false;

    var control = $("<div class='resizer'></div>").mousedown(start);
    return control;
};

})(jQuery);
