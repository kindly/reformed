
$.Buttons.action_hash = {
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    'delete':[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, node_load, ['n:test.HomePage:']]],
    new_ticket: [['new ticket', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:new']]],
    new_user: [['new user', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.User:new']]],
    new_user_group: [['new user group', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.UserGroup:new']]],
    list_user_group: [['list user group', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.UserGroup:list']]],
    new_permission: [['new permission', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Permission:new']]],
    list_tickets: [['list tickets', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:list']]]
};


$.Buttons.action_list = ['home',  'save', 'delete', 'new_ticket', 'list_tickets', 'new_permission', 'new_user', 'new_user_group', 'list_user_group'];

