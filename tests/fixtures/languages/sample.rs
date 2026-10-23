// TODO: plain tag with a colon
/// FIXME(alice): doc comment
fn first<'a>(x: &'a str) -> &'a str {
    x // HACK trailing comment after a lifetime
}

/* XXX {2030-01-02} @bob
 * second line of a block comment
 */
const TODO_LIST: &str = "TODO list";
const NOTE: &str = "// FIXME in a string";
