import json
from django.core.management.base import BaseCommand
from apps.matcher.models import SensitiveEntity


class Command(BaseCommand):
    help = 'Import sensitive entities from entities_dict.json'

    def handle(self, *args, **kwargs):
        with open('data/entities_dict.json', 'r', encoding='utf-8') as f:
            entities = json.load(f)

        for entity_id, entity_info in entities.items():
            SensitiveEntity.objects.update_or_create(
                entity_id=entity_id,
                defaults={
                    'entity_type': entity_info.get('type', ''),
                    'entity_text': entity_info.get('text', ''),
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully imported sensitive entities.'))
