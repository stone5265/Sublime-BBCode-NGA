import sublime
import sublime_plugin
import re
from .utils import *


NGA_DOMAIN = '(' + '|'.join(['bbs.nga.cn', 'ngabbs.com', 'nga.178.com']) + ')'


class ToggleBoldCommand(sublime_plugin.TextCommand):
    '''
    在选中区域两侧 添加/去除 [b][/b]
    '''
    def run(self, edit):
        toggle(self.view, edit, 'b')


class ToggleUnderlineCommand(sublime_plugin.TextCommand):
    '''
    在选中区域两侧 添加/去除 [u][/u]
    '''
    def run(self, edit):
        toggle(self.view, edit, 'u')


class ToggleItalicCommand(sublime_plugin.TextCommand):
    '''
    在选中区域两侧 添加/去除 [i][/i]
    '''
    def run(self, edit):
        toggle(self.view, edit, 'i')


class ToggleQuoteCommand(sublime_plugin.TextCommand):
    '''
    在选中区域两侧 添加/去除 [quote][/quote]
    '''
    def run(self, edit):
        toggle(self.view, edit, 'quote')


class DecodeCommand(sublime_plugin.TextCommand):
    '''BBCode转纯文本: 使选中区域内 BBCode 失去效果, 显示为纯文本

    示例
    ----
    (转换前) [b]加粗[/b] [i]斜体[/i]
    (转换后) [[size=0%][/size]b]加粗[[size=0%][/size]/b] [[size=0%][/size]i]斜体[[size=0%][/size]/i]
    '''
    def run(self, edit):
        pattern = '\['

        for select_region in self.view.sel():
            # 捕获所选区域的所有'[' (若没选中内容, 则默认对全文进行操作)
            if len(self.view.sel()) == 1 and select_region.empty():
                regions = find_all(self.view, pattern)
            else:
                regions = find_all(self.view, pattern, within=select_region)

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将"[tag]...[/tag]"变为"[[size=0%][/size]tag]...[[size=0%][/size]/tag]"
                if 'tag.bbcode.nga' in scopes[-1]:
                    self.view.insert(edit, region.a + 1, '[size=0%][/size]')

    def is_visible(self):
        return self.view.match_selector(0, 'source.bbcode.nga')


class CondenseUrlCommand(sublime_plugin.TextCommand):
    '''url精简: 精简选中区域中的url代码块中的NGA域名和B站链接

    示例-NGA域名
    ----
    (1:转换前) [url]https://bbs.nga.cn/read.php?tid=43417488[/url]
    (1:转换后) [url]/read.php?tid=43417488[/url]
    (2:转换前) [url=https://ngabbs.com/thread.php?fid=-447601]猴区[/url]
    (2:转换后) [url=/thread.php?fid=-447601]猴区[/url]

    示例-B站链接
    ----
    (转换前) [url=https://www.bilibili.com/bangumi/play/ep1642068?season_id=90684&season_type=1&aid=114424941643282&season_cover=https%3A%2F%2Fi0.hdslb.com%2Fbfs%2Fbangumi%2Fimage%2F2f5946880c07914d1cccd112702884f232b647e0.png&title=7&long_title=%E9%9E%A0%E8%BA%AC%E8%A6%81%E6%B7%B1%20%E5%BF%97%E5%90%91%E8%A6%81%E9%AB%98&player_width=1920&player_height=1080&player_rotate=0&ep_status=13&is_preview=0&spm_id_from=333.1365.list.card_pgc.click]末日后酒店EP7[/url]
    (转换后) [url=https://www.bilibili.com/bangumi/play/ep1642068]末日后酒店EP7[/url]
    '''
    def run(self, edit):
        pattern = '(https://)?(' + NGA_DOMAIN + '/)|(www.bilibili.com/[^\[\]\s]+)'

        for select_region in self.view.sel():
            # 捕获所选区域的所有NGA域名/B站链接 (若没选中内容, 则默认对全文进行操作)
            if len(self.view.sel()) == 1 and select_region.empty():
                regions = find_all(self.view, pattern)
            else:
                regions = find_all(self.view, pattern, within=select_region)

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将URL中的NGA域名精简成"/", B站链接去掉"?"之后的内容
                if 'link' in scopes[-1]:
                    url = self.view.substr(region)
                    if 'bilibili' in url:
                        self.view.replace(edit, region, url.split('?')[0])
                    else:
                        self.view.replace(edit, region, '/')

    def is_visible(self):
        return self.view.match_selector(0, 'source.bbcode.nga')


