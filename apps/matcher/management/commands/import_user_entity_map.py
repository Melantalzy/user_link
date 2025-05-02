import json
from django.core.management.base import BaseCommand
from apps.matcher.models import UserSpeech, UserEntityMap

class Command(BaseCommand):
    help = 'Import user-entity map with list of entity ids from user_entity_map.json'

    def handle(self, *args, **kwargs):
        with open('data/user_entity_map.json', 'r', encoding='utf-8') as f:
            user_entity_map = json.load(f)

        created_count = 0
        for user_id, entity_list in user_entity_map.items():
            try:
                user = UserSpeech.objects.get(id=user_id)
            except UserSpeech.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"UserSpeech with id {user_id} not found. Skipping."))
                continue

            # 这里！！直接带上 entity_ids
            map_obj, created = UserEntityMap.objects.get_or_create(
                user=user,
                defaults={'entity_ids': entity_list}
            )

            if not created:
                # 如果已经存在，就更新一下 entity_ids
                map_obj.entity_ids = entity_list
                map_obj.save()

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created or updated {created_count} user-entity maps.'))
