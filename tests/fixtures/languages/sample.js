// TODO: plain tag with a colon
/* FIXME {2030-01-02} @alice block comment on one line */
/*
 * HACK(bob): inside a block comment
 * XXX {2031-03-04} on a line that starts with a star
 */
const TODO_LIST = "TODO list";
const url = "http://example.com/TODO"; // TODO trailing comment
const template = `multi-line template
// TODO inside a template literal
`;
const todonotifier = require("todonotifier");
