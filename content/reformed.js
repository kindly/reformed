


// this calls init() onload
$(init);

function init(){

	// FIXME the initialisations need to be automated.
	// each module can add itself to a list of modules to be initialised
//	$INFO._init();
//	$FORM._init();
//	$REFORMED.init();
	$REFORMED._checkModules();
//	$REFORMED._initModules();
//	$FORM.request('form_item', 'root', 'first');
	//$FORM.request('form', 'root', 'first');
	//$FORM.request('logon', 'root', '');
	//$FORM.request('Codes', 'root2', 'first');
page();
	$(window).keydown(function(event){
	//alert(event.keyCode);
});
	$('#main').dblclick(function(event) {
	if (event.target != "[object HTMLInputElement]" &&
	    event.target != "[object HTMLButtonElement]"){
  alert( this.id );
}
	})
}


function page(){
request = {type:'page'};
data = {};
$JOB.add(request, data, 'page', true);
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
	    key.code == 0 // special key 
	    || key.code == 8 // backspace
	    || key.code == 9 // TAB
	    || key.ctrl || key.alt // special?
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

	_module: ['FORM', 'FORM_CONTROL', 'JOB', 'INFO'],
	
	_module_loaded: [],
	
	_counter: 0,
	
	init: function(){
		//for (i=0; i < this._module.length; i++){
	//		this._loadModule(this._module[i]);
	//	}		
		this._loadModule(this._module[this._counter++]);
	},
	
	_initModules: function(){
		for (i=0; i < this._module.length; i++){
			this._initModule(this._module[i]);
		//	alert(this._module[i] + $('$' + this._module[i]))
		}	
//		alert('ready to roll');	
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
		//	alert(this._counter);
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
//		alert(count);
		if (count== this._module.length){
		
			this._initModules();
		} else {
			this._counter++;
			//var moo = setTimeout($REFORMED._checkModules(),250);
		}
	},
	
	_checkModule: function(module){
		var module = module.toUpperCase();
		if(window['$' + module]){
			return true;
		} else {
			alert('no find $' + module + '\n' + window['$' + module]);
			return false;
		}
	},
		
	_initModule: function(module){
		var module = module.toUpperCase();
	//	alert('init ' + module);
		if(window['$' + module] &&  window['$' + module]['_init']){
//			alert('init ' + module);
			window['$' + module]._init();
		}
	}
	
}






