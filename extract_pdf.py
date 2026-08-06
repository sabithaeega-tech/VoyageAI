from pathlib import Path
from PyPDF2 import PdfReader

pdf = Path('Team_C_VoyageAI.pdf')
reader = PdfReader(str(pdf))
print('pages', len(reader.pages))
for i, page in enumerate(reader.pages, 1):
    text = page.extract_text() or ''
    print(f'--- PAGE {i} ---')
    print(text[:6000])
    print()
