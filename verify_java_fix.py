import sys
import re

def get_java_filename(code):
    """
    Extracts the public class name from Java code to use as a filename.
    If no public class is found, it looks for the first class defined.
    Defaults to 'Main.java' if no class is found.
    """
    # Look for: public class [Name]
    public_class_match = re.search(r'public\s+class\s+([a-zA-Z0-9_$]+)', code)
    if public_class_match:
        return f"{public_class_match.group(1)}.java"
    
    # Fallback: Look for any class definition
    class_match = re.search(r'class\s+([a-zA-Z0-9_$]+)', code)
    if class_match:
        return f"{class_match.group(1)}.java"
        
    return "Main.java"

test_cases = [
    {
        "name": "Public Class PrintNumbers",
        "code": "public class PrintNumbers { public static void main(String[] args) {} }",
        "expected": "PrintNumbers.java"
    },
    {
        "name": "Public Class MyMain",
        "code": "public class MyMain {\n    public static void main(String[] args) {}\n}",
        "expected": "MyMain.java"
    },
    {
        "name": "No Public Class",
        "code": "class Helper { }",
        "expected": "Helper.java"
    },
    {
        "name": "Default Main",
        "code": "// just comments\n",
        "expected": "Main.java"
    }
]

print("Running tests for get_java_filename logic...")
success = True
for tc in test_cases:
    result = get_java_filename(tc["code"])
    if result == tc["expected"]:
        print(f"✅ PASS: {tc['name']} -> {result}")
    else:
        print(f"❌ FAIL: {tc['name']} -> Expected {tc['expected']}, got {result}")
        success = False

if success:
    print("\nAll internal logic tests passed!")
    sys.exit(0)
else:
    print("\nSome tests failed.")
    sys.exit(1)
