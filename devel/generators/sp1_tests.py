"""Write SP1 conformance tests byte-exactly."""
import sys, pathlib
root = pathlib.Path(sys.argv[1]) / "conformance"
PROJECT_AB = '{' + chr(10) + '  "files": [' + chr(10) + '    "a.card",' + chr(10) + '    "b.card"' + chr(10) + '  ]' + chr(10) + '}' + chr(10)   # TL1: cardlang.json

def hdr(rule, source, expect, note, kind="fragment", status="agreed", also=None):
    h = [f"// rule: {rule}", f"// source: {source}", f"// status: {status}", f"// kind: {kind}", f"// expect: {expect}"]
    if also:
        h.append(f"// also: {also}")
    h.append(f"// note: {note}")
    return "\n".join(h) + "\n"

def w(rel, data):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)

V, I = "valid/", "invalid/"
w(V+"lex-001-identifiers.card", hdr("LEX-12, LEX-14", "DN §3.0", "ok", "Identifier forms, including a leading underscore.") +
  "const counter: u32 = 1;\nconst account_balance: u32 = 2;\nconst _x: u8 = 3;\nconst MAX_ACCOUNTS: u16 = 16;\n")
w(V+"lex-002-comments.card", hdr("LEX-3, LEX-7, LEX-8, LEX-9", "DN §3.0", "ok", "Comments, Unicode inside comments, comment markers inside comments.") +
  "// Grüße: comments may contain Unicode. /* This does not open a block comment.\n"
  "/* A block comment,\n   spanning lines. // This is still inside the block comment. */\n"
  "const LIMIT: u32 = 100; // A line comment after a declaration.\n")
w(V+"lex-003-integer-literals.card", hdr("LEX-17, LEX-19", "DN §3.0", "ok", "Decimal, hex and binary forms; separators; mixed-case hex; leading zero is decimal.") +
  "const A: u32 = 123;\nconst B: u8 = 0xA5;\nconst C: u8 = 0b1010;\nconst D: u32 = 1_000_000;\n"
  "const E: u32 = 0xDEAD_BEEF;\nconst F: u32 = 0xdead_beef;\nconst G: u8 = 007;\n")
w(V+"lex-004-boolean-literals.card", hdr("LEX-21", "DN §3.0", "ok", "The two Boolean literals.") +
  "const ENABLED: bool = true;\nconst DISABLED: bool = false;\n")
w(V+"lex-005-longest-match.card", hdr("LEX-10, LEX-22", "DN §3.0, §3.6", "ok", "Multi-character tokens written without spaces.") +
  "const LIMIT: u32 = 16;\nconst SMALL: bool = LIMIT<=32;\nsession buffer: u8[16];\n"
  "function clear_buffer(){for index: u8 in 0..16{buffer[index]=0;}return Ok();}\n"
  "function limit()->u32{return Ok(LIMIT);}\n")
w(V+"lex-006-two-files/cardlang.json", PROJECT_AB)
w(V+"lex-006-two-files/a.card", hdr("LEX-7, LEX-11", "DN §3.0, §4.1", "ok",
  "a.card ends with a line comment and no final line break; b.card must not be consumed. Must pass in either file order.") +
  "const A: u32 = B; // the comment ends at the end of this file")
w(V+"lex-006-two-files/b.card", "const B: u32 = 2;\n")
w(V+"lex-007-byte-order-mark.card", b"\xef\xbb\xbf" + hdr("LEX-4", "D-423", "ok", "The file starts with a UTF-8 byte-order mark, which is ignored.").encode() +
  b"const A: u32 = 1;\n")
w(V+"lex-008-line-breaks.card", hdr("LEX-5, LEX-7", "D-423", "ok",
  "Lines end with a lone CR, CRLF and LF. The line comment ends at the lone CR, so B is declared.").encode() +
  b"const A: u32 = B; // this comment ends at a lone CR\rconst B: u32 = C;\r\nconst C: u32 = 3;\n")

w(I+"lex-101-non-ascii-identifier.card", hdr("LEX-3, LEX-12", "DN §3.0", "compile-error CE-LEX-2", "A non-ASCII letter in an identifier.") +
  "const café: u32 = 1;\n")
w(I+"lex-102-unterminated-block-comment.card", hdr("LEX-8", "DN §3.0", "compile-error CE-LEX-3", "A block comment that is never closed.") +
  "const A: u32 = 1;\n/* This comment is never closed.\nconst B: u32 = 2;\n")
w(I+"lex-103-nested-block-comment.card", hdr("LEX-8, LEX-9", "DN §3.0", "compile-error CE-SYN-1", "Block comments do not nest; `tail */` is left as source text.") +
  "/* outer /* inner */ tail */\nconst A: u32 = 1;\n")
for n, slug, lit, ty, why in [
    (104, "literal-double-underscore", "1__0", "u32", "Consecutive underscores."),
    (105, "literal-trailing-underscore", "1_", "u32", "Trailing underscore."),
    (106, "literal-underscore-after-prefix", "0x_FF", "u8", "Underscore directly after the prefix."),
    (107, "empty-hex-prefix", "0x", "u8", "Prefix without digits."),
    (108, "binary-digit-out-of-base", "0b102", "u8", "Digit outside the base."),
    (109, "uppercase-prefix", "0XFF", "u8", "Uppercase prefix."),
]:
    w(I+f"lex-{n}-{slug}.card", hdr("LEX-17, LEX-18", "DN §3.0; D-414", "compile-error CE-LEX-4", why) + f"const A: {ty} = {lit};\n")
w(I+"lex-110-keyword-as-identifier.card", hdr("LEX-13", "DN §3.0; D-404", "compile-error CE-SYN-1", "A keyword used as a declaration name.") +
  "const match: u8 = 1;\n")
w(I+"lex-111-underscore-as-name.card", hdr("LEX-14", "DN §3.0", "compile-error CE-SYN-1", "A lone `_` used as a declaration name.") +
  "const _: u8 = 1;\n")
w(I+"lex-112-comment-across-files/cardlang.json", PROJECT_AB)
w(I+"lex-112-comment-across-files/a.card", hdr("LEX-8, LEX-11", "DN §3.0, §4.1", "compile-error CE-LEX-3",
  "A block comment opened in a.card cannot be closed in b.card.", also="CE-SYN-1") +
  "const A: u32 = 1;\n/* opened in this file\n")
w(I+"lex-112-comment-across-files/b.card", "closed in this file */\nconst B: u32 = 2;\n")
w(I+"lex-113-invalid-utf8.card", hdr("LEX-2", "DN §3.0", "compile-error CE-LEX-1", "A comment contains the byte FF, which is never valid UTF-8.").encode() +
  b"// invalid byte: \xff\nconst A: u32 = 1;\n")
w(I+"lex-114-preprocessor-directive.card", hdr("LEX-6, LEX-24", "DN §3.0; D-037", "compile-error CE-LEX-2", "There is no preprocessor; `#` cannot begin a token.") +
  "#include \"state.card\"\nconst A: u32 = 1;\n")
for d in ("valid", "invalid"):
    g = root / d / ".gitkeep"
    if g.exists():
        g.unlink()
print("written")
