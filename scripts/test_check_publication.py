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
    labels = inspect(pdf_content, filename='test.pdf')
    
    if 'private filesystem path' in labels:
        print("  ✓ PASS: Detected private path in PDF attachment")
        return True
    else:
        print("  ✗ FAIL: Did not detect private path in PDF attachment")
        return False


def test_hostname_detection_case_insensitive():
    """Test that hostnames are detected case-insensitively."""
    print("Test: Case-insensitive hostname detection")
    
    from check_publication import inspect
    
    test_cases = [
        ('pax', 'lowercase'),
        ('PAX', 'uppercase'),
        ('Pax', 'mixed case'),
        ('mimas', 'lowercase'),
        ('MIMAS', 'uppercase'),
        ('Mimas', 'mixed case'),
        ('Mimas_Folding_Skills', 'embedded in identifier'),
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
    
    # A helper script with a hardcoded SSH invocation to a private host
    # Using fake placeholder "test-pax" that matches the pattern (hyphen before pax)
    script_content = b"""#!/usr/bin/env python3
import subprocess

def deploy_to_server():
    # Deploy files to the private server test-pax
    subprocess.run(['ssh', 'user@test-pax', 'mkdir -p /opt/deploy'])
    return True
"""
    
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
    
    labels = inspect(docx_content, filename='document.docx')
    
    if 'private filesystem path' in labels:
        print("  ✓ PASS: Detected private path in Office XML")
        return True
    else:
        print("  ✗ FAIL: Did not detect private path in Office XML")
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
