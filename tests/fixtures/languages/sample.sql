-- TODO: plain tag with a colon
SELECT 'TODO list' AS note, 'a -- FIXME in a string' AS other; -- FIXME(alice) trailing comment
/* HACK {2030-01-02} @bob
   XXX second line of a block comment */
SELECT todo_list FROM todonotifier;
