import sublime
import sublime_plugin
import re
from threading import Timer
from collections import defaultdict



class Region(sublime.Region):
    def __init__(self, a=-1, b=-1):
        super(Region, self).__init__(a, b)


class CodeBlockHighlighter(sublime_plugin.EventListener):
    def __init__(self):
        self.debounce_timer = None
        self.last_cursor_pos = -1
        self.region_end2start = defaultdict(Region)

    def on_activated_async(self, view):
        self._check_unclosed_codes(view)

    def on_post_save_async(self, view):
        self._check_unclosed_codes(view)

    def on_modified_async(self, view):
        self._check_unclosed_codes(view)

    def on_selection_modified_async(self, view):
        # 250ms内只触发一次
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = Timer(0.25, self._process_cursor_move, [view])
        self.debounce_timer.start()

    # 检查未闭合代码块
    def _check_unclosed_codes(self, view):
        if not view.match_selector(0, "source.bbs_nga"):
            return

        self.region_end2start.clear()
        error_regions = []
        
        content = view.substr(sublime.Region(0, view.size()))
        code_stack = []

        pattern = re.compile(r"\[(/)?([^=|\[|\]| |\d]+)(\d+| [^]]+|=[^]]+)?\]")
        for match in pattern.finditer(content):
            is_end, code_name, suffix = match.groups()

            if code_name == "fixsize":
                continue

            pos = match.start()
            bias = len(code_name)
            bias += 3 if is_end else 2   # [__code__]或者[/__code__]
            bias += len(suffix) if suffix else 0
            
            scopes = view.scope_name(pos).split()

            if len(scopes) <= 1:
                continue

            if scopes[-1] not in ["keyword.control", "punctuation.definition.keyword", "variable.function", "variable.parameter"]:
                continue

            region = sublime.Region(pos, pos + bias)

            # style在randomblock外进行提示
            if code_name == "style":
                if "meta.randomblock.bbs_nga" not in scopes:
                    error_regions.append(region)
            
            if not is_end:
                # 代码块开头
                code_stack.append((code_name, region))
            else:
                # 代码块结尾
                if code_stack:
                    start_code, start_region = code_stack.pop()
                    if start_code == code_name:
                        self.region_end2start[region.to_tuple()] = start_region
                    else:
                        error_regions.append(region)

        # 标记未闭合的代码块开头
        for tag, region in code_stack:
            error_regions.append(region)

        if error_regions:
            # view.add_regions("unclosed_codes", error_regions,  "invalid.illegal", flags=sublime.RegionFlags.DRAW_SQUIGGLY_UNDERLINE)
            view.add_regions("unclosed_codes", error_regions,  "invalid.illegal", flags=2048)
        else:
            view.erase_regions("unclosed_codes")

    # 光标移动时更新高亮提示
    def _process_cursor_move(self, view):
        if not view.match_selector(0, "source.bbs_nga"):
            return

        cursor_pos = view.sel()[0].begin() if view.sel() else 0
        
        # 位置未变化时跳过
        if cursor_pos == self.last_cursor_pos:
            return
        self.last_cursor_pos = cursor_pos

        # 仅检查包裹光标的code块
        current_codes = []
        current_scopes = view.scope_name(cursor_pos).split()

        for scope in reversed(current_scopes):
            if ".bbs_nga" in scope and "source" not in scope:
                code_name = scope.split(".")[1]
                current_codes.append(code_name)

        # if current_codes:
        self._highlight_matched_codes(view, current_codes, cursor_pos)

    # 高亮包裹光标的代码块
    def _highlight_matched_codes(self, view, current_codes, cursor_pos):
        regions = []

        for code_name in current_codes:
            end_code = "[/"+ code_name + "]"

            # 只向后找[/code],然后map到对应region
            # end_region = view.find(end_code, cursor_pos - len(end_code), flags=sublime.FindFlags.LITERAL)
            end_region = view.find(end_code, cursor_pos - len(end_code), flags=1)
            start_region = self.region_end2start[end_region.to_tuple()]

            while start_region.a > cursor_pos:
                # end_region = view.find(end_code, end_region.b, flags=sublime.FindFlags.LITERAL)
                end_region = view.find(end_code, end_region.b, flags=1)
                start_region = self.region_end2start[end_region.to_tuple()]
            
            if not start_region.empty() and not end_region.empty():
                regions += [start_region, end_region]

        if regions:
            # view.add_regions("matched_codes", regions, "entity.name", flags=sublime.RegionFlags.DRAW_NO_FILL)
            view.add_regions("matched_codes", regions, "entity.name", flags=32)
        else:
            view.erase_regions("matched_codes")