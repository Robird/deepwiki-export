# deepwiki-export

`deepwiki-export` 是一个命令行工具，用于从 DeepWiki 或 GitHub URL 下载内容并将其处理为 Markdown 文件。GitHub URL 会被自动转换为相应的 DeepWiki URL。

## 功能

- 从 DeepWiki/GitHub 页面提取主要内容。
- 将提取的内容保存为结构化的 Markdown 文件。
- 支持保留原始下载的 HTML 文件。
- 可自定义 Markdown 块之间的分隔符。
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
python -m deepwiki_export.cli_tool [OPTIONS] URL [OUTPUT_PATH]
```
或者，如果通过 pip 安装并已添加到 PATH：
```bash
deepwiki-export [OPTIONS] URL [OUTPUT_PATH]
```

### 参数

-   `URL`: (必需) 要处理的 GitHub 或 DeepWiki URL。
-   `OUTPUT_PATH`: (可选) 输出路径。可以是文件或目录。如果为目录，则文件名从 URL 派生。如果未提供，则保存到当前目录，文件名从 URL 派生。

### 选项

| 选项                       | 缩写 | 描述                                                                                                                               | 默认值        |
| -------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `--keep-html`              |      | 保存原始下载的 HTML 文件。                                                                                                           | `False`       |
| `--html-output PATH_OR_DIR`|      | 原始 HTML 的输出路径或目录。仅在设置了 `--keep-html` 时使用。                                                                             | `None`        |
| `--separator STRING`       | `--sep`| Markdown 块的分隔符。使用 `\n` 表示换行。                                                                                             | `\n---\n`     |
| `--html-encoding ENCODING` |      | 下载的 HTML 内容的编码。                                                                                                             | `utf-8`       |
| `--md-encoding ENCODING`   |      | 输出 Markdown 文件的编码。如果未设置，则默认为 HTML 编码。                                                                                 | `None`        |
| `--user-agent STRING`      |      | HTTP 请求的自定义 User-Agent 字符串。覆盖默认值。                                                                                        | `None`        |
| `--timeout SECONDS`        |      | HTTP 请求超时（秒）。                                                                                                                | `30`          |
| `--version`                |      | 显示应用程序版本并退出。                                                                                                             |               |
| `--verbose`                | `-v` | 启用详细输出 (DEBUG 级别日志记录)。                                                                                                    | `False`       |
| `--help`                   | `-h` | 显示帮助信息并退出。                                                                                                               |               |

## 示例

假设您要从 Roo Code 项目的某个 DeepWiki 页面导出内容：

```bash
deepwiki-export "https://deepwiki.com/RooVetGit/Roo-Code/some-page" --output_path "output/Roo-Code-some-page.md" --keep-html
```

这将：
- 从指定的 DeepWiki URL 下载内容。
- 将提取的 Markdown 保存到 `output/Roo-Code-some-page.md`。
- 同时保存原始 HTML 文件（路径将根据 Markdown 输出路径派生，例如 `output/Roo-Code-some-page_original.html`）。

## 贡献

欢迎提出问题、错误报告和功能请求。

## 许可证

本项目根据 [MIT 许可证](LICENSE) 授权。