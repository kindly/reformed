

$.Buttons.action_hash = {
    save: [['save', 'document-save.png', 'c', 'record'],[document, node_save, ['main','']]],
    'delete':[['delete', 'edit-delete.png', 'd', 'record'],[document, node_delete, ['main','']]],
    home: [['home', 'go-home.png', 'h', 'general'],[document, node_load, ['n:test.HomePage:']]],
    new_ticket: [['new ticket', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:new']]],
    new_user: [['new user', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.User:new']]],
    list_tickets: [['list tickets', 'go-home.png', 'h', 'general'],[document, node_load, ['n:bug.Ticket:list']]]
};


$.Buttons.action_list = ['home',  'save', 'delete'];


