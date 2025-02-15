# Run

1. Install the dependencies

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_lg
```

2. Start the scraper
TODO: Add instructions

3. Generate the dataset for training

```bash
python ".\src\main\python\registration_asistant_ner\training_data\__init__.py" \
  ".\src\unittest\python\registration_asistant_ner_tests\training_data\resources\all_collected_data.jsonl .\src\unittest\python\registration_asistant_ner_tests\training_data\resources\dspace_files\" \
  ".\src\unittest\python\registration_asistant_ner_tests\training_data\resources\dspace_files\"
```

4. Train the model

```bash
python ".\src\main\python\registration_asistant_ner\training\__init__.py" \
  "<suffix>_training_data.spacy" \
  "<suffix>_test_data.spacy"
```

5. Evaluate the model

```bash
python ".\src\main\python\registration_asistant_ner\evaluation\__init__.py" \
  "<suffix>_test_data.spacy" \
  "<suffix>_model"
```

6. Run the model

```bash
python ".\src\main\python\registration_asistant_ner\__init__.py" \
  "<suffix>_model"
```