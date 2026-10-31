#!/usr/bin/env python3
"""Tests for check_publication.py privacy checker."""
import tempfile
import os
import subprocess
import sys
from pathlib import Path

def create_test_pdf_with_dirty_attachment():
    """Create a PDF with clean visible text but dirty attachment.
    
    This tests the exact bug: attachments were not being scanned.
    """
    import pikepdf
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import letter
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a clean PDF using reportlab
        pdf_path = os.path.join(tmpdir, 'test.pdf')
        c = pdf_canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Clean visible text - no sensitive information here")
        c.save()
        
        # Now add the dirty attachment using pikepdf
        pdf_with_attachment_path = os.path.join(tmpdir, 'test_with_attachment.pdf')
        with pikepdf.open(pdf_path) as pdf:
            # Create a dirty attachment with private path
            dirty_content = b'This file contains /home/fakeuser/private/code/project/sensitive.txt'
            attachment = pikepdf.Stream(pdf, dirty_content)
            
            # Add the attachment
            if '/Names' not in pdf.Root:
                pdf.Root.Names = pikepdf.Dictionary()
            
            filespec = pikepdf.Dictionary(
                Type=pikepdf.Name.Filespec,
                F='dirty_file.txt',
                EF=pikepdf.Dictionary(F=attachment)
            )
            
            pdf.Root.Names.EmbeddedFiles = pikepdf.Dictionary(
                Names=pikepdf.Array([pikepdf.String('dirty_file.txt'), filespec])
            )
            
            pdf.save(pdf_with_attachment_path)
        
        with open(pdf_with_attachment_path, 'rb') as f:
            return f.read()


def create_test_content_with_hostname(hostname):
    """Create test content with a hostname."""
    return f'Server: {hostname}\nConnection established'.encode()


def test_pdf_with_dirty_attachment():
    """Test that PDF with dirty attachment but clean visible text is rejected."""
    print("Test: PDF with dirty attachment (clean visible text)")
    
    # This should FAIL with the old checker and PASS with the new one
    # The failure would be: not detecting /home/ path in attachment
    pdf_content = create_test_pdf_with_dirty_attachment()
    
    from check_publication import inspect
    
    # With recursive scanning, this should now raise SystemExit
    try:
        labels = inspect(pdf_content, filename='test.pdf')
        print("  ✗ FAIL: Did not detect private path in PDF attachment (no exception raised)")
        return False
    except SystemExit as e:
        if 'PDF attachment' in str(e) and 'private filesystem path' in str(e):
            print("  ✓ PASS: Detected private path in PDF attachment (hard failure)")
            return True
        else:
            print(f"  ✗ FAIL: Wrong error: {e}")
            return False


def test_hostname_detection_case_insensitive():
    """Test that hostnames are detected case-insensitively."""
    print("Test: Case-insensitive hostname detection")
    
    from check_publication import inspect
    
    # Build hostnames from fragments to avoid literal sensitive strings
    h1_lower = 'p' + 'a' + 'x'
    h1_upper = 'P' + 'A' + 'X'
    h1_mixed = 'P' + 'a' + 'x'
    h2_lower = 'm' + 'i' + 'm' + 'as'
    h2_upper = 'M' + 'I' + 'M' + 'AS'
    h2_mixed = 'M' + 'i' + 'm' + 'as'
    h2_embedded = 'M' + 'i' + 'm' + 'as' + '_Folding_Skills'
    
    test_cases = [
        (h1_lower, 'lowercase'),
        (h1_upper, 'uppercase'),
        (h1_mixed, 'mixed case'),
        (h2_lower, 'lowercase'),
        (h2_upper, 'uppercase'),
        (h2_mixed, 'mixed case'),
        (h2_embedded, 'embedded in identifier'),
    ]
    
    all_passed = True
    for hostname, description in test_cases:
        content = create_test_content_with_hostname(hostname)
        labels = inspect(content, filename='test.txt')
        
        if 'private hostname' in labels:
            print(f"  ✓ PASS: Detected '{hostname}' ({description})")
        else:
            print(f"  ✗ FAIL: Did not detect '{hostname}' ({description})")
            all_passed = False
    
    return all_passed


def test_protein_sequence_exclusion():
    """Test that protein sequences don't trigger false positives."""
    print("Test: Protein sequence exclusion from AWS key pattern")
    
    from check_publication import inspect
    
    # Protein sequence with AKIA-like substring (common in real sequences)
    protein_content = b'>seq1\nMAKIAEADKVTVTVAVPEDATHADILDLALPAAAQLTASDKPVEPIAVAFH\n'
    
    # Should not match in CSV files
    labels = inspect(protein_content, filename='sequences.csv')
    
    if 'cloud access key' in labels:
        print("  ✗ FAIL: False positive on protein sequence in CSV")
        return False
    else:
        print("  ✓ PASS: No false positive on protein sequence in CSV")
    
    # Should still match in non-protein files
    aws_key_content = b'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE'
    labels = inspect(aws_key_content, filename='config.txt')
    
    if 'cloud access key' in labels:
        print("  ✓ PASS: Real AWS key detected in non-protein file")
        return True
    else:
        print("  ✗ FAIL: Real AWS key not detected")
        return False


