from django.core.management.base import BaseCommand
from app.models import Illness, Drug, DrugIllness, CustomUser

class Command(BaseCommand):

    help = 'Fills the database with test data: drugs, users, fights, and fight-drugrelationdrugs'


    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 11):
            email = f'user{i}@example.com'
            password = ''.join(str(x) for x in range(1, i+1)) 
            user, created = CustomUser.objects.get_or_create(
                email=email,
            )
            
            if created:
                user.set_password(password)  # Устанавливаем пароль, чтобы он был захеширован
                user.save()
                if i == 9 or i == 10:
                    user.is_staff = True
                    user.save()
                self.stdout.write(self.style.SUCCESS(f'User "{user.email}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.email}" already exists.'))

        URL = 'http://127.0.0.1:9000/pharma/{}.jpg'
        ILLNESS = [
            {
                'id': 1,
                'name': 'Грипп',
                'description': 'Грипп — это острое инфекционное заболевание, вызываемое вирусами гриппа. Симптомы включают лихорадку, головную боль, усталость, кашель, боль в горле и мышечные боли. В тяжелых случаях может приводить к осложнениям, таким как пневмония.',
                'spread': 'Воздушно-капельный',
                'photo': 'http://127.0.0.1:9000/pharma/1.jpg'
            },
            {
                'id': 2,
                'name': 'Диабет',
                'description': 'Диабет — это хроническое заболевание, при котором организм не может должным образом регулировать уровень сахара в крови. Существует два основных типа: диабет 1-го типа (недостаток инсулина) и диабет 2-го типа (сопротивление инсулину). Симптомы включают частое мочеиспускание, сильную жажду, усталость и потерю веса.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/2.jpg'
            },
            {
                'id': 3,
                'name': 'Астма',
                'description': 'Астма — это хроническое воспалительное заболевание дыхательных путей, которое вызывает затрудненное дыхание, кашель и приступы удушья. Обострения могут быть вызваны аллергенами, инфекциями или физической нагрузкой.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/3.jpg'
            },
            {
                'id': 4,
                'name': 'Гипертония',
                'description': 'Гипертония — это состояние, при котором повышается артериальное давление. Это увеличивает риск сердечно-сосудистых заболеваний, инсульта и других осложнений. Чаще всего заболевание протекает без симптомов, но может сопровождаться головными болями, головокружением и ухудшением зрения.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/4.jpg'
            },
            {
                'id': 5,
                'name': 'Остеопороз',
                'description': 'Остеопороз — это заболевание, при котором кости становятся хрупкими и подвержены переломам из-за снижения плотности костной ткани. Наиболее подвержены заболеванию пожилые люди, особенно женщины после менопаузы.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/5.JPG'
            },
            {
                'id': 6,
                'name': 'Мигрень',
                'description': 'Мигрень — это неврологическое заболевание, которое характеризуется интенсивными головными болями, часто сопровождаемыми тошнотой, рвотой и повышенной чувствительностью к свету и звукам. Часто мигрень имеет наследственную предрасположенность.',
                'spread': 'Наследственный',
                'photo': 'http://127.0.0.1:9000/pharma/6.jpg'
            },
            {
                'id': 7,
                'name': 'Эпилепсия',
                'description': 'Эпилепсия — это хроническое неврологическое заболевание, характеризующееся периодическими судорожными приступами. Причины могут быть генетическими, либо вызваны травмами или инфекциями.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/7.jpg'
            },
            {
                'id': 8,
                'name': 'Анемия',
                'description': 'Анемия — это состояние, при котором в организме наблюдается недостаток гемоглобина или эритроцитов. Симптомы включают слабость, усталость, бледность и головокружение. Может возникнуть из-за недостатка железа, витамина B12 или кровопотерь.',
                'spread': 'Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/8.jpg'
            },
            {
                'id': 9,
                'name': 'Ревматоидный артрит',
                'description': 'Ревматоидный артрит — это аутоиммунное заболевание, поражающее суставы и вызывающее воспаление, боль и деформацию. Заболевание имеет наследственную предрасположенность и может вызываться инфекциями.',
                'spread': 'Наследственный/Приобретенный',
                'photo': 'http://127.0.0.1:9000/pharma/9.jpg'
            }
        ]
            
            
        for ill in ILLNESS:
            illness, created = Illness.objects.get_or_create(
                id=ill['id'],
                defaults={
                    'name': ill['name'],
                    'spread': ill['spread'],
                    'description': ill['description'],
                    'photo': ill['photo']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Illness "{illness.name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Illness "{illness.name}" already exists.'))


            drugs_data = [
                {
                'name': 'Парацетамол',
                'description': 'Анальгетик и жаропонижающее средство. Помогает при головной, зубной боли и высокой температуре.'
                },
                {
                'name': 'Ибупрофен',
                'description': 'Нестероидное противовоспалительное средство, используемое для снятия боли, воспаления и жара.'
                },
                {
                'name': 'Амоксициллин',
                'description': 'Антибиотик широкого спектра действия, применяется для лечения бактериальных инфекций, включая заболевания дыхательных путей и мочеполовой системы.'
                },
                {
                'name': 'Лоратадин',
                'description': 'Антигистаминное средство, применяемое для снятия симптомов аллергии, таких как зуд, чихание и слезотечение.'
                }
            ]

        for data in drugs_data:
            drug, created = Drug.objects.get_or_create(
                name=data['name'],
                description=data['description'],
                defaults={'status': 'dr'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'drug{drug.name} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'drug{drug.name} already exists.'))

        Drug_Illness = [
            {'drug_id': 1, 'illness_id': 6, 'trial': 'Успешно' },
            {'drug_id': 2, 'illness_id': 1, 'trial': 'Успешно' },
            {'drug_id': 2, 'illness_id': 9, 'trial': 'Успешно' },
            {'drug_id': 3, 'illness_id': 1, 'trial': 'Успешно' },
            {'drug_id': 4, 'illness_id': 3, 'trial': 'Успешно' }
        ]

        for od in Drug_Illness:
            Drug_Illness, created = DrugIllness.objects.get_or_create(
                drug_id=od['drug_id'],
                illness_id=od['illness_id'],
                trial=od['trial']
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'DrugIllness entry for drug{od["drug_id"]}, illness {od["illness_id"]}, trial {od["trial"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'DrugIllness entry for drug{od["Drug_id"]}, illness {od["illness_id"]}, trial {od["trial"]} already exists.'))