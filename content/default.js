function select_box(arg){
	arg = String(arg.name);
	arg = arg.substring(0,arg.lastIndexOf(":"));
	x=document.getElementById(arg + ':_::_selected');
	if (x){
		x.checked=true;
	}
}
