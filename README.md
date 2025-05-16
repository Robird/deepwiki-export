# deepwiki-export

`deepwiki-export` 是一个命令行工具，用于从 DeepWiki 或 GitHub URL 下载内容并将其处理为按章节组织的多个 Markdown 文件。GitHub URL 会被自动转换为相应的 DeepWiki URL。

## 功能

- 从 DeepWiki/GitHub 页面提取主要内容。
- 将提取的每个内容块（章节）保存为单独的 Markdown 文件。
- 输出文件保存在一个根据 URL 自动命名的子目录中，该子目录位于用户指定的基础输出目录下。
- 对于 GitHub URL，子目录结构为 `username/reponame/`。
- 支持保留原始下载的 HTML 文件（保存在同一子目录中）。
- 可配置请求和文件编码。

## 安装

通过 pip 从 PyPI 安装 (当发布后):
```bash
pip install deepwiki-export
```

或者从源代码本地安装 (用于开发):
```bash
pip install -e .
```

## 使用方法

```
python -m deepwiki_export.cli_tool [OPTIONS] URL
```
或者，如果通过 pip 安装并已添加到 PATH：
```bash
deepwiki-export [OPTIONS] URL
```

### 参数

-   `URL`: (必需) 要处理的 GitHub 或 DeepWiki URL。

### 选项

| 选项                          | 缩写 | 描述                                                                                                                               | 默认值        |
| ----------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `--output-base-dir DIR`       | `-o` | 基础输出目录。将在此目录下创建一个新的子目录`user_name/repo_name`来存储输出文件。                               | `.` (当前目录) |
| `--keep-html`                 |      | 保存原始下载的 HTML 文件（将保存在自动生成的输出子目录中）。                                                                                       | `False`       |
| `--html-encoding ENCODING`    |      | 下载的 HTML 内容的编码。                                                                                                             | `utf-8`       |
| `--md-encoding ENCODING`      |      | 输出 Markdown 文件的编码。如果未设置，则默认为 HTML 编码。                                                                                 | `None`        |
| `--user-agent STRING`         |      | HTTP 请求的自定义 User-Agent 字符串。覆盖默认值。                                                                                        | `None`        |
| `--timeout SECONDS`           |      | HTTP 请求超时（秒）。                                                                                                                | `30`          |
| `--version`                   |      | 显示应用程序版本并退出。                                                                                                             |               |
| `--verbose`                   | `-v` | 启用详细输出 (DEBUG 级别日志记录)。                                                                                                    | `False`       |
| `--help`                      | `-h` | 显示帮助信息并退出。                                                                                                               |               |

## 示例

假设您要从 Roo Code 项目的某个 DeepWiki 页面导出内容，并希望输出到当前目录下的 `my_exports` 基础目录中：

```bash
deepwiki-export --output-base-dir ./my_exports "https://deepwiki.com/RooVetGit/Roo-Code/some-page" --keep-html
```

这将：
- 从指定的 DeepWiki URL 下载内容。
- 在 `./my_exports/` 目录下创建一个名为 `RooVetGit_Roo-Code` (或类似，取决于 `derive_dirname_from_url` 的具体实现) 的子目录。
- 在该子目录 (`./my_exports/RooVetGit_Roo-Code/`) 内，将每个提取的章节保存为单独的 Markdown 文件 (例如 `chapter_1.md`, `chapter_2.md`, ...)。
- 同时，原始 HTML 文件 (例如 `_original_page.html`) 也会保存在这个子目录中。

## 贡献

欢迎提出问题、错误报告和功能请求。

## 许可证

本项目根据 [MIT 许可证](LICENSE) 授权。