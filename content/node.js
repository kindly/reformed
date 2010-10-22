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

    node.js
    ======

*/

// JSLint directives
/*global document window */
/*global $ REBASE console_log */



var node_load;


function search_box(){
    var node = 'test.Search?q=' + $('#search').val();
    node_load(node);
    return false;
}

/*
 *           ('>
 *           /))@@@@@.
 *          /@"@@@@@()@
 *         .@@()@@()@@@@    INITIALISATIONS
 *         @@@O@@@@()@@@
 *         @()@@\@@@()@@    Code to initialise stuff.
 *          @()@||@@@@@'
 *           '@@||@@@'
 *        jgs   ||
 *       ^^^^^^^^^^^^^^^^^
 */

function init(){
    // turn off any jquery animations
    $.fx.off = CONFIG.DISABLE_FX;
    // build the user interface
    REBASE.Interface.init();
    /* helper function */
    node_load = REBASE.Node.load_node;

    $.address.change(REBASE.Node.load_page);
    // if no node info is available go to the login node
    // FIXME this needs fixing with a default node
    // also if you are auto logged in etc
    var url = $.address.value();
    if (url == '/'){
        node_load('user.User:login');
    }
}

$(document).ready(init);
