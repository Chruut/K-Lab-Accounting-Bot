"""
Payment Reminder Export Module
Alternative to Telegram bot - exports payment reminders to CSV
"""
import logging
import csv
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentReminderExport:
    """Handles payment reminder export to CSV"""
    
    def calculate_outstanding_payments(self, member_data: Dict) -> Tuple[List[str], float]:
        """
        Calculate outstanding payments for a member
        
        Args:
            member_data: Member data from database
            
        Returns:
            Tuple of (outstanding_months, total_amount)
        """
        logger.info(f"Calculating outstanding payments for {member_data.get('name', 'Unknown')}")
        
        # Determine monthly contribution amount based on member form
        member_form = member_data.get("mitgliedsform", "Aktiv")
        if member_form == "Aktiv":
            monthly_amount = 50.0  # CHF
        elif member_form == "Passiv":
            monthly_amount = 25.0  # CHF
        else:  # Inaktiv
            monthly_amount = 0.0
        
        if monthly_amount == 0.0:
            return [], 0.0
        
        # Get current year and month
        current_year = "2025"
        current_month = datetime.now().month
        current_month_str = f"{current_month:02d}"
        
        # Get paid months
        contributions = member_data.get("contributions", {}).get(current_year, {})
        paid_months = set(contributions.keys())
        
        # Calculate outstanding months (up to current month)
        outstanding_months = []
        total_outstanding = 0.0
        
        for month in range(1, current_month + 1):
            month_str = f"{month:02d}"
            if month_str not in paid_months:
                outstanding_months.append(month_str)
                total_outstanding += monthly_amount
        
        logger.info(f"Outstanding months: {outstanding_months}, Total: {total_outstanding} CHF")
        return outstanding_months, total_outstanding
    
    def format_reminder_message(self, member_name: str, member_form: str, 
                              outstanding_months: List[str], total_amount: float) -> str:
        """
        Format the payment reminder message
        
        Args:
            member_name: Name of the member
            member_form: Member form (Aktiv/Passiv/Inaktiv)
            outstanding_months: List of outstanding months
            total_amount: Total outstanding amount
            
        Returns:
            Formatted message string
        """
        if not outstanding_months:
            return f"✅ Hallo {member_name},\n\nAlle Beiträge für {datetime.now().year} sind bereits bezahlt!"
        
        month_names = {
            "01": "Januar", "02": "Februar", "03": "März", "04": "April",
            "05": "Mai", "06": "Juni", "07": "Juli", "08": "August",
            "09": "September", "10": "Oktober", "11": "November", "12": "Dezember"
        }
        
        outstanding_month_names = [month_names.get(month, month) for month in outstanding_months]
        
        message = f"💰 Zahlungserinnerung - K-Lab\n\n"
        message += f"Hallo {member_name},\n\n"
        message += f"Es fehlen noch Beiträge für folgende Monate:\n"
        
        for month_name in outstanding_month_names:
            message += f"• {month_name}\n"
        
        message += f"\nMitgliedsform: {member_form}\n"
        message += f"Monatlicher Beitrag: {50.0 if member_form == 'Aktiv' else 25.0} CHF\n"
        message += f"Gesamtbetrag ausstehend: {total_amount:.2f} CHF\n\n"
        message += f"Bitte überweise den Betrag auf unser Konto.\n\n"
        message += f"Vielen Dank!\nK-Lab Team"
        
        return message
    
    def export_reminders_to_csv(self, member_database: Dict, filename: str = "zahlungserinnerungen.csv") -> bool:
        """
        Export payment reminders to CSV file
        
        Args:
            member_database: Complete member database
            filename: Output CSV filename
            
        Returns:
            True if export successful, False otherwise
        """
        logger.info(f"Exporting payment reminders to {filename}")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Mitglied', 'Telefon', 'Email', 'Mitgliedsform', 
                    'Ausstehende_Monate', 'Monatlicher_Beitrag', 'Gesamtbetrag_CHF', 
                    'Nachricht'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                members = member_database.get("members", {})
                exported_count = 0
                
                for member_id, member_data in members.items():
                    member_name = member_data.get("name", f"Member {member_id}")
                    
                    # Skip inactive members
                    if member_data.get("mitgliedsform") == "Inaktiv":
                        logger.info(f"Skipping inactive member: {member_name}")
                        continue
                    
                    # Calculate outstanding payments
                    outstanding_months, total_amount = self.calculate_outstanding_payments(member_data)
                    
                    # Skip if no outstanding payments
                    if not outstanding_months:
                        logger.info(f"No outstanding payments for {member_name}")
                        continue
                    
                    # Format month names
                    month_names = {
                        "01": "Januar", "02": "Februar", "03": "März", "04": "April",
                        "05": "Mai", "06": "Juni", "07": "Juli", "08": "August",
                        "09": "September", "10": "Oktober", "11": "November", "12": "Dezember"
                    }
                    outstanding_month_names = [month_names.get(month, month) for month in outstanding_months]
                    
                    # Determine monthly amount
                    member_form = member_data.get("mitgliedsform", "Aktiv")
                    monthly_amount = 50.0 if member_form == "Aktiv" else 25.0
                    
                    # Format reminder message
                    message = self.format_reminder_message(
                        member_name, member_form, outstanding_months, total_amount
                    )
                    
                    # Write row
                    writer.writerow({
                        'Mitglied': member_name,
                        'Telefon': member_data.get("telefon", ""),
                        'Email': member_data.get("email", ""),
                        'Mitgliedsform': member_form,
                        'Ausstehende_Monate': ", ".join(outstanding_month_names),
                        'Monatlicher_Beitrag': f"{monthly_amount:.2f} CHF",
                        'Gesamtbetrag_CHF': f"{total_amount:.2f}",
                        'Nachricht': message.replace('\n', ' | ')
                    })
                    
                    exported_count += 1
                
                logger.info(f"Successfully exported {exported_count} payment reminders to {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting reminders to CSV: {str(e)}")
            return False
    
    def get_outstanding_summary(self, member_database: Dict) -> Dict:
        """
        Get summary of outstanding payments
        
        Args:
            member_database: Complete member database
            
        Returns:
            Dictionary with summary statistics
        """
        members = member_database.get("members", {})
        total_outstanding = 0.0
        members_with_outstanding = 0
        total_members = 0
        
        for member_id, member_data in members.items():
            if member_data.get("mitgliedsform") == "Inaktiv":
                continue
                
            total_members += 1
            outstanding_months, total_amount = self.calculate_outstanding_payments(member_data)
            
            if outstanding_months:
                members_with_outstanding += 1
                total_outstanding += total_amount
        
        return {
            "total_members": total_members,
            "members_with_outstanding": members_with_outstanding,
            "total_outstanding_amount": total_outstanding
        }
