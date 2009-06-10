INSERT INTO "_core_form" VALUES(1,'form',NULL,NULL);
INSERT INTO "_core_form" VALUES(2,'form_item',NULL,NULL);
INSERT INTO "_core_form" VALUES(3,'form_item_param',NULL,NULL);
INSERT INTO "_core_form" VALUES(8,'form_param',NULL,NULL);
INSERT INTO "_core_form" VALUES(17,'logon',NULL,NULL);
INSERT INTO "_core_form" VALUES(18,'donkey',NULL,NULL);


INSERT INTO "_core_form_item" VALUES(1,1,'_core_form.name','form name:','textbox',1,1,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(3,1,'sub1','subform','subform',1,4,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(4,1,'sub3','form parameters','subform',1,3,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(5,2,'_core_form_item.name','name:','textbox',1,1,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(6,2,'_core_form_item.label','label:','textbox',1,2,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(7,2,'_core_form_item.item','item:','dropdown',1,3,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(9,2,'sub2','subform','subform',1,7,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(10,2,'_core_form_item.sort_order','sort order:','textbox',1,4,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(11,2,'_core_form_item.active','active','checkbox',1,5,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(12,3,'_core_form_item_param.key','key','textbox',1,1,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(13,3,'_core_form_item_param.value','value','textbox',1,2,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(14,3,'save','save','submit',0,3,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(15,3,'delete','delete','submit',0,4,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(29,8,'_core_form_param.key','key:','textbox',1,1,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(30,8,'_core_form_param.value','value','textbox',1,2,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(31,8,'save','save','submit',0,3,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(32,8,'delete','delete','submit',0,4,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(49,17,'username','name:','textbox',1,1,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(50,17,'password','password','password',1,2,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(51,17,'login','ok','submit',1,3,NULL,NULL);
INSERT INTO "_core_form_item" VALUES(52,18,'donkey.name','name:','textbox',1,1,'2009-06-08 19:00:30.937626',1);
INSERT INTO "_core_form_item" VALUES(53,18,'donkey.age','age:','textbox',1,2,'2009-06-08 19:00:54.259513',1);


INSERT INTO "_core_form_item_param" VALUES(1,3,'subform_name','form_item',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(2,3,'child_id','_core_form_id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(3,3,'parent_id','id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(4,3,'child_object','_core_form_item',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(5,4,'subform_name','form_param',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(6,4,'child_id','_core_form_id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(7,4,'parent_id','id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(8,4,'child_object','_core_form_param',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(9,4,'form_type','grid',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(10,7,'type','list',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(11,7,'values','textbox|dropdown|password|submit|subform|checkbox|codelist|record_navigation',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(12,9,'child_id','_core_form_item_id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(13,9,'parent_id','id',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(14,9,'subform_name','form_item_param',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(15,9,'child_object','_core_form_item_param',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(16,9,'form_type','grid',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(40,3,'form_type','normal',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(64,51,'command','login',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(65,51,'object','authentication',NULL,NULL);
INSERT INTO "_core_form_item_param" VALUES(66,1,'fdf','dfsf',NULL,NULL);


INSERT INTO "_core_form_param" VALUES(1,1,'form_object','_core_form',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(2,2,'form_object','_core_form_item',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(3,3,'form_object','_core_form_item_param',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(7,8,'form_object','_core_form_param',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(23,17,'form_type','action',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(24,1,'form_type','normal',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(25,2,'form_type','normal',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(27,18,'form_type','normal',NULL,NULL);
INSERT INTO "_core_form_param" VALUES(28,18,'form_object','donkey','2009-06-08 19:02:06.504715',1);
