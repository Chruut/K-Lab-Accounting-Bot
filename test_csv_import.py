#!/usr/bin/env python3
"""
Test script for CSV import functionality
"""

import pandas as pd
import json
import os
from csv_import_manager import CSVImportManager

def test_csv_parsing():
    """Test CSV parsing functionality"""
    print("🧪 Testing CSV parsing functionality...")
    
    # Create a test CSV file similar to the ZKB format
    test_data = {
        'Datum': ['29.08.2025', '29.08.2025', '25.08.2025'],
        'Buchungstext': ['Gutschrift Auftraggeber: Test Member 1', 'Gutschrift Auftraggeber: Test Member 2', 'Gutschrift Auftraggeber: Test Member 3'],
        'Gutschrift CHF': ['50.00', '25.00', '50.00'],
        'Zahlungszweck': ['Monatsbeitrag', 'Mitgliederbeitrag', 'Einführungskurs'],
        'Details': ['Test Member 1, Test Address', 'Test Member 2, Test Address', 'Test Member 3, Test Address'],
        'ZKB-Referenz': ['SL250829579C9948', 'SL250829579BD487', 'SL250829579B1869']
    }
    
    test_df = pd.DataFrame(test_data)
    test_csv_path = 'test_kontoauszug.csv'
    test_df.to_csv(test_csv_path, sep=';', index=False)
    
    print(f"✅ Created test CSV file: {test_csv_path}")
    
    # Test CSV parsing
    manager = CSVImportManager()
    
    # Simulate file upload by reading the test file
    with open(test_csv_path, 'rb') as f:
        result_df = manager.parse_csv_file(f)
    
    if result_df is not None:
        print(f"✅ CSV parsing successful: {len(result_df)} transactions found")
        print("📊 Sample data:")
        print(result_df[['Datum', 'Details', 'Amount', 'Zahlungszweck', 'Mitglied', 'Monat']].head())
        
        # Test member names loading
        member_names = manager.get_member_names()
        print(f"✅ Member names loaded: {len(member_names)} members found")
        if member_names:
            print(f"   Sample members: {member_names[:3]}")
        
        return True
    else:
        print("❌ CSV parsing failed")
        return False

def test_member_database_structure():
    """Test member database structure"""
    print("\n🧪 Testing member database structure...")
    
    # Check if member database exists
    if os.path.exists('k-lab_member_database.json'):
        with open('k-lab_member_database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        members = data.get('members', {})
        print(f"✅ Member database found with {len(members)} members")
        
        if members:
            # Show sample member structure
            sample_member_id = list(members.keys())[0]
            sample_member = members[sample_member_id]
            print(f"📊 Sample member structure:")
            print(f"   ID: {sample_member_id}")
            print(f"   Name: {sample_member.get('name', 'N/A')}")
            print(f"   Mitgliedsform: {sample_member.get('mitgliedsform', 'N/A')}")
            print(f"   Einführungskurs: {sample_member.get('einfuehrungskurs', False)}")
            
            contributions = sample_member.get('contributions', {})
            if contributions:
                print(f"   Contributions: {len(contributions)} years")
            else:
                print(f"   Contributions: None")
        
        return True
    else:
        print("❌ Member database not found")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting CSV Import Tests")
    print("=" * 50)
    
    # Test 1: Member database structure
    db_test = test_member_database_structure()
    
    # Test 2: CSV parsing
    csv_test = test_csv_parsing()
    
    # Cleanup
    if os.path.exists('test_kontoauszug.csv'):
        os.remove('test_kontoauszug.csv')
        print("\n🧹 Cleaned up test files")
    
    print("\n" + "=" * 50)
    if db_test and csv_test:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return db_test and csv_test

if __name__ == "__main__":
    main()
