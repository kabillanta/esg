from django.core.management.base import BaseCommand
from core.models import Organization, User
from ingestion.models import DataSource, FacilityMapping
from records.models import EmissionFactor, ActivityRecord

class Command(BaseCommand):
    help = 'Seeds the database with an organization, users, data sources, and emission factors'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # 1. Organization
        org, created = Organization.objects.get_or_create(
            slug='demo-org',
            defaults={'name': 'Demo Enterprise'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created organization {org.name}'))

        # 2. Users
        admin_user, created = User.objects.get_or_create(
            username='admin_demo',
            defaults={
                'email': 'admin@demo.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'organization': org
            }
        )
        if created:
            admin_user.set_password('password123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user {admin_user.username}'))

        analyst_user, created = User.objects.get_or_create(
            username='analyst_demo',
            defaults={
                'email': 'analyst@demo.com',
                'first_name': 'Analyst',
                'last_name': 'User',
                'role': 'ANALYST',
                'organization': org
            }
        )
        if created:
            analyst_user.set_password('password123')
            analyst_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created analyst user {analyst_user.username}'))

        # 3. Data Sources
        sources = [
            {'type': 'SAP_FUEL', 'name': 'SAP Global Fuel Procurement (DE01)'},
            {'type': 'SAP_PROCUREMENT', 'name': 'SAP Procurement Materials'},
            {'type': 'UTILITY_ELECTRICITY', 'name': 'ConEd US East Facilities'},
            {'type': 'TRAVEL_FLIGHT', 'name': 'Concur Global Flights'},
            {'type': 'TRAVEL_HOTEL', 'name': 'Concur Global Hotels'},
            {'type': 'TRAVEL_GROUND', 'name': 'Concur Ground Transport'},
        ]
        
        for source in sources:
            ds, created = DataSource.objects.get_or_create(
                organization=org,
                source_type=source['type'],
                defaults={'name': source['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created data source {ds.name}'))

        # 4. Facility Mappings (SAP WERKS → friendly names)
        facility_mappings = [
            {'plant_code': 'DE01', 'facility_name': 'Hamburg Main Plant', 'city': 'Hamburg', 'country': 'DE'},
            {'plant_code': 'DE02', 'facility_name': 'Munich Distribution Center', 'city': 'Munich', 'country': 'DE'},
            {'plant_code': 'DE03', 'facility_name': 'Berlin Logistics Hub', 'city': 'Berlin', 'country': 'DE'},
            {'plant_code': 'DE04', 'facility_name': 'Frankfurt Fleet Depot', 'city': 'Frankfurt', 'country': 'DE'},
            {'plant_code': 'DE05', 'facility_name': 'Stuttgart Manufacturing', 'city': 'Stuttgart', 'country': 'DE'},
            # DE06–DE10 are intentionally UNMAPPED to test anomaly detection
        ]

        for fm_data in facility_mappings:
            fm, created = FacilityMapping.objects.get_or_create(
                organization=org,
                plant_code=fm_data['plant_code'],
                defaults={
                    'facility_name': fm_data['facility_name'],
                    'city': fm_data['city'],
                    'country': fm_data['country'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created facility mapping {fm.plant_code} -> {fm.facility_name}"))

        # 5. Emission Factors
        factors = [
            # Scope 1 – Stationary & mobile combustion
            {'category': 'diesel', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 2.68, 'unit': 'liters', 'ref': 'DEFRA 2024'},
            {'category': 'gasoline', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 2.31, 'unit': 'liters', 'ref': 'DEFRA 2024'},
            {'category': 'biodiesel', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 0.17, 'unit': 'liters', 'ref': 'DEFRA 2024 (biogenic)'},
            {'category': 'heating_oil', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 2.54, 'unit': 'liters', 'ref': 'DEFRA 2024'},
            {'category': 'natural_gas', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 2.02, 'unit': 'kg', 'ref': 'DEFRA 2024'},
            {'category': 'lpg', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 1.56, 'unit': 'liters', 'ref': 'DEFRA 2024'},
            {'category': 'kerosene', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 2.54, 'unit': 'liters', 'ref': 'DEFRA 2024'},
            {'category': 'adblue', 'scope': ActivityRecord.Scope.SCOPE_1, 'factor': 0.0, 'unit': 'liters', 'ref': 'Not a fuel – zero EF'},

            # Scope 2 – Purchased electricity
            {'category': 'electricity_us', 'scope': ActivityRecord.Scope.SCOPE_2, 'factor': 0.38, 'unit': 'kWh', 'ref': 'EPA eGRID 2023'},

            # Scope 3 – Business travel
            {'category': 'flight_short_haul', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 0.15, 'unit': 'km', 'ref': 'DEFRA 2024'},
            {'category': 'flight_medium_haul', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 0.13, 'unit': 'km', 'ref': 'DEFRA 2024'},
            {'category': 'flight_long_haul', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 0.11, 'unit': 'km', 'ref': 'DEFRA 2024'},
            {'category': 'hotel_night', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 15.0, 'unit': 'night', 'ref': 'DEFRA 2024'},
            {'category': 'taxi', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 0.17, 'unit': 'km', 'ref': 'DEFRA 2024'},
            {'category': 'rental_car', 'scope': ActivityRecord.Scope.SCOPE_3, 'factor': 0.20, 'unit': 'km', 'ref': 'DEFRA 2024'},
        ]

        for factor in factors:
            ef, created = EmissionFactor.objects.get_or_create(
                category=factor['category'],
                defaults={
                    'scope': factor['scope'],
                    'factor_kg_co2e_per_unit': factor['factor'],
                    'unit': factor['unit'],
                    'source_reference': factor['ref']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created emission factor {ef.category}"))

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
