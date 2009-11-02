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
    create_actions();
    // FIXME the initialisations need to be automated.
    // each module can add itself to a list of modules to be initialised
//    $INFO._init();
//    $FORM._init();
//    $REFORMED.init();
    $REFORMED._checkModules();
//    $REFORMED._initModules();
//    $FORM.request('form_item', 'root', 'first');
    //$FORM.request('form', 'root', 'first');
    //$FORM.request('logon', 'root', '');
    //$FORM.request('Codes', 'root2', 'first');
//page();
    $(window).keydown(function(event){
    //alert(event.keyCode);
});
    // application layout on window load/resize
    $(document).ready($REFORMED.layout);
    $(window).resize($REFORMED.layout);

    $('#main').dblclick(function(event) {
        form_dblclick(event);
    });
    
    // preload the donkey form
//    $FORM.request('donkey', 'main', 'first');
    $.address.change(page_load);
}

form_active = true;

function form_dblclick(event){

    if (event.target != "[object HTMLInputElement]" &&
      event.target != "[object HTMLButtonElement]"){
        form_mode();
    }
}
function form_mode(){

    if(!form_active){
        $('#main').find('.form,.subform,tr').addClass('active').removeClass('inactive');
        $('#main').find('input,select').removeAttr("disabled");
        form_active = true;
    } else {
        $('#main').find('.form,.subform,tr').removeClass('active').addClass('inactive');
        $('#main').find('input,select').attr("disabled", "disabled");
        form_active = false;
    }

}




function page(){
request = {type:'page'};
data = {root: 'main'};
$JOB.add(request, data, 'page', true);
//$FORM.request('form_item', 'moo', 'first');
}

function get_html(root, file){
request = {type:'page', file:file};
data = {root:root};
$JOB.add(request, data, 'html', true);
//$FORM.request('form_item', 'moo', 'first');
}



// UTILS

// THESE ARE FROM formcontrol.js

function isDate(sDate) {
    // THIS DATE VALIDATION SUCKS :(
    var scratch = new Date(sDate);
    if (scratch.toString() == "NaN" || scratch.toString() == "Invalid Date") {
        return false;
    } else {
        return true;
    }
}

function allowedKeys(key){

    // this returns true for allowed key presses
    // eg arrows cut/paste tab...

    if (
        key.code === 0 || // special key 
        key.code == 8 || // backspace
        key.code == 9 || // TAB
        key.ctrl || key.alt // special?
       ){
        return true;
    } else {
        return false;
    }
}

function getItemFromObj(obj){

    // for composite controls finds the root object and extension
    var item = {};
    if (obj.id){
        var m = String(obj.id).match(/^(.*)(__(([a-zA-Z0-9]\w?)+))$/);
        item.id = obj.id;
        if (m){
            item.root = m[1];
            item.ext = m[4];
        }
    }
    return item;
}

function getKeyPress(event){

    // returns the key info for an event
    var key = {'code' : 0}; // default key
    if(window.event){
        //IE
          key.code = event.keyCode;
      } else if(event.which){
         // Netscape/Firefox/Opera
        key.code = event.which;
      }
    key.ctrl = (event.ctrlKey);
    key.alt = (event.altKey);
    key.shift = (event.shiftKey);

    return key;
}

function makeUTC(date){

    return date.getUTCFullYear() + '-' + (date.getUTCMonth() + 1) + '-' + date.getUTCDate();
}

function UTC2Date(UTC){

// actually get this to work ;)
    if (!UTC){
        return "";
    } else {
        var m = UTC.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
        if (m){
            var date = new Date(m[1],m[2]-1,m[3]);
            return date.toLocaleDateString();
        }
    }
}

// END UTILS