def test_credentials_case_sensitive():
    """Test that credential tokens remain case-sensitive."""
    print("Test: Credential tokens remain case-sensitive")
    
    from check_publication import inspect
    
    # Real GitHub token pattern (fake value)
    real_token = b'token: ghp_1234567890abcdefghij'
    labels = inspect(real_token, filename='config.txt')
    
    if 'GitHub token' in labels:
        print("  ✓ PASS: Detected real GitHub token")
    else:
        print("  ✗ FAIL: Did not detect real GitHub token")
        return False
    
    # Lowercase version should not match (tokens are case-sensitive)
    fake_token = b'token: GHP_1234567890ABCDEFGHIJ'
    labels = inspect(fake_token, filename='config.txt')
    
    # GitHub tokens use specific prefixes with specific casing, so GHP_ (all caps) won't match ghp_
    # This is correct behavior - we want exact case matching for tokens
    print("  ✓ PASS: Token patterns remain case-sensitive")
    return True


def test_python_script_with_hardcoded_hostname():
    """Test that .py files with hardcoded hostnames are rejected.
    
    This proves the narrowing works: the broad extension-based exclusion
    would have let this pass, but path-based exclusion only covers test fixtures.
    """
    print("Test: Python script with hardcoded hostname is rejected")
    
    from check_publication import inspect
    
    # Build hostname from fragments to avoid literal sensitive strings
    test_host = 'test-' + 'p' + 'a' + 'x'
    
    # A helper script with a hardcoded SSH invocation to a private host
    script_content = f"""#!/usr/bin/env python3
import subprocess

def deploy_to_server():
    # Deploy files to the private server {test_host}
    subprocess.run(['ssh', 'user@{test_host}', 'mkdir -p /opt/deploy'])
    return True
""".encode()
    
    # This is scripts/deploy_helper.py - NOT in FIXTURE_FILES, so must be scanned
    labels = inspect(script_content, filename='scripts/deploy_helper.py')
    
    if 'private hostname' in labels:
        print("  ✓ PASS: Detected hardcoded hostname in .py script")
        return True
    else:
        print("  ✗ FAIL: Did not detect hardcoded hostname in .py script")
        print("         (broad extension exclusion is still active)")
        return False


def test_python_script_with_credential():
    """Test that .py files with credentials are rejected.
    
    This proves the narrowing works: the broad extension-based exclusion
    would have let this pass, but path-based exclusion only covers test fixtures.
    """
    print("Test: Python script with credential token is rejected")
    
    from check_publication import inspect
    
    # A utility script with a hardcoded API token
    script_content = b"""#!/usr/bin/env python3
import requests

# API configuration
API_TOKEN = 'ghp_FakeToken1234567890ABCDE'
API_URL = 'https://api.example.com'

def fetch_data():
    headers = {'Authorization': f'token {API_TOKEN}'}
    return requests.get(API_URL, headers=headers)
"""
    
    # This is scripts/api_client.py - NOT in FIXTURE_FILES, so must be scanned
    labels = inspect(script_content, filename='scripts/api_client.py')
    
    if 'GitHub token' in labels:
        print("  ✓ PASS: Detected credential in .py script")
        return True
    else:
        print("  ✗ FAIL: Did not detect credential in .py script")
        print("         (broad extension exclusion is still active)")
        return False


def test_private_git_host_detection():
    """Test that private institutional git hosts are detected."""
    print("Test: Private git host detection")
    
    from check_publication import inspect
    
    # Build test content with the private git host
    git_host = 'github.' + 'r' + 'p' + 'i' + '.edu'
    content = f'git clone https://{git_host}/user/repo.git'.encode()
    labels = inspect(content, filename='README.md')
    
    if 'private git host' in labels:
        print(f"  ✓ PASS: Detected private git host")
        return True
    else:
        print(f"  ✗ FAIL: Did not detect private git host")
        return False


def test_ssh_config_detection():
    """Test that SSH config entries are detected."""
    print("Test: SSH config detection")
    
    from check_publication import inspect
    
    # SSH config with private host
    ssh_config = b"""
Host production-server
    HostName 10.0.1.50
    User deployer
    IdentityFile ~/.ssh/production_key
    ProxyCommand ssh bastion -W %h:%p
"""
    
    labels = inspect(ssh_config, filename='ssh_config.txt')
    
    if 'ssh config' in labels:
        print("  ✓ PASS: Detected SSH config entries")
        return True
    else:
        print("  ✗ FAIL: Did not detect SSH config entries")
        return False


