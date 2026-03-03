import pymupdf.layout
import pymupdf4llm
doc = pymupdf.open("test_pdfs/s41598-022-16339-4.pdf")

text = pymupdf4llm.to_text(doc,header=False, footer=False)
with open("test_pdfs/s41598-022-16339-4.txt", "w") as f:
    f.write(text)