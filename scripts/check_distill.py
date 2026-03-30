with open('src/app/__init__.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines[980:1015], start=981):
    print(f"{i}: {line}", end="")