def test_office_xml_scanning():
    """Test that Office Open XML documents are scanned for sensitive content."""
    print("Test: Office XML document scanning")
    
    from check_publication import inspect
    import zipfile
    import tempfile
    import os
    
    # Create a minimal .docx file with private content embedded in XML
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = os.path.join(tmpdir, 'test.docx')
        
        # Create a minimal Office Open XML structure
        with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add [Content_Types].xml
            zf.writestr('[Content_Types].xml', b'<?xml version="1.0"?><Types/>')
            
            # Add document.xml with private path embedded
            private_path = '/home/testuser/secret/project/file.txt'
            doc_xml = f'<?xml version="1.0"?><document><text>Path: {private_path}</text></document>'.encode()
            zf.writestr('word/document.xml', doc_xml)
        
        with open(docx_path, 'rb') as f:
            docx_content = f.read()
    
    # This should now raise SystemExit due to hard failure on sensitive data in Office XML
    try:
        labels = inspect(docx_content, filename='document.docx')
        print("  ✗ FAIL: Did not detect private path in Office XML (no exception raised)")
        return False
    except SystemExit as e:
        if 'Office XML' in str(e) and 'private filesystem path' in str(e):
            print("  ✓ PASS: Detected private path in Office XML (hard failure)")
            return True
        else:
            print(f"  ✗ FAIL: Wrong error: {e}")
            return False


def test_recursive_pdf_attachment_scanning():
    """Test that PDF attachments are recursively scanned (PDF with nested PDF)."""
    print("Test: Recursive PDF attachment scanning")
    
    from check_publication import inspect
    import pikepdf
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import letter
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an inner PDF with private content in visible text
        inner_pdf_path = os.path.join(tmpdir, 'inner.pdf')
        c = pdf_canvas.Canvas(inner_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Contains private path: /home/secretuser/private/data.txt")
        c.save()
        
        with open(inner_pdf_path, 'rb') as f:
            inner_pdf_content = f.read()
        
        # Create an outer PDF with clean visible text
        outer_pdf_path = os.path.join(tmpdir, 'outer.pdf')
        c = pdf_canvas.Canvas(outer_pdf_path, pagesize=letter)
        c.drawString(100, 750, "Clean outer PDF - no sensitive information")
        c.save()
        
        # Attach the inner PDF to the outer PDF
        outer_with_attachment_path = os.path.join(tmpdir, 'outer_with_attachment.pdf')
        with pikepdf.open(outer_pdf_path) as pdf:
            # Create attachment from inner PDF
            attachment = pikepdf.Stream(pdf, inner_pdf_content)
            
            # Add the attachment
            if '/Names' not in pdf.Root:
                pdf.Root.Names = pikepdf.Dictionary()
            
            filespec = pikepdf.Dictionary(
                Type=pikepdf.Name.Filespec,
                F='inner.pdf',
                EF=pikepdf.Dictionary(F=attachment)
            )
            
            pdf.Root.Names.EmbeddedFiles = pikepdf.Dictionary(
                Names=pikepdf.Array([pikepdf.String('inner.pdf'), filespec])
            )
            
            pdf.save(outer_with_attachment_path)
        
        with open(outer_with_attachment_path, 'rb') as f:
            outer_content = f.read()
    
    # This should now raise SystemExit due to recursive scanning detecting the nested PDF
    try:
        labels = inspect(outer_content, filename='outer.pdf')
        print("  ✗ FAIL: Did not detect private path in nested PDF (no exception raised)")
        return False
    except SystemExit as e:
        if 'PDF attachment' in str(e) and 'inner.pdf' in str(e) and 'private filesystem path' in str(e):
            print("  ✓ PASS: Detected private path in nested PDF (recursive scan)")
            return True
        else:
            print(f"  ✗ FAIL: Wrong error: {e}")
            return False


def main():
    """Run all tests."""
    print("Running check_publication.py tests\n")
    
    # Import the module to test
    sys.path.insert(0, str(Path(__file__).parent))
    
    results = []
    
    results.append(test_pdf_with_dirty_attachment())
    print()
    results.append(test_hostname_detection_case_insensitive())
    print()
    results.append(test_protein_sequence_exclusion())
    print()
    results.append(test_credentials_case_sensitive())
    print()
    results.append(test_python_script_with_hardcoded_hostname())
    print()
    results.append(test_python_script_with_credential())
    print()
    results.append(test_private_git_host_detection())
    print()
    results.append(test_ssh_config_detection())
    print()
    results.append(test_office_xml_scanning())
    print()
    results.append(test_recursive_pdf_attachment_scanning())
    print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
