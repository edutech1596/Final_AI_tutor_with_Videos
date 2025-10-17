#!/usr/bin/env python3
"""
Security Check Script
Run this before committing to ensure no secrets are exposed
"""

import os
import re
import sys

# Patterns to check for exposed secrets
DANGEROUS_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
    (r'OPENAI_API_KEY\s*=\s*["\']sk-', 'Hardcoded OpenAI Key'),
    (r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']', 'Generic API Key'),
    (r'password\s*[:=]\s*["\'][^"\']+["\']', 'Password'),
    (r'secret\s*[:=]\s*["\'][^"\']+["\']', 'Secret'),
]

# Files to check
FILES_TO_CHECK = [
    'config.py',
    'app_optimized.py',
    'README.md',
    'SECURITY.md',
]

# Files that should NOT be committed
FORBIDDEN_FILES = [
    '.env',
    '.env.local',
    '.env.production',
]


def check_file_for_secrets(filepath):
    """Check a file for exposed secrets"""
    issues = []
    
    if not os.path.exists(filepath):
        return issues
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern, description in DANGEROUS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Skip if it's a comment or example
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                line = content[line_start:line_end if line_end != -1 else len(content)]
                
                # Skip comments, examples, and documentation
                if not ('example' in line.lower() or 
                        'your-' in line.lower() or 
                        'placeholder' in line.lower() or
                        'don\'t do this' in line.lower() or
                        'wrong' in line.lower() or
                        '1234567890' in line or
                        'sk-1234' in line or
                        line.strip().startswith('#') or
                        filepath.endswith('.md')):  # Skip markdown files
                    issues.append({
                        'file': filepath,
                        'type': description,
                        'line': line.strip()[:100]
                    })
    except Exception as e:
        print(f"⚠️  Warning: Could not check {filepath}: {e}")
    
    return issues


def check_forbidden_files():
    """Check if forbidden files exist and would be committed"""
    found = []
    for filename in FORBIDDEN_FILES:
        if os.path.exists(filename):
            found.append(filename)
    return found


def main():
    """Main security check"""
    print("🔍 Running security check...")
    print("=" * 60)
    
    all_issues = []
    
    # Check files for secrets
    for filepath in FILES_TO_CHECK:
        issues = check_file_for_secrets(filepath)
        all_issues.extend(issues)
    
    # Check for forbidden files
    forbidden = check_forbidden_files()
    
    # Report results
    if all_issues:
        print("\n❌ SECURITY ISSUES FOUND:")
        print("=" * 60)
        for issue in all_issues:
            print(f"\n📁 File: {issue['file']}")
            print(f"⚠️  Type: {issue['type']}")
            print(f"📝 Line: {issue['line']}")
        print("\n" + "=" * 60)
        print("🚨 CRITICAL: Remove all secrets before committing!")
        return 1
    
    if forbidden:
        print("\n⚠️  WARNING: Found files that should not be committed:")
        for f in forbidden:
            print(f"   - {f}")
        print("\nThese files are in .gitignore, but verify they won't be committed.")
    
    print("\n✅ Security check passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. git add <files>")
    print("2. git commit -m 'Your message'")
    print("3. git push")
    print("\n💡 Tip: Always review 'git status' before committing")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

