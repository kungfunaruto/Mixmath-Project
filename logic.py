import re

def safe_eval(expr):
    try:
        return eval(expr)
    except Exception:
        return None

def is_valid_expression(expr):
    """
    ตรวจสอบว่าเป็นสมการเลขธรรมดา ไม่มี //, **, %, ตัวหนังสือ, หรือ double operator เช่น ++, --, **, //
    """
    # ห้ามตัวอักษร
    if re.search(r"[A-Za-z]", expr):
        return False
    
    # ห้าม operator ที่ไม่อนุญาต
    if "**" in expr or "//" in expr or "%" in expr:
        return False

    # ห้าม ++, --, +-*/ ผิดรูป
    if re.search(r"[+\-*/]{2,}", expr):
        return False
    
    return True

def check_equation(tokens):
    """
    รองรับเครื่องหมาย x / ÷ และ '=' หลายตัว เช่น:
    1 + 1 = 2 = 2
    12 x 3 = 36 = 36
    """
    # รวมเป็นสตริง
    expr = "".join(tokens)

    # แปลงสัญลักษณ์
    expr = expr.replace("x", "*").replace("÷", "/")

    # แยกตาม '='
    parts = expr.split("=")

    if len(parts) < 2:
        return False   # ต้องมี '=' อย่างน้อยหนึ่งตัว

    # ตรวจสอบโครงสร้างทุกพาร์ทก่อน
    for p in parts:
        if not is_valid_expression(p):
            return False

    # เริ่มประเมินค่าพาร์ทแรก
    first_val = safe_eval(parts[0])
    if first_val is None:
        return False

    # เทียบค่าต่อกัน
    for p in parts[1:]:
        val = safe_eval(p)
        if val is None:
            return False
        if val != first_val:
            return False

    return True