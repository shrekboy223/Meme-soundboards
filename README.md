# Meme Soundboard (macOS)

Soundboard moderne pour macOS avec une interface sombre et des effets visuels.

## Structure du projet

```
.
├── app/
│   ├── __init__.py
│   └── ui.py
├── config/
│   └── sounds.json
├── sounds/
│   └── .gitkeep
├── main.py
└── requirements.txt
```

## Installation (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer l'application

```bash
python main.py
```

## Comment ajouter mes sons

1. Déposez vos fichiers audio dans `sounds/` (WAV obligatoire, MP3 possible si votre macOS a les codecs).
2. Ouvrez `config/sounds.json` et remplacez la liste `sounds` par vos sons.
3. Ajustez `columns` pour choisir votre grille (ex: 3, 4, 5...). Pour une grille 5 x 20, mettez `columns: 5` et listez 100 sons.

Exemple de config :

```json
{
  "columns": 5,
  "sounds": [
    {
      "label": "Airhorn",
      "filename": "airhorn.wav",
      "emoji": "📣"
    },
    {
      "label": "Bruh",
      "filename": "bruh.wav",
      "emoji": "🤦"
    }
  ]
}
```

## Raccourcis clavier

- `Espace` : Stop
- `Entrée` : Jouer le son sélectionné
- `Flèches` : Naviguer dans la grille

## Notes

- Si un fichier manque ou n'est pas supporté, l'UI affiche une erreur et le bouton devient rouge.
- Le dernier son joué peut être relancé avec le bouton **Rejouer**.
