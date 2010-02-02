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

    reformed.js
    ======

    A place for lost stuff at the moment but it will eventually hold the
    core functionality eg initialisation

    $REFORMED

    Public Functions
    ================

*/

// this calls init() onload
$(init);

function init(){

    $.address.change(page_load);
}

function page(){
    var request = {type:'page'};
    var data = {root: 'main'};
    $JOB.add(request, data, 'page', true);
}

function get_html(root, file){
    var request = {type:'page', file:file};
    var data = {root:root};
    $JOB.add(request, data, 'html', true);
}


// FIXME this is repeated and should be removed to the actions stuff in layout
var action_hash = {
    //previous: [['previous', 'go-previous.png', 'X', 'record'],[$FORM, $FORM._move, ['main#','prev']]],
    //next: [['next', 'go-next.png', 'Y', 'record'],[$FORM, $FORM._move, ['main#','next']]],
//    new: [['new', 'document-new.png', 'B', 'record'],[$FORM, $FORM._new, ['main']]],
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    'delete':[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, node_load, ['n:test.HomePage:']]]
//    donkey: [['donkey', 'go-home.png', 'I', 'general'],[$FORM, $FORM.request, ['donkey', 'main', 'first']]]
};


function action_call(action_name){
    // this function fires the event for action button clicks
    // we get the base object, function to call and the args from the
    // array action_hash
    var cmd_info = action_hash[action_name][1];
    cmd_info[1].apply(cmd_info[0], cmd_info[2]);
}


var status_message = '';
function msg(arg){
    status_message = arg + ' - ' + status_message;
    $('#status').html(status_message);
}

