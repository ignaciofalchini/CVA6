#!/usr/bin/env python3
"""Patch GENERATED FSBL sources only; never the installed AMD repository."""
import argparse
import re
import shutil
from pathlib import Path


def body(text, name):
    matches = list(re.finditer(r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', text))
    if len(matches) != 1:
        raise ValueError(f'Expected one definition of {name}, found {len(matches)}')
    start = matches[0].end()
    level, end = 1, start
    # Generated AMD function bodies have no brace literals in strings/comments.
    while level:
        if end >= len(text):
            raise ValueError(f'Unterminated {name}')
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return start, end - 1


def patch(psu, hooks):
    psu, hooks = Path(psu).resolve(), Path(hooks).resolve()
    if 'embeddedsw' in psu.parts or 'embeddedsw' in hooks.parts:
        raise ValueError('Refusing to modify installed/vendor sources; copy to build first')
    updates = []
    for path in (psu, hooks):
        text = path.read_text()
        if '/* KR260_RESET_HOLD_PATCH */' in text:
            continue
        if path == psu:
            a, b = body(text, 'psu_ps_pl_reset_config_data')
            old = text[a:b].lower()
            if 'ff0a' not in old or '80000000' not in old:
                raise ValueError('Unexpected generated PS reset implementation')
            text = text[:a] + '\n    Kr260HoldCva6();\n    return 1;\n' + text[b:]
        else:
            for name in ('XFsbl_HookBeforeBSDownload', 'XFsbl_HookAfterBSDownload',
                         'XFsbl_HookBeforeHandoff', 'XFsbl_HookBeforeFallback'):
                a, _ = body(text, name)
                text = text[:a] + '\n    Kr260HoldCva6();\n' + text[a:]
            a, b = body(text, 'XFsbl_HookPsuInit')
            function = text[a:b]
            if function.count('return Status;') != 1:
                raise ValueError('Unexpected PSU init hook')
            function = function.replace('return Status;', 'Kr260HoldCva6();\n\treturn Status;')
            text = text[:a] + function + text[b:]
        text = '/* KR260_RESET_HOLD_PATCH */\n#include "kr260_fsbl_reset.h"\n' + text
        updates.append((path, text))
    header = Path(__file__).resolve().parents[1] / 'src/kr260_fsbl_reset.h'
    for directory in {psu.parent, hooks.parent}:
        shutil.copy2(header, directory / header.name)
    for path, text in updates:
        backup = path.with_suffix(path.suffix + '.before_kr260')
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(text)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--psu-init', required=True)
    p.add_argument('--hooks', required=True)
    args = p.parse_args()
    patch(args.psu_init, args.hooks)
    print('FSBL: reset held; only the ARM application may release CVA6')
