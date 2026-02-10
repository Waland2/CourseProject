# Generated manually for the course project backend.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ManagingCompany',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inn', models.CharField(db_index=True, max_length=32, unique=True)),
                ('full_name', models.CharField(max_length=512)),
                ('short_name', models.CharField(blank=True, max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Управляющая организация',
                'verbose_name_plural': 'Управляющие организации',
                'ordering': ['short_name', 'full_name'],
            },
        ),
        migrations.CreateModel(
            name='ManagingCompanyYearStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(db_index=True)),
                ('adm_area', models.CharField(blank=True, db_index=True, max_length=255)),
                ('adm_areas', models.JSONField(blank=True, default=list)),
                ('houses_quantity', models.PositiveIntegerField(default=0)),
                ('houses_area', models.PositiveIntegerField(default=0)),
                ('total_area', models.PositiveIntegerField(default=0)),
                ('final_rating', models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ('total_amount_of_scores', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('public_satisfaction_scores_sum', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('public_satisfaction_appeals_score', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('public_satisfaction_responses_score', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('public_satisfaction_coefficient_value', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('public_satisfaction_intermediate_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('reliability_scores_sum', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('reliability_scores_by_standard', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('reliability_intermediate_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('violation_scores_sum', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('elimination_violations_scores', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('detected_violations_scores', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('penalty_scores', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('violation_intermediate_rating', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('issued_prescriptions', models.PositiveIntegerField(default=0)),
                ('violations_amount', models.PositiveIntegerField(default=0)),
                ('protocols_composed', models.PositiveIntegerField(default=0)),
                ('protocols_composed_for_failure', models.PositiveIntegerField(default=0)),
                ('events_executed', models.PositiveIntegerField(default=0)),
                ('events_not_executed_in_time', models.PositiveIntegerField(default=0)),
                ('sum_of_fine', models.DecimalField(decimal_places=2, default='0.00', max_digits=14)),
                ('cancelled_contracts_amount', models.PositiveIntegerField(default=0)),
                ('violations_punished', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='year_stats', to='companies.managingcompany')),
            ],
            options={
                'verbose_name': 'Статистика управляющей организации по году',
                'verbose_name_plural': 'Годовая статистика управляющих организаций',
                'ordering': ['year', 'company_id'],
                'unique_together': {('company', 'year')},
            },
        ),
        migrations.AddIndex(
            model_name='managingcompanyyearstat',
            index=models.Index(fields=['year', 'adm_area'], name='companies_m_year_95d08c_idx'),
        ),
        migrations.AddIndex(
            model_name='managingcompanyyearstat',
            index=models.Index(fields=['year', 'final_rating'], name='companies_m_year_84eb54_idx'),
        ),
    ]
