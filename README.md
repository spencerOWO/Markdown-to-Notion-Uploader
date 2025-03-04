# Markdown-to-Notion-Uploader

A Python script that converts Markdown (.md) files into Notion-compatible blocks and uploads them to your Notion workspace. This tool is designed to streamline your research paper management workflow by allowing you to convert PDF files (recommend **MinerU** highly) into Markdown along with associated images, then restore them into an editable and commentable document format within Notion.

## Prerequisites
Python 3.x :Ensure you have Python installed on your system.

Pandoc :Required for converting Markdown to LaTeX. If Pandoc is not already installed, the script can download it automatically when enabled.

Notion API Key :Obtain your API key from Notion's Integration Settings. [https://developers.notion.com/docs/create-a-notion-integration]

Imgur Client ID:Notion did'nt support local image so need for  the third platform to upload images. You can register an application on Imgur to obtain this.[https://apidocs.imgur.com/]

Python Packages :Install the necessary packages using pip in terminal: `pip install requests pypandoc`

## Usage
### Prepare Your Content:
1. Convert your PDFs to Markdown using **MinerU** (or your preferred tool).
2. Organize the Markdown file and the corresponding folder containing images.
3. Run the Script: Execute the script in your terminal: `python uploadMdToNotion.py`
4. Enter the Configuration Details:
- Imgur Client ID: Your Imgur application’s Client ID.
- Notion API Key: Your Notion integration API key.
- Upload Destination: Specify whether to upload to a "database" or a "page".
- Parent ID: Provide the Notion Database ID or the Parent Notion Page ID as prompted.
- Markdown File Path: Enter the path to the Markdown file.
- Images Folder Path: Enter the path to the folder containing the images.
- Pandoc Option: Choose whether the script should download Pandoc automatically if it is not installed.
### Upload Process:
- The script converts the Markdown file into Notion blocks, processing text, math expressions, and images.
- A new Notion page (or database entry) is created, with content uploaded in chunks if it exceeds Notion’s block limits.
- Upon successful upload, you will see confirmation messages in the terminal.

## How It Works
- Markdown Parsing: 
The script splits the Markdown content into segments (paragraphs, math blocks, images) and converts each segment into a Notion block.

- Math Conversion:
Inline math expressions `($...$)` and block math expressions `($$...$$)` are processed using pypandoc to convert them into LaTeX. The conversion is enhanced with additional sanitization to ensure compatibility with KaTeX rendering in Notion.

- Image Handling:
Images in the Markdown (formatted as `![alt text](image_path)`) are uploaded to Imgur. The returned public URL is then embedded into the Notion page as an image block.

- Pandoc Dependency:
Before processing, the script checks for Pandoc. If it isn’t found and the download option is enabled, it downloads and installs Pandoc automatically.

## Tips

- How to find the Imgur API you need : [https://dubble.so/guides/how-to-get-imgur-client-id-purlxhv84a0m3mlsiak7] 
- How to find the Imgur API you need :[https://neverproductive.com/notion-api/]
- The step of sharing your databases/pages with your integration is necessary and important!
- How to find the Notion page/database ID you need: [https://neverproductive.com/database-id-notion/]
- plz pay attention to the Notion ID you need is whether page or database.

