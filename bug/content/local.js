
$.Buttons.action_hash = {
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    'delete':[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, node_load, ['n:test.HomePage:']]],
    new_ticket: [['new ticket', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:new']]],
    new_user: [['new user', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.User:new']]],
    user_admin : [['user admin', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.UserAdmin:']]],
    user_about_me : [['about me', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.User:about_me']]],
    new_user_group: [['new user group', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.UserGroup:new']]],
    list_user_group: [['list user group', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.UserGroup:list']]],
    new_permission: [['new permission', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Permission:new']]],
    list_tickets: [['list tickets', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:list']]],
    list_permission: [['list permisions', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Permission:list']]],
    sys_info: [['sys info', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.SysInfo:list']]],
    list_user: [['list Users', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.User:list']]]
};


$.Buttons.action_list = ['home',  'save', 'delete', 'new_ticket', 'user_admin', 'user_about_me', 'sys_info' ];

