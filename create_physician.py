import os
import sys
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebApp.settings.dev")
django.setup()

from django.contrib.auth.models import User
from nodule.models import Physicist


def crear_physician(username, password, experience):
    experience = int(experience)  # convertir a entero

    user, _ = User.objects.get_or_create(username=username)
    user.set_password(
        password
    )  # para asegurarse de que la contraseña se guarde correctamente
    user.save()

    physician, _ = Physicist.objects.get_or_create(user=user, experience=experience)
    physician.save()

    print(
        f"✅ Usuario '{username}' creado y vinculado como Physician con {experience} años de experiencia."
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python crear_physician.py <username> <password> <experience>")
    else:
        _, username, password, experience = sys.argv
        crear_physician(username, password, experience)
