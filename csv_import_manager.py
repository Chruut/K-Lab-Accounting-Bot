import streamlit as st
import pandas as pd
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CSVImportManager:
    def __init__(self):
        self.member_db_file = "k-lab_member_database.json"
        self.categories_file = "categories.json"
        self.imported_data = None
        self.processed_data = None
        
    def load_member_database(self) -> Dict[str, Any]:
        """Load member database from JSON file"""
        logger.info("Loading member database for CSV import")
        try:
            if os.path.exists(self.member_db_file):
                with open(self.member_db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Successfully loaded {len(data.get('members', {}))} members")
                    return data
            else:
                logger.warning("Member database file not found")
                return {"members": {}}
        except Exception as e:
            logger.error(f"Error loading member database: {str(e)}")
            st.error(f"Fehler beim Laden der Mitgliederdatenbank: {str(e)}")
            return {"members": {}}
    
    def get_member_names(self) -> List[str]:
        """Get list of all member names for dropdown"""
        member_db = self.load_member_database()
        return [member_data["name"] for member_data in member_db.get("members", {}).values()]
    
    def _add_smart_month_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add smart month defaults based on payment date"""
        logger.info("Adding smart month defaults")
        
        # Month names mapping
        month_names = {
            1: "Januar", 2: "Februar", 3: "März", 4: "April",
            5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
            9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
        }
        
        for idx, row in df.iterrows():
            payment_date = row['Datum']
            if pd.isna(payment_date):
                continue
                
            # Check if payment is within first 7 days of the month
            day_of_month = payment_date.day
            
            if day_of_month <= 7:
                # No default for payments within first 7 days
                df.at[idx, 'Monat'] = ''
            else:
                # Set default to current month
                month_name = month_names[payment_date.month]
                df.at[idx, 'Monat'] = month_name
        
        logger.info("Smart month defaults added")
        return df
    
    def _check_existing_entries(self, df: pd.DataFrame) -> List[str]:
        """Check if entries already exist in the member database"""
        logger.info("Checking for existing entries in database")
        
        member_db = self.load_member_database()
        conflicts = []
        
        # Month name to number mapping
        month_to_num = {
            "Januar": "01", "Februar": "02", "März": "03", "April": "04",
            "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
            "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
        }
        
        for idx, row in df.iterrows():
            member_name = str(row['Mitglied']).strip()
            month_name = str(row['Monat']).strip()
            purpose = str(row['Zahlungszweck']).strip()
            
            # Find member ID
            member_id = None
            for mid, member_data in member_db.get("members", {}).items():
                if member_data["name"] == member_name:
                    member_id = mid
                    break
            
            if member_id is None:
                continue
            
            # Check if entry already exists
            month_num = month_to_num.get(month_name)
            if month_num:
                contributions = member_db["members"][member_id].get("contributions", {}).get("2025", {})
                if month_num in contributions:
                    existing_entry = contributions[month_num]
                    conflicts.append(f"{member_name} - {month_name} ({purpose})")
        
        logger.info(f"Found {len(conflicts)} existing conflicts")
        return conflicts
    
    def load_member_mappings(self) -> Dict[str, str]:
        """Load member mappings from JSON file (Details -> Member Name)"""
        logger.info("Loading member mappings for auto-assignment")
        try:
            if os.path.exists(self.categories_file):
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    mappings = json.load(f)
                    logger.info(f"Successfully loaded {len(mappings)} member mappings")
                    return mappings
            else:
                logger.warning("Member mappings file not found, creating empty structure")
                return {}
        except Exception as e:
            logger.error(f"Error loading member mappings: {str(e)}")
            return {}
    
    def save_member_mappings(self, mappings: Dict[str, str]) -> bool:
        """Save member mappings to JSON file"""
        logger.info("Saving member mappings to file")
        try:
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
            logger.info("Successfully saved member mappings")
            return True
        except Exception as e:
            logger.error(f"Error saving member mappings: {str(e)}")
            return False
    
    def auto_assign_members(self, df: pd.DataFrame) -> pd.DataFrame:
        """Automatically assign members based on Details field"""
        logger.info("Auto-assigning members based on Details field")
        
        mappings = self.load_member_mappings()
        
        for idx, row in df.iterrows():
            details = str(row['Details']).lower().strip()
            current_member = row['Mitglied']
            
            # Skip if already assigned
            if current_member and current_member != '':
                continue
            
            # Check if details matches any known mapping
            for details_key, member_name in mappings.items():
                if details_key.lower() in details:
                    df.at[idx, 'Mitglied'] = member_name
                    logger.info(f"Auto-assigned member: '{details}' -> '{member_name}'")
                    break
        
        logger.info("Auto-assignment completed")
        return df
    
    def add_member_mapping(self, details: str, member_name: str) -> bool:
        """Add a member mapping for future auto-assignment"""
        logger.info(f"Adding member mapping: '{details}' -> '{member_name}'")
        
        mappings = self.load_member_mappings()
        
        details_key = details.strip()
        if details_key and details_key not in mappings:
            mappings[details_key] = member_name
            if self.save_member_mappings(mappings):
                logger.info(f"Successfully added mapping: '{details_key}' -> '{member_name}'")
                return True
            else:
                logger.error("Failed to save member mappings")
                return False
        
        return False
    
    def parse_csv_file(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Parse uploaded CSV file and extract relevant transactions"""
        logger.info("Parsing CSV file for bank statement import")
        try:
            # Read CSV with semicolon separator
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
            logger.info(f"CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
            
            # Clean column names
            df.columns = [col.strip().replace('"', '') for col in df.columns]
            
            # Filter for credit transactions (Gutschrift) only
            credit_df = df[df['Gutschrift CHF'].notna() & (df['Gutschrift CHF'] != '')].copy()
            logger.info(f"Found {len(credit_df)} credit transactions")
            
            if credit_df.empty:
                st.warning("Keine Gutschriften in der CSV-Datei gefunden.")
                return None
            
            # Convert amount to float
            credit_df['Amount'] = pd.to_numeric(credit_df['Gutschrift CHF'], errors='coerce')
            
            # Convert date
            credit_df['Date'] = pd.to_datetime(credit_df['Datum'], format='%d.%m.%Y', errors='coerce')
            
            # Create processed dataframe with required columns
            processed_df = pd.DataFrame({
                'Datum': credit_df['Date'],
                'Details': credit_df['Details'].fillna(''),
                'Amount': credit_df['Amount'],
                'Zahlungszweck': 'Mitgliederbeitrag',  # Set default for ALL rows
                'Mitglied': '',  # Will be filled by user
                'Monat': '',  # Will be filled by user with smart defaults
                'Bemerkungen': credit_df['Zahlungszweck'].fillna(''),  # Show Zahlungszweck info here
                'ZKB-Referenz': credit_df['ZKB-Referenz'].fillna('')  # Include ZKB reference
            })
            
            # Remove rows with invalid amounts
            processed_df = processed_df[processed_df['Amount'].notna() & (processed_df['Amount'] > 0)]
            
            # Add smart month defaults
            processed_df = self._add_smart_month_defaults(processed_df)
            
            # Auto-assign members based on Details field
            processed_df = self.auto_assign_members(processed_df)
            
            logger.info(f"Processed {len(processed_df)} valid transactions")
            return processed_df
            
        except Exception as e:
            logger.error(f"Error parsing CSV file: {str(e)}")
            st.error(f"Fehler beim Verarbeiten der CSV-Datei: {str(e)}")
            return None
    
    def create_interactive_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interactive table for CSV import with dropdowns"""
        logger.info("Creating interactive table for CSV import")
        
        member_names = self.get_member_names()
        payment_purposes = ["Mitgliederbeitrag", "Einführungskurs"]
        month_options = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", 
                        "Juli", "August", "September", "Oktober", "November", "Dezember"]
        
        # Create column configuration
        column_config = {
            "Datum": st.column_config.DateColumn(
                "Datum", 
                format="DD.MM.YYYY",
                disabled=True
            ),
            "Details": st.column_config.TextColumn(
                "Details",
                disabled=True
            ),
            "Amount": st.column_config.NumberColumn(
                "Betrag (CHF)",
                format="%.2f",
                disabled=True
            ),
            "Zahlungszweck": st.column_config.SelectboxColumn(
                "Zahlungszweck",
                options=payment_purposes,
                required=True
            ),
            "Mitglied": st.column_config.SelectboxColumn(
                "Mitglied",
                options=[""] + member_names,
                required=True
            ),
            "Monat": st.column_config.SelectboxColumn(
                "Monat",
                options=month_options,
                required=True
            ),
            "Bemerkungen": st.column_config.TextColumn(
                "Bemerkungen",
                disabled=True
            ),
            "ZKB-Referenz": st.column_config.TextColumn(
                "ZKB-Referenz",
                disabled=True
            )
        }
        
        # Display the interactive table
        st.subheader("📊 Interaktive Tabelle - Kontoauszug Import")
        st.markdown("Bitte wählen Sie für jede Transaktion den Zahlungszweck, das entsprechende Mitglied und den Monat aus.")
        
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key="csv_import_editor",
            num_rows="dynamic"
        )
        
        return edited_df
    
    def validate_import_data(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate the imported data before transfer"""
        logger.info("Validating import data")
        
        # Check if all required fields are filled
        missing_zweck = df['Zahlungszweck'].isna() | (df['Zahlungszweck'] == '')
        missing_member = df['Mitglied'].isna() | (df['Mitglied'] == '')
        missing_month = df['Monat'].isna() | (df['Monat'] == '')
        
        if missing_zweck.any():
            missing_rows = df[missing_zweck].index.tolist()
            return False, f"Bitte wählen Sie für alle Transaktionen einen Zahlungszweck aus. Fehlende Zeilen: {missing_rows}"
        
        if missing_member.any():
            missing_rows = df[missing_member].index.tolist()
            return False, f"Bitte wählen Sie für alle Transaktionen ein Mitglied aus. Fehlende Zeilen: {missing_rows}"
        
        if missing_month.any():
            missing_rows = df[missing_month].index.tolist()
            return False, f"Bitte wählen Sie für alle Transaktionen einen Monat aus. Fehlende Zeilen: {missing_rows}"
        
        # Check for duplicate member assignments for the same month
        duplicates = df.groupby(['Mitglied', 'Monat', 'Zahlungszweck']).size()
        duplicates = duplicates[duplicates > 1]
        
        if not duplicates.empty:
            return False, f"Es wurden mehrere Transaktionen für dasselbe Mitglied im selben Monat gefunden: {duplicates.to_dict()}"
        
        # Check if entries already exist in the database
        existing_conflicts = self._check_existing_entries(df)
        if existing_conflicts:
            return False, f"Folgende Einträge existieren bereits in der Matrix: {existing_conflicts}"
        
        logger.info("Import data validation successful")
        return True, "Validierung erfolgreich"
    
    def transfer_to_member_database(self, df: pd.DataFrame) -> bool:
        """Transfer validated data to member database"""
        logger.info("Transferring data to member database")
        
        try:
            # Load current member database
            member_db = self.load_member_database()
            
            # Group by member and process each transaction
            for member_name, group in df.groupby('Mitglied'):
                # Find member ID
                member_id = None
                for mid, member_data in member_db["members"].items():
                    if member_data["name"] == member_name:
                        member_id = mid
                        break
                
                if member_id is None:
                    logger.warning(f"Member not found: {member_name}")
                    continue
                
                # Process each transaction for this member
                for _, row in group.iterrows():
                    # Use the selected month instead of date month
                    month_name = str(row['Monat']).strip()
                    year = str(row['Datum'].year)
                    amount = float(row['Amount'])
                    purpose = str(row['Zahlungszweck']).strip()
                    
                    # Convert month name to number
                    month_to_num = {
                        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
                        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
                        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
                    }
                    month = month_to_num.get(month_name, row['Datum'].strftime('%m'))
                    
                    # Initialize contributions structure if not exists
                    if "contributions" not in member_db["members"][member_id]:
                        member_db["members"][member_id]["contributions"] = {}
                    if year not in member_db["members"][member_id]["contributions"]:
                        member_db["members"][member_id]["contributions"][year] = {}
                    
                    # Add contribution entry
                    zkb_reference = str(row['ZKB-Referenz']).strip() if 'ZKB-Referenz' in row else ""
                    transaction_id = zkb_reference if zkb_reference else f"CSV_{member_id}_{year}{month}_{int(datetime.now().timestamp())}"
                    
                    member_db["members"][member_id]["contributions"][year][month] = {
                        "amount": amount,
                        "date": row['Datum'].strftime('%Y-%m-%d'),
                        "transaction_id": transaction_id,
                        "source": "csv_import",
                        "purpose": purpose,
                        "details": str(row['Details']).strip(),
                        "month_name": month_name,
                        "zkb_reference": zkb_reference
                    }
                    
                # If it's an Einführungskurs payment, mark as completed
                if purpose == "Einführungskurs":
                    member_db["members"][member_id]["einfuehrungskurs"] = True
                
                # Add member mapping for future auto-assignment
                self.add_member_mapping(str(row['Details']).strip(), member_name.strip())
                    
                logger.info(f"Added {purpose} for {member_name} in {year}-{month}: {amount} CHF")
            
            # Save updated database
            with open(self.member_db_file, "w", encoding="utf-8") as f:
                json.dump(member_db, f, ensure_ascii=False, indent=2)
            
            logger.info("Successfully transferred data to member database")
            return True
            
        except Exception as e:
            logger.error(f"Error transferring data to member database: {str(e)}")
            st.error(f"Fehler beim Übertragen der Daten: {str(e)}")
            return False
    
    def display_import_summary(self, df: pd.DataFrame):
        """Display summary of imported data"""
        logger.info("Displaying import summary")
        
        st.subheader("📈 Import-Zusammenfassung")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Anzahl Transaktionen", len(df))
        
        with col2:
            total_amount = df['Amount'].sum()
            st.metric("Gesamtbetrag", f"{total_amount:.2f} CHF")
        
        with col3:
            unique_members = df['Mitglied'].nunique()
            st.metric("Betroffene Mitglieder", unique_members)
        
        with col4:
            zweck_counts = df['Zahlungszweck'].value_counts()
            st.metric("Mitgliederbeiträge", zweck_counts.get('Mitgliederbeitrag', 0))
        
        # Show breakdown by member and month
        st.subheader("📊 Aufschlüsselung nach Mitgliedern und Monaten")
        member_summary = df.groupby(['Mitglied', 'Monat', 'Zahlungszweck']).agg({
            'Amount': ['sum', 'count']
        }).round(2)
        member_summary.columns = ['Betrag (CHF)', 'Anzahl']
        st.dataframe(member_summary, use_container_width=True)
    
    def run_csv_import_interface(self):
        """Main interface for CSV import functionality"""
        logger.info("Starting CSV import interface")
        
        st.title("📥 Kontoauszug CSV Import")
        st.markdown("Importieren Sie Kontoauszüge und übertragen Sie die Daten in die Mitgliedermatrix.")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Wählen Sie eine CSV-Datei (Kontoauszug) aus",
            type=["csv"],
            help="Die CSV-Datei sollte im ZKB-Format vorliegen mit Spalten wie 'Datum', 'Gutschrift CHF', 'Zahlungszweck', etc."
        )
        
        if uploaded_file is not None:
            # Parse CSV file
            with st.spinner("Verarbeite CSV-Datei..."):
                self.imported_data = self.parse_csv_file(uploaded_file)
            
            if self.imported_data is not None and not self.imported_data.empty:
                # Display file info
                st.success(f"✅ CSV erfolgreich geladen: {len(self.imported_data)} Transaktionen gefunden")
                
                # Show raw data preview
                with st.expander("🔍 Rohdaten-Vorschau", expanded=False):
                    st.dataframe(self.imported_data.head(10), use_container_width=True)
                
                # Create interactive table
                self.processed_data = self.create_interactive_table(self.imported_data)
                
                # Validation and transfer section
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("✅ Daten validieren", type="secondary"):
                        is_valid, message = self.validate_import_data(self.processed_data)
                        if is_valid:
                            st.success(message)
                            st.session_state.csv_validation_passed = True
                        else:
                            st.error(message)
                            st.session_state.csv_validation_passed = False
                
                with col2:
                    if st.button("📊 Zusammenfassung anzeigen", type="secondary"):
                        self.display_import_summary(self.processed_data)
                
                # Transfer button
                st.markdown("---")
                if st.button("🔄 Daten in die Matrix übertragen", type="primary"):
                    # Validate again before transfer
                    is_valid, message = self.validate_import_data(self.processed_data)
                    
                    if is_valid:
                        with st.spinner("Übertrage Daten in die Mitgliederdatenbank..."):
                            if self.transfer_to_member_database(self.processed_data):
                                st.success("✅ Daten erfolgreich in die Matrix übertragen!")
                                st.balloons()
                                
                                # Show summary
                                self.display_import_summary(self.processed_data)
                                
                                # Clear session state
                                if 'csv_validation_passed' in st.session_state:
                                    del st.session_state.csv_validation_passed
                                
                                # Rerun to refresh the interface
                                st.rerun()
                            else:
                                st.error("❌ Fehler beim Übertragen der Daten")
                    else:
                        st.error(f"❌ Validierung fehlgeschlagen: {message}")
            else:
                st.warning("⚠️ Keine gültigen Transaktionen in der CSV-Datei gefunden.")

if __name__ == "__main__":
    # This allows the module to be run standalone for testing
    manager = CSVImportManager()
    manager.run_csv_import_interface()
