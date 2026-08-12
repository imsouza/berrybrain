# BerryBrain Flashcards v1

Generate active-recall flashcards from the note.

Rules:

- clear questions;
- short but complete answers;
- no trivial questions;
- preservar termos tecnicos em ingles quando fizer sentido;
- prioritize concepts, relationships, and applications.

Formato esperado:

```json
{
  "flashcards": [
    {
      "question": "Question in English",
      "answer": "Answer in English",
      "difficulty": "medium",
      "topic": "Primary topic or concept in English"
    }
  ]
}

The `topic` field must be the concept, subject area, or category name in English (for example, "K-Means", "Linear Regression", or "Python Decorators"). Group flashcards by topic when possible.
```
