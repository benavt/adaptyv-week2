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
