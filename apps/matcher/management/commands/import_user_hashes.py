import csv
from django.core.management.base import BaseCommand
from apps.matcher.models import UserSpeech, UserHash

class Command(BaseCommand):
    help = 'Import user hashes from CSV file and create UserHash objects.'

    def handle(self, *args, **kwargs):
        with open('data/user_hashes.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 👉 加这一行，跳过表头

            for row in reader:
                user_id, hash_value = row
                user = UserSpeech.objects.get(id=int(user_id))
                UserHash.objects.create(user=user, hash_value=hash_value)

        self.stdout.write(self.style.SUCCESS('Successfully imported user hashes.'))
