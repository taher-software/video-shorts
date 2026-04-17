# Stack technique
- Framework : Fastapi
- Langage : python3.11

# Documentation du projet
Voir @README.md pour la vue d'ensemble du projet.
Voir @ARCHITECTURE.md pour l'architecture détaillée.

# Structure du projet
Voir @ARCHITECTURE.md pour créer l'architecture adaptée à python pour le projet picsou-shorts

Etape 3 — Preparation des assets visuels
- opter pour l'option B pour utiliser DALL-E  pour génerer deux images de Picsou sur fond trasparent , une avec bouche fermée et une avec bouche ouvert. on doit créer ces deux images une seule fois et les mettre dans le dossier assets. donc la fonction doit vérifier si ces deux images existes et procéder à en créer une seule fois s'il n'existe pas.
- Animation de parole : opter pour le niveau 2 out en utilisant un seuil adpatif comme indiqué sur @ARCHITECTURE.md
- Fond / Background: utiliser la `background_description` de l'etape 1 pour generer un fond via DALL-E 3.

### 6. Cout et performance

| Etape | API | Cout estime |
|---|---|---|
| Script | GPT-4o | ~$0.003 (prompt_tokens = 450 ,completion_tokens=215) | 
| TTS | OpenAI tts-1 | ~$0.015 / 1000 chars | ~$0.00225 (80- 200 words)
| Whisper | OpenAI Whisper | ~$0.006 / minute | ~$0.0045 (45 secondes)
| Image fond | DALL-E 3 (optionnel) | ~$0.040 |
| **Total** | | **~$0.05 / video** |