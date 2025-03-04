#!/usr/bin/env python
import os
import re
import requests
import pypandoc

# ----- Dependency Check -----

def check_dependencies(download_pandoc_flag):
    """
    Check if Pandoc is available. If not, and if download_pandoc_flag is True,
    download it automatically.
    """
    try:
        pandoc_path = pypandoc.get_pandoc_path()
        print(f"Pandoc is installed at: {pandoc_path}")
    except OSError:
        print("Pandoc was not found.")
        if download_pandoc_flag:
            print("Downloading Pandoc now...")
            pypandoc.download_pandoc()
            try:
                pandoc_path = pypandoc.get_pandoc_path()
                print(f"Pandoc successfully downloaded at: {pandoc_path}")
            except OSError as e:
                print("Error: Pandoc could not be downloaded. Please install it manually.")
                exit(1)
        else:
            print("Please install Pandoc or run the script with download enabled.")
            exit(1)

# ----- Utility Functions -----

def upload_to_imgur(image_path, client_id):
    """Uploads an image to Imgur and returns its public URL."""
    headers = {"Authorization": f"Client-ID {client_id}"}
    with open(image_path, "rb") as img:
        response = requests.post("https://api.imgur.com/3/upload", headers=headers, files={"image": img})
    if response.status_code == 200:
        return response.json()["data"]["link"]
    else:
        print(f"Failed to upload {image_path}: {response.json()}")
        return None

def split_text_content(text, limit=2000):
    """Splits text into substrings each at most 'limit' characters long (Notion's limit)."""
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def sanitize_for_katex(expr):
    """
    Applies replacements to make LaTeX expressions KaTeX‑compatible.
    Extend these rules as necessary.
    """
    # 1. Replace \mathrm{\x} with \times
    expr = expr.replace(r'\mathrm{\x}', r'\times')
    expr = expr.replace(r'\x', r'\times')
    # 2. Replace accidental \dot{,} with a comma
    expr = expr.replace(r'\dot{,}', ',')
    # 3. Replace \;x\; with \times (with trailing space)
    expr = expr.replace(r'\;x\;', r'\times ')
    # 4. Ensure \mid has a space if merged with letters
    expr = re.sub(r'(\\mid)([A-Za-z])', r'\1 \2', expr)
    # 5. Replace any raw vertical bar with \mid (if not already escaped)
    expr = re.sub(r'(?<!\\)\|', r'\\mid ', expr)
    return expr

def convert_division(expr):
    """
    If the expression contains an equals sign and a division operator (marked by \mid)
    at the right-hand side, converts that part into a fraction.
    For example:
       A = B \mid C  becomes  A = \frac{B}{C}
    (Assumes the last occurrence of "\mid" in the part after "=" represents division.)
    """
    if '=' in expr:
        lhs, rhs = expr.split('=', 1)
        idx = rhs.rfind(r'\mid')
        if idx != -1:
            numerator = rhs[:idx].strip()
            denominator = rhs[idx+len(r'\mid'):].strip()
            rhs_new = r'\frac{' + numerator + '}{' + denominator + '}'
            expr = lhs.strip() + ' = ' + rhs_new
    return expr

def convert_math_expression(math_expr):
    """
    Converts a Markdown math expression to LaTeX (using pypandoc) and sanitizes it for KaTeX.
    For complex environments (e.g. containing \begin{array}), bypass conversion and division handling.
    """
    if r'\begin{array}' in math_expr:
        return sanitize_for_katex(math_expr)
    try:
        wrapped = f"${math_expr}$"
        converted = pypandoc.convert_text(wrapped, 'latex', format='md')
        converted = converted.strip()
        if converted.startswith("\\(") and converted.endswith("\\)"):
            converted = converted[2:-2].strip()
        elif converted.startswith("$") and converted.endswith("$"):
            converted = converted[1:-1].strip()
        converted = sanitize_for_katex(converted)
        converted = convert_division(converted)
        return converted
    except Exception as e:
        print("pypandoc conversion error:", e)
        return convert_division(sanitize_for_katex(math_expr))

def parse_paragraph(text):
    """
    Finds inline math expressions (wrapped in single $ delimiters) in the paragraph,
    converts them to KaTeX‑friendly LaTeX, and splits large text.
    Returns a list of Notion rich_text objects.
    """
    inline_eq_pattern = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')
    rich_texts = []
    last_end = 0
    for match in inline_eq_pattern.finditer(text):
        pre_text = text[last_end:match.start()]
        if pre_text:
            for chunk in split_text_content(pre_text):
                rich_texts.append({"type": "text", "text": {"content": chunk}})
        raw_expr = match.group(1).strip()
        converted_expr = convert_math_expression(raw_expr)
        rich_texts.append({"type": "equation", "equation": {"expression": converted_expr}})
        last_end = match.end()
    remaining = text[last_end:]
    if remaining:
        for chunk in split_text_content(remaining):
            rich_texts.append({"type": "text", "text": {"content": chunk}})
    return rich_texts

