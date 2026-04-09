from django.core.management.base import BaseCommand
from chat.bot_logic import start_bot

class Command(BaseCommand):
    help = "Run the Telegram bot"

    def handle(self, *args, **options):
        self.stdout.write("Bot is running...")
        start_bot()