var $REFORMED = {

    // Constants for application layout
    SIDE_WIDTH : 150,
    LOGO_HEIGHT : 100,
    ACTION_HEIGHT : 100,
    INFO_HEIGHT : 30,
    STATUS_HEIGHT : 80,
    MIN_APP_WIDTH : 800,
    MAX_APP_WIDTH : 1000,
    ACTION_PAD : 2,
    INFO_PAD : 3,
    MAIN_PAD : 5,
    STATUS_PAD : 3,
    SIDEBAR_PAD : 4,
    LOGO_PAD : 3,
    WORKSPACE_PAD : 4,
    LEFT_PAD : 2,
    BOTTOM_PAD : 2,
    RIGHT_PAD : 2,

    _initialisation_list: [],
/*    
    registerInitFunction: function(initialtion_function){
        alert (typeof(initialtion_function));
        if (typeof(initialtion_function) != 'undefined'){
            this._initialisation_list.push(initialtion_function)
        }
    },
    
    _initialiseModules: function(){
    alert ('moo');
        for (i=0; i < this._initialisation_list.length; i++){
            this._initialisation_list[i]();
        }
    },
    
    
*/    

    _module: [ 'FORM_CONTROL', 'JOB', 'INFO'],
    
    _module_loaded: [],
    
    _counter: 0,
    
    init: function(){
        //for (i=0; i < this._module.length; i++){
    //        this._loadModule(this._module[i]);
    //    }        
        this._loadModule(this._module[this._counter++]);
    },
    
    _initModules: function(){
        for (i=0; i < this._module.length; i++){
            this._initModule(this._module[i]);
        //    alert(this._module[i] + $('$' + this._module[i]))
        }    
//        alert('ready to roll');    
    },
    
    _loadModule: function(module){
        $.getScript(module.toLowerCase() + '.js',
                    $REFORMED._scriptLoaded(module));
    },
    
    _scriptLoaded: function(module){
        this._module_loaded.push(module);
        if (this._counter<this._module.length){
            this._loadModule(this._module[this._counter++]);
        } else {
            this._checkModuleLoad();
        //    alert(this._counter);
        }
    },
    
    _checkModuleLoad: function(){
        var number_modules = this._module.length;
        var number_loaded = this._module_loaded.length;
        if (number_modules == number_loaded){
            var moo = setTimeout($REFORMED._checkModules(),250);
        }    
    },
    
    _checkModules: function(){
        var count = 0;
        for (i=0; i < this._module.length; i++){
            if (this._checkModule(this._module[i])){
                
                count++;
            }
            
        }
//        alert(count);
        if (count== this._module.length){
        
            this._initModules();
        } else {
            this._counter++;
            //var moo = setTimeout($REFORMED._checkModules(),250);
        }
    },
    
    _checkModule: function(module){
        module = module.toUpperCase();
        if(window['$' + module]){
            return true;
        } else {
            alert('no find $' + module + '\n' + window['$' + module]);
            return false;
        }
    },
        
    _initModule: function(module){
        module = module.toUpperCase();
    //    alert('init ' + module);
        if(window['$' + module] &&  window['$' + module]._init){
//            alert('init ' + module);
            window['$' + module]._init();
        }
    },
    
    layout: function(){

        var r = $REFORMED;
        
        var app_width = $(window).width();
        var app_height = $(window).height();

        var workspace_start = r.LEFT_PAD + r.SIDE_WIDTH + r.WORKSPACE_PAD;
        var workspace_width = app_width - workspace_start - r.RIGHT_PAD;
        var resize = false;
        if (workspace_width + workspace_start + r.RIGHT_PAD > r.MAX_APP_WIDTH){
            workspace_width = r.MAX_APP_WIDTH - workspace_start - r.RIGHT_PAD;
            left_margin = (app_width - workspace_width - workspace_start)/2;
            workspace_start = left_margin + r.SIDE_WIDTH + r.WORKSPACE_PAD;
        } else {
            left_margin = r.LEFT_PAD;
            if (workspace_width + workspace_start + r.RIGHT_PAD < r.MIN_APP_WIDTH){
                workspace_width = r.MIN_APP_WIDTH - workspace_start - r.RIGHT_PAD;
                resize = true;
            }
        }
    

    
        r.layout_set('logo',
               left_margin,
               r.LOGO_PAD,
               r.LOGO_HEIGHT,
               r.SIDE_WIDTH);

        var used_height = r.LOGO_PAD + r.LOGO_HEIGHT + r.SIDEBAR_PAD;
        r.layout_set('sidebar',
               left_margin,
               used_height,
               app_height - used_height - r.BOTTOM_PAD,
               r.SIDE_WIDTH);

        r.layout_set('action',
               workspace_start,
               r.ACTION_PAD,
               r.ACTION_HEIGHT,
               workspace_width);

        used_height = r.ACTION_PAD + r.ACTION_HEIGHT + r.INFO_PAD;
        r.layout_set('info',
               workspace_start,
               used_height,
               r.INFO_HEIGHT,
               workspace_width);

        var main_height = app_height - used_height - r.INFO_HEIGHT - 
                    r.MAIN_PAD - r.STATUS_HEIGHT - r.STATUS_PAD - r.BOTTOM_PAD;
        used_height += r.INFO_HEIGHT + r.MAIN_PAD;
        r.layout_set('main',
               workspace_start,
               used_height,
               main_height,
               workspace_width);

        used_height += main_height + r.STATUS_PAD;
        r.layout_set('status',
               workspace_start,
               used_height,
               r.STATUS_HEIGHT,
               workspace_width);

        if (resize){
            if ($('body').css('overflow') != 'auto'){
                $('body').css('overflow','auto');
                r.layout();
            }
        } else {
            if ($('body').css('overflow') != 'hidden'){
                $('body').css('overflow','hidden');
                r.layout();
            }
        }

        position_actions();
        
    },

    layout_set: function(id, top_, left, height, width){

        // determine the amount of 'space' around the item
        top_offset = 0;
        bottom_offset = 0;
        left_offset = 0;
        right_offset = 0;

    //    top_offset += parseInt($('#' + id).css('padding-top'), 10);
    //    bottom_offset += parseInt($('#' + id).css('padding-bottom'), 10); 
        top_offset += parseInt($('#' + id).css('border-top-width'), 10);
        bottom_offset += parseInt($('#' + id).css('border-bottom-width'), 10); 
        top_offset += parseInt($('#' + id).css('margin-top'), 10);
        bottom_offset += parseInt($('#' + id).css('margin-bottom'), 10); 

    //    left_offset += parseInt($('#' + id).css('padding-left'), 10);
    //    right_offset += parseInt($('#' + id).css('padding-right'), 10); 
        left_offset += parseInt($('#' + id).css('border-left-width'), 10);
        right_offset += parseInt($('#' + id).css('border-right-width'), 10); 
        left_offset += parseInt($('#' + id).css('margin-left'), 10);
        right_offset += parseInt($('#' + id).css('margin-right'), 10); 

        // adjust the height, width, top and left
        height = height - top_offset - bottom_offset;
        width = width - left_offset - right_offset;
    //    left += left_offset;
    //    top_ += top_offset;

        css = { 'top' : String(left) + 'px',
            'left' : String(top_) + 'px',
            'height' : String(height) + 'px',
            'width' : String(width) + 'px',
            'position' : 'absolute' };
        $('#' + id).css(css);
    }
    
};
NUM_ACTION_BUTTONS = 20;
NUM_ACTION_ROWS = 4;

