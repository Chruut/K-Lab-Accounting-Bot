import streamlit as st
import pandas as pd
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('member_management.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import Telegram modules
try:
    from telegram_reminder import PaymentReminder
    from telegram_config import is_telegram_configured
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Telegram modules not available: {e}")
    TELEGRAM_AVAILABLE = False

# Always available CSV export
from payment_reminder_export import PaymentReminderExport

# CSV import functionality
from csv_import_manager import CSVImportManager

st.set_page_config(page_title="K-Lab Member Management", page_icon="👥", layout="wide")

# Custom CSS to remove bullet points from checkbox columns and make checkboxes green
st.markdown("""
<style>
    /* Remove bullet points from checkbox columns */
    .stDataEditor .stCheckbox > div > label::before {
        display: none !important;
    }
    
    /* Make checkbox columns more compact */
    .stDataEditor .stCheckbox {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Optimize column widths */
    .stDataEditor [data-testid="column"] {
        min-width: 60px !important;
    }
    
    /* Hide bullet points in data editor */
    .stDataEditor ul {
        list-style: none !important;
        padding-left: 0 !important;
    }
    
    /* Make checkboxes green when checked */
    .stDataEditor .stCheckbox input[type="checkbox"]:checked {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    
    .stDataEditor .stCheckbox input[type="checkbox"]:checked:after {
        color: white !important;
    }
    
    /* Alternative approach for green checkboxes */
    .stDataEditor .stCheckbox input[type="checkbox"]:checked + label::before {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }
    
    /* Ensure checkbox styling is applied */
    .stDataEditor .stCheckbox input[type="checkbox"] {
        accent-color: #28a745 !important;
    }
</style>
""", unsafe_allow_html=True)

# Constants
MEMBER_DB_FILE = "k-lab_member_database.json"
MITGLIEDSFORM_OPTIONS = ["Aktiv", "Passiv", "Inaktiv"]
MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
MONTH_NAMES = {
    "01": "Januar", "02": "Februar", "03": "März", "04": "April",
    "05": "Mai", "06": "Juni", "07": "Juli", "08": "August",
    "09": "September", "10": "Oktober", "11": "November", "12": "Dezember"
}

def load_member_database() -> Dict[str, Any]:
    """Load member database from JSON file"""
    logger.info("Loading member database from file")
    try:
        if os.path.exists(MEMBER_DB_FILE):
            with open(MEMBER_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Successfully loaded {len(data.get('members', {}))} members")
                return data
        else:
            logger.warning("Member database file not found, creating empty structure")
            return {"members": {}, "transactions_unknown": []}
    except Exception as e:
        logger.error(f"Error loading member database: {str(e)}")
        st.error(f"Fehler beim Laden der Mitgliederdatenbank: {str(e)}")
        return {"members": {}, "transactions_unknown": []}

def save_member_database(data: Dict[str, Any]) -> bool:
    """Save member database to JSON file"""
    logger.info("Saving member database to file")
    try:
        with open(MEMBER_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Successfully saved member database")
        return True
    except Exception as e:
        logger.error(f"Error saving member database: {str(e)}")
        st.error(f"Fehler beim Speichern der Mitgliederdatenbank: {str(e)}")
        return False

def get_payment_status(member_id: str, month: str, year: str = "2025") -> bool:
    """Check if member has paid for a specific month"""
    if "members" not in st.session_state.member_db:
        return False
    
    member = st.session_state.member_db["members"].get(member_id, {})
    contributions = member.get("contributions", {}).get(year, {})
    return month in contributions

def get_introduction_course_status(member_id: str) -> bool:
    """Check if member has completed introduction course"""
    if "members" not in st.session_state.member_db:
        return False
    
    member = st.session_state.member_db["members"].get(member_id, {})
    return member.get("einfuehrungskurs", False)

def create_member_dataframe() -> pd.DataFrame:
    """Create DataFrame for member management table"""
    logger.info("Creating member dataframe for display")
    
    if not st.session_state.member_db.get("members"):
        return pd.DataFrame()
    
    data = []
    for member_id, member_data in st.session_state.member_db["members"].items():
        row = {
            "Mitglied": member_data["name"],
            "Mitgliedsform": member_data.get("mitgliedsform", "Aktiv"),
            "Einführungskurs": get_introduction_course_status(member_id)
        }
        
        # Add month columns
        for month in MONTHS:
            row[MONTH_NAMES[month]] = get_payment_status(member_id, month)
        
        data.append(row)
    
    df = pd.DataFrame(data)
    logger.info(f"Created dataframe with {len(df)} members and {len(df.columns)} columns")
    return df

def update_member_from_dataframe(df: pd.DataFrame) -> bool:
    """Update member database based on dataframe changes"""
    logger.info("Updating member database from dataframe changes")
    
    try:
        for idx, row in df.iterrows():
            # Find member by name
            member_id = None
            for mid, member_data in st.session_state.member_db["members"].items():
                if member_data["name"] == row["Mitglied"]:
                    member_id = mid
                    break
            
            if member_id is None:
                logger.warning(f"Member not found for name: {row['Mitglied']}")
                continue
            
            # Update member form
            st.session_state.member_db["members"][member_id]["mitgliedsform"] = row["Mitgliedsform"]
            
            # Update introduction course status
            st.session_state.member_db["members"][member_id]["einfuehrungskurs"] = row["Einführungskurs"]
            
            # Update monthly payment status
            for month in MONTHS:
                month_name = MONTH_NAMES[month]
                is_paid = row[month_name]
                
                if is_paid and not get_payment_status(member_id, month):
                    # Add payment entry
                    if "contributions" not in st.session_state.member_db["members"][member_id]:
                        st.session_state.member_db["members"][member_id]["contributions"] = {}
                    if "2025" not in st.session_state.member_db["members"][member_id]["contributions"]:
                        st.session_state.member_db["members"][member_id]["contributions"]["2025"] = {}
                    
                    # Correct amount: 50.00 for Aktiv, 25.00 for Passiv
                    amount = 50.00 if row["Mitgliedsform"] == "Aktiv" else 25.00
                    
                    st.session_state.member_db["members"][member_id]["contributions"]["2025"][month] = {
                        "amount": amount,
                        "date": None,  # No default date for direct table entries
                        "transaction_id": None  # No default transaction_id for direct table entries
                    }
                elif not is_paid and get_payment_status(member_id, month):
                    # Remove payment entry
                    if month in st.session_state.member_db["members"][member_id]["contributions"]["2025"]:
                        del st.session_state.member_db["members"][member_id]["contributions"]["2025"][month]
        
        logger.info("Successfully updated member database from dataframe")
        return True
    except Exception as e:
        logger.error(f"Error updating member database: {str(e)}")
        return False

def main():
    st.title("K-Lab Mitgliederverwaltung")
    st.markdown("---")
    
    # Initialize session state
    if "member_db" not in st.session_state:
        logger.info("Initializing session state with member database")
        st.session_state.member_db = load_member_database()
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["👥 Mitgliederverwaltung", "📥 CSV Import"])
    
    with tab1:
        run_member_management()
    
    with tab2:
        run_csv_import()

def add_new_member(name: str, phone: str, email: str, mitgliedsform: str) -> bool:
    """Add a new member to the database"""
    logger.info(f"Adding new member: {name}")
    
    try:
        # Generate new member ID
        existing_ids = list(st.session_state.member_db["members"].keys())
        if existing_ids:
            # Extract numeric part and find next ID
            max_num = max([int(mid[1:]) for mid in existing_ids if mid.startswith('M') and mid[1:].isdigit()])
            new_id = f"M{max_num + 1:03d}"
        else:
            new_id = "M001"
        
        # Create new member entry with trimmed data
        new_member = {
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "mitgliedsform": mitgliedsform.strip(),
            "einfuehrungskurs": False,
            "contributions": {"2025": {}},
            "telegram_chat_id": None
        }
        
        # Add to database
        st.session_state.member_db["members"][new_id] = new_member
        
        # Save to file
        if save_member_database(st.session_state.member_db):
            logger.info(f"Successfully added member {name} with ID {new_id}")
            return True
        else:
            logger.error("Failed to save member database")
            return False
            
    except Exception as e:
        logger.error(f"Error adding new member: {str(e)}")
        return False

def run_member_management():
    """Main member management functionality"""
    
    # Add new member form
    st.subheader("➕ Neues Mitglied hinzufügen")
    
    with st.expander("Mitglied hinzufügen", expanded=False):
        col1, col2 = st.columns(2)
        
        # Initialize session state for form fields
        if "new_member_name" not in st.session_state:
            st.session_state.new_member_name = ""
        if "new_member_phone" not in st.session_state:
            st.session_state.new_member_phone = ""
        if "new_member_email" not in st.session_state:
            st.session_state.new_member_email = ""
        if "new_member_form" not in st.session_state:
            st.session_state.new_member_form = "Aktiv"
        
        with col1:
            new_name = st.text_input("Name *", value=st.session_state.new_member_name, placeholder="Max Mustermann", key="name_input")
            new_phone = st.text_input("Telefonnummer *", value=st.session_state.new_member_phone, placeholder="+41 79 123 45 67", key="phone_input")
            new_email = st.text_input("E-Mail *", value=st.session_state.new_member_email, placeholder="max.mustermann@example.com", key="email_input")
        
        with col2:
            new_mitgliedsform = st.selectbox(
                "Mitgliedsform *",
                options=MITGLIEDSFORM_OPTIONS,
                index=MITGLIEDSFORM_OPTIONS.index(st.session_state.new_member_form),
                key="form_input"
            )
            
            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("➕ Mitglied hinzufügen", type="primary"):
                if new_name and new_phone and new_email and new_mitgliedsform:
                    if add_new_member(new_name, new_phone, new_email, new_mitgliedsform):
                        st.success(f"✅ Mitglied '{new_name}' erfolgreich hinzugefügt!")
                        # Clear the form fields
                        st.session_state.new_member_name = ""
                        st.session_state.new_member_phone = ""
                        st.session_state.new_member_email = ""
                        st.session_state.new_member_form = "Aktiv"
                        st.rerun()
                    else:
                        st.error("❌ Fehler beim Hinzufügen des Mitglieds")
                else:
                    st.error("❌ Bitte füllen Sie alle Pflichtfelder aus (Name, Telefonnummer, E-Mail, Mitgliedsform)")
    
    st.markdown("---")
    
    # Create member dataframe
    member_df = create_member_dataframe()
    
    if member_df.empty:
        st.warning("Keine Mitglieder in der Datenbank gefunden.")
        return
    
    st.subheader("Mitgliedertabelle")
    st.markdown("Bearbeiten Sie die Tabelle direkt. Änderungen werden beim Speichern in die Datenbank übernommen.")
    
    # Create column configuration for data editor
    column_config = {
        "Mitglied": st.column_config.TextColumn("Mitglied", disabled=True),
        "Mitgliedsform": st.column_config.SelectboxColumn(
            "Mitgliedsform",
            options=MITGLIEDSFORM_OPTIONS
        ),
        "Einführungskurs": st.column_config.CheckboxColumn(
            "Einführungskurs", 
            help="Einführungskurs abgeschlossen",
            width=80
        )
    }
    
    # Add month columns configuration
    for month in MONTHS:
        month_name = MONTH_NAMES[month]
        column_config[month_name] = st.column_config.CheckboxColumn(
            month_name,
            help=f"Bezahlt für {month_name} 2025",
            width=60
        )
    
    # Display data editor
    edited_df = st.data_editor(
        member_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key="member_editor",
        num_rows="dynamic"
    )
    
    # Save button
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        if st.button("💾 Änderungen speichern", type="primary"):
            logger.info("User clicked save button")
            if update_member_from_dataframe(edited_df):
                if save_member_database(st.session_state.member_db):
                    st.success("✅ Änderungen erfolgreich gespeichert!")
                    st.rerun()
                else:
                    st.error("❌ Fehler beim Speichern der Datenbank")
            else:
                st.error("❌ Fehler beim Aktualisieren der Daten")
    
    with col2:
        if st.button("🔄 Neu laden"):
            logger.info("User clicked reload button")
            st.session_state.member_db = load_member_database()
            st.rerun()
    
    with col3:
        if st.button("📱 Telegram Erinnerungen senden", type="secondary"):
            logger.info("User clicked Telegram reminder button")
            if not TELEGRAM_AVAILABLE:
                st.error("❌ Telegram-Abhängigkeiten nicht installiert. Führen Sie 'uv sync' aus.")
            elif not is_telegram_configured():
                st.error("❌ Telegram Bot nicht konfiguriert. Bitte TELEGRAM_BOT_TOKEN setzen.")
            else:
                with st.spinner("Sende Zahlungserinnerungen..."):
                    reminder = PaymentReminder()
                    results = reminder.send_reminders_sync(st.session_state.member_db)
                    
                    if results:
                        success_count = sum(1 for success in results.values() if success)
                        total_count = len(results)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}/{total_count} Erinnerungen erfolgreich gesendet!")
                        
                        # Show detailed results
                        st.subheader("📊 Versand-Ergebnisse")
                        for member_name, success in results.items():
                            status = "✅ Erfolgreich" if success else "❌ Fehler"
                            st.write(f"• {member_name}: {status}")
                    else:
                        st.warning("⚠️ Keine ausstehenden Zahlungen gefunden oder keine Mitglieder mit Telegram-Chat-ID.")
    
    with col4:
        if st.button("📄 CSV Export", type="secondary"):
            logger.info("User clicked CSV export button")
            with st.spinner("Erstelle CSV-Export..."):
                exporter = PaymentReminderExport()
                filename = f"zahlungserinnerungen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                if exporter.export_reminders_to_csv(st.session_state.member_db, filename):
                    st.success(f"✅ CSV-Export erfolgreich erstellt: {filename}")
                    
                    # Show summary
                    summary = exporter.get_outstanding_summary(st.session_state.member_db)
                    st.info(f"📊 Exportiert: {summary['members_with_outstanding']}/{summary['total_members']} Mitglieder mit ausstehenden Zahlungen")
                    st.info(f"💰 Gesamtbetrag ausstehend: {summary['total_outstanding_amount']:.2f} CHF")
                else:
                    st.error("❌ Fehler beim Erstellen des CSV-Exports")
    
    with col5:
        if st.button("📊 Zusammenfassung", type="secondary"):
            logger.info("User clicked summary button")
            exporter = PaymentReminderExport()
            summary = exporter.get_outstanding_summary(st.session_state.member_db)
            
            st.subheader("📊 Zahlungsübersicht")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Mitglieder gesamt", summary['total_members'])
            
            with col_b:
                st.metric("Mit ausstehenden Zahlungen", summary['members_with_outstanding'])
            
            with col_c:
                st.metric("Gesamtbetrag ausstehend", f"{summary['total_outstanding_amount']:.2f} CHF")
    
    # Display summary statistics
    st.markdown("---")
    st.subheader("Zusammenfassung")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_members = len(st.session_state.member_db["members"])
        st.metric("Gesamtmitglieder", total_members)
    
    with col2:
        active_members = sum(1 for member in st.session_state.member_db["members"].values() 
                           if member.get("mitgliedsform") == "Aktiv")
        st.metric("Aktive Mitglieder", active_members)
    
    with col3:
        passive_members = sum(1 for member in st.session_state.member_db["members"].values() 
                            if member.get("mitgliedsform") == "Passiv")
        st.metric("Passive Mitglieder", passive_members)
    
    with col4:
        inactive_members = sum(1 for member in st.session_state.member_db["members"].values() 
                             if member.get("mitgliedsform") == "Inaktiv")
        st.metric("Inaktive Mitglieder", inactive_members)
    
    # Outstanding payments section
    st.subheader("💸 Ausstehende Zahlungen")
    
    # Create outstanding payments dataframe
    outstanding_data = []
    for member_id, member_data in st.session_state.member_db["members"].items():
        if member_data.get("mitgliedsform") == "Inaktiv":
            continue
            
        # Calculate outstanding payments
        member_form = member_data.get("mitgliedsform", "Aktiv")
        monthly_amount = 50.0 if member_form == "Aktiv" else 25.0
        
        contributions = member_data.get("contributions", {}).get("2025", {})
        paid_months = set(contributions.keys())
        
        current_month = datetime.now().month
        outstanding_months = []
        total_outstanding = 0.0
        
        for month in range(1, current_month + 1):
            month_str = f"{month:02d}"
            if month_str not in paid_months:
                outstanding_months.append(MONTH_NAMES[month_str])
                total_outstanding += monthly_amount
        
        if outstanding_months:
            outstanding_data.append({
                "Mitglied": member_data["name"],
                "Mitgliedsform": member_form,
                "Ausstehende Monate": ", ".join(outstanding_months),
                "Betrag (CHF)": f"{total_outstanding:.2f}"
            })
    
    if outstanding_data:
        outstanding_df = pd.DataFrame(outstanding_data)
        st.dataframe(outstanding_df, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 Alle aktiven Mitglieder haben ihre Beiträge bezahlt!")
    
    # Payment overview
    st.subheader("📊 Zahlungsübersicht")
    payment_data = []
    for month in MONTHS:
        month_name = MONTH_NAMES[month]
        paid_count = sum(1 for member in st.session_state.member_db["members"].values()
                        if get_payment_status(list(st.session_state.member_db["members"].keys())[
                            list(st.session_state.member_db["members"].values()).index(member)], month))
        payment_data.append({
            "Monat": month_name,
            "Bezahlt": paid_count,
            "Nicht bezahlt": total_members - paid_count
        })
    
    payment_df = pd.DataFrame(payment_data)
    st.dataframe(payment_df, use_container_width=True, hide_index=True)

def run_csv_import():
    """CSV import functionality"""
    logger.info("Starting CSV import interface")
    
    # Initialize CSV import manager
    csv_manager = CSVImportManager()
    
    # Run the CSV import interface
    csv_manager.run_csv_import_interface()

if __name__ == "__main__":
    logger.info("Starting K-Lab Member Management application")
    main()
