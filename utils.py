import sublime
from collections import defaultdict


__all__ = ['toggle', 'find_all', 'MarkdownTable']

NGA_HOSTING = 'https://bbs.nga.cn'
NGA_IMAGE_HOSTING = 'https://img.nga.178.com/attachments'
BBCODE2MD = defaultdict(str)
BBCODE2MD.update({
    'b': '**',
    'i': '*',
    'del': '~~',
    'code': '`'
})


def toggle(view, edit, tag):
    '''
    在选中区域两侧 添加/去除 [tag][/tag]
    '''
    if not view.match_selector(0, 'source.bbcode.nga'):
        return

    start_tag = '[' + tag + ']'
    end_tag = '[/' + tag + ']'

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
    '''
    查找region中的所有pattern
    '''
    if within is not None:
        if sublime.version() >= '4181':
            regions = view.find_all(pattern, within=within)
        else:
            regions = view.find_all(pattern)
            regions = [region for region in regions if region.a >= select_region.begin() and region.b <= select_region.end()]
    else:
        regions = view.find_all(pattern)

    return regions


def _get_display_width(text):
    '''
    获取UTF-8编码字符串的显示宽度
    '''
    width = 0
    for char in text:
        code = ord(char)
        if (0x4E00 <= code <= 0x9FFF or  # CJK统一表意文字
            0x3040 <= code <= 0x309F or  # 平假名
            0x30A0 <= code <= 0x30FF or  # 片假名
            0xFF00 <= code <= 0xFFEF):   # 全角符号
            width += 2
        else:
            width += 1
    return width


def _fill_url(url, img=False):
    if img:
        # 若NGA图床为相对路径(默认), 则填充为完整路径
        return NGA_IMAGE_HOSTING + url[1:] if url[0] == '.' else url
    else:
        # 若url为精简过NGA域名的链接, 则填充上NGA域名
        return NGA_HOSTING + url if url[0] == '/' else url


class MarkdownTable:
    def __init__(self, start_pos):
        self.start_pos = start_pos
        self.end_pos = -1
        self.rows = []
        self.len_cols = defaultdict(int)
        self.row = []
        self.cell = ''
        self.cur_col = 0
        self.buffer = defaultdict(lambda: None)

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
        self.len_cols[self.cur_col] = max(self.len_cols[self.cur_col], _get_display_width(self.cell))

    def update_cell(self, text, tag=''):
        if tag == 'tr':
            self.update_row()
        elif tag == 'td':
            self.cell += text
            self.update_col()
        elif tag == 'url':
            # "[url]链接[/url]"变为"链接", "[url=链接]描述[/url]"变为"[描述](链接)"
            if self.buffer['url']:
                caption, url = text, _fill_url(self.buffer['url'])
                self.cell += '[{}]({})'.format(caption, url)
            else:
                url = _fill_url(text)
                self.cell += url
            self.buffer['url'] = None
        elif tag == 'img':
            img_url = _fill_url(text, img=True)
            self.cell += '![IMG]({})'.format(img_url)
        else:
            self.cell += BBCODE2MD[tag] + text + BBCODE2MD[tag]

    def build(self, end_pos):
        self.end_pos = end_pos
        filled_rows = []

        for row in self.rows:
            # 填充缺少的列
            row += [''] * (self.n_cols - len(row))
            # 填充单元格, 使得每个单元格长度一样 (中文占两个显示宽度, 需要手动处理)
            row = ['{:<{:}}'.format(cell, self.len_cols[i + 1] - _get_display_width(cell) + len(cell)) for i, cell in enumerate(row)]
            # 转为字符串
            filled_rows.append('| ' + ' | '.join(row) + ' |')

        split_row = '| ' + ' | '.join([':' + '-' * (self.len_cols[i + 1] - 1) for i in range(self.n_cols)]) + ' |'
        filled_rows.insert(1, split_row)

        # 转为字符串
        table = '\n'.join(filled_rows)
        return table