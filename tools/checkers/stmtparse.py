"""The statement parser shared by the reference interpreter and the prototype compiler (VM4 stage 1).

Statements become tuples; expressions come from the checkers' expression parser (expcheck.p_expr). The parser
assumes a program the checkers have accepted, so it reports no errors of its own beyond CE-SYN-1 from expcheck.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from expcheck import P, p_expr, p_postfix, p_type

def parse_block(p):
    p.expect("{"); out = []
    while p.peek() != "}":
        out.append(parse_stmt(p))
    p.expect("}"); return out

def parse_pattern(p):
    if p.peek() == "Ok":
        p.take(); p.expect("(")
        name = None if p.peek() == ")" else p.take()
        p.expect(")"); return ("ok", name)
    if p.peek() == "Err":
        p.take(); p.expect("(")
        if p.peek(1) == ".":
            owner = p.take(); p.take(); member = p.take(); p.expect(")"); return ("err_member", owner, member)
        if p.peek(1) == "(":
            owner = p.take(); p.take(); name = p.take(); p.expect(")"); p.expect(")"); return ("err_set", owner, name)
        name = p.take(); p.expect(")"); return ("err_bind", name)
    if p.peek() == "_":
        p.take(); return ("wild",)
    owner = p.take(); p.expect("."); return ("enum", owner, p.take())

def parse_stmt(p):
    v = p.peek()
    if v == "var":
        p.take(); name = p.take(); p.expect(":"); ty = p_type(p); init = None
        if p.peek() == "=":
            p.take(); init = p_expr(p)
        p.expect(";"); return ("var", name, ty, init)
    if v == "if":
        branches = []; p.take(); c = p_expr(p, True); branches.append((c, parse_block(p))); other = None
        while p.peek() == "else":
            p.take()
            if p.peek() == "if":
                p.take(); c = p_expr(p, True); branches.append((c, parse_block(p)))
            else:
                other = parse_block(p)
        return ("if", branches, other)
    if v == "while":
        p.take(); c = p_expr(p, True); return ("while", c, parse_block(p))
    if v == "for":
        p.take(); name = p.take(); p.expect(":"); ty = p_type(p); p.expect("in")
        lo = p_expr(p, True); p.expect(".."); hi = p_expr(p, True); return ("for", name, ty, lo, hi, parse_block(p))
    if v == "match":
        p.take(); s = p_expr(p, True); p.expect("{"); arms = []
        while p.peek() != "}":
            pat = parse_pattern(p); p.expect("=>"); arms.append((pat, parse_block(p)))
        p.expect("}"); return ("match", s, arms)
    if v in ("break", "continue"):
        p.take(); p.expect(";"); return (v,)
    if v == "return":
        p.take()
        if p.peek() == "Ok":
            p.take(); p.expect("(")
            e = None if p.peek() == ")" else p_expr(p)
            p.expect(")"); p.expect(";"); return ("return_ok", e)
        if p.peek() == "Err":
            p.take(); p.expect("("); e = p_expr(p); p.expect(")"); p.expect(";"); return ("return_err", e)
        e = p_expr(p); p.expect(";"); return ("return_fwd", e)
    if v == "require":
        p.take(); c = p_expr(p); p.expect("else"); e = p_expr(p); p.expect(";"); return ("require", c, e)
    if v == "attempt":
        p.take(); e = p_postfix(p, False); other = None
        if p.peek() == "else": p.take(); other = p_postfix(p, False)
        p.expect(";"); return ("attempt", e, other)
    if v == "ignore":
        p.take(); e = p_postfix(p, False); p.expect(";"); return ("ignore", e)
    if v == "transaction":
        p.take(); return ("transaction", parse_block(p))
    if v == "wipe":
        p.take(); e = p_expr(p); p.expect(";"); return ("wipe", e)
    if v == "abort":
        p.take(); p.expect("Err"); p.expect("("); e = p_expr(p); p.expect(")"); p.expect(";"); return ("abort", e)
    dest = p_expr(p)
    if p.peek() in ("+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="):
        op = p.take()[:-1]; e = p_expr(p); p.expect(";"); return ("compound", dest, op, e)
    p.expect("="); e = p_expr(p); p.expect(";"); return ("assign", dest, e)
