import sublime
import sublime_plugin
import re
from collections import defaultdict
 

__NGA_DOMAIN__ = "(" + "|".join(["bbs.nga.cn", "ngabbs.com", "nga.178.com"]) + ")"
__NGA_IMAGE_HOSTING__ = 'https://img.nga.178.com/attachments'
__BBCODE2MARKDOWN__ = defaultdict(str)
__BBCODE2MARKDOWN__.update({
    'b': '**',
    'i': '*',
    'del': '~~',
    'code': '`'
})


def toggle(view, edit, tag):
    if not view.match_selector(0, "source.bbcode.nga"):
        return

    start_tag = "[" + tag + "]"
    end_tag = "[/" + tag + "]"

    new_selections = []
    
    for region in view.sel():
        bias = 0
        start_check, end_check = region.begin() - len(start_tag), region.end() + len(end_tag)

        # 检查所选区域前后是否存在tag
        exist_start = view.substr(sublime.Region(start_check, region.begin())) == start_tag
        exist_end = view.substr(sublime.Region(region.end(), end_check)) == end_tag

        if exist_start and exist_end:
            # 删除代码块
            view.erase(edit, sublime.Region(region.end(), end_check))
            view.erase(edit, sublime.Region(start_check, region.begin()))
            bias = -len(start_tag)
        else:
            # 添加代码块
            view.insert(edit, region.end(), end_tag)
            view.insert(edit, region.begin(), start_tag)
            bias = len(start_tag)

        new_selections.append(sublime.Region(region.a + bias, region.b + bias))

    # 重新选择区域
    view.sel().clear()
    for selection in new_selections:
        view.sel().add(selection)


def find_all(view, pattern, within=None):
    if within is not None:
        if sublime.version() >= "4181":
            regions = view.find_all(pattern, within=within)
        else:
            regions = view.find_all(pattern)
            regions = [region for region in regions if region.a >= select_region.begin() and region.b <= select_region.end()]
    else:
        regions = view.find_all(pattern)

    return regions


class ToggleBoldCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "b")


class ToggleUnderlineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "u")


class ToggleItalicCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "i")


class ToggleQuoteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "quote")


class DecodeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not self.view.match_selector(0, "source.bbcode.nga"):
            return

        pattern = "\["

        for select_region in self.view.sel():
            # 捕获所选区域的所有'[' (若没选中内容, 则默认对全文进行操作)
            if len(self.view.sel()) == 1 and select_region.empty():
                regions = find_all(self.view, pattern)
            else:
                regions = find_all(self.view, pattern, within=select_region)

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将[tag]...[/tag]变为[[size=0%][/size]tag]...[[size=0%][/size]/tag]
                if "tag.bbcode.nga" in scopes[-1]:
                    self.view.insert(edit, region.a + 1, "[size=0%][/size]")



class CondenseUrlCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not self.view.match_selector(0, "source.bbcode.nga"):
            return

        pattern = "(https://)?" + __NGA_DOMAIN__ + "/"

        for select_region in self.view.sel():
            # 捕获所选区域的所有NGA域名 (若没选中内容, 则默认对全文进行操作)
            if len(self.view.sel()) == 1 and select_region.empty():
                regions = find_all(self.view, pattern)
            else:
                regions = find_all(self.view, pattern, within=select_region)

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将URL中的NGA域名精简成/
                if "link" in scopes[-1]:
                    self.view.replace(edit, region, "/")


