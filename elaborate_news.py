import csv
import re
from html.parser import HTMLParser
from io import StringIO
import html2text

#!/usr/bin/env python3
"""
Script to convert news.csv to news_prod.csv with transformations.
"""


# Configuration
INPUT_FILE = 'news.csv'
OUTPUT_FILE = 'news_prod.csv'
BASE_COVER_PATH = '/media/covers/'

# Category mapping dictionary - TO BE COMPLETED MANUALLY
CATEGORY_MAPPING = {
    '1': 'seminars',
    '2': 'publications',
    '3': 'press',
    '4': 'press',
    # Add more mappings as needed
}


def html_to_markdown(html_content):
    """Convert HTML content to Markdown."""
    if not html_content or html_content.strip() == '':
        return ''
    
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0  # Don't wrap text
    markdown = h.handle(html_content)
    return markdown.strip()


def get_first_sentence_or_words(text, max_words=50):
    """Extract first sentence or first max_words words from text."""
    # Remove markdown formatting for description
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove markdown links
    text = re.sub(r'[*_#`]', '', text)  # Remove markdown formatting
    text = text.strip()
    
    if not text:
        return ''
    
    # Try to find first sentence
    sentence_match = re.match(r'^([^.!?]+[.!?])', text)
    if sentence_match:
        sentence = sentence_match.group(1).strip()
        words = sentence.split()
        if len(words) <= max_words:
            return sentence
    
    # Return first max_words words
    words = text.split()[:max_words]
    return ' '.join(words) + ('...' if len(text.split()) > max_words else '')


def title_case_if_uppercase(title):
    """Convert title to title case if it's all uppercase."""
    if title.isupper():
        return title.title()
    return title


def generate_slug(title, created_at):
    """Generate slug from title and date."""
    # Extract year from title if present
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    
    if year_match:
        year = year_match.group(0)
        # Get words before the year
        words_before_year = title[:year_match.start()].strip()
        words = re.findall(r'\w+', words_before_year.lower())[:5]
    else:
        # Use year from created_at
        year = created_at.split('-')[0] if created_at else '2024'
        # Get first 5 words from title
        words = re.findall(r'\w+', title.lower())[:5]
    
    # Create slug
    slug_parts = [year] + words
    slug = '-'.join(slug_parts)
    
    return slug


def get_cover_path(id_cover):
    """Generate cover path from id_cover."""
    if not id_cover or id_cover == '0':
        return ''
    return f"{BASE_COVER_PATH}{id_cover}.jpg"


def invert_hidden_to_published(hidden):
    """Convert hidden column to is_published (inverted logic)."""
    if hidden == '0':
        return '1'
    elif hidden == '1':
        return '0'
    return '1'  # Default to published if unclear


def process_csv():
    """Main function to process the CSV file."""
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Define output columns
        output_columns = [
            'slug', 'cover', 'title', 'description', 'content', 
            'created_at', 'updated_by', 'is_published', 'category'
        ]
        
        writer = csv.DictWriter(outfile, fieldnames=output_columns)
        writer.writeheader()
        
        seen_slugs = set()
        
        for row in reader:
            # Convert HTML content to Markdown
            markdown_content = html_to_markdown(row['content'])
            
            # Generate description
            description = get_first_sentence_or_words(markdown_content)
            
            # Process title
            title = title_case_if_uppercase(row['title'])
            
            # Generate slug
            slug = generate_slug(title, row['created_at'])
            # Ensure slug uniqueness by appending a counter if needed
            unique_slug = slug
            counter = 1
            while unique_slug in seen_slugs:
                unique_slug = f"{slug}-{counter}"
                counter += 1
            seen_slugs.add(unique_slug)
            slug = unique_slug
            
            # Convert category to string using mapping
            category_id = row['id_category']
            category = CATEGORY_MAPPING.get(category_id, f'category_{category_id}')
            
            # Generate cover path
            cover = get_cover_path(row['id_cover'])
            
            # Convert hidden to is_published
            is_published = invert_hidden_to_published(row['hidden'])
            
            # Write output row
            output_row = {
                'slug': slug,
                'cover': cover,
                'title': title,
                'description': description,
                'content': markdown_content,
                'created_at': row['created_at'],
                'updated_by': row['updated_by'],
                'is_published': is_published,
                'category': category
            }
            
            writer.writerow(output_row)
    
    print(f"Conversion complete! Output saved to {OUTPUT_FILE}")
    print(f"\nRemember to update the CATEGORY_MAPPING dictionary in the script.")


if __name__ == '__main__':
    process_csv()