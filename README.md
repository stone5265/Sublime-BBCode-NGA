BBCode (NGA) - Sublime Text Package
=============

支持 NGA (艾泽拉斯国家地理) BBCode 语法 的 Sublime Text 插件。自动识别后缀为 `.nga` 和 `.bbsnga` 的文件。

覆盖 NGA 常用 BBCode 的**语法高亮**、**代码片段**。

## 特性

| 语法高亮                 | 代码片段                   | 快捷键 & 右键菜单          |
| :---------------------: | :-----------------------: | :-----------------------: |
| ![syntax1][syntax1_gif] | ![snippets][snippets_gif] | ![commands][commands_gif] |
| ![syntax2][syntax2_gif] |                           |                           |

- **语法高亮**
  
  - BBCode 代码块高亮提示
  
  - 包裹光标的代码块高亮提示
  
  - 未闭合的代码块警告提示

- **代码片段**
  
  - BBCode 代码块 ( 对应 tag 并双写其首字母，比如 **bb** 对应 `[b][/b]` )

  - 专楼模板 ( 前缀为 `template` )
    
    - `template_character`: 角色模块
    
    - `template_video`: 视频模块
    
    - `template_episode_preview`: 先行情报模块
    
    - `template_overall`: 整体模块

- **快捷键**
  
  - **ctrl+b**: 在选中区域两侧 添加/去除 `[b][/b]`
  
  - **ctrl+i**: 在选中区域两侧 添加/去除 `[i][/i]`
  
  - **ctrl+u**: 在选中区域两侧 添加/去除 `[u][/u]`
  
  - **ctrl+q**: 在选中区域两侧 添加/去除 `[quote][/quote]`

- **右键菜单**
  
  - **BBCode转纯文本**: 使选中区域内 BBCode 失去效果, 显示为纯文本
    
    <details>
    <summary>示例</summary>
    
    ```
        (转换前) [b]加粗[/b] [i]斜体[/i]
        (转换后) [[size=0%][/size]b]加粗[[size=0%][/size]/b] [[size=0%][/size]i]斜体[[size=0%][/size]/i]
    ```
    
    </details>

  - **url精简**: 精简选中区域中的url代码块中的NGA域名和B站链接
    
    <details>
    <summary>示例-NGA域名</summary>
    
    ```
    (1:转换前) [url]https://bbs.nga.cn/read.php?tid=43417488[/url]
    (1:转换后) [url]/read.php?tid=43417488[/url]
    ```
    ```
    (2:转换前) [url=https://ngabbs.com/thread.php?fid=-447601]猴区[/url]
    (2:转换后) [url=/thread.php?fid=-447601]猴区[/url]
    ```
    
    </details>

    <details>
    <summary>示例-B站链接</summary>
    
    ```
    (转换前) [url=https://www.bilibili.com/bangumi/play/ep1642068?season_id=90684&season_type=1&aid=114424941643282&season_cover=https%3A%2F%2Fi0.hdslb.com%2Fbfs%2Fbangumi%2Fimage%2F2f5946880c07914d1cccd112702884f232b647e0.png&title=7&long_title=%E9%9E%A0%E8%BA%AC%E8%A6%81%E6%B7%B1%20%E5%BF%97%E5%90%91%E8%A6%81%E9%AB%98&player_width=1920&player_height=1080&player_rotate=0&ep_status=13&is_preview=0&spm_id_from=333.1365.list.card_pgc.click]末日后酒店EP7[/url]
    (转换后) [url=https://www.bilibili.com/bangumi/play/ep1642068]末日后酒店EP7[/url]
    ```

    </details>

  - **img转占位符**: 将选中区域中的img代码块替换为"\__图__"
    
    <details>
    <summary>示例</summary>

    ```
    (转换前) [quote][img]./mon_202505/22/-9lddQ1aa-axbtK2aT1kSac-ac.png[/img][/quote]
    (转换后) [quote]__图__[/quote]
    ```

    </details>

  - **table转Markdown格式**: 将选中区域中的table代码块转换为Markdown格式, 仅支持基础表格 (加粗/斜体/删除线/代码/url/补全NGA图床图片的完整URL)
    
    <details>
    <summary>示例</summary>

    ```
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
    ```

    </details>

## 安装

- (推荐)**使用 [Package Control](https://packagecontrol.io/installation#Manual)** : 搜索 `BBCode (NGA)`

- **不使用Git** : 从 [GitHub](https://github.com/stone5265/Sublime-BBCode-NGA) 下载最新的源码，将整个文件夹（若是打包下载，则将解压出来的文件夹重命名为`BBCode (NGA)`，不要保留如`-master/-vX.X`的后缀，以支持覆盖更新）复制到 Packages 目录下

- **使用Git** : 在 Packages 目录下克隆仓库：

      git clone git://github.com/stone5265/Sublime-BBCode-NGA.git

  Packages 目录在不同电脑位于不同位置，可以通过以下操作找到该目录：

      Preferences -> Browse Packages (Sublime Text 菜单)

  ![access_packages](https://raw.githubusercontent.com/stone5265/Sublime-BBCode-NGA/refs/heads/master/figs/access_packages.jpg)


[commands_gif]: https://raw.githubusercontent.com/stone5265/Sublime-BBCode-NGA/refs/heads/master/figs/commands.gif
[snippets_gif]: https://raw.githubusercontent.com/stone5265/Sublime-BBCode-NGA/refs/heads/master/figs/snippets.gif
[syntax2_gif]: https://raw.githubusercontent.com/stone5265/Sublime-BBCode-NGA/refs/heads/master/figs/syntax_error.gif
[syntax1_gif]: https://raw.githubusercontent.com/stone5265/Sublime-BBCode-NGA/refs/heads/master/figs/syntax_surroundings.gif