class MarkdownTable:
    def __init__(self, start_pos):
        self.start_pos = start_pos
        self.end_pos = -1
        self.rows = []
        self.len_cols = defaultdict(int)
        self.row = []
        self.cell = ''
        self.cur_col = 0

    @property
    def n_cols(self):
        return max(self.len_cols.keys())

    @property
    def region(self):
        return sublime.Region(self.start_pos, self.end_pos) if self.end_pos != -1 else None

    def new_row(self):
        self.row = []
        self.cur_col = 0

    def new_col(self):
        self.new_cell()
        self.cur_col += 1

    def new_cell(self):
        self.cell = ''

    def update_row(self):
        self.rows.append(self.row)

    def update_col(self):
        self.cell = self.cell.replace('\n', '<br>')
        self.row.append(self.cell)
        self.len_cols[self.cur_col] = max(self.len_cols[self.cur_col], len(self.cell.encode('gbk')))

    def update_cell(self, s):
        self.cell += s

    def build(self, end_pos):
        self.end_pos = end_pos
        filled_rows = []

        for row in self.rows:
            # 填充缺少的列
            row += [''] * (self.n_cols - len(row))
            # 填充单元格, 使得每个单元格长度一样 (中文占占两字节, 需要手动处理)
            row = ['{:<{:}}'.format(cell, self.len_cols[i + 1] - len(cell.encode('gbk')) + len(cell)) for i, cell in enumerate(row)]
            # 转为字符串
            filled_rows.append('| ' + ' | '.join(row) + ' |')

        split_row = '| ' + ' | '.join([':' + '-' * (self.len_cols[i + 1] - 1) for i in range(self.n_cols)]) + ' |'
        filled_rows.insert(1, split_row)

        # 转为字符串
        table = '\n' + '\n'.join(filled_rows) + '\n'
        return table


class ToggleMarkdownTableCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not self.view.match_selector(0, "source.bbcode.nga"):
            return

        for select_region in self.view.sel():
            start = select_region.begin()
            cur_col = 0
            row = []
            cell = ''
            url = None
            len_cols = defaultdict(int)
            md_table = None
            replaces = []
            
            content = self.view.substr(select_region)
            tag_stack = []
            pattern = re.compile("\[(/)?([^=\[\] \d]+|\*)(\d+| [^\[\]]+|=[^\]]+)?\]")
            for match in pattern.finditer(content):
                is_end, tag, suffix = match.groups()

                pos = start + match.start()
                end_pos = pos + len(match.group())
                region = sublime.Region(pos, end_pos)
                
                scopes = self.view.scope_name(pos).split()
                if "tag.bbcode.nga" not in scopes[-1]:
                    continue

                # 跳过表格外部区域
                if not is_end and tag != 'table' and not md_table:
                    continue
                
                # 跳过不支持转换的BBCode
                if tag not in ['table', 'tr', 'td', 'b', 'i', 'del', 'code', 'url', 'img']:
                    if md_table:
                        md_table.update_cell(self.view.substr(sublime.Region(last_pos, pos)))
                    last_pos = end_pos
                    continue

                if not is_end:
                    # 开头tag
                    if tag == 'table':
                        if md_table:
                            self.view.show_popup('不支持嵌套表格')
                            break
                        # 表格初始化
                        md_table = MarkdownTable(pos)
                    elif tag == 'tr':
                        md_table.new_row()
                    elif tag == 'td':
                        md_table.new_col()
                    elif tag == 'url' and suffix:
                        url = suffix[1:]
                    tag_stack.append(tag)
                else:
                    # 结尾tag
                    if not tag_stack:
                        continue
                    start_tag = tag_stack.pop()
                    if start_tag == tag:
                        if tag == 'table':
                            # 生成markdown格式的表格
                            replace_str = md_table.build(end_pos=end_pos)
                            replaces.append((replace_str, md_table.region))
                            md_table = None
                        elif tag == 'tr':
                            md_table.update_row()
                        elif tag == 'td':
                            print(self.view.substr(sublime.Region(last_pos, pos)))
                            md_table.update_cell(self.view.substr(sublime.Region(last_pos, pos)))
                            md_table.update_col()
                        elif tag == 'url':
                            if url:
                                caption = self.view.substr(sublime.Region(last_pos, pos))
                                md_table.update_cell('[{}]({})'.format(caption, url))
                            else:
                                url = self.view.substr(sublime.Region(last_pos, pos))
                                md_table.update_cell('{}'.format(url))
                            url = None
                        elif tag == 'img':
                            img_url = __NGA_IMAGE_HOSTING__ + self.view.substr(sublime.Region(last_pos, pos))[1:]
                            md_table.update_cell('![IMG]({})'.format(img_url))
                        else:
                            md_table.update_cell(__BBCODE2MARKDOWN__[tag] + self.view.substr(sublime.Region(last_pos, pos)) + __BBCODE2MARKDOWN__[tag])
                    else:
                        self.view.show_popup('检测到未闭合/不当闭合顺序代码块 ' + tag_stack[-1])
                        break

                # 跳过BBCode tag
                last_pos = end_pos

            for replace_str, replace_region in reversed(replaces):
                self.view.replace(edit, replace_region, replace_str)