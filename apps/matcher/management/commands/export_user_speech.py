from django.core.management.base import BaseCommand
import csv
from apps.matcher.models import UserSpeech

class Command(BaseCommand):
    help = 'Export UserSpeech data to CSV'

    def handle(self, *args, **options):
        with open('data/users_speech.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Email', 'Comment', 'Embedding'])  # 写表头

            for speech in UserSpeech.objects.all():
                writer.writerow([speech.id, speech.email, speech.comment, speech.embedding])

        self.stdout.write(self.style.SUCCESS('Successfully exported users.csv'))
