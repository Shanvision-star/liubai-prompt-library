# Liubai · Prompt Library

[简体中文](README.md) | **English**

Liubai is a local-first tool for collecting, finding, reading and reusing prompts. It keeps original text, adaptations, sources and analysis separate so that changes remain traceable. Browsing, saving, copying and backups do not require a model account; AI-assisted analysis uses your own client and provider.

Liubai 0.8.0 includes a Chinese and English interface and Windows setup wizard. All 252 items in the bundled collection can be read in English, using either the original or a separate translation linked to the source text.

[Download for Windows](https://github.com/Shanvision-star/liubai-prompt-library/releases/latest) · [Chinese user guide](docs/USER-GUIDE.md) · [Integrations](docs/INTEGRATIONS.md) · [Report an issue](https://github.com/Shanvision-star/liubai-prompt-library/issues)

## Install and run

On Windows 10/11 x64, download the installer from Releases and open **Liubai** or **留白** from the Start menu. The installed app includes its runtime and runs without a separate Python, Node.js or database installation. Application files are stored in `%LOCALAPPDATA%\Programs\Liubai`. Your library is stored separately in `%LOCALAPPDATA%\Liubai\library`. The current download is unsigned.

For source use on Windows, macOS or Linux, install Python 3.11 or later and run:

```sh
git clone https://github.com/Shanvision-star/liubai-prompt-library.git
cd liubai-prompt-library
python -X utf8 start.py
```

Use `python3` when appropriate. The local service listens on loopback. To use a separate data directory, run `python -X utf8 start.py --data-root /absolute/path/to/my-library --port 8767`. Add `--with-collection` to include the bundled collection in a new directory. Existing libraries keep their content and versions.

## Language and feedback

Open the **•••** menu to select **English**, **中文**, or **Automatic**. A manual selection is saved locally. Language selection requires no IP lookup. In English mode, the English reading appears first when available and matched to the original. Expand the folded reading section for the other language. The original and the translation have separate copy controls.

The same menu opens **Feedback**. Email opens your mail app. GitHub Issues are public and may require signing in.

## Save, organize and reuse

Create an item by pasting a prompt or importing a UTF-8 `.md` or `.txt` file. Choose a category and optionally add tags, source details and an adaptation. Liubai checks the exact original text to identify duplicates. Edit the category or add an adaptation version without losing the original and previous versions.

Open the in-app guide for backup and setup instructions. Liubai exposes a local REST API and eight MCP tools for compatible clients such as Codex and Claude Code. Copy the command for your actual installation and library path from the guide. For a model-assisted analysis, select the material you want to share with your configured client. [Integration instructions](docs/INTEGRATIONS.md)

## Data, sources and backup

Originals and translations are distinct. Translations are associated with the source text; missing or mismatched material must not be treated as verified. The primary original-copy action copies the original. Some sources contain only excerpts or an index rather than the full original. Check each source and licence before reuse; see [collection scope and licences](bundled-library/README.md).

To add a GitHub source, open **References**, choose **Add source**, enter a supported repository or file URL and select a category. A repository may first present a list of files to choose from. Import checks source identity and exact content hashes. A second source for matching content can be retained as an alternate. If a file's licence does not clearly permit copying, Liubai may retain only its link and metadata. Failed fetches show an error. The import form accepts supported GitHub links.

Export a backup from the in-app guide before upgrading. Extract the ZIP to a new, empty folder and follow its bilingual `RESTORE.txt`. For a Windows installation, run `.\Liubai.exe --data-root "C:\path\to\restored-library"` from the installation directory. From source, run `python -X utf8 start.py --data-root /path/to/restored-library`. Check your entries, versions and favorites in the restored copy before using it. Keep backups secure because they may contain personal material. The ZIP excludes the program, API tokens and machine schedules.

Basic local use does not upload your library or call a model. GitHub search and source checks use the network. When you ask your own AI client to process material, that client's and provider's policies apply. See the [integration guide](docs/INTEGRATIONS.md) for configuration.

## Development and licence

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest desktop/tests tests -q
node --test "desktop/tests/*.test.js"
```

The application code is [MIT licensed](LICENSE). Source prompts and reference materials retain their own licences; inclusion does not make them MIT licensed. Please report issues through GitHub or email rome@chatpaperhub.com. GitHub issues are public.
