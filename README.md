# Zotero CLI

Command-line tool for working with annotations and notes in Zotero database. Allows extracting annotations from PDF files and exporting them to various formats for further work.

## Features

- **Collection Extraction**: Get collections from Zotero database
- **Annotation Management**: Extract annotations and notes from PDF files
- **Multiple Export Formats**:
  - Markdown (.md)
  - Gingko format (.md)
  - XMind text format (.txt)
  - Obsidian notes
- **Color Ranking System**: Support for various Zotero annotation colors
- **Mnemonic Versions**: Generate enhanced versions with mnemonic tags
- **Search and Filtering**: Search by keys, names, and content

## Project Structure

```
ZoteroCLI/
├── db.py          # Main module for Zotero database operations
├── obs.py         # Obsidian export module
├── zg.py          # Main CLI interface
├── .gitignore     # Git ignore file
└── README.md      # Project documentation
```

## Installation

### Requirements

- Python 3.6+
- Zotero with SQLite database
- Required Python packages (install via pip):

```bash
pip install typer
```

### Setup

1. Ensure Zotero is installed and contains annotations in PDF files
2. Zotero database is typically located at:
   - Windows: `%USERPROFILE%\Zotero\zotero.sqlite`
   - macOS: `~/Zotero/zotero.sqlite`
   - Linux: `~/Zotero/zotero.sqlite`

## Usage

### Basic Commands

```bash
# Show all collections
python zg.py get-cols

# Generate collection in Markdown
python zg.py gen-col-md "Collection Name"

# Generate attachment in Markdown
python zg.py gen-attach-md "File Name"

# Generate collection in text format for XMind
python zg.py gen-col-xmind "Collection Name"

# Generate mnemonic version of collection
python zg.py gen-mnemo "Collection Name"
```

### Getting Keys

```bash
# Get collection key
python zg.py get-col-key "Collection Name"

# Get attachment key
python zg.py get-attach-key "File Name"

# Get item key
python zg.py get-item-key "attach_key" "item name"
```

### Working with Objects

```bash
# Get object tree
python zg.py get-obj-tree "key" 3

# Get object tree with tag filter
python zg.py get-obj-tree-tag "key" 3 "tag"
```

### Export to Obsidian

```python
# Using obs.py module
from obs import gen_obs

# Generate Obsidian notes for a book
gen_obs("Book Name")
```

## Annotation Color Rankings

The tool supports Zotero's standard color system:

1. **Yellow** (#ffd400) - Rank 1
2. **Red** (#ff6666) - Rank 2  
3. **Green** (#5fb236) - Rank 3
4. **Blue** (#2ea8e5) - Rank 4
5. **Purple** (#a28ae5) - Rank 5
6. **Pink** (#e56eee) - Rank 6
7. **Orange** (#f19837) - Rank 7
8. **Gray** (#aaaaaa) - Rank 8

## Export Formats

### Markdown Format
Structured Markdown with headings, Zotero links, and tags.

### Gingko Format
Export in Gingko Card format with HTML-like markup.

### XMind Text Format
Hierarchical text format for import into XMind.

### Obsidian Notes
Create separate .md files for each item with YAML frontmatter.

## Usage Examples

### Export Collection to Markdown
```bash
python zg.py gen-col-md "Research Papers"
```

### Create Mnemonic Version
```bash
python zg.py gen-mnemo "Machine Learning"
```

### Generate for XMind
```bash
python zg.py gen-col-xmind "Data Science" --lvl-limit 5
```

## Path Configuration

In `obs.py` you can configure the Obsidian directory:
```python
dir_obs = 'C:\\Users\\mholo\\WD\\Obsidian\\ENGLISH\\Inbox'
```

In `zg.py` the save path is configured:
```python
file_path = str(Path.home()) + os.sep + 'WD\\Gingko\\Mnemo'
```

## Database Operations

The tool works directly with Zotero's SQLite database, extracting:
- Collections (`collections`)
- Collection items (`collectionItems`) 
- Attachments (`itemAttachments`)
- Annotations (`itemAnnotations`)
- Tags (`itemTags`, `tags`)

## Additional Features

- **Item Unlocking**: `unlock-items` command to remove restrictions on imported items
- **Content Search**: Functions to search annotation text
- **Hierarchical Structure**: Support for nested collections and items
- **Sorting**: Automatic sorting by page number and position

## Contributing

The project is open for improvements and additions. Main development areas:
- Support for additional export formats
- User interface improvements
- Adding filters and search
- Integration with other knowledge management tools

## License

This project was created for personal use with Zotero tools and can be adapted to your needs.