def markdown_to_notion_blocks(md_text, image_folder, imgur_client_id):
    """
    Converts Markdown into Notion API‑compatible blocks.
    Processes block‑level math (wrapped in $$...$$) and inline math ($...$) so that math is KaTeX‑friendly.
    Also uploads images found in the Markdown to Imgur.
    """
    blocks = []
    segments = md_text.split("\n\n")
    block_eq_pattern = re.compile(r'^\s*\$\$(.*?)\$\$\s*$', re.DOTALL)
    image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        block_eq_match = block_eq_pattern.match(segment)
        if block_eq_match:
            raw_expr = block_eq_match.group(1).strip()
            converted_expr = convert_math_expression(raw_expr)
            blocks.append({"object": "block", "type": "equation", "equation": {"expression": converted_expr}})
            continue
        last_end = 0
        for match in image_pattern.finditer(segment):
            pre_text = segment[last_end:match.start()].strip()
            if pre_text:
                rich_texts = parse_paragraph(pre_text)
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_texts}})
            alt_text = match.group(1)
            img_path = match.group(2)
            full_img_path = os.path.join(image_folder, os.path.basename(img_path))
            img_url = upload_to_imgur(full_img_path, imgur_client_id)
            if img_url:
                blocks.append({"object": "block", "type": "image", "image": {"type": "external", "external": {"url": img_url}}})
            else:
                blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"[Image upload failed: {img_path}]"}}]}})
            last_end = match.end()
        post_text = segment[last_end:].strip()
        if post_text:
            rich_texts = parse_paragraph(post_text)
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_texts}})
    return blocks

def upload_markdown_to_notion(md_file, notion_api_key, parent_id, parent_type, image_folder, imgur_client_id):
    """
    Reads a Markdown file, converts it to Notion blocks (with KaTeX‑friendly math),
    and creates a new page in Notion.
    
    parent_type must be either "database" or "page":
      - For "database", parent_id is the Notion Database ID.
      - For "page", parent_id is the parent Notion Page ID.
    """
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    try:
        with open(md_file, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading Markdown file: {e}")
        return

    notion_blocks = markdown_to_notion_blocks(content, image_folder, imgur_client_id)

    if parent_type == "database":
        parent = {"database_id": parent_id}
        title = "Uploaded Markdown"
    elif parent_type == "page":
        parent = {"page_id": parent_id}
        title = "Uploaded Markdown Page"
    else:
        print("Invalid parent type. Must be 'database' or 'page'.")
        return

    data = {
        "parent": parent,
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        "children": notion_blocks[:100]
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    if response.status_code == 200:
        print("✅ Markdown uploaded successfully as a new Notion page.")
        new_page_id = response.json().get("id")
        # Append any remaining blocks in chunks of 100.
        if len(notion_blocks) > 100:
            for i in range(1, (len(notion_blocks) // 100) + 1):
                chunk = notion_blocks[i*100 : (i+1)*100]
                chunk_data = {"children": chunk}
                response = requests.patch(f"https://api.notion.com/v1/blocks/{new_page_id}/children",
                                          headers=headers, json=chunk_data)
                if response.status_code == 200:
                    print(f"✅ Uploaded chunk {i+1}.")
                else:
                    print(f"❌ Failed to upload chunk {i+1}: {response.json()}")
                    break
    else:
        print(f"❌ Failed to create a new Notion page: {response.json()}")

# ----- Main Program -----

def main():
    print("Enter the following configuration information:")
    imgur_client_id = input("Imgur Client ID: ").strip()
    notion_api_key = input("Notion API Key: ").strip()
    parent_type = input("Upload to a 'database' or a 'page'? ").strip().lower()
    if parent_type == "database":
        parent_id = input("Notion Database ID: ").strip()
    elif parent_type == "page":
        parent_id = input("Parent Notion Page ID: ").strip()
    else:
        print("Invalid parent type. Exiting.")
        return
    md_file = input("Path to the Markdown file: ").strip()
    image_folder = input("Path to the images folder: ").strip()
    download_pandoc_flag = input("Download Pandoc if not installed? (y/n): ").strip().lower() == 'y'

    check_dependencies(download_pandoc_flag)

    upload_markdown_to_notion(md_file, notion_api_key, parent_id, parent_type, image_folder, imgur_client_id)

if __name__ == '__main__':
    main()
