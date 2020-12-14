import os
from detect_secrets.core import baseline
from detect_secrets.main import parse_args, build_automaton
from detect_secrets.plugins.common import initialize
from detect_secrets import util

def scan(argv):
    args = parse_args(argv)
    automaton = None
    word_list_hash = None
    if args.word_list_file:
        automaton, word_list_hash = build_automaton(args.word_list_file)

    # Plugins are *always* rescanned with fresh settings, because
    # we want to get the latest updates.
    plugins = initialize.from_parser_builder(
        plugins_dict=args.plugins,
        custom_plugin_paths=args.custom_plugin_paths,
        exclude_lines_regex=args.exclude_lines,
        automaton=automaton,
        should_verify_secrets=not args.no_verify,
    )
    return baseline.initialize(
        path=args.path,
        plugins=plugins,
        custom_plugin_paths=args.custom_plugin_paths,
        exclude_files_regex=args.exclude_files,
        exclude_lines_regex=args.exclude_lines,
        word_list_file=args.word_list_file,
        word_list_hash=word_list_hash,
        should_scan_all_files=args.all_files,
    )

def get_path_if_in_root(root, filepath):
    filepath = os.path.realpath(
        os.path.join(root, filepath),
    )
    if os.path.isfile(filepath):
        return filepath
    return None


util.get_relative_path_if_in_cwd = get_path_if_in_root