function create_actions(){

    var html = '';
    for (var i = 0; i < NUM_ACTION_BUTTONS; i++){
        html += '<div id="action' + i + '" class="action"><a href="javascript:action_call(' + i + ')"><img src="icon/22x22/go-home.png" /><span class="command">moo ' + i + '</span><span class="shortcut">A</span></a></div>';
    }
    $('#action').html(html);
}

function position_actions(){
    var action_m_width = $('#action').width();
    var action_m_height = $('#action').height();

    var cols = Math.ceil(NUM_ACTION_BUTTONS / NUM_ACTION_ROWS);
    var action_width = parseInt(action_m_width/cols, 10);
    var action_height = parseInt(action_m_height/NUM_ACTION_ROWS, 10);

    for (var i = 0; i < NUM_ACTION_BUTTONS; i++){
        var y = action_height * (i % NUM_ACTION_ROWS);
        var x = action_width * (Math.floor(i/NUM_ACTION_ROWS));
        $REFORMED.layout_set('action' + i, x, y, action_height, action_width);
        action_a_width = $('#action' + i).width();
        action_a_height = $('#action' + i).height();
        $REFORMED.layout_set('action' + i + '>a>img', 0, 0,action_a_height, 22);
        $REFORMED.layout_set('action' + i + '>a>.shortcut', action_a_width -22, 0, action_a_height, 22);
        $REFORMED.layout_set('action' + i + '>a>.command', 22, 0, action_a_height, action_a_width - 22 * 2);
        $REFORMED.layout_set('action' + i + '>a', 0, 0, action_a_height, action_a_width);
    }
    action_change();

}

function action_set(action_id, action_info){
    var command = action_info[0];
    var img = action_info[1];
    var shortcut = action_info[2];
    var type = action_info[3];
    $('#action' + action_id + '>a>.command').text(command);
    $('#action' + action_id + '>a>.shortcut').text(shortcut);
    $('#action' + action_id + '>a>img').attr('src', 'icon/22x22/' + img);
    $('#action' + action_id + '>a').attr('accesskey', shortcut);
    $('#action' + action_id + '>a').attr('class', type);
}

function action_hide(action_id){
    $('#action' + action_id + '').addClass('action_hidden');
    $('#action' + action_id + '>a').attr('accesskey', '');
}

action_hash = {
    //previous: [['previous', 'go-previous.png', 'X', 'record'],[$FORM, $FORM._move, ['main#','prev']]],
    //next: [['next', 'go-next.png', 'Y', 'record'],[$FORM, $FORM._move, ['main#','next']]],
//    new: [['new', 'document-new.png', 'B', 'record'],[$FORM, $FORM._new, ['main']]],
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    delete:[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, get_html, ['main', 'frontpage']]]
//    donkey: [['donkey', 'go-home.png', 'I', 'general'],[$FORM, $FORM.request, ['donkey', 'main', 'first']]]
};

action_list = ['home',  'save', null, 'delete']; 

function action_change(){
    for (var i=0; i<action_list.length; i++){
        if(action_list[i]){ 
            action_set(i, action_hash[action_list[i]][0]);
        } else {
            action_hide(i);
        }
    }
    for ( ; i<NUM_ACTION_BUTTONS; i++){
        action_hide(i);
    }
}

function action_call(action_id){
    // this function fires the event for action button clicks
    // we get the base object, function to call and the args from the 
    // array action_hash
    var cmd_info = action_hash[action_list[action_id]][1];
    cmd_info[1].apply(cmd_info[0], cmd_info[2]);
}


status_message = '';
function msg(arg){
    status_message = arg + ' - ' + status_message;
    $('#status').html(status_message);
}
