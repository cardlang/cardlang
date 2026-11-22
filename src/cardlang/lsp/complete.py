"""Completion (TL1): the runtime APIs and the members of enums and error sets.

completions(target, texts, line, character) returns LSP CompletionItems for the position, 0-based, in file target:
- after `card.` and each namespace below it: the next path segments of the Base Profile catalog
  (platform/base-catalog.txt). A namespace is a Module, with its description from platform/base-profile.md. An API
  is a Function, with its signature, summary, transaction rule and errors. It inserts a snippet with a placeholder
  per argument and the argument's mode (`ref`, `inout`) written in. The test-only catalog (card.test.*) is left out;
- after `Owner.`, where Owner is an enum or an error set: its members. This covers the Base Profile's (KeyType,
  DigestAlgorithm and the rest), CardError, and the program's own.
"""
import re, sys, pathlib
from cardlang.lsp import semantic
from cardlang.front import pltcheck
from cardlang.front.lexcheck import lex, LexError
from cardlang import layout

FUNCTION, MODULE, ENUM_MEMBER = 3, 9, 20          # LSP CompletionItemKind
SNIPPET = 2                                        # LSP InsertTextFormat

_api = None

def type_text(t):
    if isinstance(t, tuple) and t[0] == "arr": return f"{type_text(t[1])}[{'' if t[2] is None else t[2]}]"
    return str(t)

def apis():
    """{path: {"params", "ret", "tx", "errors", "summary"}}, and {namespace: description}."""
    global _api
    if _api is None:
        catalog, blocks = pltcheck.load_block_catalog()
        summaries = {b["api"]: dict(b["fields"]).get("summary", "") for b in blocks}
        for path, e in catalog.items(): e["summary"] = summaries.get(path, "")
        profile = layout.at().base_profile
        text = profile.read_text(encoding="utf-8") if profile.exists() else ""
        spaces = {m.group(1): m.group(2).strip() for m in re.finditer(r"^\| `(card\.[a-z_]+)` \| ([^|]+) \|", text, re.M)}
        _api = (catalog, spaces)
    return _api

def signature(path, e):
    params = ", ".join((f"{mode} " if mode else "") + f"{name}: {type_text(t)}" for name, mode, t in e["params"])
    return f"{path}({params})" + ("" if e["ret"] == "none" else f" -> {type_text(e['ret'])}")

def snippet(name, e):
    args = ", ".join((f"{mode} " if mode else "") + f"${{{k}:{pname}}}" for k, (pname, mode, _) in enumerate(e["params"], 1))
    return f"{name}({args})"

def api_items(prefix):
    catalog, spaces = apis()
    items, seen = [], set()
    for path, e in sorted(catalog.items()):
        if not path.startswith(prefix + "."): continue
        rest = path[len(prefix) + 1:].split(".")
        seg = rest[0]
        if seg in seen: continue
        seen.add(seg)
        if len(rest) > 1:
            ns = f"{prefix}.{seg}"
            items.append({"label": seg, "kind": MODULE, "detail": ns, "documentation": spaces.get(ns, "")})
        else:
            doc = (e.get("summary") or "") + f"\n\nTransaction: {e['tx']}." + (f" Errors: {', '.join(e['errors'])}." if e["errors"] else "")
            items.append({"label": seg, "kind": FUNCTION, "detail": signature(path, e),
                          "documentation": {"kind": "markdown", "value": doc.strip()},
                          "insertText": snippet(seg, e), "insertTextFormat": SNIPPET})
    return items

def member_items(owner, texts):
    syms = semantic.Symbols(); syms.merge(semantic.prelude_symbols())
    for path, text in texts.items():
        try: semantic.collect(lex(text.encode("utf-8"), path), syms)
        except LexError: pass
    members = syms.members.get(owner)
    if members is None: return []
    lib = owner in semantic.prelude_symbols().members
    order = [m for (o, m), _ in syms.member_decls.items() if o == owner] or sorted(members)
    return [{"label": m, "kind": ENUM_MEMBER, "detail": f"{owner}.{m}" + (" (Base Profile)" if lib else ""), "sortText": f"{k:04d}"}
            for k, m in enumerate(order)]

def completions(target, texts, line, character):
    lines = texts.get(target, "").splitlines()
    before = lines[line][:character] if line < len(lines) else ""
    m = re.search(r"\bcard((?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.([A-Za-z_][A-Za-z0-9_]*)?$", before)
    if m:
        prefix = "card" + m.group(1)
        if prefix.startswith("card.test"): return []
        return [i for i in api_items(prefix) if not (prefix == "card" and i["label"] == "test")]
    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)?$", before)
    if m: return member_items(m.group(1), texts)
    return []
