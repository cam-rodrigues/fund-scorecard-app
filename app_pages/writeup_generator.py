import pdfplumber
import re
from jinja2 import Template
from pathlib import Path

# Load and clean PDF text
def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Basic performance metric extractor
def extract_metrics(text, fund_name):
    pattern = rf"{re.escape(fund_name)}.*?(-?\d+\.\d+)[^\d-]+(-?\d+\.\d+)[^\d-]+(-?\d+\.\d+)[^\d-]+(-?\d+\.\d+)[^\d-]+(-?\d+\.\d+)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return {
            "qtd": match.group(1),
            "1yr": match.group(2),
            "3yr": match.group(3),
            "5yr": match.group(4),
            "10yr": match.group(5)
        }
    return {}

# Fill writeup using Jinja2 template
def generate_writeup(metrics, fund_name, manager="N/A", peer_rank="N/A", rec="Hold"):
    template = Template("""
### Fund Review: {{ fund_name }}

**Performance Overview**
- QTD: {{ metrics.qtd }}%
- 1 Year: {{ metrics.1yr }}%
- 3 Year: {{ metrics.3yr }}%
- 5 Year: {{ metrics.5yr }}%
- 10 Year: {{ metrics.10yr }}%

**Management and Strategy**
{{ fund_name }} is currently managed by {{ manager }}. It ranks {{ peer_rank }} relative to its peers. 

**Recommendation**
Action: {{ rec }}
""")
    return template.render(metrics=metrics, fund_name=fund_name, manager=manager, peer_rank=peer_rank, rec=rec)

# Example usage
pdf_text = extract_pdf_text("MPI.pdf")
fund_name = "Janus Henderson Enterprise N"
metrics = extract_metrics(pdf_text, fund_name)
writeup = generate_writeup(metrics, fund_name, manager="Brian Demain", peer_rank="Top Quartile", rec="Recommended for Consideration")
print(writeup)
