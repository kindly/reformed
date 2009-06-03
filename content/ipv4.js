// this is a crude IP address control made of 4 boxes
// it needs some more work on large numbers and 001 . in pastes etc
// this is a demo complex control


$FORM_CONTROL['ipv4'] = function(item, id){

	var x = this.label(item, id);
	for (var i=1; i<5; i++){
		x += '<input id="' + id + '__' + i + '" size="3" type="text" onchange="$FORM_CONTROL.ipv4_change(this)" onkeypress="return $FORM_CONTROL.ipv4_keydown(this, event)" onkeyup="$FORM_CONTROL.ipv4_change(this)" />';
		if (i<4){
			x += '.';
		}
	}
	x += '<input id="' + id + '" type="text" class="hidden" />';
	return x;
};

$FORM_CONTROL['ipv4_set'] = function(id, val){

	var m = val.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
	if (m){
		$("#" + id + "__1").val(m[1]);
		$("#" + id + "__2").val(m[2]);
		$("#" + id + "__3").val(m[3]);
		$("#" + id + "__4").val(m[4]);
		$("#" + id).val(val);
	} else {
		$("#" + id + "__1").val('');
		$("#" + id + "__2").val('');
		$("#" + id + "__3").val('');
		$("#" + id + "__4").val('');
		$("#" + id).val('');
	}
};

$FORM_CONTROL['ipv4_change'] = function(obj){

	var item = getItemFromObj(obj);
	var val = $(obj).val();

	// check if a real IP address has been pasted
	var m = val.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
	if (m){
		var valid = true; 
		for (var i=1; i<5 ;i++){
			if (m[i]<0 || m[i]>255){
				valid = false;
				break;
			}
		}
		if (valid){
			$FORM_CONTROL.ipv4_set(item.root, val);
		} else {
			$(obj).val(m[1]);
		}
	}

	$FORM_CONTROL.ipv4_check(obj);
};

$FORM_CONTROL['ipv4_check'] = function(obj){

	var error = false;
	var item = getItemFromObj(obj);
	for (var i=1; i<5; i++){
		var v = $("#" + item.root + "__" + i).val();
		if (!(v.match(/^\d{1,3}$/) && parseInt(v) >= 0 && parseInt(v) <= 255)){
			error = true;
		}
	}

	if (!error){
		v = "";
		for (var i=1; i<5; i++){
			v += $("#" + item.root + "__" + i).val()
			if (i < 4){
				v+= '.';
			}
		}
	} else {
		v = '';
	}
	$("#" + item.root).val(v);

	// set error highlighting?
};

$FORM_CONTROL['ipv4_keydown'] = function(obj, event){

	var key = getKeyPress(event);
	if (key.code == 46){ // '.' pressed so skip to next box
		var item = getItemFromObj(obj);
		if (parseInt(item.ext)<4){
			$("#" + item.root + '__' + (parseInt(item.ext) + 1)).trigger("focus").select();
		}
		return false;
	}
	if ((key.code > 47 && key.code < 59) // numbers
	   || allowedKeys(key) ){
		return true;
	} else {
		return false;
	}
};

