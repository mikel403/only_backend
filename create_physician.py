import os
import sys
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebApp.settings.dev")
django.setup()

from django.contrib.auth.models import User
from nodule.models import Physicist


def crear_physician(username, password, experience=None, profession=None):
    

    user, _ = User.objects.get_or_create(username=username)
    user.set_password(
        password
    )  # para asegurarse de que la contraseña se guarde correctamente
    user.save()

    physician, _ = Physicist.objects.get_or_create(user=user)
    # Solo setear si viene informado (no obligatorio)
    if experience is not None:
        physician.experience = int(experience)

    if profession is not None:
        physician.profession = profession
    physician.save()

    print(
        f"✅ Usuario '{username}' creado/actualizado y vinculado como Physicist."
        f" experience={physician.experience} profession={physician.profession}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python crear_physician.py <username> <password> [experience] [profession]")
        sys.exit(1)
    else:
        username = sys.argv[1]
        password = sys.argv[2]
        experience = sys.argv[3] if len(sys.argv) >= 4 else None
        profession = sys.argv[4] if len(sys.argv) >= 5 else None

        crear_physician(username, password, experience, profession)
