from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE auth_user ADD CONSTRAINT unique_user_email UNIQUE (email);',
            reverse_sql='ALTER TABLE auth_user DROP CONSTRAINT unique_user_email;',
        ),
    ]