class ReplaceImgCommand(sublime_plugin.TextCommand):
    '''img转占位符: 将选中区域中的img代码块替换为"__图__"

    示例
    ----
    (转换前) [quote][img]./mon_202505/22/-9lddQ1aa-axbtK2aT1kSac-ac.png[/img][/quote]
    (转换后) [quote]__图__[/quote]
    '''
    def run(self, edit):
        pattern = '\[img\](.+?)\[/img\]'

        for select_region in self.view.sel():
            # 捕获所选区域的img块 (若没选中内容, 则默认对全文进行操作)
            if len(self.view.sel()) == 1 and select_region.empty():
                regions = find_all(self.view, pattern)
            else:
                regions = find_all(self.view, pattern, within=select_region)

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将"[img]...[/img]"变为"__图__"
                if 'img.tag.bbcode.nga' in scopes[-1]:
                    self.view.replace(edit, region, '__图__')

    def is_visible(self):
        return self.view.match_selector(0, 'source.bbcode.nga')


class TableToMarkdownCommand(sublime_plugin.TextCommand):
    '''table转Markdown格式: 将选中区域中的table代码块转换为Markdown格式, 仅支持基础表格 (加粗/斜体/删除线/代码/url/补全NGA图床图片的完整URL)
    
    示例
    ----
    (转换前)
    
    [table]
    [tr][td15][b]功能[/b][/td][td35][b]展示[/b][/td][td15][b]功能[/b][/td][td35][b]展示[/b][/td][/tr]
    [tr]
    [td]加粗[/td][td][b]加粗[/b][/td]
    [td]斜体[/td][td][i]斜体[/i][/td]
    [/tr]
    [tr]
    [td]删除线[/td][td][del]删除线[/del][/td]
    [td]换行[/td][td]第一段
    第二段[/td]
    [/tr]
    [tr]
    [td]代码[/td][td][code]代码[/code][/td]
    [td]图片[/td][td][quote][img]./mon_202505/22/-9lddQ1aa-axbtK2aT1kSac-ac.png[/img][/quote][/td]
    [/tr]
    [tr]
    [td]链接1[/td][td][url]/thread.php?fid=-447601[/url][/td]
    [td]链接2[/td][td][url=/thread.php?fid=-447601]猴区[/url][/td]
    [/tr]
    [/table]
    
    (转换后)
    
    | **功能** | **展示**                                  | **功能** | **展示**                                                                                 |
    | :------- | :---------------------------------------- | :------- | :--------------------------------------------------------------------------------------- |
    | 加粗     | **加粗**                                  | 斜体     | *斜体*                                                                                   |
    | 删除线   | ~~删除线~~                                | 换行     | 第一段<br>第二段                                                                         |
    | 代码     | `代码`                                    | 图片     | ![IMG](https://img.nga.178.com/attachments/mon_202505/22/-9lddQ1aa-axbtK2aT1kSac-ac.png) |
    | 链接1    | https://bbs.nga.cn/thread.php?fid=-447601 | 链接2    | [猴区](https://bbs.nga.cn/thread.php?fid=-447601)                                        |
    
    '''
    def run(self, edit):
        for select_region in self.view.sel():
            start = select_region.begin()
            url = None
            md_table = None
            replaces = []
            
            content = self.view.substr(select_region)
            tag_stack = []
            pattern = re.compile('\[(/)?([^=\[\] \d]+|\*)(\d+| [^\[\]]+|=[^\]]+)?\]')
            for match in pattern.finditer(content):
                is_end, tag, suffix = match.groups()

                pos = start + match.start()
                end_pos = pos + len(match.group())
                
                scopes = self.view.scope_name(pos).split()
                if 'tag.bbcode.nga' not in scopes[-1]:
                    continue

                # 跳过表格外部区域
                if not md_table and tag != 'table' and not is_end:
                    continue
                
                # 跳过不支持转换的BBCode
                if tag not in ['table', 'tr', 'td', 'b', 'i', 'del', 'code', 'url', 'img']:
                    if md_table:
                        text = self.view.substr(sublime.Region(last_pos, pos))
                        md_table.update_cell(text)
                    last_pos = end_pos
                    continue

                if not is_end:
                    # 开头tag
                    if tag == 'table':
                        if md_table:
                            self.view.show_popup('不支持嵌套表格', location=pos)
                            break
                        # 表格初始化
                        md_table = MarkdownTable(pos)
                    elif tag == 'tr':
                        md_table.new_row()
                    elif tag == 'td':
                        md_table.new_col()
                    elif tag == 'url' and suffix:
                        md_table.buffer['url'] = suffix[1:]
                    tag_stack.append(tag)
                else:
                    # 结尾tag
                    if tag_stack and tag_stack.pop() == tag:
                        text = self.view.substr(sublime.Region(last_pos, pos))
                        if tag == 'table':
                            # 生成markdown格式的表格
                            replace_str = md_table.build(end_pos=end_pos)
                            replaces.append((md_table.region, replace_str))
                            md_table = None
                        else:
                            md_table.update_cell(text, tag)
                    else:
                        self.view.show_popup('检测到未闭合/不当闭合顺序代码块 ' + tag_stack[-1], location=pos)
                        break

                # 跳过BBCode tag
                last_pos = end_pos

            for replace_region, replace_str in reversed(replaces):
                self.view.replace(edit, replace_region, replace_str)

    def is_visible(self):
        return self.view.match_selector(0, 'source.bbcode.nga')