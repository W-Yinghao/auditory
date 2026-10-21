import sys, fitz
d = fitz.open(sys.argv[1]); out = open(sys.argv[2], "w")
for i, p in enumerate(d):
    out.write(f"\n=== PAGE {i+1} ===\n" + p.get_text())
print(len(d), "pages")
