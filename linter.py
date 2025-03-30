import sublime
import sublime_plugin
import re
from threading import Timer
from collections import defaultdict


class Region(sublime.Region):
    def __init__(self, a=-1, b=-1):
        super(Region, self).__init__(a, b)


class Linter(sublime_plugin.EventListener):
    '''
    警告未闭合/不当闭合顺序代码块的开头tag 与 高亮提示包裹光标所在位置代码块的tag
    '''
    def __init__(self):
        # 防抖计时器
        self.debounce_timer = None
        # 上一次(多行)光标的位置
        self.last_cursors_pos = []
        # 代码块的结尾tag映射开头tag
        self.region_end2start = defaultdict(Region)
        # list中所属[*]的区域
        self.list_items = defaultdict(list)

    def on_activated_async(self, view):
        self._check_unclosed_tags(view)

    def on_post_save_async(self, view):
        self._check_unclosed_tags(view)

    def on_modified_async(self, view):
        self._check_unclosed_tags(view)

    def on_selection_modified_async(self, view):
        # 200ms内只触发一次
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = Timer(0.2, self._process_cursor_move, [view])
        self.debounce_timer.start()

    # 检查未闭合tag
    def _check_unclosed_tags(self, view):
        if not view.match_selector(0, "source.bbcode.nga"):
            return

        self.region_end2start.clear()
        self.list_items.clear()
        error_regions = []
        
        content = view.substr(sublime.Region(0, view.size()))
        tag_stack = []
        list_stack = []     # 用于list多层嵌套时, 获取当前最内层的list

        pattern = re.compile("\[(/)?([^=\[\] \d]+|\*)(\d+| [^\[\]]+|=[^\]]+)?\]")
        for match in pattern.finditer(content):
            is_end, tag, suffix = match.groups()

            # 跳过fixsize
            if tag == "fixsize":
                continue

            pos = match.start()
            region = sublime.Region(pos, pos + len(match.group()))

            # 记录当前list所属[*]的区域
            if tag == "*":
                if list_stack:
                    self.list_items[list_stack[-1]].append(region)
                continue
            
            scopes = view.scope_name(pos).split()

            # 若非支持的BBCode tag, 则跳过
            if "tag.bbcode.nga" not in scopes[-1]:
                continue

            # style在randomblock外进行警告
            if tag == "style" and "meta.randomblock.bbcode.nga" not in scopes:
                error_regions.append(region)

            # list多层嵌套处理
            if tag == "list":
                if not is_end:
                    list_stack.append(region.to_tuple())
                else:
                    list_stack.pop()
            
            if not is_end:
                # 开头tag
                tag_stack.append((tag, region))
            else:
                # 结尾tag
                if tag_stack:
                    start_tag, start_region = tag_stack.pop()
                    if start_tag == tag:
                        self.region_end2start[region.to_tuple()] = start_region
                    else:
                        # 标记未闭合/不当闭合顺序代码块的开头tag
                        error_regions.append(start_region)

        # 标记未闭合代码块的开头tag
        for _, region in tag_stack:
            error_regions.append(region)

        # 覆盖更新错误区域
        # view.add_regions("error", error_regions,  "invalid.illegal", flags=sublime.RegionFlags.DRAW_SQUIGGLY_UNDERLINE)
        view.add_regions("error", error_regions,  "invalid.illegal", flags=2048)

    # 光标移动时更新高亮提示
    def _process_cursor_move(self, view):
        if not view.match_selector(0, "source.bbcode.nga"):
            return

        cursors_pos = [region.b for region in view.sel()]
        
        # 位置未变化时跳过
        if cursors_pos == self.last_cursors_pos:
            return
        self.last_cursors_pos = cursors_pos

        highlight_regions = []

        for cursor_pos in cursors_pos:
            # 若光标没有被任何代码块包裹, 则跳过
            if len(view.scope_name(cursor_pos).split()) <= 1:
                continue

            for end_region in self.region_end2start.keys():
                # 若该tag已被标记为高亮显示, 则跳过
                if end_region in highlight_regions:
                    continue

                start_region = self.region_end2start[end_region]
                end_region = sublime.Region(a=end_region[0], b=end_region[1])

                # 若光标被该代码块包裹, 则高亮标记该代码块的tag
                if start_region.begin() <= cursor_pos < end_region.end():
                    highlight_regions += [start_region, end_region]

                    # 在list中, 从最后一个所属的[*]开始, 找第一个位于光标前面的[*]
                    if view.substr(end_region) == "[/list]":
                        for item_region in reversed(self.list_items[start_region.to_tuple()]):
                            if item_region.begin() <= cursor_pos:
                                highlight_regions.append(item_region)
                                break
        
        # 覆盖更新高亮区域
        # view.add_regions("highlight", highlight_regions, "entity.name", flags=sublime.RegionFlags.DRAW_NO_FILL)
        view.add_regions("highlight", highlight_regions, "entity.name", flags=32)
