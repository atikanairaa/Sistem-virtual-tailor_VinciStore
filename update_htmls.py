import os

files = ['index.html', 'product_detail.html', 'virtual_tailor.html', 'keranjang.html']

for filename in files:
    filepath = f'backend/static/{filename}'
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    body_end_idx = -1
    
    for i, line in enumerate(lines):
        if '<header' in line and start_idx == -1:
            start_idx = i
        if '</header>' in line and end_idx == -1:
            end_idx = i
        if '</body>' in line:
            body_end_idx = i
            
    if start_idx != -1 and end_idx != -1:
        # Replace header block
        del lines[start_idx:end_idx+1]
        lines.insert(start_idx, '    <div id="navbar-container"></div>\n')
        
    # Recalculate body_end_idx since lines changed
    body_end_idx = -1
    for i, line in enumerate(lines):
        if '</body>' in line:
            body_end_idx = i
            
    if body_end_idx != -1:
        # Check if script is already there
        has_script = any('navbar.js' in l for l in lines)
        if not has_script:
            lines.insert(body_end_idx, '    <script src="/static/js/navbar.js"></script>\n')
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
print("HTML files updated!")
