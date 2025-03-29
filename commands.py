import sublime
import sublime_plugin
 

__NGA_DOMAIN__ = "(" + "|".join(["bbs.nga.cn", "ngabbs.com", "nga.178.com"]) + ")"


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
