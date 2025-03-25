import sublime
import sublime_plugin


def toggle(view, edit, code_name):
    if not view.match_selector(0, "source.bbs_nga"):
        return

    start_code = "[" + code_name + "]"
    end_code = "[/" + code_name + "]"

    selections = view.sel()
    new_selections = []
    
    for region in selections:
        bias = 0
        start_check, end_check = region.begin() - len(start_code), region.end() + len(end_code)

        # 检查所选区域前后是否存在代码块
        exist_start = view.substr(sublime.Region(start_check, region.begin())) == start_code
        exist_end = view.substr(sublime.Region(region.end(), end_check)) == end_code

        if exist_start and exist_end:
            # 删除代码块
            view.erase(edit, sublime.Region(region.end(), end_check))
            view.erase(edit, sublime.Region(start_check, region.begin()))
            bias = -len(start_code)
        else:
            # 添加代码块
            view.insert(edit, region.end(), end_code)
            view.insert(edit, region.begin(), start_code)
            bias = len(start_code)

        new_selections.append(sublime.Region(region.a + bias, region.b + bias))

    selections.clear()
    for selection in new_selections:
        selections.add(selection)


class ToggleBoldCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "b")


class ToggleUnderlineCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "u")


class ToggleItalicCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        toggle(self.view, edit, "i")


class DecodeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for select_region in self.view.sel():
            # 捕获所选区域的所有'['和'[/'
            if sublime.version() >= "4181":
                regions = self.view.find_all("\[|/\[", within=select_region)
            else:
                regions = self.view.find_all("\[|/\[")
                regions = [region for region in regions if region.a >= select_region.begin() and region.b <= select_region.end()]

            for region in reversed(regions):
                scopes = self.view.scope_name(region.a).split()
                # 将代码块的[code_name]和[/code_name]变为[[size=100%][/size]code_name]和[[size=100%][/size]/code_name]
                if scopes[-1] in ["keyword.control", "punctuation.definition.keyword", "variable.function", "variable.parameter"]:
                    self.view.insert(edit, region.a + 1, "[size=100%][/size]")


class CreateTableCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for select_region in self.view.sel():
            try:
                n_rows, n_cols = map(int, self.view.substr(select_region).split())
            except:
                continue
                
            if n_rows < 1 or n_cols < 1 or n_cols > 50:
                self.view.replace(edit, select_region, "__请[行数>0][0<列数<=20]__")
                continue

            table = "[table]\n"
            for i in range(n_rows):
                table += "[tr]"
                for j in range(n_cols):
                    table += "[td]" + "{}_{}".format(i + 1, j + 1) + "[/td]"
                table += "[/tr]\n"
            table += "[/table]"

            self.view.replace(edit, select_region, table)