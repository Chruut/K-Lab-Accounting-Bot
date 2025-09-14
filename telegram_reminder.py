"""
Telegram Payment Reminder Module
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from telegram_config import TELEGRAM_BOT_TOKEN, get_telegram_chat_id, is_telegram_configured

logger = logging.getLogger(__name__)

class PaymentReminder:
    """Handles payment reminders via Telegram"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.bot_token) if self.bot_token else None
        
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
    
    async def send_reminder_to_member(self, member_data: Dict) -> bool:
        """
        Send payment reminder to a specific member
        
        Args:
            member_data: Member data from database
            
        Returns:
            True if message sent successfully, False otherwise
        """
        member_name = member_data.get("name", "Unbekannt")
        phone_number = member_data.get("telefon", "")
        
        logger.info(f"Sending reminder to {member_name} ({phone_number})")
        
        # Get Telegram chat ID
        chat_id = get_telegram_chat_id(phone_number)
        if not chat_id:
            logger.warning(f"No Telegram chat ID found for {member_name} ({phone_number})")
            return False
        
        # Calculate outstanding payments
        outstanding_months, total_amount = self.calculate_outstanding_payments(member_data)
        
        # Format message
        message = self.format_reminder_message(
            member_name, 
            member_data.get("mitgliedsform", "Aktiv"),
            outstanding_months, 
            total_amount
        )
        
        try:
            # Send message
            await self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Successfully sent reminder to {member_name}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send reminder to {member_name}: {str(e)}")
            return False
    
    async def send_reminders_to_all_members(self, member_database: Dict) -> Dict[str, bool]:
        """
        Send payment reminders to all members with outstanding payments
        
        Args:
            member_database: Complete member database
            
        Returns:
            Dictionary with member names and success status
        """
        if not is_telegram_configured():
            logger.error("Telegram bot not properly configured")
            return {}
        
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return {}
        
        logger.info("Starting to send payment reminders to all members")
        
        results = {}
        members = member_database.get("members", {})
        
        for member_id, member_data in members.items():
            member_name = member_data.get("name", f"Member {member_id}")
            
            # Skip inactive members
            if member_data.get("mitgliedsform") == "Inaktiv":
                logger.info(f"Skipping inactive member: {member_name}")
                continue
            
            # Check if member has outstanding payments
            outstanding_months, total_amount = self.calculate_outstanding_payments(member_data)
            if not outstanding_months:
                logger.info(f"No outstanding payments for {member_name}")
                continue
            
            # Send reminder
            success = await self.send_reminder_to_member(member_data)
            results[member_name] = success
        
        logger.info(f"Completed sending reminders. Results: {results}")
        return results
    
    def send_reminders_sync(self, member_database: Dict) -> Dict[str, bool]:
        """
        Synchronous wrapper for sending reminders
        
        Args:
            member_database: Complete member database
            
        Returns:
            Dictionary with member names and success status
        """
        try:
            return asyncio.run(self.send_reminders_to_all_members(member_database))
        except Exception as e:
            logger.error(f"Error in synchronous reminder sending: {str(e)}")
            return {}
