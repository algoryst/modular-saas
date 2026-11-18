# Translations

## Glossary

Use these words everywhere: templates, form labels, emails, error messages. English is the
source; French is the reference translation. Sentence case in both languages ("Sign in", not
"Sign In"). Plain words over jargon: "Créer un compte", never "S'enregistrer" or "S'inscrire".

| English | Français | Avoid |
|---|---|---|
| Sign in | Se connecter | S'identifier, Connexion (as a verb) |
| Sign out | Se déconnecter | Déconnexion (as a verb) |
| Create an account / Create account | Créer un compte | S'inscrire, S'enregistrer |
| Email address | Adresse e-mail | Courriel, Mail |
| Password | Mot de passe | |
| Code (one-time) | Code | Jeton, Token |
| Sign-in code | Code de connexion | |
| Workspace | Espace de travail | Tenant, Organisation |
| Waitlist | Liste d'attente | |


Start by configuring the `LANGUAGES` settings in `base.py`, by uncommenting languages you are willing to support. Then, translation strings will be placed in this folder when running:

```bash
docker compose -f docker-compose.local.yml run --rm django python manage.py makemessages --all --no-location
```

This should generate `django.po` (stands for Portable Object) files under each locale `<locale name>/LC_MESSAGES/django.po`. Each translatable string in the codebase is collected with its `msgid` and need to be translated as `msgstr`, for example:

```po
msgid "users"
msgstr "utilisateurs"
```

Once all translations are done, they need to be compiled into `.mo` files (stands for Machine Object), which are the actual binary files used by the application:

```bash
docker compose -f docker-compose.local.yml run --rm django python manage.py compilemessages
```

Note that the `.po` files are NOT used by the application directly, so if the `.mo` files are out of date, the content won't appear as translated even if the `.po` files are up-to-date.

## Production

The production image runs `compilemessages` automatically at build time, so as long as your translated source files (PO) are up-to-date, you're good to go.

## Add a new language

1. Update the [`LANGUAGES` setting](https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-LANGUAGES) to your project's base settings.
2. Create the locale folder for the language next to this file, e.g. `fr_FR` for French. Make sure the case is correct.
3. Run `makemessages` (as instructed above) to generate the PO files for the new language.
