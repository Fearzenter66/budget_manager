from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_income_subcategory_expense_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='income',
            name='amount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
                verbose_name='Сумма',
            ),
            preserve_default=False,
        ),
    ]
